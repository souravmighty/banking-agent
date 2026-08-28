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
    if isinstance(schema, dict):
        import json

        schema_str = json.dumps(schema, indent=2)
    else:
        schema_str = str(schema)

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
        config={"temperature": 0.05},
    )

    sql = response.text or ""
    if sql:
        sql = sql.replace("```sql", "").replace("```", "").strip()

    logger.debug("bigquery_nl2sql - generated sql:\n%s", sql)
    tool_context.state["sql_query"] = sql
    return sql
