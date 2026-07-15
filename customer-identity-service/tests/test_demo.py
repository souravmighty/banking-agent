import pytest
from mock import MagicMock, patch
from app.services.demo_service import DemoService
from app.utils.exceptions import CustomerIdentityException
from datetime import datetime, timezone

@pytest.fixture
def mock_demo_repo():
    return MagicMock()

@pytest.fixture
def mock_view_service():
    return MagicMock()

@pytest.fixture
def demo_service(mock_demo_repo, mock_view_service):
    return DemoService(mock_demo_repo, mock_view_service)

def test_allocate_demo_customer_success(demo_service, mock_demo_repo):
    mock_demo_repo.is_email_allocated.return_value = False
    mock_demo_repo.get_available_demo_customer.return_value = {
        "customer_id": "12345",
        "original_name": "Original Name",
        "original_email": "original@example.com"
    }
    mock_demo_repo.allocate_customer.return_value = True
    
    result = demo_service.allocate_demo_customer(
        name="John Doe",
        email="john@gmail.com",
        approved_by="Sourav"
    )
    
    assert result["customer_id"] == 12345
    assert result["status"] == "APPROVED"
    assert "expires_at" in result
    mock_demo_repo.allocate_customer.assert_called_once()
    assert mock_demo_repo.log_audit.call_count == 2

def test_allocate_demo_customer_already_allocated(demo_service, mock_demo_repo):
    mock_demo_repo.is_email_allocated.return_value = True
    
    with pytest.raises(CustomerIdentityException) as exc_info:
        demo_service.allocate_demo_customer(
            name="John Doe",
            email="john@gmail.com",
            approved_by="Sourav"
        )
    
    assert exc_info.value.status_code == 400
    assert "already associated" in exc_info.value.detail

def test_allocate_demo_customer_none_available(demo_service, mock_demo_repo):
    mock_demo_repo.is_email_allocated.return_value = False
    mock_demo_repo.get_available_demo_customer.return_value = None
    
    with pytest.raises(CustomerIdentityException) as exc_info:
        demo_service.allocate_demo_customer(
            name="John Doe",
            email="john@gmail.com",
            approved_by="Sourav"
        )
        
    assert exc_info.value.status_code == 400
    assert "No demo customers are currently available" in exc_info.value.detail

def test_release_demo_customer_success(demo_service, mock_demo_repo, mock_view_service):
    mock_demo_repo.release_customer.return_value = {
        "customer_id": "12345",
        "demo_name": "John Doe",
        "demo_email": "john@gmail.com",
        "firebase_uid": "uid123"
    }
    mock_view_service.delete_authorized_views.return_value = ["view1", "view2"]
    
    result = demo_service.release_demo_customer(customer_id="12345")
    
    assert result["customer_id"] == 12345
    assert result["status"] == "AVAILABLE"
    assert result["deleted_views_count"] == 2
    mock_demo_repo.release_customer.assert_called_with("12345")
    mock_view_service.delete_authorized_views.assert_called_with(12345)
    mock_demo_repo.log_audit.assert_called_with(
        action="Release",
        customer_id="12345",
        demo_email="john@gmail.com",
        firebase_uid="uid123",
        performed_by="Admin",
        remarks="Manual Release. Views deleted: 2"
    )

def test_release_demo_customer_not_found(demo_service, mock_demo_repo):
    mock_demo_repo.release_customer.return_value = None
    
    with pytest.raises(CustomerIdentityException) as exc_info:
        demo_service.release_demo_customer(customer_id="99999")
        
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail


@patch("app.repositories.identity_repository.IdentityRepository")
def test_submit_demo_request_success(mock_identity_repo_class, demo_service, mock_demo_repo):
    mock_identity_repo = mock_identity_repo_class.return_value
    mock_identity_repo.get_by_email.return_value = None
    
    mock_demo_repo.is_email_active_or_pending.return_value = False
    mock_demo_repo.create_demo_request.return_value = {
        "request_id": "req-123",
        "name": "Jane Recruiter",
        "email": "jane@example.com",
        "company": "TestCorp",
        "role": "HR",
        "linkedin": "https://linkedin.com/in/jane",
        "purpose": "Hiring",
        "status": "PENDING",
        "created_at": "2026-07-14T18:00:00+00:00"
    }
    
    result = demo_service.submit_demo_request(
        name="Jane Recruiter",
        email="jane@example.com",
        company="TestCorp",
        role="HR",
        linkedin="https://linkedin.com/in/jane",
        purpose="Hiring"
    )
    
    assert result["request_id"] == "req-123"
    assert result["status"] == "PENDING"
    mock_demo_repo.is_email_active_or_pending.assert_called_once_with("jane@example.com")
    mock_demo_repo.create_demo_request.assert_called_once()


