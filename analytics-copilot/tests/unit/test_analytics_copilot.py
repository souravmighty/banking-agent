from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.agent import (
    analytics_metadata_cache,
    get_root_agent,
    load_analytics_metadata_in_context,
    reconstruct_database_settings_from_analytics_metadata,
)
from app.prompts import return_instructions_root
from app.sub_agents.bigquery.agent import setup_before_agent_call
from app.sub_agents.bigquery.prompts import return_instructions_bigquery
from app.sub_agents.bigquery.tools import (
    bigquery_nl2sql,
    get_analytics_metadata,
    prune_schema_for_nl2sql,
)

SAMPLE_ANALYTICS_METADATA = {
    "authorized": True,
    "user_role": "BANK_STAFF",
    "datasets": {
        "banking-agent-rag-mcp.banking_data": {
            "dataset_description": "Core operational banking data store.",
            "tables": {
                "banking-agent-rag-mcp.banking_data.customers": {
                    "table_name": "banking-agent-rag-mcp.banking_data.customers",
                    "query_object": "banking-agent-rag-mcp.banking_data.customers",
                    "logical_name": "customers",
                    "object_type": "TABLE",
                    "table_description": "Customer demographic master.",
                    "primary_business_key": "customer_id",
                    "grain": "One record per customer version (SCD Type 2)",
                    "relationship_information": "Joined with accounts, loans.",
                    "is_scd_type_2": True,
                    "scd_columns": ["is_current", "record_version"],
                    "ai_usage_guidance": "Use is_current = TRUE for current active state.",
                    "typical_ai_questions": ["What is customer distribution by state?"],
                    "schema": [
                        {
                            "column_name": "customer_id",
                            "type": "INTEGER",
                            "description": "Unique customer identifier.",
                            "mode": "REQUIRED",
                        },
                        {
                            "column_name": "customer_segment",
                            "type": "STRING",
                            "description": "Customer segment (e.g. Mass, HNW).",
                            "mode": "NULLABLE",
                        },
                        {
                            "column_name": "is_current",
                            "type": "BOOLEAN",
                            "description": "SCD Type 2 active flag.",
                            "mode": "REQUIRED",
                        },
                    ],
                }
            },
        },
        "banking-agent-rag-mcp.analytics": {
            "dataset_description": "Curated analytical marts and dimensional views.",
            "views": {
                "banking-agent-rag-mcp.analytics.analytics_customer_360": {
                    "view_name": "banking-agent-rag-mcp.analytics.analytics_customer_360",
                    "query_object": "banking-agent-rag-mcp.analytics.analytics_customer_360",
                    "logical_name": "analytics_customer_360",
                    "object_type": "VIEW",
                    "table_description": "360-degree customer analytical view.",
                    "primary_business_key": "customer_id",
                    "grain": "One record per customer",
                    "relationship_information": "Curated 360 view joining accounts and balances.",
                    "is_scd_type_2": False,
                    "scd_columns": [],
                    "ai_usage_guidance": "Preferred single-pane analytical source for customer metrics.",
                    "typical_ai_questions": ["What is the total balance by segment?"],
                    "schema": [
                        {
                            "column_name": "customer_id",
                            "type": "INTEGER",
                            "description": "Customer identifier.",
                            "mode": "NULLABLE",
                        },
                        {
                            "column_name": "total_balance",
                            "type": "NUMERIC",
                            "description": "Aggregated balance across all accounts.",
                            "mode": "NULLABLE",
                        },
                    ],
                }
            },
        },
    },
}


def test_get_analytics_metadata_success():
    """Test: Calls /analytics-metadata and propagates auth token."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_ANALYTICS_METADATA

    with patch("httpx.Client.get", return_value=mock_response) as mock_get:
        metadata = get_analytics_metadata(token="test-staff-jwt")
        assert metadata["authorized"] is True
        assert metadata["user_role"] == "BANK_STAFF"
        assert "banking-agent-rag-mcp.banking_data" in metadata["datasets"]
        assert "banking-agent-rag-mcp.analytics" in metadata["datasets"]

        call_args, call_kwargs = mock_get.call_args
        assert call_args[0].endswith("/analytics-metadata")
        assert "/adk/context" not in call_args[0]
        assert call_kwargs["headers"]["Authorization"] == "Bearer test-staff-jwt"


def test_get_analytics_metadata_fallback_api_v1():
    """Test: Falls back to /api/v1/analytics-metadata if root endpoint 404s."""
    mock_404 = MagicMock(status_code=404)
    mock_200 = MagicMock(status_code=200, json=lambda: SAMPLE_ANALYTICS_METADATA)

    with patch("httpx.Client.get", side_effect=[mock_404, mock_200]) as mock_get:
        metadata = get_analytics_metadata(token="test-staff-jwt")
        assert metadata["authorized"] is True
        assert mock_get.call_count == 2
        fallback_call = mock_get.call_args_list[1]
        assert fallback_call[0][0].endswith("/api/v1/analytics-metadata")


def test_get_analytics_metadata_unauthorized():
    """Test: 401 Unauthorized prevents execution."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    with patch("httpx.Client.get", return_value=mock_response):
        with pytest.raises(RuntimeError) as exc_info:
            get_analytics_metadata(token="invalid-token")
        assert "Authentication failed" in str(exc_info.value)


