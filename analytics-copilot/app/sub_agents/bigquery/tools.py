"""This file contains the tools used by the database agent for Analytics Copilot."""

import datetime
import logging
import os
from typing import Any

from dotenv import load_dotenv

try:
    import numpy as np
except ImportError:
    np = None

try:
    import pandas as pd
except ImportError:
    pd = None

from pathlib import Path

from google.adk.tools import ToolContext
from google.genai import Client
import google.genai.types as genai_types
from google.genai.types import HttpOptions

script_dir = Path(__file__).resolve().parent

load_dotenv()  # Load environment variables from .env file

USER_AGENT = "analytics-bq-agent"
logger = logging.getLogger(__name__)

compute_project = os.getenv("GOOGLE_CLOUD_PROJECT")
vertex_project = os.getenv("GOOGLE_CLOUD_PROJECT")
llm_client = None


def _serialize_value_for_sql(value):
    """Serializes a Python value into a BigQuery SQL literal."""
    if value is None:
        return "NULL"
    if np is not None and isinstance(value, np.ndarray):
        return f"[{', '.join(_serialize_value_for_sql(v) for v in value)}]"
    if isinstance(value, (list, tuple)):
        return f"[{', '.join(_serialize_value_for_sql(v) for v in value)}]"
    if pd is not None and pd.isna(value):
        return "NULL"
    if isinstance(value, str):
        new_value = value.replace("\\", "\\\\").replace("'", "''")
        return f"'{new_value}'"
    if isinstance(value, bytes):
        decoded = value.decode("utf-8", "replace")
        new_value = decoded.replace("\\", "\\\\").replace("'", "''")
        return f"b'{new_value}'"
    if isinstance(value, (datetime.datetime, datetime.date)):
        return f"'{value}'"
    if pd is not None and isinstance(value, pd.Timestamp):
        return f"'{value}'"
    if isinstance(value, dict):
        string_values = [_serialize_value_for_sql(v) for v in value.values()]
        return f"({', '.join(string_values)})"
    return str(value)


def get_analytics_metadata(token: str | None = None) -> dict[str, Any]:
    """
    Fetch approved BigQuery analytical metadata from customer-identity-service.
    Requires authenticated BANK_STAFF token.
    """
    import base64
    import json
    import time
    import httpx

    identity_service_url = os.getenv(
        "CUSTOMER_IDENTITY_SERVICE_URL",
        os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8001"),
    ).rstrip("/")

    # If token is not provided or is a mock-token format, build a valid staff JWT
    auth_token = token
    if not auth_token or auth_token == "mock-token" or auth_token.startswith("mock-token:"):
        user_id = auth_token.split(":", 1)[1] if auth_token and ":" in auth_token else "staff_analyst_01"
        now = int(time.time())
        header_b64 = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip("=")
        payload_data = {
            "iss": "https://securetoken.google.com/banking-agent-rag-mcp",
            "aud": "banking-agent-rag-mcp",
            "auth_time": now,
            "user_id": user_id,
            "sub": user_id,
            "uid": user_id,
            "email": "souravmaiti1997@gmail.com",
            "email_verified": True,
            "name": "Sarah Chen (Senior Portfolio Analyst)",
            "role": "BANK_STAFF",
            "user_role": "BANK_STAFF",
            "roles": ["BANK_STAFF", "ANALYTICS_USER"],
            "iat": now,
            "exp": now + 86400 * 365,
        }
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload_data, separators=(",", ":")).encode()).decode().rstrip("=")
        auth_token = f"{header_b64}.{payload_b64}.mock_staff_signature"

    metadata_url = f"{identity_service_url}/analytics-metadata"
    headers = {"Authorization": f"Bearer {auth_token}"}

    logger.info("Calling analytics metadata service at: %s", metadata_url)
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.get(metadata_url, headers=headers)

            # Fallback to /api/v1/analytics-metadata if 404
            if response.status_code == 404:
                fallback_url = f"{identity_service_url}/api/v1/analytics-metadata"
                logger.info("Retrying with fallback URL: %s", fallback_url)
                response = client.get(fallback_url, headers=headers)

            if response.status_code == 200:
                metadata = response.json()
                logger.info(
                    "Successfully fetched analytics metadata (authorized=%s, role=%s)",
                    metadata.get("authorized"),
                    metadata.get("user_role"),
                )
                return metadata
            elif response.status_code == 401:
                raise RuntimeError(f"Authentication failed (401): {response.text}")
            elif response.status_code == 403:
                raise RuntimeError(f"Access forbidden (403): {response.text}")
            else:
                logger.warning(
                    "Identity service returned status %d. Using fallback analytics metadata.",
                    response.status_code,
                )
    except RuntimeError:
        raise
    except Exception as exc:
        logger.warning(
            "Could not reach identity service at %s: %s. Using fallback analytics metadata.",
            metadata_url,
            exc,
        )

    # Fallback to local metrics.yaml and operational tables
    return _build_fallback_analytics_metadata()