@patch("app.repositories.identity_repository.IdentityRepository")
def test_submit_demo_request_duplicate(mock_identity_repo_class, demo_service, mock_demo_repo):
    mock_identity_repo = mock_identity_repo_class.return_value
    mock_identity_repo.get_by_email.return_value = None
    
    mock_demo_repo.is_email_active_or_pending.return_value = True
    
    with pytest.raises(CustomerIdentityException) as exc_info:
        demo_service.submit_demo_request(
            name="Jane Recruiter",
            email="jane@example.com"
        )
        
    assert exc_info.value.status_code == 400
    assert "already associated with an active or pending" in exc_info.value.detail


@patch("app.repositories.identity_repository.IdentityRepository")
def test_submit_demo_request_existing_customer(mock_identity_repo_class, demo_service, mock_demo_repo):
    mock_identity_repo = mock_identity_repo_class.return_value
    mock_identity_repo.get_by_email.return_value = {
        "customer_id": 1001,
        "email_id": "jane@example.com"
    }
    
    with pytest.raises(CustomerIdentityException) as exc_info:
        demo_service.submit_demo_request(
            name="Jane Recruiter",
            email="jane@example.com"
        )
        
    assert exc_info.value.status_code == 400
    assert "already associated with an existing active bank customer" in exc_info.value.detail


def test_approve_demo_request_success(demo_service, mock_demo_repo):
    mock_demo_repo.get_demo_request_by_id.return_value = {
        "request_id": "req-123",
        "name": "Jane Recruiter",
        "email": "jane@example.com",
        "status": "PENDING"
    }
    mock_demo_repo.is_email_allocated.return_value = False
    mock_demo_repo.get_available_demo_customer.return_value = {
        "customer_id": "111222",
        "original_name": "Original User",
        "original_email": "orig@example.com"
    }
    mock_demo_repo.allocate_customer.return_value = True
    
    result = demo_service.approve_demo_request(request_id="req-123", approved_by="Admin")
    
    assert result["customer_id"] == 111222
    assert result["status"] == "APPROVED"
    mock_demo_repo.update_demo_request_status.assert_called_once_with(
        request_id="req-123",
        status="ALLOCATED",
        approved_by="Admin",
        customer_id="111222",
        expires_at=result["expires_at"],
        remarks="Allocated customer 111222"
    )


def test_approve_demo_request_idempotent(demo_service, mock_demo_repo):
    mock_demo_repo.get_demo_request_by_id.return_value = {
        "request_id": "req-123",
        "name": "Jane Recruiter",
        "email": "jane@example.com",
        "status": "ALLOCATED",
        "customer_id": "111222",
        "expires_at": datetime(2026, 7, 21, tzinfo=timezone.utc)
    }
    
    result = demo_service.approve_demo_request(request_id="req-123", approved_by="Admin")
    
    assert result["customer_id"] == 111222
    assert result["status"] == "ALLOCATED"
    assert "already approved" in result["message"]
    mock_demo_repo.allocate_customer.assert_not_called()


def test_reject_demo_request_success(demo_service, mock_demo_repo):
    mock_demo_repo.get_demo_request_by_id.return_value = {
        "request_id": "req-123",
        "name": "Jane Recruiter",
        "email": "jane@example.com",
        "status": "PENDING"
    }
    
    result = demo_service.reject_demo_request(request_id="req-123", rejected_by="Admin", remarks="Invalid profile")
    
    assert result["status"] == "REJECTED"
    mock_demo_repo.update_demo_request_status.assert_called_once_with(
        request_id="req-123",
        status="REJECTED",
        approved_by="Admin",
        remarks="Invalid profile"
    )


def test_get_dashboard_summary_success(demo_service, mock_demo_repo):
    mock_demo_repo.get_dashboard_summary.return_value = {
        "pending_requests": 5,
        "allocated_customers": 12,
        "available_customers": 8,
        "expired_today": 2
    }
    
    result = demo_service.get_dashboard_summary()
    assert result["pending_requests"] == 5
    assert result["allocated_customers"] == 12
    assert result["available_customers"] == 8
    assert result["expired_today"] == 2