def test_get_analytics_metadata_forbidden():
    """Test: 403 Forbidden for non-staff prevents execution."""
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden: Customer role cannot access analytics"

    with patch("httpx.Client.get", return_value=mock_response):
        with pytest.raises(RuntimeError) as exc_info:
            get_analytics_metadata(token="customer-token")
        assert "Access forbidden" in str(exc_info.value)


def test_reconstruct_database_settings():
    """Test: Reconstructs schema for both actual tables and analytical views."""
    db_settings = reconstruct_database_settings_from_analytics_metadata(
        SAMPLE_ANALYTICS_METADATA
    )
    assert "bigquery" in db_settings
    schema = db_settings["bigquery"]["schema"]

    tbl_key = "banking-agent-rag-mcp.banking_data.customers"
    assert tbl_key in schema
    assert schema[tbl_key]["object_type"] == "TABLE"
    assert schema[tbl_key]["is_scd_type_2"] is True
    assert schema[tbl_key]["scd_columns"] == ["is_current", "record_version"]
    assert "Joined with accounts" in schema[tbl_key]["relationship_information"]
    assert len(schema[tbl_key]["table_schema"]) == 3

    view_key = "banking-agent-rag-mcp.analytics.analytics_customer_360"
    assert view_key in schema
    assert schema[view_key]["object_type"] == "VIEW"
    assert schema[view_key]["is_scd_type_2"] is False
    assert schema[view_key]["scd_columns"] == []
    assert "Curated 360 view" in schema[view_key]["relationship_information"]
    assert len(schema[view_key]["table_schema"]) == 2


def test_load_analytics_metadata_callback():
    """Test: Callback loads metadata into state and caches it; avoids customer PII."""
    analytics_metadata_cache.clear()

    callback_context = SimpleNamespace(
        state={}, session=SimpleNamespace(id="sess-123", user_id="staff@bank.com")
    )

    with patch(
        "app.agent.get_analytics_metadata", return_value=SAMPLE_ANALYTICS_METADATA
    ) as mock_fetch:
        load_analytics_metadata_in_context(callback_context)

        assert mock_fetch.call_count == 1
        assert "analytics_metadata" in callback_context.state
        assert "database_settings" in callback_context.state
        assert callback_context.state["user_role"] == "BANK_STAFF"

        assert "customer_id" not in callback_context.state
        assert "customer_profile" not in callback_context.state
        assert "authorized_account" not in callback_context.state
        assert "authorized_views" not in callback_context.state

        load_analytics_metadata_in_context(callback_context)
        assert mock_fetch.call_count == 1

    new_context = SimpleNamespace(
        state={}, session=SimpleNamespace(id="sess-456", user_id="staff@bank.com")
    )
    with patch(
        "app.agent.get_analytics_metadata", return_value=SAMPLE_ANALYTICS_METADATA
    ) as mock_fetch_2:
        load_analytics_metadata_in_context(new_context)
        assert mock_fetch_2.call_count == 0  # hit cache
        assert "analytics_metadata" in new_context.state
        assert "database_settings" in new_context.state


def test_subagent_setup_before_agent_call_reuses_state():
    """Test: BigQuery subagent reuses populated state without second fetch."""
    callback_context = SimpleNamespace(
        state={"database_settings": {"bigquery": {"schema": {}}}},
        session=SimpleNamespace(id="sess-789", user_id="staff@bank.com"),
    )

    with patch("app.agent.get_analytics_metadata") as mock_fetch:
        setup_before_agent_call(callback_context)
        assert mock_fetch.call_count == 0


