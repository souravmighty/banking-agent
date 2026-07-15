from app.services.bigquery_service import BigQueryService
from app.config import settings
from google.cloud import bigquery
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid

class DemoRepository:
    def __init__(self, bq_service: BigQueryService):
        self.bq = bq_service
        self.demo_dataset = f"{settings.GOOGLE_CLOUD_PROJECT}.customer_identity"
        self.demo_customers_table = f"{self.demo_dataset}.demo_customers"
        self.demo_audit_table = f"{self.demo_dataset}.demo_customer_audit"
        self.demo_requests_table = f"{self.demo_dataset}.demo_requests"
        self.customers_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.customers"
        self.mapping_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.customer_identity_mapping"

    def get_available_demo_customer(self) -> Optional[Dict[str, Any]]:
        query = f"""
            SELECT * FROM `{self.demo_customers_table}`
            WHERE status = 'AVAILABLE'
            ORDER BY customer_id
            LIMIT 1
        """
        results = self.bq.execute_query(query)
        return results[0] if results else None

    def get_by_demo_email(self, email: str) -> Optional[Dict[str, Any]]:
        query = f"""
            SELECT * FROM `{self.demo_customers_table}`
            WHERE LOWER(demo_email) = LOWER(@email)
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", email)]
        )
        results = self.bq.execute_query(query, job_config=job_config)
        return results[0] if results else None

    def get_by_customer_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        query = f"""
            SELECT * FROM `{self.demo_customers_table}`
            WHERE customer_id = @customer_id
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id)]
        )
        results = self.bq.execute_query(query, job_config=job_config)
        return results[0] if results else None

    def get_all_demo_customers(self) -> List[Dict[str, Any]]:
        query = f"""
            SELECT * FROM `{self.demo_customers_table}`
            ORDER BY customer_id
        """
        return self.bq.execute_query(query)

    def is_email_allocated(self, email: str) -> bool:
        query = f"""
            SELECT COUNT(*) as cnt FROM `{self.demo_customers_table}`
            WHERE LOWER(demo_email) = LOWER(@email) AND status IN ('APPROVED', 'ACTIVE')
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", email)]
        )
        results = self.bq.execute_query(query, job_config=job_config)
        return results[0]["cnt"] > 0 if results else False

    def allocate_customer(
        self, 
        customer_id: str, 
        demo_name: str, 
        demo_email: str, 
        allocated_by: str, 
        expires_at: str
    ) -> bool:
        """
        Perform transactional updates to allocate a demo customer.
        Updates demo_customers, customers, and customer_identity_mapping in a single transaction.
        """
        # Formulate a multi-statement transaction in BigQuery for atomic state update
        txn_query = f"""
            DECLARE is_avail INT64;
            BEGIN TRANSACTION;
            
            -- 1. Ensure the demo customer is still AVAILABLE
            SET is_avail = (
                SELECT COUNT(*) FROM `{self.demo_customers_table}`
                WHERE customer_id = @customer_id AND status = 'AVAILABLE'
            );

            
            IF is_avail = 0 THEN
                ROLLBACK TRANSACTION;
                SELECT FALSE as success;
            ELSE
                -- 2. Update demo_customers
                UPDATE `{self.demo_customers_table}`
                SET demo_name = @demo_name,
                    demo_email = @demo_email,
                    status = 'APPROVED',
                    allocated_at = CURRENT_TIMESTAMP(),
                    expires_at = TIMESTAMP(@expires_at),
                    allocated_by = @allocated_by,
                    remarks = 'Allocated via demo request service'
                WHERE customer_id = @customer_id;
                
                -- 3. Update customers table (overwrite original info with demo info)
                UPDATE `{self.customers_table}`
                SET name = @demo_name,
                    email = @demo_email
                WHERE customer_id = CAST(@customer_id AS INT64) AND is_current = TRUE;
                
                -- 4. Update customer_identity_mapping to reset registration status
                UPDATE `{self.mapping_table}`
                SET email_id = @demo_email,
                    firebase_uid = NULL,
                    registration_status = 'NOT REGISTERED',
                    linked_at = NULL
                WHERE customer_id = CAST(@customer_id AS INT64);
                
                COMMIT TRANSACTION;
                SELECT TRUE as success;
            END IF;
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id),
                bigquery.ScalarQueryParameter("demo_name", "STRING", demo_name),
                bigquery.ScalarQueryParameter("demo_email", "STRING", demo_email),
                bigquery.ScalarQueryParameter("allocated_by", "STRING", allocated_by),
                bigquery.ScalarQueryParameter("expires_at", "STRING", expires_at),
            ]
        )
        try:
            results = self.bq.execute_query(txn_query, job_config=job_config)
            return results[0]["success"] if results else False
        except Exception as e:
            # If transaction fails, return False
            print(f"Transaction failed during allocation: {e}")
            return False

    def release_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Transactional release of a demo customer.
        Restores customers table and customer_identity_mapping table, and resets demo_customers table.
        """
        # Fetch the original demo details first to restore them
        demo_cust = self.get_by_customer_id(customer_id)
        if not demo_cust:
            return None

        original_name = demo_cust["original_name"]
        original_email = demo_cust["original_email"]

        txn_query = f"""
            BEGIN TRANSACTION;
            
            -- 1. Restore customers table
            UPDATE `{self.customers_table}`
            SET name = @original_name,
                email = @original_email
            WHERE customer_id = CAST(@customer_id AS INT64) AND is_current = TRUE;
            
            -- 2. Restore customer_identity_mapping table
            UPDATE `{self.mapping_table}`
            SET email_id = @original_email,
                firebase_uid = NULL,
                registration_status = 'NOT REGISTERED',
                linked_at = NULL
            WHERE customer_id = CAST(@customer_id AS INT64);
            
            -- 3. Reset demo_customers table
            UPDATE `{self.demo_customers_table}`
            SET demo_name = NULL,
                demo_email = NULL,
                firebase_uid = NULL,
                status = 'AVAILABLE',
                released_at = CURRENT_TIMESTAMP(),
                allocated_at = NULL,
                expires_at = NULL,
                allocated_by = NULL,
                remarks = 'Released via demo release service'
            WHERE customer_id = @customer_id;
            
            COMMIT TRANSACTION;
            SELECT TRUE as success;
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id),
                bigquery.ScalarQueryParameter("original_name", "STRING", original_name),
                bigquery.ScalarQueryParameter("original_email", "STRING", original_email),
            ]
        )
        try:
            results = self.bq.execute_query(txn_query, job_config=job_config)
            if results and results[0]["success"]:
                return demo_cust
        except Exception as e:
            print(f"Transaction failed during release: {e}")
        return None

    def update_status_to_active(self, customer_id: str, firebase_uid: str) -> bool:
        query = f"""
            UPDATE `{self.demo_customers_table}`
            SET firebase_uid = @firebase_uid,
                status = 'ACTIVE'
            WHERE customer_id = @customer_id
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("firebase_uid", "STRING", firebase_uid),
                bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id),
            ]
        )
        try:
            self.bq.execute_query(query, job_config=job_config)
            return True
        except Exception as e:
            print(f"Failed to update demo_customers status to ACTIVE: {e}")
            return False

    def get_expired_allocations(self) -> List[Dict[str, Any]]:
        query = f"""
            SELECT * FROM `{self.demo_customers_table}`
            WHERE status IN ('APPROVED', 'ACTIVE') AND expires_at <= CURRENT_TIMESTAMP()
        """
        return self.bq.execute_query(query)

    def log_audit(
        self, 
        action: str, 
        customer_id: Optional[str] = None, 
        demo_email: Optional[str] = None, 
        firebase_uid: Optional[str] = None, 
        performed_by: Optional[str] = None, 
        remarks: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """
        Log an entry into customer_identity.demo_customer_audit.
        """
        query = f"""
            INSERT INTO `{self.demo_audit_table}` (
                timestamp, action, customer_id, demo_email, firebase_uid, performed_by, remarks, request_id
            ) VALUES (
                CURRENT_TIMESTAMP(), @action, @customer_id, @demo_email, @firebase_uid, @performed_by, @remarks, @request_id
            )
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("action", "STRING", action),
                bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id),
                bigquery.ScalarQueryParameter("demo_email", "STRING", demo_email),
                bigquery.ScalarQueryParameter("firebase_uid", "STRING", firebase_uid),
                bigquery.ScalarQueryParameter("performed_by", "STRING", performed_by),
                bigquery.ScalarQueryParameter("remarks", "STRING", remarks),
                bigquery.ScalarQueryParameter("request_id", "STRING", request_id),
            ]
        )
        try:
            self.bq.execute_query(query, job_config=job_config)
        except Exception as e:
            print(f"Failed to insert audit record: {e}")

    def create_demo_request(
        self,
        name: str,
        email: str,
        company: Optional[str] = None,
        role: Optional[str] = None,
        linkedin: Optional[str] = None,
        purpose: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a new demo request record with status PENDING.
        """
        request_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        
        query = f"""
            INSERT INTO `{self.demo_requests_table}` (
                request_id, name, email, company, role, linkedin, purpose, status, created_at
            ) VALUES (
                @request_id, @name, @email, @company, @role, @linkedin, @purpose, 'PENDING', TIMESTAMP(@created_at)
            )
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("request_id", "STRING", request_id),
                bigquery.ScalarQueryParameter("name", "STRING", name),
                bigquery.ScalarQueryParameter("email", "STRING", email),
                bigquery.ScalarQueryParameter("company", "STRING", company),
                bigquery.ScalarQueryParameter("role", "STRING", role),
                bigquery.ScalarQueryParameter("linkedin", "STRING", linkedin),
                bigquery.ScalarQueryParameter("purpose", "STRING", purpose),
                bigquery.ScalarQueryParameter("created_at", "STRING", created_at),
            ]
        )
        self.bq.execute_query(query, job_config=job_config)
        
        self.log_audit(
            action="Demo Requested",
            demo_email=email,
            performed_by="Public User",
            remarks=f"Demo request submitted by {name} ({email})",
            request_id=request_id
        )
        
        return {
            "request_id": request_id,
            "name": name,
            "email": email,
            "company": company,
            "role": role,
            "linkedin": linkedin,
            "purpose": purpose,
            "status": "PENDING",
            "created_at": created_at
        }

    def get_demo_request_by_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        query = f"SELECT * FROM `{self.demo_requests_table}` WHERE request_id = @request_id LIMIT 1"
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("request_id", "STRING", request_id)]
        )
        results = self.bq.execute_query(query, job_config=job_config)
        return results[0] if results else None

    def get_all_demo_requests(self) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM `{self.demo_requests_table}` ORDER BY created_at DESC"
        return self.bq.execute_query(query)

    def is_email_active_or_pending(self, email: str) -> bool:
        """
        Check if an email has a pending or active/allocated demo request.
        """
        query = f"""
            SELECT COUNT(*) as cnt FROM `{self.demo_requests_table}`
            WHERE LOWER(email) = LOWER(@email) AND status IN ('PENDING', 'APPROVED', 'ALLOCATED')
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", email)]
        )
        results = self.bq.execute_query(query, job_config=job_config)
        has_active_request = results[0]["cnt"] > 0 if results else False
        
        # Also check if it's currently allocated in demo_customers
        has_active_allocation = self.is_email_allocated(email)
        
        return has_active_request or has_active_allocation

    def update_demo_request_status(
        self,
        request_id: str,
        status: str,
        approved_by: Optional[str] = None,
        remarks: Optional[str] = None,
        customer_id: Optional[str] = None,
        expires_at: Optional[str] = None
    ) -> bool:
        """
        Updates the status and other fields of a demo request.
        """
        updated_at = datetime.now(timezone.utc).isoformat()
        query = f"""
            UPDATE `{self.demo_requests_table}`
            SET status = @status,
                approved_by = COALESCE(@approved_by, approved_by),
                remarks = COALESCE(@remarks, remarks),
                customer_id = COALESCE(@customer_id, customer_id),
                expires_at = COALESCE(TIMESTAMP(@expires_at), expires_at),
                updated_at = TIMESTAMP(@updated_at)
            WHERE request_id = @request_id
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("status", "STRING", status),
                bigquery.ScalarQueryParameter("approved_by", "STRING", approved_by),
                bigquery.ScalarQueryParameter("remarks", "STRING", remarks),
                bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id),
                bigquery.ScalarQueryParameter("expires_at", "STRING", expires_at),
                bigquery.ScalarQueryParameter("updated_at", "STRING", updated_at),
                bigquery.ScalarQueryParameter("request_id", "STRING", request_id),
            ]
        )
        try:
            self.bq.execute_query(query, job_config=job_config)
            return True
        except Exception as e:
            print(f"Failed to update demo request status: {e}")
            return False

    def update_request_by_customer_id(self, customer_id: str, status: str, remarks: Optional[str] = None) -> bool:
        """
        Updates the status of a demo request by customer_id (e.g. when released or expired).
        """
        updated_at = datetime.now(timezone.utc).isoformat()
        query = f"""
            UPDATE `{self.demo_requests_table}`
            SET status = @status,
                remarks = COALESCE(@remarks, remarks),
                updated_at = TIMESTAMP(@updated_at)
            WHERE customer_id = @customer_id AND status = 'ALLOCATED'
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("status", "STRING", status),
                bigquery.ScalarQueryParameter("remarks", "STRING", remarks),
                bigquery.ScalarQueryParameter("updated_at", "STRING", updated_at),
                bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id),
            ]
        )
        try:
            self.bq.execute_query(query, job_config=job_config)
            return True
        except Exception as e:
            print(f"Failed to update demo request by customer ID: {e}")
            return False

    def get_dashboard_summary(self) -> Dict[str, int]:
        """
        Retrieves summary metrics for dashboard cards.
        """
        query = f"""
            SELECT
              (SELECT COUNT(*) FROM `{self.demo_requests_table}` WHERE status = 'PENDING') as pending_requests,
              (SELECT COUNT(*) FROM `{self.demo_customers_table}` WHERE status IN ('APPROVED', 'ACTIVE')) as allocated_customers,
              (SELECT COUNT(*) FROM `{self.demo_customers_table}` WHERE status = 'AVAILABLE') as available_customers,
              (SELECT COUNT(*) FROM `{self.demo_requests_table}` WHERE status = 'EXPIRED' AND DATE(updated_at, 'UTC') = CURRENT_DATE('UTC')) as expired_today
        """
        results = self.bq.execute_query(query)
        if results:
            row = results[0]
            return {
                "pending_requests": int(row.get("pending_requests", 0)),
                "allocated_customers": int(row.get("allocated_customers", 0)),
                "available_customers": int(row.get("available_customers", 0)),
                "expired_today": int(row.get("expired_today", 0))
            }
        return {
            "pending_requests": 0,
            "allocated_customers": 0,
            "available_customers": 0,
            "expired_today": 0
        }
