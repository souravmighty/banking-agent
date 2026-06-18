import pytest
from mock import MagicMock, patch
from app.services.authorization_service import AuthorizationService
from app.utils.exceptions import EmailNotVerifiedException, CustomerNotFoundException

@pytest.fixture
def mock_identity_repo():
    return MagicMock()

@pytest.fixture
def mock_view_service():
    return MagicMock()

@pytest.fixture
def auth_service(mock_identity_repo, mock_view_service):
    return AuthorizationService(mock_identity_repo, mock_view_service)

def test_check_email_availability_exists(auth_service, mock_identity_repo):
    mock_identity_repo.get_by_email.return_value = {"customer_id": 1, "email_id": "test@test.com", "firebase_uid": None}
    
    result = auth_service.check_email_availability("test@test.com")
    
    assert result["customer_exists"] is True
    assert result["already_registered"] is False

def test_check_email_availability_not_found(auth_service, mock_identity_repo):
    mock_identity_repo.get_by_email.return_value = None
    
    result = auth_service.check_email_availability("missing@test.com")
    
    assert result["customer_exists"] is False

def test_link_firebase_user_unverified(auth_service):
    token = {"email_verified": False}
    
    with pytest.raises(EmailNotVerifiedException):
        auth_service.link_firebase_user(token)

def test_link_firebase_user_success(auth_service, mock_identity_repo, mock_view_service):
    token = {
        "email_verified": True,
        "uid": "fb-uid-123",
        "email": "test@test.com"
    }
    mock_identity_repo.get_by_email.return_value = {"customer_id": 1001, "email_id": "test@test.com", "firebase_uid": None}
    
    result = auth_service.link_firebase_user(token)
    
    assert result["customer_id"] == 1001
    assert result["registration_completed"] is True
    mock_identity_repo.update_firebase_uid.assert_called_once()
    args, kwargs = mock_identity_repo.update_firebase_uid.call_args
    assert args[0] == 1001
    assert args[1] == "fb-uid-123"
    assert args[2] == "REGISTERED"
    assert isinstance(args[3], str)
    mock_view_service.create_authorized_views.assert_called_with(1001)
