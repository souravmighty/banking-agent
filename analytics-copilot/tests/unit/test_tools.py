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

import pytest
from app.metadata_client import metadata_client
from app.tools import execute_bigquery_query


def test_metadata_catalog():
    catalog = metadata_client.get_compact_catalog()
    assert "tables" in catalog
    assert len(catalog["tables"]) > 0
    table_names = [t["table_name"] for t in catalog["tables"]]
    assert "credit_cards" in table_names or "customers" in table_names


def test_metadata_nl2sql_context():
    context = metadata_client.get_nl2sql_context(
        selected_tables=["credit_cards", "analytics_balances"],
        selected_metrics=["credit_card_payoff_rate", "credit_card_total_balance"],
        selected_dimensions=["customer_segment", "card_type", "month"],
        question="Why did credit card balances decline?",
    )
    assert context["validation_passed"] is True
    assert "prompt_context_str" in context
    assert "credit_cards" in context["prompt_context_str"]


def test_execute_bigquery_select_query():
    # Test query with fully-qualified BigQuery table names and backticks
    res = execute_bigquery_query(
        "SELECT customer_segment, AVG(total_balance) as avg_bal FROM `banking-agent-rag-mcp.analytics.analytics_balances` GROUP BY customer_segment"
    )
    assert res["status"] == "SUCCESS"
    assert res["row_count"] > 0
    assert "customer_segment" in res["columns"]
    assert "avg_bal" in res["columns"]


def test_execute_scd2_query():
    res = execute_bigquery_query(
        "SELECT card_type, SUM(outstanding_balance) as total_bal FROM `banking-agent-rag-mcp.banking_data.credit_cards` WHERE is_current = TRUE GROUP BY card_type"
    )
    assert res["status"] == "SUCCESS"
    assert res["row_count"] > 0
    assert "card_type" in res["columns"]


def test_reject_mutating_query():
    res = execute_bigquery_query("DROP TABLE credit_cards")
    assert res["status"] == "FAILED"
    assert "Only read-only SELECT or WITH" in res["error"]
