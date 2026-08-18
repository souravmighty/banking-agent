import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_detailed_context_endpoint():
    payload = {
        "tables": ["customers", "accounts"],
        "metrics": ["total_customer_balance", "new_customer_count"],
        "dimensions": ["customer_segment", "region"],
        "exclude_pii": True
    }
    response = client.post("/metadata/context", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["tables"]) == 2
    assert len(data["metrics"]) == 2
    assert len(data["dimensions"]) == 2
    assert "customers" in data["scd_guidance"]
    assert "accounts" in data["scd_guidance"]
    
    # Check SCD guidance content
    cust_scd = data["scd_guidance"]["customers"]
    assert cust_scd["scd_type"] == "SCD_TYPE_2"
    assert "is_current = TRUE" in cust_scd["current_query_filter"]
    
    # Check relationship was found
    assert len(data["relationships"]) > 0

def test_nl2sql_context_endpoint():
    payload = {
        "question": "What is the total balance of active customers by customer segment?",
        "selected_tables": ["customers", "accounts"],
        "selected_metrics": ["total_customer_balance"],
        "selected_dimensions": ["customer_segment"],
        "strict_governance": True
    }
    response = client.post("/metadata/nl2sql-context", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["validation_passed"] is True
    assert "prompt_context_str" in data
    assert len(data["prompt_context_str"]) > 0
    assert "ANALYTICAL CONTEXT" in data["prompt_context_str"]
    assert "Slowly Changing Dimension" in data["prompt_context_str"]
    assert "is_current = TRUE" in data["prompt_context_str"]

    # Verify PII column exclusions are recorded in governance notes
    assert len(data["governance_notes"]) > 0
