import time
from typing import Dict, Any, List, Optional
from app.config import settings
from app.services.bigquery_service import BigQueryService
from app.schemas.responses import (
    AnalyticsMetadataResponse,
    DatasetDetail,
    TableMetadataDetail,
    ViewMetadataDetail,
    FieldMetadata
)
from app.utils.logger import logger


# Curated catalog containing semantic metadata for operational tables and analytical views
OPERATIONAL_TABLES_CATALOG: Dict[str, Dict[str, Any]] = {
    "customers": {
        "primary_business_key": "customer_id",
        "grain": "One record per customer version (SCD Type 2)",
        "relationship_information": "customer_id joins to accounts, loans, credit_cards, fixed_deposits, credit_scores, beneficiaries.",
        "is_scd_type_2": True,
        "scd_columns": ["eff_start_ts", "eff_end_ts", "is_current", "record_version"],
        "ai_usage_guidance": "Use is_current = TRUE unless historical customer version analysis is explicitly requested.",
        "typical_ai_questions": [
            "How many active customers exist across different segments?",
            "What is the demographic breakdown of customers by region and state?",
            "Which customer occupation cohorts have the highest annual income?"
        ]
    },
    "accounts": {
        "primary_business_key": "account_number",
        "grain": "One record per account version (SCD Type 2)",
        "relationship_information": "Joined with customers via customer_id; joined with transactions via account_number.",
        "is_scd_type_2": True,
        "scd_columns": ["eff_start_ts", "eff_end_ts", "is_current", "record_version"],
        "ai_usage_guidance": "Use is_current = TRUE and account_status = 'ACTIVE' for current balance and active account queries.",
        "typical_ai_questions": [
            "What is the total deposit balance across SAVINGS and CURRENT accounts?",
            "How many active accounts does each customer segment hold on average?",
            "What is the average balance per account across branches?"
        ]
    },
    "transactions": {
        "primary_business_key": "transaction_id",
        "grain": "One record per banking financial transaction event",
        "relationship_information": "account_number links to accounts.account_number; transacting customer resolved via accounts.customer_id.",
        "is_scd_type_2": False,
        "scd_columns": [],
        "ai_usage_guidance": "For spending analysis, filter direction = 'DEBIT'. Use transaction_timestamp or DATE(transaction_timestamp) for temporal filtering.",
        "typical_ai_questions": [
            "What is the monthly debit spend trend over the last 6 months?",
            "Which merchant categories generate the highest debit transaction volume?",
            "What is the average transaction amount for Credit vs Debit?"
        ]
    },
    "credit_cards": {
        "primary_business_key": "card_account_number",
        "grain": "One record per credit card version (SCD Type 2)",
        "relationship_information": "customer_id joins with customers; card_account_number links to card transaction activity.",
        "is_scd_type_2": True,
        "scd_columns": ["eff_start_ts", "eff_end_ts", "is_current", "record_version"],
        "ai_usage_guidance": "Use is_current = TRUE and status = 'ACTIVE' for active credit card portfolio metrics.",
        "typical_ai_questions": [
            "What is the average credit limit and outstanding balance across card types (Platinum, Gold, Silver)?",
            "What is the credit card utilization rate by customer segment?"
        ]
    },
    "loans": {
        "primary_business_key": "loan_account_number",
        "grain": "One record per loan facility contract",
        "relationship_information": "customer_id joins with customers.customer_id.",
        "is_scd_type_2": False,
        "scd_columns": [],
        "ai_usage_guidance": "Filter status = 'ACTIVE' when calculating current loan portfolio outstanding balances and active borrowing counts.",
        "typical_ai_questions": [
            "What is the total outstanding loan principal by loan type (Home, Auto, Personal)?",
            "What is the average interest rate across loan products?"
        ]
    },
    "fixed_deposits": {
        "primary_business_key": "fd_account_number",
        "grain": "One record per fixed deposit contract",
        "relationship_information": "customer_id joins with customers.customer_id.",
        "is_scd_type_2": False,
        "scd_columns": [],
        "ai_usage_guidance": "Filter status = 'ACTIVE' to measure active locked deposit principal and interest liabilities.",
        "typical_ai_questions": [
            "What is the total principal amount locked in fixed deposits?",
            "What is the maturity distribution of active fixed deposits?"
        ]
    },
    "credit_scores": {
        "primary_business_key": "customer_id",
        "grain": "One record per customer credit bureau snapshot",
        "relationship_information": "customer_id joins with customers.customer_id.",
        "is_scd_type_2": False,
        "scd_columns": [],
        "ai_usage_guidance": "Use the latest score assessment (e.g. ORDER BY last_updated DESC) when evaluating creditworthiness.",
        "typical_ai_questions": [
            "What is the distribution of customer credit scores across risk profiles?",
            "What percentage of customers have a credit score above 750?"
        ]
    }
}

