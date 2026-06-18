import pytest
from mock import MagicMock, patch
from app.services.view_service import map_to_source_table, get_scd_metadata, ViewService
from app.schemas.responses import FieldMetadata, AuthorizedViewDetail, ADKContextResponse

def test_map_to_source_table():
    assert map_to_source_table("customer_1001_customer_v") == "customers"
    assert map_to_source_table("customer_1001_accounts_v") == "accounts"
    assert map_to_source_table("customer_1001_transactions_v") == "transactions"
    assert map_to_source_table("credit_cards") == "credit_cards"
    assert map_to_source_table("loans") == "loans"
    assert map_to_source_table("some_unknown_table") == "some_unknown_table"

def test_get_scd_metadata():
    customers_meta = get_scd_metadata("customer_1001_customer_v")
    assert customers_meta["is_scd_type_2"] is True
    assert "is_current" in customers_meta["scd_columns"]

    transactions_meta = get_scd_metadata("customer_1001_transactions_v")
    assert transactions_meta["is_scd_type_2"] is False
    assert len(transactions_meta["scd_columns"]) == 0

def test_view_service_metadata_construction():
    mock_bq = MagicMock()
    
    # Mock return value of get_table_metadata
    mock_bq.get_table_metadata.return_value = {
        "table_description": "Mock table description for accounts",
        "fields": [
            {"name": "account_number", "type": "STRING", "description": "Acc num desc", "is_nullable": False, "mode": "REQUIRED"},
            {"name": "balance", "type": "FLOAT", "description": "Balance desc", "is_nullable": False, "mode": "REQUIRED"}
        ]
    }
    
    view_service = ViewService(mock_bq)
    
    view_names = ["project.customer_views.customer_1001_accounts_v"]
    results = view_service.get_authorized_views_metadata(view_names)
    
    assert len(results) == 1
    view_meta = results[0]
    
    assert view_meta["view_name"] == "customer_views.customer_1001_accounts_v"
    assert "accounts" in view_meta["table_description"]
    # Check that SCD query guidance was added to the ai_usage_guidance field
    assert "is_current = TRUE" in view_meta["ai_usage_guidance"]
    assert view_meta["is_scd_type_2"] is True
    assert "eff_start_ts" in view_meta["scd_columns"]
    
    assert len(view_meta["schema"]) == 2
    assert view_meta["schema"][0]["column_name"] == "account_number"
    assert view_meta["schema"][0]["description"] == "Acc num desc"

@patch("app.routers.adk.get_current_user")
@patch("app.routers.adk.get_customer_service")
@patch("app.routers.adk.get_view_service")
def test_adk_context_schema_validation(mock_get_view_service, mock_get_customer_service, mock_get_current_user):
    # This test validates that the response returned from ViewService complies with Pydantic model schemas
    
    mock_view_service = MagicMock()
    mock_view_service.create_authorized_views.return_value = ["customer_views.customer_1001_accounts_v"]
    mock_view_service.get_authorized_views_metadata.return_value = [
        {
            "view_name": "customer_views.customer_1001_accounts_v",
            "table_description": "Accounts description with AI guidance.",
            "is_scd_type_2": True,
            "scd_columns": ["eff_start_ts", "eff_end_ts", "is_current", "record_version"],
            "schema": [
                {"column_name": "account_number", "type": "STRING", "description": "Acc num desc", "mode": "REQUIRED"}
            ]
        }
    ]
    
    # Try validating response model with pydantic
    response_data = {
        "customer_id": 1001,
        "customer": {"customer_id": 1001, "name": "Test User"},
        "authorized_views": mock_view_service.get_authorized_views_metadata("..."),
        "authorized_accounts": [
            {"account_number": "100234567890", "account_type": "SAVINGS", "account_status": "ACTIVE"}
        ]
    }
    
    validated = ADKContextResponse(**response_data)
    assert validated.customer_id == 1001
    assert len(validated.authorized_views) == 1
    assert validated.authorized_views[0].view_name == "customer_views.customer_1001_accounts_v"
    assert validated.authorized_views[0].is_scd_type_2 is True
    assert validated.authorized_views[0].schema[0].column_name == "account_number"
    assert validated.authorized_accounts is not None
    assert len(validated.authorized_accounts) == 1
    assert validated.authorized_accounts[0].account_number == "100234567890"
    assert validated.authorized_accounts[0].account_type == "SAVINGS"
    assert validated.authorized_accounts[0].account_status == "ACTIVE"
