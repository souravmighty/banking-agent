import pytest
from mock import MagicMock, patch
from app.services.authorization_service import AuthorizationService
from app.utils.exceptions import EmailNotVerifiedException, CustomerNotFoundException

@pytest.fixture
def mock_identity_repo():
    mock = MagicMock()
    mock.get_staff_by_email.return_value = None
    return mock

@pytest.fixture
def mock_view_service():
    return MagicMock()

@pytest.fixture
def auth_service(mock_identity_repo, mock_view_service):
    return AuthorizationService(mock_identity_repo, mock_view_service)

def test_check_email_availability_exists(auth_service, mock_identity_repo):
    mock_identity_repo.get_by_email.return_value = {"customer_id": 1, "email_id": "test@test.com", "firebase_uid": None}
    mock_identity_repo.get_staff_by_email.return_value = None
    mock_identity_repo.is_staff_email.return_value = False
    
    result = auth_service.check_email_availability("test@test.com")
    
    assert result["customer_exists"] is True
    assert result["is_staff"] is False
    assert result["already_registered"] is False
    assert result["customer_id"] == 1

def test_check_email_availability_dual_role(auth_service, mock_identity_repo):
    mock_identity_repo.get_by_email.return_value = {"customer_id": 105, "email_id": "staff.customer@bank.com", "firebase_uid": "uid123"}
    mock_identity_repo.get_staff_by_email.return_value = {"email": "staff.customer@bank.com", "firebase_uid": "uid123"}
    mock_identity_repo.is_staff_email.return_value = True
    
    result = auth_service.check_email_availability("staff.customer@bank.com")
    
    assert result["customer_exists"] is True
    assert result["is_staff"] is True
    assert result["already_registered"] is True
    assert result["customer_id"] == 105

def test_check_email_availability_staff_only(auth_service, mock_identity_repo):
    mock_identity_repo.get_by_email.return_value = None
    mock_identity_repo.get_staff_by_email.return_value = {"email": "staff@bank.com", "firebase_uid": "uid123"}
    mock_identity_repo.is_staff_email.return_value = True
    
    result = auth_service.check_email_availability("staff@bank.com")
    
    assert result["customer_exists"] is False
    assert result["is_staff"] is True
    assert result["already_registered"] is True
    assert result["customer_id"] is None

def test_check_email_availability_not_found(auth_service, mock_identity_repo):
    mock_identity_repo.get_by_email.return_value = None
    mock_identity_repo.get_staff_by_email.return_value = None
    mock_identity_repo.is_staff_email.return_value = False
    
    result = auth_service.check_email_availability("missing@test.com")
    
    assert result["customer_exists"] is False
    assert result["is_staff"] is False
    assert result["already_registered"] is False
    assert result["customer_id"] is None

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