def test_root_agent_instructions_prompts():
    """Test: Root Agent instructions contain analytics context and no customer profile."""
    state = {"analytics_metadata": SAMPLE_ANALYTICS_METADATA}
    context = SimpleNamespace(state=state)
    instructions = return_instructions_root(context)

    assert "Analytics Copilot" in instructions
    assert "BANK_STAFF" in instructions
    assert "<ANALYTICS_DATA_CONTEXT>" in instructions
    assert "banking-agent-rag-mcp.banking_data.customers" in instructions
    assert "banking-agent-rag-mcp.analytics.analytics_customer_360" in instructions

    assert "<CUSTOMER_PROFILE>" not in instructions
    assert "<AUTHORIZED_ACCOUNTS>" not in instructions


def test_bigquery_agent_instructions():
    """Test: BigQuery subagent instructions enforce actual table/view names and SCD guidance."""
    instructions = return_instructions_bigquery()

    assert "BANK_STAFF" in instructions
    assert "SCD Type 2" in instructions
    assert "is_current = TRUE" in instructions
    assert "execute_sql" in instructions
    assert "bigquery_nl2sql" in instructions
    assert "customer_views" not in instructions


def test_bigquery_nl2sql_prompt_construction():
    """Test: NL2SQL prompt receives full schema for tables and analytical views."""
    db_settings = reconstruct_database_settings_from_analytics_metadata(
        SAMPLE_ANALYTICS_METADATA
    )
    tool_context = SimpleNamespace(
        state={
            "database_settings": db_settings,
        }
    )

    mock_llm_response = MagicMock(
        text="```sql\nSELECT COUNT(*) FROM `banking-agent-rag-mcp.banking_data.customers` WHERE is_current = TRUE\n```"
    )

    with patch("google.genai.Client.models") as mock_models:
        mock_models.generate_content.return_value = mock_llm_response
        with patch("app.sub_agents.bigquery.tools.llm_client", None):
            with patch("app.sub_agents.bigquery.tools.Client") as mock_client_cls:
                mock_client_instance = MagicMock()
                mock_client_instance.models.generate_content.return_value = (
                    mock_llm_response
                )
                mock_client_cls.return_value = mock_client_instance

                sql = bigquery_nl2sql(
                    question="How many active customers do we have?",
                    tool_context=tool_context,
                )

                assert "SELECT COUNT(*)" in sql
                assert "banking-agent-rag-mcp.banking_data.customers" in sql
                assert tool_context.state["sql_query"] == sql


def test_root_agent_tools_registry():
    """Test: Root agent registers call_bigquery_agent and call_visualization_agent."""
    agent = get_root_agent()
    tool_names = [
        getattr(t, "__name__", getattr(t, "name", str(t))) for t in agent.tools
    ]
    assert "call_bigquery_agent" in tool_names
    assert "call_visualization_agent" in tool_names


def test_prune_schema_for_nl2sql_keyword_match():
    """Test: Question matching balances and customers prunes schema to top relevant tables."""
    db_settings = reconstruct_database_settings_from_analytics_metadata(
        SAMPLE_ANALYTICS_METADATA
    )
    schema = db_settings["bigquery"]["schema"]

    pruned = prune_schema_for_nl2sql(
        schema=schema,
        question="What is the deposit balance by customer segment?",
        force_full=False,
        max_full_tables=2,
    )

    assert "PRIMARY RELEVANT TABLES & VIEWS" in pruned
    assert "OTHER AVAILABLE ENTERPRISE TABLES" in pruned
    assert "analytics_balances" in pruned or "analytics_customer_360" in pruned or "customers" in pruned


def test_prune_schema_for_nl2sql_fallback_hub_views():
    """Test: Generic question with no keyword match falls back to core analytical hub views."""
    db_settings = reconstruct_database_settings_from_analytics_metadata(
        SAMPLE_ANALYTICS_METADATA
    )
    schema = db_settings["bigquery"]["schema"]

    pruned = prune_schema_for_nl2sql(
        schema=schema,
        question="Hello, show me general performance summary",
        force_full=False,
    )

    assert "PRIMARY RELEVANT TABLES & VIEWS" in pruned
    assert "analytics_balances" in pruned or "customers" in pruned


def test_prune_schema_for_nl2sql_force_full():
    """Test: force_full=True returns the complete unpruned schema dictionary."""
    db_settings = reconstruct_database_settings_from_analytics_metadata(
        SAMPLE_ANALYTICS_METADATA
    )
    schema = db_settings["bigquery"]["schema"]

    full_output = prune_schema_for_nl2sql(
        schema=schema,
        question="What is the total balance?",
        force_full=True,
    )

    assert "PRIMARY RELEVANT TABLES" not in full_output
    assert "customers" in full_output

