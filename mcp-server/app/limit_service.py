import logging
import threading
from typing import Dict, Optional
from app.config import settings
from app.schemas import (
    TransactionLimitResponse,
    UpdateLimitResponse,
    TransactionStatus,
    TransactionType,
)
from app.otp_service import otp_service

logger = logging.getLogger(__name__)


class LimitService:
    def __init__(self):
        # In-memory customer limit overrides (e.g. customer_id -> float)
        self._customer_limits: Dict[int, float] = {}
        self._lock = threading.Lock()

    def get_customer_limit(self, customer_id: int) -> float:
        """Returns the configured transaction threshold for the customer."""
        with self._lock:
            return self._customer_limits.get(customer_id, settings.DEFAULT_TRANSACTION_THRESHOLD)

    def get_limit_details(self, customer_id: int) -> TransactionLimitResponse:
        """Returns a comprehensive transaction limit report."""
        cust_limit = self.get_customer_limit(customer_id)
        return TransactionLimitResponse(
            currency="INR",
            default_threshold=settings.DEFAULT_TRANSACTION_THRESHOLD,
            customer_limit=cust_limit,
            effective_limit=cust_limit,
            max_allowed_limit=settings.MAX_TRANSACTION_LIMIT,
            requires_otp_above=cust_limit,
            explanation=(
                f"Transactions exceeding INR {cust_limit:,.2f} require two-factor OTP verification sent to your registered email. "
                f"Maximum configurable limit is INR {settings.MAX_TRANSACTION_LIMIT:,.2f}."
            )
        )

    def requires_otp(self, customer_id: int, amount: float) -> bool:
        """Determines if a transaction amount strictly exceeds the customer limit."""
        threshold = self.get_customer_limit(customer_id)
        return float(amount) > threshold

    def initiate_limit_update(
        self,
        customer_id: int,
        customer_email: str,
        customer_name: str,
        new_limit: float,
        currency: str = "INR"
    ) -> UpdateLimitResponse:
        """
        Initiates a step-up OTP challenge to update the customer transaction limit.
        """
        if new_limit <= 0:
            return UpdateLimitResponse(
                status=TransactionStatus.FAILED,
                message="Transaction limit must be greater than zero.",
                current_limit=self.get_customer_limit(customer_id),
                requested_limit=new_limit,
                currency=currency
            )

        if new_limit > settings.MAX_TRANSACTION_LIMIT:
            return UpdateLimitResponse(
                status=TransactionStatus.FAILED,
                message=(
                    f"Requested limit of INR {new_limit:,.2f} exceeds the maximum allowable bank limit "
                    f"of INR {settings.MAX_TRANSACTION_LIMIT:,.2f}."
                ),
                current_limit=self.get_customer_limit(customer_id),
                requested_limit=new_limit,
                currency=currency
            )

        # Create security challenge
        payload = {
            "new_limit": new_limit,
            "currency": currency,
            "previous_limit": self.get_customer_limit(customer_id)
        }
        challenge, _ = otp_service.create_challenge(
            customer_id=customer_id,
            customer_email=customer_email,
            customer_name=customer_name,
            transaction_type=TransactionType.LIMIT_UPDATE,
            payload=payload
        )

        return UpdateLimitResponse(
            status=TransactionStatus.OTP_REQUIRED,
            message=(
                f"A step-up verification code has been sent to your registered email to approve changing your "
                f"transaction limit to INR {new_limit:,.2f}. Please call verify_transaction_otp with challenge_id '{challenge.challenge_id}' and the 6-digit code."
            ),
            challenge_id=challenge.challenge_id,
            current_limit=self.get_customer_limit(customer_id),
            requested_limit=new_limit,
            currency=currency,
            expires_in_seconds=settings.OTP_EXPIRY_SECONDS
        )

    def apply_limit_update(self, customer_id: int, new_limit: float) -> float:
        """Applies the approved new limit for the customer."""
        with self._lock:
            self._customer_limits[customer_id] = float(new_limit)
        logger.info("Updated transaction limit for customer %s to INR %.2f", customer_id, new_limit)
        return float(new_limit)


limit_service = LimitService()