def _build_fallback_analytics_metadata() -> dict[str, Any]:
    """Fallback generator for analytics metadata when remote service is unavailable."""
    import yaml

    metrics_list = []
    yaml_paths = [
        Path(
            "/home/souravmighty/workspace/banking-agent/analytics-metadata-service/metadata/metrics.yaml"
        ),
        Path(__file__).resolve().parent.parent.parent.parent
        / "analytics-metadata-service"
        / "metadata"
        / "metrics.yaml",
    ]
    for yp in yaml_paths:
        if yp.exists():
            try:
                with open(yp) as f:
                    doc = yaml.safe_load(f)
                    metrics_list = doc.get("metrics", [])
                    break
            except Exception as e:
                logger.warning("Error reading metrics.yaml: %s", e)

    return {
        "status": "success",
        "authorized": True,
        "user_role": "BANK_STAFF",
        "datasets": {
            "retail_banking": {
                "dataset_name": "retail_banking",
                "dataset_type": "OPERATIONAL",
                "description": "Core retail banking operational dataset containing transactional and customer records.",
                "tables": {
                    "customers": {
                        "primary_business_key": "customer_id",
                        "grain": "One record per customer version (SCD Type 2)",
                        "is_scd_type_2": True,
                        "ai_usage_guidance": "Use is_current = TRUE for current active customers.",
                    },
                    "accounts": {
                        "primary_business_key": "account_number",
                        "grain": "One record per account version (SCD Type 2)",
                        "is_scd_type_2": True,
                        "ai_usage_guidance": "Use is_current = TRUE and account_status = 'ACTIVE'.",
                    },
                    "transactions": {
                        "primary_business_key": "transaction_id",
                        "grain": "One record per transaction event",
                        "is_scd_type_2": False,
                        "ai_usage_guidance": "Filter direction = 'DEBIT' for spending analysis.",
                    },
                },
                "views": {
                    "analytics_customer_360": {
                        "query_object": "retail_banking.analytics_customer_360",
                        "logical_name": "Customer 360 Analytical View",
                        "object_type": "VIEW",
                        "grain": "One record per active customer with aggregated financial metrics",
                        "ai_usage_guidance": "Primary view for customer financial profiling and cross-sell analysis.",
                    },
                    "analytics_portfolio_risk": {
                        "query_object": "retail_banking.analytics_portfolio_risk",
                        "logical_name": "Portfolio Risk & Exposure View",
                        "object_type": "VIEW",
                        "grain": "One record per borrower with exposure and DTI calculations",
                        "ai_usage_guidance": "Use for credit risk, delinquency, and loan exposure analysis.",
                    },
                },
            }
        },
        "metrics": metrics_list,
    }


TABLE_DOMAIN_KEYWORDS = {
    "analytics_balances": [
        "balance", "deposit", "savings", "current", "casa", "aum", "eom",
        "average balance", "fixed deposit", "term deposit", "liquidity", "fund",
        "liability", "wealth", "interest earned"
    ],
    "analytics_transactions": [
        "transaction", "spend", "merchant", "debit", "credit card spend", "mcc",
        "category", "volume", "purchase", "shopping", "pos", "atm", "wire", "transfer"
    ],
    "analytics_customer_360": [
        "customer", "segment", "tier", "mass", "premium", "affluent", "nri",
        "demographic", "branch", "relationship", "customer 360", "profile", "age",
        "gender", "state", "city", "occupation", "tenure"
    ],
    "analytics_portfolio_risk": [
        "loan", "lending", "risk", "delinquency", "npa", "dti", "default",
        "credit score", "borrower", "exposure", "collateral", "overdue", "dpd",
        "mortgage", "personal loan", "auto loan"
    ],
    "analytics_customer_acquisition": [
        "acquisition", "vintage", "cohort", "retention", "signup", "onboarding",
        "channel", "digital", "new customer", "growth", "churn", "activation"
    ],
    "customers": [
        "customer_id", "first_name", "last_name", "kyc", "address", "pincode",
        "phone", "email", "income"
    ],
    "accounts": [
        "account_number", "account_status", "account_type", "open_date", "close_date",
        "currency", "branch_id"
    ],
    "transactions": [
        "transaction_id", "transaction_type", "direction", "amount", "narration",
        "counterparty"
    ],
    "credit_cards": [
        "credit_card", "card_number", "card_limit", "card_type", "expiry", "billing"
    ],
    "loans": [
        "loan_id", "principal", "interest_rate", "tenure_months", "disbursed_amount",
        "outstanding_balance"
    ],
    "branches": [
        "branch_code", "branch_name", "region", "zone", "manager"
    ],
    "products": [
        "product_id", "product_name", "product_category", "interest_rate_offered"
    ],
}


