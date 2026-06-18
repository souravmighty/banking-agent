from app.services.bigquery_service import BigQueryService
from app.config import settings
from google.cloud import bigquery
from typing import Optional, Dict, Any

class IdentityRepository:
    def __init__(self, bq_service: BigQueryService):
        self.bq = bq_service
        self.table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.customer_identity_mapping"

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        query = f"SELECT customer_id, email_id, firebase_uid FROM `{self.table}` WHERE email_id = @email"
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", email)]
        )
        results = self.bq.execute_query(query, job_config=job_config)
        return results[0] if results else None

    def get_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        query = f"SELECT customer_id, email_id, firebase_uid FROM `{self.table}` WHERE firebase_uid = @uid"
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("uid", "STRING", uid)]
        )
        results = self.bq.execute_query(query, job_config=job_config)
        return results[0] if results else None

    def update_firebase_uid(self, customer_id: int, uid: str, status: str, linked_at: str):
        query = f"""
            UPDATE `{self.table}` 
            SET firebase_uid = @uid, 
                registration_status = @status,
                linked_at = @linked_at
            WHERE customer_id = @customer_id
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("uid", "STRING", uid),
                bigquery.ScalarQueryParameter("status", "STRING", status),
                bigquery.ScalarQueryParameter("linked_at", "TIMESTAMP", linked_at),
                bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)
            ]
        )
        self.bq.execute_query(query, job_config=job_config)
