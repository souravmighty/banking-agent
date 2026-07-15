from app.repositories.demo_repository import DemoRepository
from app.services.view_service import ViewService
from app.utils.exceptions import CustomerIdentityException
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class DemoService:
    def __init__(self, demo_repo: DemoRepository, view_service: ViewService):
        self.demo_repo = demo_repo
        self.view_service = view_service

    def _send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> None:
        """
        Internal helper to dispatch emails. Uses Resend if API key is configured,
        otherwise falls back to console logs for local developer testing.
        """
        from app.config import settings
        
        # 1. Print cleaner fallback notification to console/logs regardless of delivery method
        print("\n" + "="*50)
        print(f"OUTBOX TRIGGERED FOR: {to_email}")
        print(f"SUBJECT: {subject}")
        print("-"*50)
        print(body)
        print("="*50 + "\n")
        
        # 2. Dispatch via Resend (Sole real-world delivery method)
        if settings.RESEND_API_KEY:
            try:
                import resend
                
                # Configure the API key on the global SDK client
                resend.api_key = settings.RESEND_API_KEY
                
                # Set reply_to to admin email
                reply_to_addr = settings.ADMIN_EMAIL or "souravmaiti1997@gmail.com"
                
                payload = {
                    "from": settings.EMAIL_FROM,
                    "to": [to_email],
                    "subject": subject,
                    "text": body,
                    "reply_to": reply_to_addr
                }
                
                if html_body:
                    payload["html"] = html_body
                
                # Dispatch the email using the official Emails interface
                resend.Emails.send(payload)
                
                logger.info(f"Email successfully sent via Resend Python SDK to {to_email}")
                return
            except Exception as e:
                logger.error(f"Failed to deliver email via Resend Python SDK: {e}")
        else:
            logger.info(f"Resend API key not configured. Logged email for {to_email} to console fallback.")

    def allocate_demo_customer(self, name: str, email: str, approved_by: str) -> Dict[str, Any]:
        """
        Allocates an available demo customer to the applicant.
        """
        # 1. Validate that the demo email is not already allocated
        if self.demo_repo.is_email_allocated(email):
            raise CustomerIdentityException(
                status_code=400,
                detail=f"The email {email} is already associated with an active or approved demo allocation."
            )

        # 2. Find an available demo customer
        available_customer = self.demo_repo.get_available_demo_customer()
        if not available_customer:
            raise CustomerIdentityException(
                status_code=400,
                detail="No demo customers are currently available in the pool. Please release or wait for an expiry."
            )

        customer_id = available_customer["customer_id"]
        
        # 3. Calculate expires_at (7 days from now)
        now = datetime.now(timezone.utc)
        expires_at_dt = now + timedelta(days=7)
        expires_at_str = expires_at_dt.isoformat()

        # 4. Perform transactional allocation
        success = self.demo_repo.allocate_customer(
            customer_id=customer_id,
            demo_name=name,
            demo_email=email,
            allocated_by=approved_by,
            expires_at=expires_at_str
        )

        if not success:
            raise CustomerIdentityException(
                status_code=500,
                detail="Failed to allocate demo customer due to concurrent modification or database error."
            )

        # 5. Log audit entries
        self.demo_repo.log_audit(
            action="Approval",
            customer_id=customer_id,
            demo_email=email,
            performed_by=approved_by,
            remarks=f"Demo approved for {name} ({email})"
        )
        self.demo_repo.log_audit(
            action="Allocation",
            customer_id=customer_id,
            demo_email=email,
            performed_by=approved_by,
            remarks=f"Allocated demo customer {customer_id} to {email}"
        )

        # 6. Send Approval Email (Log it to the output console & structured logging)
        expiry_formatted = expires_at_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        email_subject = "Your BankPilot Demo is Ready"
        email_body = f"""Hi {name},

Your request has been approved.

Login URL
https://bankpilot.souravmaiti.dev

Please sign in using Google using
{email}

Your access expires on
{expiry_formatted}

Thank you.

Sourav Maiti"""

        from app.utils.email_templates import get_approval_email_html
        html_body = get_approval_email_html(name, email, expiry_formatted)

        # Send Email using SMTP helper
        self._send_email(email, email_subject, email_body, html_body=html_body)

        return {
            "customer_id": int(customer_id),
            "expires_at": expires_at_str,
            "status": "APPROVED"
        }

    def release_demo_customer(self, customer_id: str, performed_by: str = "Admin", remarks: str = "Manual Release") -> Dict[str, Any]:
        """
        Releases a demo customer back into the pool.
        """
        # 1. Perform transactional database update
        released_cust = self.demo_repo.release_customer(customer_id)
        if not released_cust:
            raise CustomerIdentityException(
                status_code=404,
                detail=f"Demo customer with ID {customer_id} not found or cannot be released."
            )

        demo_email = released_cust.get("demo_email")
        firebase_uid = released_cust.get("firebase_uid")

        # Update corresponding request status in demo_requests to EXPIRED
        self.demo_repo.update_request_by_customer_id(customer_id, "EXPIRED", remarks=f"Released by {performed_by}")

        # 2. Delete BigQuery views associated with the customer
        deleted_views = []
        try:
            deleted_views = self.view_service.delete_authorized_views(int(customer_id))
            logger.info(f"Deleted BigQuery views for customer {customer_id}: {deleted_views}")
        except Exception as e:
            logger.error(f"Error deleting BigQuery views for customer {customer_id}: {e}")

        # 3. Log audit entry
        self.demo_repo.log_audit(
            action="Release",
            customer_id=customer_id,
            demo_email=demo_email,
            firebase_uid=firebase_uid,
            performed_by=performed_by,
            remarks=f"{remarks}. Views deleted: {len(deleted_views)}"
        )

        return {
            "customer_id": int(customer_id),
            "status": "AVAILABLE",
            "released_at": datetime.now(timezone.utc).isoformat(),
            "deleted_views_count": len(deleted_views)
        }

    def get_demo_status(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the demo allocation record for the specified email.
        """
        record = self.demo_repo.get_by_demo_email(email)
        if not record:
            raise CustomerIdentityException(
                status_code=404,
                detail=f"No demo customer allocation found for email {email}"
            )
        return {
            "demo_customer_id": record["demo_customer_id"],
            "customer_id": int(record["customer_id"]),
            "original_name": record["original_name"],
            "original_email": record["original_email"],
            "demo_name": record["demo_name"],
            "demo_email": record["demo_email"],
            "firebase_uid": record["firebase_uid"],
            "status": record["status"],
            "allocated_at": record["allocated_at"].isoformat() if record["allocated_at"] else None,
            "expires_at": record["expires_at"].isoformat() if record["expires_at"] else None,
            "released_at": record["released_at"].isoformat() if record["released_at"] else None,
            "allocated_by": record["allocated_by"],
            "remarks": record["remarks"]
        }

    def get_all_demo_customers(self) -> List[Dict[str, Any]]:
        """
        Lists all demo customers and their current allocation statuses.
        """
        records = self.demo_repo.get_all_demo_customers()
        transformed = []
        for r in records:
            transformed.append({
                "demo_customer_id": r["demo_customer_id"],
                "customer_id": int(r["customer_id"]),
                "original_name": r["original_name"],
                "original_email": r["original_email"],
                "demo_name": r["demo_name"],
                "demo_email": r["demo_email"],
                "firebase_uid": r["firebase_uid"],
                "status": r["status"],
                "allocated_at": r["allocated_at"].isoformat() if r["allocated_at"] else None,
                "expires_at": r["expires_at"].isoformat() if r["expires_at"] else None,
                "released_at": r["released_at"].isoformat() if r["released_at"] else None,
                "allocated_by": r["allocated_by"],
                "remarks": r["remarks"]
            })
        return transformed

    def release_expired_customers(self) -> List[int]:
        """
        Finds all APPROVED/ACTIVE demo allocations that have expired and releases them.
        """
        expired_allocations = self.demo_repo.get_expired_allocations()
        released_ids = []
        for alloc in expired_allocations:
            cust_id = alloc["customer_id"]
            try:
                self.release_demo_customer(
                    customer_id=cust_id,
                    performed_by="Scheduler",
                    remarks="Automatic Expiry"
                )
                released_ids.append(int(cust_id))
            except Exception as e:
                logger.error(f"Failed to auto-expire demo customer {cust_id}: {e}")
        return released_ids

    def submit_demo_request(
        self,
        name: str,
        email: str,
        company: Optional[str] = None,
        role: Optional[str] = None,
        linkedin: Optional[str] = None,
        purpose: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit a new demo request. Validates email is not already active or pending,
        and is not an existing pre-authorized retail bank customer.
        """
        # 1. Check if the email is an existing retail customer in customer_identity_mapping
        try:
            from app.repositories.identity_repository import IdentityRepository
            identity_repo = IdentityRepository(self.demo_repo.bq)
            existing_mapping = identity_repo.get_by_email(email)
            if existing_mapping:
                raise CustomerIdentityException(
                    status_code=400,
                    detail=f"The email {email} is already associated with an existing active bank customer. Please sign in directly."
                )
        except CustomerIdentityException:
            raise
        except Exception as e:
            logger.error(f"Error checking customer identity mapping table in submit_demo_request: {e}")

        # 2. Check if there is an active or pending demo request
        if self.demo_repo.is_email_active_or_pending(email):
            raise CustomerIdentityException(
                status_code=400,
                detail=f"The email {email} is already associated with an active or pending demo request."
            )
            
        request = self.demo_repo.create_demo_request(
            name=name,
            email=email,
            company=company,
            role=role,
            linkedin=linkedin,
            purpose=purpose
        )
        
        # Log to audit (already logged in repo, but let's log any service specifics here if needed)
        
        # Send New Demo Request Email to Admin/Staff (Printed to console as required)
        created_at_dt = datetime.fromisoformat(request["created_at"])
        requested_at_formatted = created_at_dt.strftime("%d %b %Y %H:%M")
        
        email_subject = "New BankPilot Demo Request"
        email_body = f"""New BankPilot Demo Request:

Name: {name}
Email: {email}
Company: {company or "N/A"}
Role: {role or "N/A"}
LinkedIn: {linkedin or "N/A"}
Purpose: {purpose or "N/A"}
Requested: {requested_at_formatted} UTC

Actions:
Review Dashboard: https://bankpilot.souravmaiti.dev/staff/demo-requests
Approve Request: https://bankpilot.souravmaiti.dev/staff/demo-requests/{request['request_id']}?action=approve
Reject Request: https://bankpilot.souravmaiti.dev/staff/demo-requests/{request['request_id']}?action=reject"""

        from app.utils.email_templates import get_admin_request_email_html
        html_body = get_admin_request_email_html(
            name=name,
            email=email,
            company=company,
            role=role,
            linkedin=linkedin,
            purpose=purpose,
            requested_at_formatted=requested_at_formatted,
            request_id=request["request_id"]
        )

        # Send New Demo Request Email to Admins/Staff configured in Settings
        from app.config import settings
        admin_source = settings.ADMIN_EMAIL or settings.ADMIN_EMAILS
        admin_emails = [email.strip() for email in admin_source.split(",") if email.strip()]
        for admin_email in admin_emails:
            self._send_email(admin_email, email_subject, email_body, html_body=html_body)
        
        return request

    def get_all_demo_requests(self) -> List[Dict[str, Any]]:
        records = self.demo_repo.get_all_demo_requests()
        transformed = []
        for r in records:
            transformed.append({
                "request_id": r["request_id"],
                "name": r["name"],
                "email": r["email"],
                "company": r["company"],
                "role": r["role"],
                "linkedin": r["linkedin"],
                "purpose": r["purpose"],
                "status": r["status"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
                "approved_by": r["approved_by"],
                "remarks": r["remarks"],
                "customer_id": r["customer_id"],
                "expires_at": r["expires_at"].isoformat() if r["expires_at"] else None,
            })
        return transformed

    def get_demo_request_by_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        r = self.demo_repo.get_demo_request_by_id(request_id)
        if not r:
            return None
        return {
            "request_id": r["request_id"],
            "name": r["name"],
            "email": r["email"],
            "company": r["company"],
            "role": r["role"],
            "linkedin": r["linkedin"],
            "purpose": r["purpose"],
            "status": r["status"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
            "approved_by": r["approved_by"],
            "remarks": r["remarks"],
            "customer_id": r["customer_id"],
            "expires_at": r["expires_at"].isoformat() if r["expires_at"] else None,
        }

    def approve_demo_request(self, request_id: str, approved_by: str) -> Dict[str, Any]:
        """
        Approves a demo request and allocates a customer. Idempotent.
        """
        req = self.demo_repo.get_demo_request_by_id(request_id)
        if not req:
            raise CustomerIdentityException(status_code=404, detail="Demo request not found.")
            
        if req["status"] == "ALLOCATED":
            return {
                "customer_id": int(req["customer_id"]),
                "expires_at": req["expires_at"].isoformat() if req["expires_at"] else None,
                "status": "ALLOCATED",
                "message": "Demo request was already approved and allocated."
            }
            
        if req["status"] == "REJECTED":
            raise CustomerIdentityException(
                status_code=400,
                detail="Cannot approve a previously rejected demo request."
            )
            
        # Allocate demo customer
        alloc_res = self.allocate_demo_customer(
            name=req["name"],
            email=req["email"],
            approved_by=approved_by
        )
        
        # Update demo requests status to ALLOCATED
        cust_id = str(alloc_res["customer_id"])
        expires_at = alloc_res["expires_at"]
        
        self.demo_repo.update_demo_request_status(
            request_id=request_id,
            status="ALLOCATED",
            approved_by=approved_by,
            customer_id=cust_id,
            expires_at=expires_at,
            remarks=f"Allocated customer {cust_id}"
        )
        
        # Log to audit (allocation is logged in allocate_demo_customer, let's log the Approval with request_id)
        self.demo_repo.log_audit(
            action="Approved",
            customer_id=cust_id,
            demo_email=req["email"],
            performed_by=approved_by,
            remarks=f"Request {request_id} approved and allocated to {cust_id}",
            request_id=request_id
        )
        
        return alloc_res

    def reject_demo_request(self, request_id: str, rejected_by: str, remarks: Optional[str] = None) -> Dict[str, Any]:
        """
        Rejects a demo request. Idempotent.
        """
        req = self.demo_repo.get_demo_request_by_id(request_id)
        if not req:
            raise CustomerIdentityException(status_code=404, detail="Demo request not found.")
            
        if req["status"] == "REJECTED":
            return {
                "status": "REJECTED",
                "message": "Demo request was already rejected."
            }
            
        if req["status"] == "ALLOCATED":
            raise CustomerIdentityException(
                status_code=400,
                detail="Cannot reject an already allocated demo request."
            )
            
        # Update request status to REJECTED
        remarks_str = remarks or "Request rejected by administrator"
        self.demo_repo.update_demo_request_status(
            request_id=request_id,
            status="REJECTED",
            approved_by=rejected_by,
            remarks=remarks_str
        )
        
        # Send Rejection Email (Printed to console as required)
        email_subject = "BankPilot Demo Request Update"
        email_body = f"""Hi {req['name']},

Thank you for your interest in BankPilot.

Unfortunately we are unable to approve your request at this time.

Thank you.

Sourav Maiti"""

        from app.utils.email_templates import get_rejection_email_html
        html_body = get_rejection_email_html(req['name'], req['email'])

        # Send Rejection Email using SMTP helper
        self._send_email(req['email'], email_subject, email_body, html_body=html_body)
        
        # Log to audit
        self.demo_repo.log_audit(
            action="Rejected",
            demo_email=req["email"],
            performed_by=rejected_by,
            remarks=remarks_str,
            request_id=request_id
        )
        
        return {
            "status": "REJECTED",
            "message": "Demo request rejected successfully."
        }

    def get_dashboard_summary(self) -> Dict[str, int]:
        return self.demo_repo.get_dashboard_summary()
