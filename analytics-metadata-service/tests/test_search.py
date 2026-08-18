import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_search_business_term():
    response = client.post("/metadata/search", json={"query": "churn", "top_k": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] > 0
    names = [r["name"] for r in data["results"]]
    assert any("churn" in n.lower() or "attrition" in n.lower() for n in names)

def test_search_metric():
    response = client.post("/metadata/search", json={"query": "card spend", "top_k": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] > 0
    names = [r["name"] for r in data["results"]]
    assert any("credit_card_spend" in n or "card spend" in n for n in names)

def test_search_column():
    response = client.post("/metadata/search", json={"query": "merchant_category", "top_k": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] > 0