ANALYTICAL_VIEWS_CATALOG: Dict[str, Dict[str, Any]] = {
    "analytics_customer_360": {
        "primary_business_key": "customer_id",
        "grain": "One record per active customer",
        "relationship_information": "Curated 360 view joining customers, accounts, cards, loans, fixed deposits, and credit scores. Primary dimension for customer profiling.",
        "is_scd_type_2": False,
        "scd_columns": [],
        "ai_usage_guidance": "Preferred single-pane analytical source for customer-level profiling, holdings aggregation, and demographics. Underlying tables are pre-filtered for active and current records.",
        "typical_ai_questions": [
            "What is the total relationship balance and product count for High Value customers?",
            "What percentage of Wealth customers hold both a credit card and a loan?",
            "Which customer age cohorts hold the highest average deposit balance?",
            "What is the distribution of customers across lifecycle stages and risk segments?"
        ]
    },
    "analytics_customer_acquisition": {
        "primary_business_key": "acquisition_id",
        "grain": "One record per customer acquisition/onboarding event",
        "relationship_information": "Joined with analytics_customer_360 and customers via customer_id. Enriched with initial account funding balance.",
        "is_scd_type_2": False,
        "scd_columns": [],
        "ai_usage_guidance": "Use this view when analyzing how customers joined the bank, comparing channel effectiveness, or calculating customer acquisition cost (CAC) trends.",
        "typical_ai_questions": [
            "What is the total acquisition cost and volume by channel (Branch vs. Digital)?",
            "Which marketing channel produces customers with the highest initial deposit amount?",
            "How has customer onboarding volume grown month-over-month by segment?"
        ]
    },
    "analytics_transactions": {
        "primary_business_key": "transaction_id",
        "grain": "One record per enriched transaction",
        "relationship_information": "Sourced from transactions, enriched with accounts and customers dimensions. Linked to customer_id.",
        "is_scd_type_2": False,
        "scd_columns": [],
        "ai_usage_guidance": "Preferred source for transaction and spend analysis. For spend analysis, filter direction = 'DEBIT'. Use transaction_date or month for time slicing.",
        "typical_ai_questions": [
            "What is the total transaction volume and average spend by merchant category for Premium customers?",
            "How did debit transaction volume change between Q1 and Q2?",
            "Which geographic regions generate the highest transaction spend?"
        ]
    },
    "analytics_products": {
        "primary_business_key": "holding_id",
        "grain": "One record per customer product holding",
        "relationship_information": "Unioned view combining accounts, credit_cards, loans, and fixed_deposits, enriched with customer segment and geography.",
        "is_scd_type_2": False,
        "scd_columns": [],
        "ai_usage_guidance": "Use this view when asked about how many products customers hold, which product lines are growing fastest, or product penetration by customer segment.",
        "typical_ai_questions": [
            "What is the total number of active product holdings across SAVINGS, CREDIT_CARD, and LOAN categories?",
            "Which customer segment has the highest proportion of credit card holders?",
            "How many new product holdings were opened per month by product type?"
        ]
    },
    "analytics_balances": {
        "primary_business_key": "snapshot_id",
        "grain": "One record per account daily balance snapshot",
        "relationship_information": "Sourced from active records in accounts, joined with customers for demographic segmentation.",
        "is_scd_type_2": False,
        "scd_columns": [],
        "ai_usage_guidance": "Preferred source for calculating total deposit balances, account-level balance distributions, and customer liquidity metrics.",
        "typical_ai_questions": [
            "What is the total and average savings account balance by customer segment?",
            "Which branch regions have the highest concentration of high-balance accounts?",
            "What is the distribution of deposit balances across Wealth vs. Retail customer tiers?"
        ]
    }
}


