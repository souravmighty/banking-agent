import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app
from app.services.analytics_metadata_service import AnalyticsMetadataService
from app.dependencies import get_current_user, get_identity_repository, get_analytics_metadata_service
from app.schemas.responses import AnalyticsMetadataResponse

client = TestClient(app)


@pytest.fixture
def mock_bq_service():
    mock_bq = MagicMock()
    # Provide sample metadata for tables and views
    def mock_get_table_metadata(dataset_id, table_id):
        if "customers" in table_id:
            return {
                "table_description": "Business Purpose: Stores customer master records.",
                "fields": [
                    {"name": "customer_id", "type": "INTEGER", "description": "Business meaning: Unique 16-digit customer identifier.", "is_nullable": False, "mode": "REQUIRED"},
                    {"name": "customer_status", "type": "STRING", "description": "Business meaning: Operational status.", "is_nullable": False, "mode": "REQUIRED"},
                    {"name": "eff_start_ts", "type": "TIMESTAMP", "description": "Start timestamp", "is_nullable": False, "mode": "REQUIRED"},
                    {"name": "eff_end_ts", "type": "TIMESTAMP", "description": "End timestamp", "is_nullable": True, "mode": "NULLABLE"},
                    {"name": "is_current", "type": "BOOLEAN", "description": "Current flag", "is_nullable": False, "mode": "REQUIRED"},
                    {"name": "record_version", "type": "INTEGER", "description": "Version", "is_nullable": False, "mode": "REQUIRED"}
                ]
            }
        elif "analytics_customer_360" in table_id:
            return {
                "table_description": "Business Purpose: Curated 360-degree customer view.",
                "fields": [
                    {"name": "customer_id", "type": "INTEGER", "description": "Business meaning: Unique 16-digit customer identifier.", "is_nullable": False, "mode": "REQUIRED"},
                    {"name": "age", "type": "INTEGER", "description": "Customer age.", "is_nullable": True, "mode": "NULLABLE"},
                    {"name": "total_deposit_balance", "type": "FLOAT", "description": "Total liquid balance.", "is_nullable": True, "mode": "NULLABLE"}
                ]
            }
        else:
            return {
                "table_description": f"Metadata description for {table_id}",
                "fields": [
                    {"name": "id", "type": "STRING", "description": f"ID for {table_id}", "is_nullable": False, "mode": "REQUIRED"}
                ]
            }
    mock_bq.get_table_metadata.side_effect = mock_get_table_metadata
    return mock_bq


def test_unauthenticated_user_receives_401():
    """Unauthenticated request must return 401 Unauthorized."""
    # Ensure no bypass is active
    with patch.dict("os.environ", {"MOCK_AUTH_BYPASS": "false"}):
        response = client.get("/analytics-metadata")
        assert response.status_code == 401