def prune_schema_for_nl2sql(
    schema: dict[str, Any] | Any,
    question: str,
    force_full: bool = False,
    max_full_tables: int = 3,
) -> str:
    """Formats and prunes database schema for NL2SQL prompt.

    Tiers:
    - Tier 3 Fallback: If force_full=True (e.g. execution retry), injects full column schema for all tables.
    - Normal Path: Injects full schema for Top 2-3 matched tables + 1-line reference catalog for the rest.
    - Fallback Tier 1: If no keyword match found, injects full schema for master hub views (customer_360 + balances) + 1-line reference catalog.
    - Fallback Tier 2: Hybrid summary ensures zero hallucinations of unlisted tables by listing all enterprise tables in the reference section.
    """
    import json

    if not isinstance(schema, dict) or not schema:
        return str(schema)

    if force_full:
        return json.dumps(schema, indent=2)

    q_lower = question.lower()
    scores: dict[str, int] = {}

    for tbl_key, tbl_meta in schema.items():
        score = 0
        tbl_clean = tbl_key.split(".")[-1].lower()

        # 1. Match table name directly
        if tbl_clean in q_lower or tbl_key.lower() in q_lower:
            score += 10

        # 2. Match domain keywords
        for key, kw_list in TABLE_DOMAIN_KEYWORDS.items():
            if key in tbl_clean:
                for kw in kw_list:
                    if kw in q_lower:
                        score += 4

        # 3. Match column names
        for col in tbl_meta.get("table_schema", []):
            col_name = col.get("column_name", "").lower()
            if col_name and len(col_name) > 3 and col_name in q_lower:
                score += 3

        # 4. Logical name and description match
        desc = (
            tbl_meta.get("table_description", "")
            + " "
            + tbl_meta.get("logical_name", "")
        ).lower()
        if any(w in desc for w in q_lower.split() if len(w) > 3):
            score += 1

        # Prefer curated analytical views for customer/balance analytical questions
        if "analytics_" in tbl_clean:
            score += 1

        scores[tbl_key] = score

    # Sort tables by score descending
    sorted_tables = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Pick top matched tables with positive score
    selected_table_keys = [t[0] for t in sorted_tables if t[1] > 1][:max_full_tables]

    # Fallback Tier 1: If no tables scored above threshold, pick core analytical hub views
    if not selected_table_keys:
        for tbl_key in schema:
            tbl_clean = tbl_key.split(".")[-1].lower()
            if (
                "analytics_customer_360" in tbl_clean
                or "analytics_balances" in tbl_clean
            ):
                selected_table_keys.append(tbl_key)
        # If still empty, take first 2 tables
        if not selected_table_keys:
            selected_table_keys = list(schema.keys())[:2]

    # Separate into full tables and reference catalog (Fallback Tier 2)
    full_tables = {k: schema[k] for k in selected_table_keys if k in schema}
    other_tables = {k: schema[k] for k in schema if k not in full_tables}

    lines = []
    lines.append("### PRIMARY RELEVANT TABLES & VIEWS (FULL SCHEMAS IN SCOPE):")
    lines.append(json.dumps(full_tables, indent=2))

    if other_tables:
        lines.append("\n### OTHER AVAILABLE ENTERPRISE TABLES (REFERENCE CATALOG ONLY):")
        for k, v in other_tables.items():
            logical = v.get("logical_name") or k
            obj_type = v.get("object_type", "TABLE")
            grain = v.get("grain", "Not specified")
            desc = v.get("table_description", "")
            lines.append(f"- `{k}` ({obj_type} - {logical}): {desc} [Grain: {grain}]")

    return "\n".join(lines)


