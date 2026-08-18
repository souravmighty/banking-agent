import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "BankPilot Analytics Metadata Service" in data["service"]

def test_compact_catalog():
    response = client.get("/metadata/catalog")
    assert response.status_code == 200
    data = response.json()
    
    assert "tables" in data
    assert "metrics" in data
    assert "dimensions" in data
    assert len(data["tables"]) > 0
    assert len(data["metrics"]) > 0
    assert len(data["dimensions"]) > 0

    # Verify table fields
    table_names = [t["table"] for t in data["tables"]]
    assert "customers" in table_names
    assert "accounts" in table_names
    assert "transactions" in table_names
    assert "analytics_customer_360" in table_names

    # Check SCD flag and grain
    customers_table = next(t for t in data["tables"] if t["table"] == "customers")
    assert customers_table["scd_type"] == "SCD_TYPE_2"
    assert customers_table["grain"] is not None
    assert len(customers_table["key_metrics"]) > 0

def test_compact_catalog_domain_filter():
    response = client.get("/metadata/catalog?domain=CUSTOMER")
    assert response.status_code == 200
    data = response.json()
    for t in data["tables"]:
        assert t["business_domain"] == "CUSTOMER"