class AnalyticsMetadataService:
    def __init__(self, bq_service: BigQueryService):
        self.bq = bq_service
        self._cached_response: Optional[AnalyticsMetadataResponse] = None
        self._cache_timestamp: float = 0.0

    def invalidate_cache(self) -> None:
        """Explicitly invalidates the cached analytics metadata response."""
        self._cached_response = None
        self._cache_timestamp = 0.0
        logger.info("Analytics metadata service cache invalidated.")

    def get_allowed_tables(self) -> List[str]:
        raw = getattr(settings, "ANALYTICS_ALLOWED_TABLES", "customers,accounts,transactions,credit_cards,loans,fixed_deposits,credit_scores")
        return [t.strip() for t in raw.split(",") if t.strip()]

    def get_allowed_views(self) -> List[str]:
        raw = getattr(settings, "ANALYTICS_ALLOWED_VIEWS", "analytics_customer_360,analytics_customer_acquisition,analytics_transactions,analytics_products,analytics_balances")
        return [v.strip() for v in raw.split(",") if v.strip()]

    def get_analytics_metadata(self) -> AnalyticsMetadataResponse:
        """
        Retrieves curated analytics metadata for approved tables and views.
        Uses in-memory caching with configurable TTL.
        """
        current_time = time.time()
        ttl = getattr(settings, "ANALYTICS_METADATA_CACHE_TTL_SECONDS", 3600)

        if self._cached_response and (current_time - self._cache_timestamp) < ttl:
            return self._cached_response

        project_id = settings.GOOGLE_CLOUD_PROJECT
        banking_dataset_id = settings.BIGQUERY_DATASET
        analytics_dataset_id = getattr(settings, "BIGQUERY_ANALYTICS_DATASET", "analytics")

        allowed_tables = self.get_allowed_tables()
        allowed_views = self.get_allowed_views()

        # 1. Build operational tables dictionary
        tables_dict: Dict[str, TableMetadataDetail] = {}
        for tbl in allowed_tables:
            full_table_name = f"{project_id}.{banking_dataset_id}.{tbl}"
            catalog_meta = OPERATIONAL_TABLES_CATALOG.get(tbl, {})

            # Retrieve schema and descriptions from BigQuery
            bq_meta = self.bq.get_table_metadata(banking_dataset_id, tbl)
            table_desc = bq_meta.get("table_description") or catalog_meta.get("table_description") or f"Operational table for {tbl}."

            fields = [
                FieldMetadata(
                    column_name=f["name"],
                    type=f["type"],
                    description=f.get("description") or "",
                    mode=f.get("mode") or ("NULLABLE" if f.get("is_nullable", True) else "REQUIRED")
                )
                for f in bq_meta.get("fields", [])
            ]

            is_scd = catalog_meta.get("is_scd_type_2", False)
            scd_cols = catalog_meta.get("scd_columns", ["eff_start_ts", "eff_end_ts", "is_current", "record_version"] if is_scd else [])

            tables_dict[full_table_name] = TableMetadataDetail(
                table_name=full_table_name,
                query_object=full_table_name,
                logical_name=tbl,
                object_type="TABLE",
                table_description=table_desc,
                primary_business_key=catalog_meta.get("primary_business_key"),
                grain=catalog_meta.get("grain"),
                relationship_information=catalog_meta.get("relationship_information"),
                is_scd_type_2=is_scd,
                scd_columns=scd_cols,
                ai_usage_guidance=catalog_meta.get("ai_usage_guidance"),
                typical_ai_questions=catalog_meta.get("typical_ai_questions"),
                schema=fields
            )

        # 2. Build analytical views dictionary
        views_dict: Dict[str, ViewMetadataDetail] = {}
        for view_name in allowed_views:
            full_view_name = f"{project_id}.{analytics_dataset_id}.{view_name}"
            catalog_meta = ANALYTICAL_VIEWS_CATALOG.get(view_name, {})

            # Retrieve schema and descriptions from BigQuery
            bq_meta = self.bq.get_table_metadata(analytics_dataset_id, view_name)
            view_desc = bq_meta.get("table_description") or catalog_meta.get("table_description") or f"Analytical view for {view_name}."

            fields = [
                FieldMetadata(
                    column_name=f["name"],
                    type=f["type"],
                    description=f.get("description") or "",
                    mode=f.get("mode") or ("NULLABLE" if f.get("is_nullable", True) else "REQUIRED")
                )
                for f in bq_meta.get("fields", [])
            ]

            views_dict[full_view_name] = ViewMetadataDetail(
                view_name=full_view_name,
                query_object=full_view_name,
                logical_name=view_name,
                object_type="VIEW",
                table_description=view_desc,
                primary_business_key=catalog_meta.get("primary_business_key"),
                grain=catalog_meta.get("grain"),
                relationship_information=catalog_meta.get("relationship_information"),
                is_scd_type_2=catalog_meta.get("is_scd_type_2", False),
                scd_columns=catalog_meta.get("scd_columns", []),
                ai_usage_guidance=catalog_meta.get("ai_usage_guidance"),
                typical_ai_questions=catalog_meta.get("typical_ai_questions"),
                schema=fields
            )

        # 3. Construct datasets structure
        datasets = {
            f"{project_id}.{banking_dataset_id}": DatasetDetail(
                dataset_description="Core operational banking data store containing customer demographics, accounts, credit cards, loans, deposits, and transaction histories.",
                tables=tables_dict,
                views=None
            ),
            f"{project_id}.{analytics_dataset_id}": DatasetDetail(
                dataset_description="Curated analytical marts and enriched dimensional models for cross-functional business intelligence, portfolio analytics, and customer 360 insights.",
                tables=None,
                views=views_dict
            )
        }

        response = AnalyticsMetadataResponse(
            authorized=True,
            user_role="BANK_STAFF",
            datasets=datasets
        )

        self._cached_response = response
        self._cache_timestamp = current_time
        return response
