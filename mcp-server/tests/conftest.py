import pytest
from unittest.mock import MagicMock
from app.schemas import (
    CustomerAuthContext,
    AuthorizedAccountInfo,
    AuthorizedCardInfo,
    AuthorizedBeneficiaryInfo,
)


@pytest.fixture
def mock_customer_context():
    return CustomerAuthContext(
        customer_id=1001,
        email="souravmaiti1997@gmail.com",
        name="Sourav Maiti",
        firebase_uid="mock-uid-1001",
        kyc_status="VERIFIED",
        customer_segment="RETAIL",
        accounts=[
            AuthorizedAccountInfo(
                account_number="ACC100101",
                account_type="SAVINGS",
                account_status="ACTIVE",
                balance=25000.0,
                currency="INR"
            ),
            AuthorizedAccountInfo(
                account_number="ACC100102",
                account_type="CURRENT",
                account_status="ACTIVE",
                balance=5000.0,
                currency="INR"
            )
        ],
        credit_cards=[
            AuthorizedCardInfo(
                card_account_number="CARD_ACC_1001",
                card_number="4111-2222-3333-4444",
                card_type="PLATINUM",
                credit_limit=100000.0,
                available_credit=85000.0,
                outstanding_balance=15000.0,
                status="ACTIVE"
            )
        ],
        beneficiaries=[
            AuthorizedBeneficiaryInfo(
                beneficiary_id=1,
                beneficiary_name="Aarav Sharma",
                beneficiary_account_number="ACC200201",
                bank_name="HDFC Bank",
                ifsc_code="HDFC0001234",
                status="ACTIVE"
            ),
            AuthorizedBeneficiaryInfo(
                beneficiary_id=2,
                beneficiary_name="Priya Patel",
                beneficiary_account_number="ACC300301",
                bank_name="ICICI Bank",
                ifsc_code="ICIC0005678",
                status="ACTIVE"
            )
        ]
    )
