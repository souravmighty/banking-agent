from fastapi.testclient import TestClient
from app.server import app


def test_server_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "tools" in data
    assert "transfer_money" in data["tools"]
    assert "pay_credit_card" in data["tools"]
    assert "verify_transaction_otp" in data["tools"]
    assert "get_transaction_limit" in data["tools"]
    assert "update_transaction_limit" in data["tools"]
    assert "get_transaction_status" in data["tools"]
    assert "add_beneficiary" in data["tools"]