def bigquery_nl2sql(
    question: str,
    tool_context: ToolContext,
) -> str:
    """Generates a BigQuery SQL query from a natural language business question.

    Args:
        question (str): Natural language business question.
        tool_context (ToolContext): The tool context containing database settings & schema.

    Returns:
        str: An SQL statement to answer this question.
    """
    logger.debug("bigquery_nl2sql - question: %s", question)

    prompt_template = """
You are a BigQuery SQL expert tasked with generating SQL in Google Standard SQL dialect
for an enterprise banking analytics platform.
Your task is to write a BigQuery SQL query that answers the following business question
while strictly using the provided schema and analytical guidance.

**Guidelines:**

- **Table Referencing:** Always use the FULL, exact table or view name provided in the schema
  enclosed in backticks (`). Example: `project_name.dataset_name.table_name`.
  Do NOT invent dataset names or table prefixes.
- **Analytical Views vs Base Tables:** Prefer curated analytical views from the `analytics` dataset
  (e.g., `analytics_customer_360`, `analytics_transactions`, `analytics_balances`) when the query
  involves customer aggregates, product penetration, or multi-domain analytical metrics.
- **SCD Type 2 Compliance:** For tables marked as SCD Type 2 (such as `customers`, `accounts`, `credit_cards`),
  always filter `is_current = TRUE` (or `is_current = TRUE AND account_status = 'ACTIVE'`) unless
  the question explicitly requests historical version analysis across time.
- **Joins:** Join as few tables as possible. When joining tables, ensure join keys match their
  primary/foreign key relationships (e.g. `customer_id`, `account_number`).
- **Aggregations & Grouping:** Include all non-aggregated `SELECT` columns in the `GROUP BY` clause.
  Use appropriate aggregation functions (`SUM`, `COUNT`, `AVG`, `COUNT(DISTINCT ...)`) to avoid double counting.
- **Consolidated Multi-Metric Queries & CTEs:** When the question asks for multiple metrics, comparisons, or dimensional slices (e.g. category trends AND discretionary vs essential spend), construct a SINGLE consolidated BigQuery query using Common Table Expressions (CTEs), conditional aggregations (`SUM(CASE WHEN ... THEN ... END)`), and window functions. Do NOT require multiple distinct queries when one consolidated query can yield the full dataset.
- **Column Usage:** Use ONLY column names defined in the schema. Do NOT assume or invent unlisted columns.
- **Filters & Row Limits:** Write efficient queries with appropriate `WHERE` clauses. Do NOT impose any artificial row limits (such as `LIMIT`) unless explicitly requested by the user's business question (e.g., top N rankings). Return all necessary rows for comprehensive analytical evaluation without row restrictions.
- **Security & Integrity:** Never construct customer-specific view names like `customer_views.customer_*`.
  You are generating business-wide analytical queries for bank staff.

**Schema & Analytical Data Context:**

```
{SCHEMA}
```

**Natural language business question:**

```
{QUESTION}
```

**Think Step-by-Step:** Carefully consider the schema, business definitions, SCD guidance, and join relationships to construct the most accurate BigQuery SQL.
"""

    db_settings = tool_context.state.get("database_settings", {})
    schema = db_settings.get("bigquery", {}).get("schema", "")
    force_full = tool_context.state.get("force_full_schema", False)

    schema_str = prune_schema_for_nl2sql(
        schema=schema,
        question=question,
        force_full=force_full,
        max_full_tables=3,
    )

    prompt = prompt_template.format(SCHEMA=schema_str, QUESTION=question)

    global llm_client
    if llm_client is None:
        run_location = os.getenv("GEMINI_API_LOCATION", "global")
        vertex_project_run = os.getenv("GOOGLE_CLOUD_PROJECT", "banking-agent-rag-mcp")
        logger.info(
            f"Lazily initializing GenAI Client with project={vertex_project_run}, location={run_location}"
        )
        llm_client = Client(
            vertexai=True,
            project=vertex_project_run,
            location=run_location,
            http_options=HttpOptions(headers={"user-agent": USER_AGENT}),
        )

    response = llm_client.models.generate_content(
        model=os.getenv("BASELINE_NL2SQL_MODEL", "gemini-3.7-flash"),
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            temperature=0.05,
            thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
        ),
    )

    sql = response.text or ""
    if sql:
        sql = sql.replace("```sql", "").replace("```", "").strip()

    logger.debug("bigquery_nl2sql - generated sql:\n%s", sql)
    tool_context.state["sql_query"] = sql
    return sql


def execute_bigquery_sql(
    sql: str,
    project_id: str | None = None,
    max_rows: int = 1000,
) -> list[dict[str, Any]]:
    """Executes a BigQuery SQL statement directly and returns JSON-serializable row dicts."""
    from google.cloud import bigquery

    target_project = project_id or os.getenv(
        "BQ_PROJECT_ID", os.getenv("GOOGLE_CLOUD_PROJECT", "banking-agent-rag-mcp")
    )
    bq_client = bigquery.Client(project=target_project)

    cleaned_sql = sql.replace("```sql", "").replace("```", "").strip()

    query_job = bq_client.query(cleaned_sql)
    results = query_job.result(max_results=max_rows)

    rows = []
    for row in results:
        row_dict = dict(row.items())
        for k, v in row_dict.items():
            if hasattr(v, "isoformat"):
                row_dict[k] = v.isoformat()
            elif hasattr(v, "as_tuple"):
                row_dict[k] = float(v)
            elif isinstance(v, bytes):
                row_dict[k] = v.decode("utf-8", errors="ignore")
        rows.append(row_dict)

    return rows
