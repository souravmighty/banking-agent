from google.cloud import bigquery
from app.config import settings
from typing import List, Dict, Any, Optional

class BigQueryService:
    def __init__(self):
        self.client = bigquery.Client(project=settings.GOOGLE_CLOUD_PROJECT)

    def execute_query(self, query: str, job_config: bigquery.QueryJobConfig = None) -> List[Dict[str, Any]]:
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        return [dict(row) for row in results]
