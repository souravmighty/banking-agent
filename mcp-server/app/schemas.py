from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TransactionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    OTP_REQUIRED = "OTP_REQUIRED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    EXPIRED = "EXPIRED"
    LOCKED = "LOCKED"


class TransactionType(str, Enum):
    TRANSFER = "TRANSFER"
    CARD_PAYMENT = "CARD_PAYMENT"
    LIMIT_UPDATE = "LIMIT_UPDATE"


class AuthorizedAccountInfo(BaseModel):
    account_number: str
    account_type: str
    account_status: str
    balance: float = 0.0
    currency: str = "INR"


class AuthorizedCardInfo(BaseModel):
    card_account_number: str
    card_number: str
    card_type: str
    credit_limit: float = 0.0
    available_credit: float = 0.0
    outstanding_balance: float = 0.0
    status: str = "ACTIVE"


class AuthorizedBeneficiaryInfo(BaseModel):
    beneficiary_id: int
    beneficiary_name: str
    beneficiary_account_number: str
    bank_name: str
    ifsc_code: str
    status: str = "ACTIVE"


class CustomerAuthContext(BaseModel):
    customer_id: int
    email: str
    name: str = "Valued Customer"
    firebase_uid: Optional[str] = None
    kyc_status: str = "VERIFIED"
    customer_segment: str = "RETAIL"
    accounts: List[AuthorizedAccountInfo] = Field(default_factory=list)
    credit_cards: List[AuthorizedCardInfo] = Field(default_factory=list)
    beneficiaries: List[AuthorizedBeneficiaryInfo] = Field(default_factory=list)


class TransferMoneyResponse(BaseModel):
    status: TransactionStatus
    message: str
    transaction_id: Optional[str] = None
    reference_id: Optional[str] = None
    challenge_id: Optional[str] = None
    source_account: Optional[str] = None
    beneficiary_name: Optional[str] = None
    beneficiary_account: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "INR"
    remaining_balance: Optional[float] = None
    expires_in_seconds: Optional[int] = None


class PayCreditCardResponse(BaseModel):
    status: TransactionStatus
    message: str
    transaction_id: Optional[str] = None
    reference_id: Optional[str] = None
    challenge_id: Optional[str] = None
    source_account: Optional[str] = None
    card_account_number: Optional[str] = None
    card_number_masked: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "INR"
    remaining_account_balance: Optional[float] = None
    new_outstanding_balance: Optional[float] = None
    new_available_credit: Optional[float] = None
    expires_in_seconds: Optional[int] = None


class VerifyOtpResponse(BaseModel):
    status: TransactionStatus
    message: str
    challenge_id: Optional[str] = None
    transaction_type: Optional[TransactionType] = None
    details: Optional[Dict[str, Any]] = None
    remaining_attempts: Optional[int] = None


class TransactionLimitResponse(BaseModel):
    currency: str = "INR"
    default_threshold: float
    customer_limit: float
    effective_limit: float
    max_allowed_limit: float
    requires_otp_above: float
    explanation: str


class UpdateLimitResponse(BaseModel):
    status: TransactionStatus
    message: str
    challenge_id: Optional[str] = None
    current_limit: float
    requested_limit: float
    currency: str = "INR"
    expires_in_seconds: Optional[int] = None


class TransactionStatusResponse(BaseModel):
    status: TransactionStatus
    identifier: str
    transaction_type: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    source_account: Optional[str] = None
    destination: Optional[str] = None
    timestamp: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class AddBeneficiaryResponse(BaseModel):
    status: TransactionStatus
    message: str
    beneficiary_id: Optional[int] = None
    beneficiary_name: Optional[str] = None
    beneficiary_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc_code: Optional[str] = None

