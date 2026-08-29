import datetime
from app.otp_service import OTPService, mask_email, mask_identifier
from app.schemas import TransactionStatus, TransactionType


def test_mask_helpers():
    assert mask_email("souravmaiti1997@gmail.com") == "s***7@gmail.com"
    assert mask_email("ab@bank.com") == "a***@bank.com"
    assert mask_identifier("ACC100101") == "****0101"
    assert mask_identifier("4111-2222-3333-4444") == "****4444"


def test_create_and_verify_otp_success():
    service = OTPService()
    payload = {"amount": 7500.0, "currency": "INR", "source_account": "ACC100101"}
    
    challenge, raw_otp = service.create_challenge(
        customer_id=1001,
        customer_email="test@example.com",
        customer_name="Test User",
        transaction_type=TransactionType.TRANSFER,
        payload=payload
    )
    
    assert len(raw_otp) == 6
    assert raw_otp.isdigit()
    assert challenge.status == TransactionStatus.PENDING
    assert not challenge.is_expired()
    
    # Verify with correct OTP
    success, msg, ch = service.verify_otp(challenge.challenge_id, raw_otp)
    assert success is True
    assert ch.status == TransactionStatus.COMPLETED


def test_verify_otp_incorrect_attempts_and_lock():
    service = OTPService()
    payload = {"amount": 7500.0}
    
    challenge, raw_otp = service.create_challenge(
        customer_id=1001,
        customer_email="test@example.com",
        customer_name="Test User",
        transaction_type=TransactionType.TRANSFER,
        payload=payload
    )
    
    # 1st wrong attempt
    success, msg, ch = service.verify_otp(challenge.challenge_id, "000000" if raw_otp != "000000" else "111111")
    assert success is False
    assert "2 attempt(s) remaining" in msg
    assert ch.status == TransactionStatus.PENDING
    
    # 2nd wrong attempt
    success, msg, ch = service.verify_otp(challenge.challenge_id, "000000" if raw_otp != "000000" else "111111")
    assert success is False
    assert "1 attempt(s) remaining" in msg
    
    # 3rd wrong attempt -> locked
    success, msg, ch = service.verify_otp(challenge.challenge_id, "000000" if raw_otp != "000000" else "111111")
    assert success is False
    assert ch.status == TransactionStatus.LOCKED
    assert "Maximum attempts exceeded" in msg


def test_verify_otp_expired():
    service = OTPService()
    payload = {"amount": 7500.0}
    
    challenge, raw_otp = service.create_challenge(
        customer_id=1001,
        customer_email="test@example.com",
        customer_name="Test User",
        transaction_type=TransactionType.TRANSFER,
        payload=payload
    )
    
    # Force expired time
    challenge.expires_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=10)
    
    success, msg, ch = service.verify_otp(challenge.challenge_id, raw_otp)
    assert success is False
    assert ch.status == TransactionStatus.EXPIRED
    assert "expired" in msg.lower()
