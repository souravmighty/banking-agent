import pytest
from app.auth import AuthManager, AuthError
from app.schemas import CustomerAuthContext


def test_extract_token_from_headers():
    auth_mgr = AuthManager()
    
    # Bearer standard
    assert auth_mgr.extract_token_from_headers({"authorization": "Bearer token123"}) == "token123"
    assert auth_mgr.extract_token_from_headers({"Authorization": "Bearer token456"}) == "token456"
    
    # Custom headers
    assert auth_mgr.extract_token_from_headers({"x-firebase-id-token": "custom_fb_token"}) == "custom_fb_token"
    assert auth_mgr.extract_token_from_headers({"x-auth-token": "custom_auth_token"}) == "custom_auth_token"
    
    # Empty
    assert auth_mgr.extract_token_from_headers({}) is None


def test_decode_token_payload():
    auth_mgr = AuthManager()
    
    p1 = auth_mgr.decode_token_payload("mock-token:user@example.com")
    assert p1["email"] == "user@example.com"
    
    p2 = auth_mgr.decode_token_payload("mock-uid-1001")
    assert p2["firebase_uid"] == "mock-uid-1001"


def test_resolve_source_account(mock_customer_context):
    auth_mgr = AuthManager()
    
    # Default selection (primary savings)
    acc = auth_mgr.resolve_source_account(mock_customer_context)
    assert acc.account_number == "ACC100101"
    
    # Explicit match
    acc2 = auth_mgr.resolve_source_account(mock_customer_context, "ACC100102")
    assert acc2.account_number == "ACC100102"
    
    # Unauthorized account
    with pytest.raises(AuthError):
        auth_mgr.resolve_source_account(mock_customer_context, "ACC999999")


def test_resolve_beneficiary(mock_customer_context):
    auth_mgr = AuthManager()
    
    # By Name
    ben = auth_mgr.resolve_beneficiary(mock_customer_context, "Aarav Sharma")
    assert ben.beneficiary_id == 1
    
    # By partial name
    ben2 = auth_mgr.resolve_beneficiary(mock_customer_context, "Priya")
    assert ben2.beneficiary_id == 2
    
    # By ID
    ben3 = auth_mgr.resolve_beneficiary(mock_customer_context, "1")
    assert ben3.beneficiary_name == "Aarav Sharma"
    
    # Non-existent
    with pytest.raises(AuthError):
        auth_mgr.resolve_beneficiary(mock_customer_context, "Unknown Payee")


def test_resolve_credit_card(mock_customer_context):
    auth_mgr = AuthManager()
    
    # By last 4 digits
    card = auth_mgr.resolve_credit_card(mock_customer_context, "4444")
    assert card.card_account_number == "CARD_ACC_1001"
    
    # By account number
    card2 = auth_mgr.resolve_credit_card(mock_customer_context, "CARD_ACC_1001")
    assert card2.card_number == "4111-2222-3333-4444"
    
    # Non-existent
    with pytest.raises(AuthError):
        auth_mgr.resolve_credit_card(mock_customer_context, "9999")
