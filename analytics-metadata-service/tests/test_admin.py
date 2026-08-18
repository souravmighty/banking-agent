import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_admin_validate_endpoint():
    response = client.post("/admin/validate")
    assert response.status_code == 200
    data = response.json()
    assert "valid" in data
    assert data["total_tables"] > 0
    assert data["total_metrics"] > 0

def test_admin_sync_endpoint():
    response = client.post("/admin/sync", json={"force_refresh": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["tables_curated"] > 0
    assert data["metrics_synced"] > 0