def test_customer_role_receives_403(mock_bq_service):
    """Authenticated customer/demo user must return 403 Forbidden."""
    mock_identity_repo = MagicMock()
    mock_identity_repo.is_staff_email.return_value = False
    mock_identity_repo.get_staff_by_uid.return_value = None

    async def mock_user_customer():
        return {
            "uid": "customer-uid-123",
            "email": "customer@example.com",
            "role": "CUSTOMER"
        }

    app.dependency_overrides[get_current_user] = mock_user_customer
    app.dependency_overrides[get_identity_repository] = lambda: mock_identity_repo
    app.dependency_overrides[get_analytics_metadata_service] = lambda: AnalyticsMetadataService(mock_bq_service)

    try:
        response = client.get("/analytics-metadata")
        assert response.status_code == 403
        assert "not authorized as BANK_STAFF" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_demo_user_receives_403(mock_bq_service):
    """Demo user must return 403 Forbidden."""
    mock_identity_repo = MagicMock()
    mock_identity_repo.is_staff_email.return_value = False
    mock_identity_repo.get_staff_by_uid.return_value = None

    async def mock_user_demo():
        return {
            "uid": "demo-uid-999",
            "email": "demo_guest@demo.bankpilot.internal"
        }

    app.dependency_overrides[get_current_user] = mock_user_demo
    app.dependency_overrides[get_identity_repository] = lambda: mock_identity_repo
    app.dependency_overrides[get_analytics_metadata_service] = lambda: AnalyticsMetadataService(mock_bq_service)

    try:
        response = client.get("/analytics-metadata")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_bank_staff_receives_200_and_correct_structure(mock_bq_service):
    """Authenticated BANK_STAFF receives 200 and complete analytics data context."""
    mock_identity_repo = MagicMock()
    mock_identity_repo.is_staff_email.return_value = True

    async def mock_user_staff():
        return {
            "uid": "staff-uid-001",
            "email": "souravmaiti1997@gmail.com",
            "role": "BANK_STAFF"
        }

    app.dependency_overrides[get_current_user] = mock_user_staff
    app.dependency_overrides[get_identity_repository] = lambda: mock_identity_repo
    app.dependency_overrides[get_analytics_metadata_service] = lambda: AnalyticsMetadataService(mock_bq_service)

    try:
        response = client.get("/analytics-metadata")
        assert response.status_code == 200
        data = response.json()

        # 1. Check top-level properties
        assert data["authorized"] is True
        assert data["user_role"] == "BANK_STAFF"
        assert "datasets" in data

        # 2. Strict verification: MUST NOT contain customer-specific fields
        assert "customer_id" not in data
        assert "customer_profile" not in data
        assert "authorized_account" not in data
        assert "authorized_views" not in data

        # 3. Check datasets
        datasets = data["datasets"]
        assert len(datasets) == 2
        
        # Operational dataset
        banking_key = [k for k in datasets.keys() if "banking_data" in k][0]
        banking_ds = datasets[banking_key]
        assert banking_ds["dataset_description"] is not None
        assert banking_ds["tables"] is not None
        assert banking_ds["views"] is None

        # Verify operational tables
        tables = banking_ds["tables"]
        cust_table_key = [k for k in tables.keys() if "customers" in k][0]
        cust_table = tables[cust_table_key]
        assert cust_table["object_type"] == "TABLE"
        assert cust_table["query_object"] == cust_table_key
        assert cust_table["logical_name"] == "customers"
        assert cust_table["is_scd_type_2"] is True
        assert "is_current" in cust_table["scd_columns"]
        assert "is_current = TRUE" in cust_table["ai_usage_guidance"]
        assert cust_table["primary_business_key"] == "customer_id"
        assert len(cust_table["schema"]) > 0
        assert cust_table["schema"][0]["column_name"] == "customer_id"
        assert cust_table["schema"][0]["mode"] == "REQUIRED"

        # Analytical views dataset
        analytics_key = [k for k in datasets.keys() if "analytics" in k and "banking_data" not in k][0]
        analytics_ds = datasets[analytics_key]
        assert analytics_ds["views"] is not None
        assert analytics_ds["tables"] is None

        # Verify analytics views
        views = analytics_ds["views"]
        c360_key = [k for k in views.keys() if "analytics_customer_360" in k][0]
        c360_view = views[c360_key]
        assert c360_view["object_type"] == "VIEW"
        assert c360_view["query_object"] == c360_key
        assert c360_view["logical_name"] == "analytics_customer_360"
        assert c360_view["is_scd_type_2"] is False
        assert len(c360_view["scd_columns"]) == 0
        assert c360_view["primary_business_key"] == "customer_id"
        assert len(c360_view["schema"]) > 0

        # Verify customer-specific views are not in response
        for k in views.keys():
            assert "customer_views" not in k
            assert "customer_" not in k.split(".")[-1] or "analytics_customer" in k

    finally:
        app.dependency_overrides.clear()


def test_api_v1_prefix_route(mock_bq_service):
    """GET /api/v1/analytics-metadata also works identically."""
    mock_identity_repo = MagicMock()
    mock_identity_repo.is_staff_email.return_value = True

    async def mock_user_staff():
        return {
            "uid": "staff-uid-001",
            "email": "staff@bankpilot.com",
            "role": "BANK_STAFF"
        }

    app.dependency_overrides[get_current_user] = mock_user_staff
    app.dependency_overrides[get_identity_repository] = lambda: mock_identity_repo
    app.dependency_overrides[get_analytics_metadata_service] = lambda: AnalyticsMetadataService(mock_bq_service)

    try:
        response = client.get("/api/v1/analytics-metadata")
        assert response.status_code == 200
        assert response.json()["authorized"] is True
    finally:
        app.dependency_overrides.clear()


def test_caching_and_refresh(mock_bq_service):
    """Test that metadata caching works and refresh query parameter invalidates cache."""
    service = AnalyticsMetadataService(mock_bq_service)
    
    # First call - BigQuery is consulted
    res1 = service.get_analytics_metadata()
    initial_call_count = mock_bq_service.get_table_metadata.call_count
    assert initial_call_count > 0

    # Second call without refresh - returned from cache, call count does not increase
    res2 = service.get_analytics_metadata()
    assert mock_bq_service.get_table_metadata.call_count == initial_call_count

    # Invalidate cache
    service.invalidate_cache()
    res3 = service.get_analytics_metadata()
    assert mock_bq_service.get_table_metadata.call_count > initial_call_count
