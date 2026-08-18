import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_operational_table_governance_block():
    # customer_identity_mapping is marked allowed_for_analytics = False
    payload = {
        "tables": ["customer_identity_mapping"],
        "metrics": [],
        "dimensions": [],
    }
    response = client.post("/metadata/context", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["validation"]["valid"] is False
    errors = [e["message"] for e in data["validation"]["errors"]]
    assert any("restricted" in msg.lower() for msg in errors)

def test_pii_column_filtering():
    payload = {
        "tables": ["customers"],
        "metrics": [],
        "dimensions": [],
        "exclude_pii": True
    }
    response = client.post("/metadata/context", json=payload)
    assert response.status_code == 200
    data = response.json()
    cust_table = data["tables"][0]
    col_names = [c["column_name"] for c in cust_table["columns"]]
    
    # Sensitive PII columns should be excluded
    assert "email" not in col_names
    assert "phone" not in col_names
    assert "address" not in col_names
    # Non-sensitive / analytic identifier columns should remain
    assert "customer_id" in col_names
    assert "customer_segment" in col_names
