from unittest.mock import patch, MagicMock
from app import tools
from app.schemas import TransactionStatus


def test_transfer_money_below_threshold(mock_customer_context):
    with patch("app.tools.auth_manager.get_auth_context", return_value=mock_customer_context), \
         patch("app.tools.ledger_service.execute_transfer") as mock_exec:
        
        mock_exec.return_value = {
            "status": "COMPLETED",
            "transaction_id": "TXN_TEST123",
            "reference_id": "REF_TEST123",
            "remaining_balance": 22000.0,
            "message": "Transfer successful"
        }
        
        # Transfer 3,000 (< default limit of 5,000)
        res = tools.transfer_money(
            beneficiary="Aarav Sharma",
            amount=3000.0,
            currency="INR"
        )
        
        assert res["status"] == TransactionStatus.COMPLETED
        assert res["transaction_id"] == "TXN_TEST123"
        assert res["remaining_balance"] == 22000.0
        mock_exec.assert_called_once()


def test_transfer_money_above_threshold_triggers_otp(mock_customer_context):
    with patch("app.tools.auth_manager.get_auth_context", return_value=mock_customer_context):
        
        # Transfer 8,000 (> default limit of 5,000)
        res = tools.transfer_money(
            beneficiary="Aarav Sharma",
            amount=8000.0,
            currency="INR"
        )
        
        assert res["status"] == TransactionStatus.OTP_REQUIRED
        assert res["challenge_id"] is not None
        assert res["amount"] == 8000.0
        assert "OTP verification code has been dispatched" in res["message"]


def test_verify_transaction_otp_flow(mock_customer_context):
    with patch("app.tools.auth_manager.get_auth_context", return_value=mock_customer_context), \
         patch("app.tools.ledger_service.execute_transfer") as mock_exec:
        
        mock_exec.return_value = {
            "status": "COMPLETED",
            "transaction_id": "TXN_OTP_OK",
            "reference_id": "REF_OTP_OK",
            "remaining_balance": 15000.0,
            "message": "Transfer successful after OTP verification"
        }
        
        # Trigger OTP
        res = tools.transfer_money(beneficiary="Aarav Sharma", amount=10000.0)
        challenge_id = res["challenge_id"]
        
        # Get the OTP challenge from service
        from app.otp_service import otp_service
        ch = otp_service.get_challenge(challenge_id)
        
        # Verify with wrong OTP
        res_wrong = tools.verify_transaction_otp(challenge_id, "999999")
        assert res_wrong["status"] == TransactionStatus.FAILED
        assert "Incorrect OTP" in res_wrong["message"]
        
        # Verify with correct OTP using challenge salt
        from app.otp_service import otp_service
        # Re-fetch raw OTP or verify using test OTP
        success, _, _ = otp_service.verify_otp(challenge_id, "123456") # test verification


def test_add_beneficiary_tool(mock_customer_context):
    with patch("app.tools.auth_manager.get_auth_context", return_value=mock_customer_context), \
         patch("app.tools.ledger_service.add_beneficiary") as mock_add:
        
        mock_add.return_value = {
            "status": "COMPLETED",
            "beneficiary_id": 5010,
            "beneficiary_name": "Karan Mehra",
            "beneficiary_account_number": "991234567890",
            "bank_name": "State Bank of India",
            "ifsc_code": "SBIN0001234",
            "message": "Successfully registered beneficiary"
        }

        res = tools.add_beneficiary(
            beneficiary_name="Karan Mehra",
            beneficiary_account_number="991234567890",
            bank_name="State Bank of India",
            ifsc_code="SBIN0001234"
        )

        assert res["status"] == TransactionStatus.COMPLETED
        assert res["beneficiary_id"] == 5010
        assert res["beneficiary_name"] == "Karan Mehra"
        assert res["beneficiary_account_number"] == "991234567890"
        mock_add.assert_called_once()

