from app.limit_service import LimitService
from app.schemas import TransactionStatus


def test_limit_thresholds():
    service = LimitService()
    
    # Default is 5,000
    assert service.get_customer_limit(1001) == 5000.0
    assert not service.requires_otp(1001, 4999.0)
    assert not service.requires_otp(1001, 5000.0)
    assert service.requires_otp(1001, 5001.0)


def test_initiate_and_apply_limit_update():
    service = LimitService()
    
    # Invalid zero / negative
    res_neg = service.initiate_limit_update(1001, "test@test.com", "Test", -50.0)
    assert res_neg.status == TransactionStatus.FAILED
    
    # Invalid exceeds maximum 100,000
    res_max = service.initiate_limit_update(1001, "test@test.com", "Test", 150000.0)
    assert res_max.status == TransactionStatus.FAILED
    
    # Valid limit update -> requires OTP
    res_valid = service.initiate_limit_update(1001, "test@test.com", "Test", 25000.0)
    assert res_valid.status == TransactionStatus.OTP_REQUIRED
    assert res_valid.challenge_id is not None
    
    # Apply
    service.apply_limit_update(1001, 25000.0)
    assert service.get_customer_limit(1001) == 25000.0
    assert not service.requires_otp(1001, 20000.0)
    assert service.requires_otp(1001, 25001.0)
