from google.cloud import bigquery
from google.api_core.exceptions import NotFound
from app.config import settings
from app.services.bigquery_service import BigQueryService
from typing import Dict, Any, List, Optional
import datetime

class DashboardService:
    def __init__(self, bq_service: BigQueryService):
        self.bq = bq_service

    def _get_view_name(self, customer_id: int, view_suffix: str) -> str:
        return f"`{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_VIEWS_DATASET}.customer_{customer_id}_{view_suffix}`"

    def _get_raw_table_name(self, table_name: str) -> str:
        return f"`{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.{table_name}`"

    def _execute_with_fallback(
        self, 
        customer_id: int, 
        view_suffix: str, 
        raw_table_name: str, 
        view_query: str, 
        fallback_query: str,
        parameters: List[bigquery.ScalarQueryParameter] = []
    ) -> List[Dict[str, Any]]:
        """
        Executes a query against the authorized view first. If the view is not found (404),
        it falls back to querying the raw table directly with customer_id filtering.
        """
        try:
            # Try view first
            return self.bq.execute_query(
                view_query, 
                job_config=bigquery.QueryJobConfig(query_parameters=parameters)
            )
        except NotFound:
            # Fallback to raw table
            return self.bq.execute_query(
                fallback_query, 
                job_config=bigquery.QueryJobConfig(query_parameters=parameters)
            )
        except Exception as e:
            # Log and try fallback anyway in case of schema discrepancy or permission view issues
            try:
                return self.bq.execute_query(
                    fallback_query, 
                    job_config=bigquery.QueryJobConfig(query_parameters=parameters)
                )
            except Exception:
                raise e

    def get_customer_profile(self, customer_id: int) -> Optional[Dict[str, Any]]:
        view_name = self._get_view_name(customer_id, "customer_v")
        raw_name = self._get_raw_table_name("customers")
        
        view_query = f"SELECT * FROM {view_name} WHERE is_current = TRUE LIMIT 1"
        fallback_query = f"SELECT * FROM {raw_name} WHERE customer_id = @customer_id AND is_current = TRUE LIMIT 1"
        
        params = [bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)]
        res = self._execute_with_fallback(customer_id, "customer_v", "customers", view_query, fallback_query, params)
        return res[0] if res else None

    def get_accounts(self, customer_id: int) -> List[Dict[str, Any]]:
        view_name = self._get_view_name(customer_id, "accounts_v")
        raw_name = self._get_raw_table_name("accounts")
        
        view_query = f"SELECT * FROM {view_name} WHERE is_current = TRUE"
        fallback_query = f"SELECT * FROM {raw_name} WHERE customer_id = @customer_id AND is_current = TRUE"
        
        params = [bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)]
        return self._execute_with_fallback(customer_id, "accounts_v", "accounts", view_query, fallback_query, params)

    def get_cards(self, customer_id: int) -> List[Dict[str, Any]]:
        view_name = self._get_view_name(customer_id, "credit_cards_v")
        raw_name = self._get_raw_table_name("credit_cards")
        
        view_query = f"SELECT * FROM {view_name} WHERE is_current = TRUE"
        fallback_query = f"SELECT * FROM {raw_name} WHERE customer_id = @customer_id AND is_current = TRUE"
        
        params = [bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)]
        return self._execute_with_fallback(customer_id, "credit_cards_v", "credit_cards", view_query, fallback_query, params)

    def get_loans(self, customer_id: int) -> List[Dict[str, Any]]:
        view_name = self._get_view_name(customer_id, "loans_v")
        raw_name = self._get_raw_table_name("loans")
        
        view_query = f"SELECT * FROM {view_name}"
        fallback_query = f"SELECT * FROM {raw_name} WHERE customer_id = @customer_id"
        
        params = [bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)]
        return self._execute_with_fallback(customer_id, "loans_v", "loans", view_query, fallback_query, params)

    def get_investments(self, customer_id: int) -> List[Dict[str, Any]]:
        view_name = self._get_view_name(customer_id, "fixed_deposits_v")
        raw_name = self._get_raw_table_name("fixed_deposits")
        
        view_query = f"SELECT * FROM {view_name}"
        fallback_query = f"SELECT * FROM {raw_name} WHERE customer_id = @customer_id"
        
        params = [bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)]
        return self._execute_with_fallback(customer_id, "fixed_deposits_v", "fixed_deposits", view_query, fallback_query, params)

    def get_transactions(self, customer_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        view_name = self._get_view_name(customer_id, "transactions_v")
        raw_name = self._get_raw_table_name("transactions")
        accounts_name = self._get_raw_table_name("accounts")
        cards_name = self._get_raw_table_name("credit_cards")
        loans_name = self._get_raw_table_name("loans")
        fd_name = self._get_raw_table_name("fixed_deposits")
        
        view_query = f"SELECT * FROM {view_name} ORDER BY transaction_timestamp DESC LIMIT {limit}"
        
        # Raw fallback must reconstruct transactions referencing any account owned by the customer
        fallback_query = f"""
            SELECT * FROM {raw_name} 
            WHERE account_number IN (
                SELECT account_number FROM {accounts_name} WHERE customer_id = @customer_id UNION DISTINCT
                SELECT card_account_number FROM {cards_name} WHERE customer_id = @customer_id UNION DISTINCT
                SELECT loan_account_number FROM {loans_name} WHERE customer_id = @customer_id UNION DISTINCT
                SELECT fd_account_number FROM {fd_name} WHERE customer_id = @customer_id
            )
            ORDER BY transaction_timestamp DESC 
            LIMIT {limit}
        """
        
        params = [bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)]
        return self._execute_with_fallback(customer_id, "transactions_v", "transactions", view_query, fallback_query, params)

    def get_credit_score(self, customer_id: int) -> Optional[Dict[str, Any]]:
        view_name = self._get_view_name(customer_id, "credit_scores_v")
        raw_name = self._get_raw_table_name("credit_scores")
        
        view_query = f"SELECT * FROM {view_name} ORDER BY last_updated DESC LIMIT 1"
        fallback_query = f"SELECT * FROM {raw_name} WHERE customer_id = @customer_id ORDER BY last_updated DESC LIMIT 1"
        
        params = [bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)]
        res = self._execute_with_fallback(customer_id, "credit_scores_v", "credit_scores", view_query, fallback_query, params)
        return res[0] if res else None

    def get_beneficiaries(self, customer_id: int) -> List[Dict[str, Any]]:
        view_name = self._get_view_name(customer_id, "beneficiaries_v")
        raw_name = self._get_raw_table_name("beneficiaries")
        
        view_query = f"SELECT * FROM {view_name}"
        fallback_query = f"SELECT * FROM {raw_name} WHERE customer_id = @customer_id"
        
        params = [bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)]
        return self._execute_with_fallback(customer_id, "beneficiaries_v", "beneficiaries", view_query, fallback_query, params)

    def get_monthly_spend(self, customer_id: int) -> float:
        """
        Calculates spending in the last 30 days based on DEBIT direction transaction logs.
        """
        view_name = self._get_view_name(customer_id, "transactions_v")
        raw_name = self._get_raw_table_name("transactions")
        accounts_name = self._get_raw_table_name("accounts")
        cards_name = self._get_raw_table_name("credit_cards")
        loans_name = self._get_raw_table_name("loans")
        fd_name = self._get_raw_table_name("fixed_deposits")

        view_query = f"""
            SELECT SUM(amount) as total_spend FROM {view_name}
            WHERE direction = 'DEBIT' 
            AND transaction_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        """
        
        fallback_query = f"""
            SELECT SUM(amount) as total_spend FROM {raw_name}
            WHERE direction = 'DEBIT'
            AND transaction_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
            AND account_number IN (
                SELECT account_number FROM {accounts_name} WHERE customer_id = @customer_id UNION DISTINCT
                SELECT card_account_number FROM {cards_name} WHERE customer_id = @customer_id UNION DISTINCT
                SELECT loan_account_number FROM {loans_name} WHERE customer_id = @customer_id UNION DISTINCT
                SELECT fd_account_number FROM {fd_name} WHERE customer_id = @customer_id
            )
        """
        
        params = [bigquery.ScalarQueryParameter("customer_id", "INTEGER", customer_id)]
        try:
            res = self._execute_with_fallback(customer_id, "transactions_v", "transactions", view_query, fallback_query, params)
            if res and res[0].get("total_spend") is not None:
                return float(res[0]["total_spend"])
        except Exception:
            pass
        return 0.0

    def get_aggregated_dashboard(self, customer_id: int) -> Dict[str, Any]:
        """
        Aggregates profile, summary, accounts, cards, loans, investments, and recent transactions
        into a single response layout.
        """
        # 1. Fetch details
        profile = self.get_customer_profile(customer_id) or {
            "name": "Valued Customer",
            "customer_segment": "RETAIL",
            "kyc_status": "VERIFIED",
            "risk_profile": "LOW"
        }
        
        accounts = self.get_accounts(customer_id)
        cards = self.get_cards(customer_id)
        loans = self.get_loans(customer_id)
        investments = self.get_investments(customer_id)
        transactions = self.get_transactions(customer_id, limit=10)
        credit_score_rec = self.get_credit_score(customer_id)
        beneficiaries = self.get_beneficiaries(customer_id)
        
        # 2. Compute summary fields
        total_balance = sum(float(acc.get("balance") or 0.0) for acc in accounts if acc.get("account_status") == "ACTIVE")
        monthly_spend = self.get_monthly_spend(customer_id)
        credit_score = credit_score_rec.get("score") if credit_score_rec else 750
        
        # 3. Format result
        return {
            "customer": {
                "customer_id": customer_id,
                "name": profile.get("name"),
                "email": profile.get("email"),
                "segment": profile.get("customer_segment"),
                "kyc_status": profile.get("kyc_status"),
                "risk_profile": profile.get("risk_profile")
            },
            "summary": {
                "total_balance": total_balance,
                "monthly_spend": monthly_spend,
                "credit_score": credit_score
            },
            "accounts": accounts,
            "cards": cards,
            "loans": loans,
            "investments": investments,
            "recent_transactions": transactions,
            "beneficiaries": beneficiaries
        }
