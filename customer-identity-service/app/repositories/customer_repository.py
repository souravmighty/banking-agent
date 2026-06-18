from app.services.bigquery_service import BigQueryService
from app.config import settings
from google.cloud import bigquery
from typing import Optional, Dict, Any, List

class CustomerRepository:
    def __init__(self, bq_service: BigQueryService):
        self.bq = bq_service
        self.customers_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.customers"
        self.accounts_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.accounts"
        self.credit_cards_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.credit_cards"
        self.fixed_deposits_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.fixed_deposits"
        self.loans_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.loans"
        self.beneficiaries_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.beneficiaries"

    def get_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        query = f"SELECT * FROM `{self.customers_table}` WHERE customer_id = @customer_id"
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)]
        )
        results = self.bq.execute_query(query, job_config=job_config)
        return results[0] if results else None

    def get_accounts(self, customer_id: int) -> List[Dict[str, Any]]:
        query = f"SELECT account_number, account_type, account_status FROM `{self.accounts_table}` WHERE customer_id = @customer_id"
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)]
        )
        return self.bq.execute_query(query, job_config=job_config)

    def get_credit_cards(self, customer_id: int) -> List[Dict[str, Any]]:
        query = f"SELECT card_account_number, 'Credit Card' as account_type, status as account_status FROM `{self.credit_cards_table}` WHERE customer_id = @customer_id"
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)]
        )
        return self.bq.execute_query(query, job_config=job_config)

    def get_fixed_deposits(self, customer_id: int) -> List[Dict[str, Any]]:
        query = f"SELECT fd_account_number, 'Fixed Deposit' as account_type, status as account_status FROM `{self.fixed_deposits_table}` WHERE customer_id = @customer_id"
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)]
        )
        return self.bq.execute_query(query, job_config=job_config)

    def get_loans(self, customer_id: int) -> List[Dict[str, Any]]:
        query = f"SELECT loan_account_number, loan_type as account_type, status as account_status FROM `{self.loans_table}` WHERE customer_id = @customer_id"
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)]
        )
        return self.bq.execute_query(query, job_config=job_config)
    
    def get_beneficiaries(self, customer_id: int) -> List[Dict[str, Any]]:
        query = f"SELECT beneficiary_id, beneficiary_name, beneficiary_account_number, bank_name, ifsc_code, status FROM `{self.beneficiaries_table}` WHERE customer_id = @customer_id"
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)]
        )
        return self.bq.execute_query(query, job_config=job_config)
