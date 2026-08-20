# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tools and BigQuery execution utilities for analytics-copilot.

Supports execution against Google BigQuery warehouse (banking-agent-rag-mcp)
with seamless offline/test fallback.
"""

import datetime
import logging
import os
import re
import sqlite3
from typing import Any, Dict, List, Optional

from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger(__name__)

USER_AGENT = "analytics-copilot"
MAX_NUM_ROWS = 10000

BQ_PROJECT_ID = os.getenv("BQ_PROJECT_ID", "banking-agent-rag-mcp")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "banking-agent-rag-mcp")
BQ_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

_bq_client: Optional[bigquery.Client] = None


def _serialize_value_for_sql(value: Any) -> str:
    """Serializes a Python value into a BigQuery SQL literal."""
    if value is None:
        return "NULL"
    if isinstance(value, (list, tuple, set)):
        return f"[{', '.join(_serialize_value_for_sql(v) for v in value)}]"
    if isinstance(value, str):
        new_value = value.replace("\\", "\\\\").replace("'", "''")
        return f"'{new_value}'"
    if isinstance(value, bytes):
        decoded = value.decode("utf-8", "replace")
        new_value = decoded.replace("\\", "\\\\").replace("'", "''")
        return f"b'{new_value}'"
    if isinstance(value, (datetime.datetime, datetime.date)):
        return f"'{value}'"
    if isinstance(value, dict):
        string_values = [_serialize_value_for_sql(v) for v in value.values()]
        return f'({", ".join(string_values)})'
    return str(value)


def get_bq_client() -> Optional[bigquery.Client]:
    """Lazily initializes the Google Cloud BigQuery client."""
    global _bq_client
    if _bq_client is None:
        try:
            _bq_client = bigquery.Client(
                project=GOOGLE_CLOUD_PROJECT,
                location=BQ_LOCATION,
                client_info=bigquery.client.ClientInfo(user_agent=USER_AGENT),
            )
        except Exception as e:
            logger.debug("BigQuery client initialization deferred or offline: %s", e)
            return None
    return _bq_client


# In-memory warehouse database for local simulation & testing
_DB_CONN = sqlite3.connect(":memory:", check_same_thread=False)
_DB_CONN.row_factory = sqlite3.Row


def _init_local_db():
    """Initializes local tables representing banking_data and analytics datasets."""
    cursor = _DB_CONN.cursor()

    # 1. credit_cards (banking_data.credit_cards)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS credit_cards (
        card_account_number TEXT PRIMARY KEY,
        customer_id TEXT,
        card_type TEXT,
        credit_limit REAL,
        available_credit REAL,
        outstanding_balance REAL,
        statement_amount REAL,
        minimum_due REAL,
        payment_due_date TEXT,
        status TEXT,
        created_at TEXT,
        eff_start_ts TEXT,
        eff_end_ts TEXT,
        is_current INTEGER,
        record_version INTEGER
    )
    """)

    # 2. customers (banking_data.customers)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id TEXT PRIMARY KEY,
        customer_status TEXT,
        customer_segment TEXT,
        risk_profile TEXT,
        kyc_status TEXT,
        created_at TEXT,
        eff_start_ts TEXT,
        eff_end_ts TEXT,
        is_current INTEGER,
        record_version INTEGER
    )
    """)

    # 3. accounts (banking_data.accounts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        account_number TEXT PRIMARY KEY,
        customer_id TEXT,
        account_type TEXT,
        account_status TEXT,
        balance REAL,
        currency TEXT,
        ifsc_code TEXT,
        branch_name TEXT,
        created_at TEXT,
        eff_start_ts TEXT,
        eff_end_ts TEXT,
        is_current INTEGER,
        record_version INTEGER
    )
    """)

    # 4. transactions (banking_data.transactions)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id TEXT PRIMARY KEY,
        reference_id TEXT,
        account_number TEXT,
        counterparty_account_number TEXT,
        transaction_type TEXT,
        currency TEXT,
        direction TEXT,
        amount REAL,
        merchant_name TEXT,
        category TEXT,
        description TEXT,
        transaction_timestamp TEXT
    )
    """)

    # 5. analytics_balances (analytics.analytics_balances)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analytics_balances (
        month TEXT,
        customer_segment TEXT,
        card_type TEXT,
        total_balance REAL,
        previous_month_balance REAL,
        balance_change REAL,
        total_payments REAL,
        payoff_rate REAL,
        avg_revolving_rate REAL,
        total_spend REAL,
        active_accounts INTEGER,
        PRIMARY KEY (month, customer_segment, card_type)
    )
    """)

    # 6. analytics_customer_360 (analytics.analytics_customer_360)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analytics_customer_360 (
        customer_id TEXT PRIMARY KEY,
        customer_segment TEXT,
        risk_profile TEXT,
        customer_status TEXT,
        total_deposit_balance REAL,
        total_loan_balance REAL,
        total_credit_card_balance REAL,
        active_product_count INTEGER,
        last_activity_date TEXT
    )
    """)

    # Populate representative banking sample data
    customers_data = [
        ("CUST_001", "ACTIVE", "Prime", "LOW", "VERIFIED", "2023-01-15", "2023-01-15", None, 1, 1),
        ("CUST_002", "ACTIVE", "Prime", "LOW", "VERIFIED", "2022-05-20", "2022-05-20", None, 1, 1),
        ("CUST_003", "ACTIVE", "Affluent", "LOW", "VERIFIED", "2021-11-10", "2021-11-10", None, 1, 1),
        ("CUST_004", "ACTIVE", "Affluent", "LOW", "VERIFIED", "2020-03-01", "2020-03-01", None, 1, 1),
        ("CUST_005", "ACTIVE", "Subprime", "HIGH", "VERIFIED", "2024-02-14", "2024-02-14", None, 1, 1),
        ("CUST_006", "ACTIVE", "Subprime", "HIGH", "VERIFIED", "2023-09-18", "2023-09-18", None, 1, 1),
        ("CUST_007", "ACTIVE", "Student", "MEDIUM", "VERIFIED", "2024-08-01", "2024-08-01", None, 1, 1),
        ("CUST_008", "CLOSED", "Prime", "LOW", "VERIFIED", "2021-04-12", "2021-04-12", None, 1, 1),
        ("CUST_009", "DORMANT", "Affluent", "LOW", "VERIFIED", "2019-07-22", "2019-07-22", None, 1, 1),
    ]
    cursor.executemany("INSERT OR IGNORE INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", customers_data)

    cards_data = [
        ("CARD_001", "CUST_001", "VISA", 15000.0, 11800.0, 3200.0, 3200.0, 150.0, "2026-07-05", "ACTIVE", "2023-01-15", "2023-01-15", None, 1, 1),
        ("CARD_002", "CUST_002", "MASTERCARD", 12000.0, 10800.0, 1200.0, 1200.0, 100.0, "2026-07-05", "ACTIVE", "2022-05-20", "2022-05-20", None, 1, 1),
        ("CARD_003", "CUST_003", "VISA", 35000.0, 30500.0, 4500.0, 4500.0, 200.0, "2026-07-05", "ACTIVE", "2021-11-10", "2021-11-10", None, 1, 1),
        ("CARD_004", "CUST_004", "MASTERCARD", 40000.0, 33900.0, 6100.0, 6100.0, 300.0, "2026-07-05", "ACTIVE", "2020-03-01", "2020-03-01", None, 1, 1),
        ("CARD_005", "CUST_005", "RUPAY", 3500.0, 700.0, 2800.0, 2800.0, 150.0, "2026-07-05", "ACTIVE", "2024-02-14", "2024-02-14", None, 1, 1),
        ("CARD_006", "CUST_006", "RUPAY", 2500.0, 600.0, 1900.0, 1900.0, 100.0, "2026-07-05", "ACTIVE", "2023-09-18", "2023-09-18", None, 1, 1),
    ]
    cursor.executemany("INSERT OR IGNORE INTO credit_cards VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", cards_data)

    balances_data = [
        # Jan 2026
        ("2026-01", "Prime", "VISA", 125000000.0, 130000000.0, -5000000.0, 38000000.0, 0.30, 0.65, 42000000.0, 45000),
        ("2026-01", "Affluent", "VISA", 210000000.0, 215000000.0, -5000000.0, 80000000.0, 0.38, 0.45, 85000000.0, 28000),
        ("2026-01", "Subprime", "RUPAY", 45000000.0, 44500000.0, 500000.0, 10500000.0, 0.23, 0.88, 12000000.0, 22000),
        # Feb 2026
        ("2026-02", "Prime", "VISA", 122000000.0, 125000000.0, -3000000.0, 41000000.0, 0.33, 0.63, 39000000.0, 45100),
        ("2026-02", "Affluent", "VISA", 202000000.0, 210000000.0, -8000000.0, 86000000.0, 0.42, 0.42, 79000000.0, 28100),
        ("2026-02", "Subprime", "RUPAY", 45500000.0, 45000000.0, 500000.0, 10800000.0, 0.24, 0.89, 11500000.0, 22100),
        # Mar 2026
        ("2026-03", "Prime", "VISA", 116000000.0, 122000000.0, -6000000.0, 46000000.0, 0.39, 0.58, 41000000.0, 45200),
        ("2026-03", "Affluent", "VISA", 188000000.0, 202000000.0, -14000000.0, 95000000.0, 0.50, 0.38, 82000000.0, 28200),
        ("2026-03", "Subprime", "RUPAY", 46000000.0, 45500000.0, 500000.0, 11200000.0, 0.24, 0.90, 13000000.0, 22200),
        # Apr 2026 (Tax refund payoff spike)
        ("2026-04", "Prime", "VISA", 108000000.0, 116000000.0, -8000000.0, 47500000.0, 0.44, 0.52, 40000000.0, 45300),
        ("2026-04", "Affluent", "VISA", 168000000.0, 188000000.0, -20000000.0, 99000000.0, 0.59, 0.32, 80000000.0, 28300),
        ("2026-04", "Subprime", "RUPAY", 44800000.0, 46000000.0, -1200000.0, 13200000.0, 0.29, 0.86, 12500000.0, 22250),
        # May 2026
        ("2026-05", "Prime", "VISA", 104000000.0, 108000000.0, -4000000.0, 46800000.0, 0.45, 0.50, 43000000.0, 45350),
        ("2026-05", "Affluent", "VISA", 159000000.0, 168000000.0, -9000000.0, 94000000.0, 0.59, 0.30, 86000000.0, 28400),
        ("2026-05", "Subprime", "RUPAY", 45200000.0, 44800000.0, 400000.0, 12600000.0, 0.28, 0.87, 13100000.0, 22300),
        # Jun 2026
        ("2026-06", "Prime", "VISA", 101000000.0, 104000000.0, -3000000.0, 46900000.0, 0.46, 0.49, 44000000.0, 45400),
        ("2026-06", "Affluent", "VISA", 152000000.0, 159000000.0, -7000000.0, 94500000.0, 0.62, 0.28, 88000000.0, 28500),
        ("2026-06", "Subprime", "RUPAY", 45800000.0, 45200000.0, 600000.0, 12700000.0, 0.28, 0.88, 13400000.0, 22350),
    ]
    cursor.executemany("INSERT OR IGNORE INTO analytics_balances VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", balances_data)

    c360_data = [
        ("CUST_001", "Prime", "LOW", "ACTIVE", 45000.0, 0.0, 3200.0, 2, "2026-06-28"),
        ("CUST_002", "Prime", "LOW", "ACTIVE", 28000.0, 150000.0, 1200.0, 3, "2026-06-29"),
        ("CUST_003", "Affluent", "LOW", "ACTIVE", 185000.0, 0.0, 4500.0, 4, "2026-06-30"),
        ("CUST_004", "Affluent", "LOW", "ACTIVE", 220000.0, 350000.0, 6100.0, 3, "2026-06-30"),
        ("CUST_005", "Subprime", "HIGH", "ACTIVE", 1500.0, 8000.0, 2800.0, 2, "2026-06-25"),
        ("CUST_006", "Subprime", "HIGH", "ACTIVE", 2200.0, 0.0, 1900.0, 1, "2026-06-26"),
    ]
    cursor.executemany("INSERT OR IGNORE INTO analytics_customer_360 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", c360_data)

    _DB_CONN.commit()


# Register custom SQLite functions to emulate Google BigQuery SQL functions
def _safe_divide(a, b):
    if a is None or b is None:
        return None
    try:
        b_val = float(b)
        return float(a) / b_val if b_val != 0 else None
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def _ifnull(a, b):
    return a if a is not None else b


_DB_CONN.create_function("SAFE_DIVIDE", 2, _safe_divide)
_DB_CONN.create_function("IFNULL", 2, _ifnull)
_DB_CONN.create_function("CURRENT_DATE", 0, lambda: "2026-06-30")
_DB_CONN.create_function("CURRENT_TIMESTAMP", 0, lambda: "2026-06-30 00:00:00")


_init_local_db()


def _clean_sql_for_local_execution(sql_query: str) -> str:
    """Adapts BigQuery Google SQL for local SQLite execution fallback."""
    cleaned = sql_query.strip().rstrip(";")
    # Replace fully-qualified and dataset-qualified table names
    cleaned = re.sub(r"`[a-zA-Z0-9_\-]+\.(banking_data|analytics)\.([a-zA-Z0-9_]+)`", r"\2", cleaned)
    cleaned = re.sub(r"`(banking_data|analytics)\.([a-zA-Z0-9_]+)`", r"\2", cleaned)
    cleaned = re.sub(r"(banking_data|analytics)\.([a-zA-Z0-9_]+)", r"\2", cleaned)
    # Replace backticks around simple identifiers
    cleaned = re.sub(r"`([a-zA-Z0-9_]+)`", r"\1", cleaned)

    # Date and interval BigQuery expressions
    cleaned = re.sub(
        r"(?:DATE_SUB|TIMESTAMP_SUB)\s*\(\s*(?:CURRENT_DATE|CURRENT_TIMESTAMP)\s*\(\s*\)\s*,\s*INTERVAL\s+(\d+)\s+(?:MONTH|DAY|YEAR)\s*\)",
        r"'2026-01-01'",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"(?:DATE_SUB|TIMESTAMP_SUB)\s*\(\s*[^,]+,\s*INTERVAL\s+(\d+)\s+(?:MONTH|DAY|YEAR)\s*\)",
        r"'2026-01-01'",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"EXTRACT\s*\(\s*YEAR\s+FROM\s+([^\)]+)\)", r"strftime('%Y', \1)", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"EXTRACT\s*\(\s*MONTH\s+FROM\s+([^\)]+)\)", r"strftime('%m', \1)", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"FORMAT_DATE\s*\(\s*'[^']+'\s*,\s*([^\)]+)\)", r"\1", cleaned, flags=re.IGNORECASE)

    # BigQuery boolean literals and expressions
    cleaned = re.sub(r"\bTRUE\b", r"1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bFALSE\b", r"0", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"COUNTIF\(([^)]+)\)", r"SUM(CASE WHEN \1 THEN 1 ELSE 0 END)", cleaned, flags=re.IGNORECASE)
    return cleaned


def execute_bigquery_query(sql_query: str) -> Dict[str, Any]:
    """Validates and executes a SQL query on BigQuery with local warehouse fallback.

    Args:
        sql_query: The standard Google SQL query to execute.

    Returns:
        Dict containing columns, rows, row_count, and execution status.
    """
    cleaned_query = sql_query.strip().rstrip(";")
    if not re.match(r"^\s*(SELECT|WITH)\b", cleaned_query, re.IGNORECASE):
        return {
            "status": "FAILED",
            "error": "Only read-only SELECT or WITH statements are allowed.",
            "rows": [],
            "row_count": 0,
        }

    # 1. Try BigQuery Client if configured and online
    client = get_bq_client()
    if client is not None:
        try:
            logger.info("Executing query on BigQuery project %s", GOOGLE_CLOUD_PROJECT)
            job = client.query(cleaned_query)
            df = job.to_dataframe(max_results=MAX_NUM_ROWS)
            row_dicts = df.to_dict(orient="records")
            # Format row values
            formatted_rows = []
            for row in row_dicts:
                formatted_row = {k: _serialize_value_for_sql(v) for k, v in row.items()}
                formatted_rows.append(formatted_row)
            return {
                "status": "SUCCESS",
                "columns": list(df.columns),
                "row_count": len(formatted_rows),
                "rows": formatted_rows[:50],
            }
        except Exception as e:
            logger.warning("BigQuery live query execution failed (%s). Falling back to local warehouse engine.", e)

    # 2. Local warehouse simulation execution
    try:
        local_sql = _clean_sql_for_local_execution(cleaned_query)
        cursor = _DB_CONN.cursor()
        cursor.execute(local_sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        row_dicts = [dict(zip(columns, row)) for row in rows]
        return {
            "status": "SUCCESS",
            "columns": columns,
            "row_count": len(row_dicts),
            "rows": row_dicts[:50],
        }
    except Exception as e:
        return {
            "status": "FAILED",
            "error": str(e),
            "rows": [],
            "row_count": 0,
        }
