import datetime
import hashlib
import hmac
import logging
import os
import secrets
import threading
import uuid
from typing import Optional, Dict, Any, Tuple
from app.config import settings
from app.schemas import TransactionStatus, TransactionType

logger = logging.getLogger(__name__)


def mask_email(email: str) -> str:
    """Masks an email address for security, e.g. j***e@example.com"""
    if not email or "@" not in email:
        return "***"
    parts = email.split("@")
    user, domain = parts[0], parts[1]
    if len(user) <= 2:
        masked_user = user[0] + "***"
    else:
        masked_user = user[0] + "***" + user[-1]
    return f"{masked_user}@{domain}"


def mask_identifier(ident: str, visible_suffix: int = 4) -> str:
    """Masks an account or card number, e.g. ****1234"""
    if not ident:
        return "****"
    s = str(ident).strip()
    if len(s) <= visible_suffix:
        return "****" + s
    return "****" + s[-visible_suffix:]


class OTPChallenge:
    def __init__(
        self,
        challenge_id: str,
        customer_id: int,
        customer_email: str,
        customer_name: str,
        transaction_type: TransactionType,
        payload: Dict[str, Any],
        otp_hash: str,
        salt: str,
        expires_at: datetime.datetime,
        max_attempts: int = 3,
        idempotency_key: Optional[str] = None
    ):
        self.challenge_id = challenge_id
        self.customer_id = customer_id
        self.customer_email = customer_email
        self.customer_name = customer_name
        self.transaction_type = transaction_type
        self.payload = payload
        self.otp_hash = otp_hash
        self.salt = salt
        self.created_at = datetime.datetime.now(datetime.timezone.utc)
        self.expires_at = expires_at
        self.attempt_count = 0
        self.max_attempts = max_attempts
        self.status = TransactionStatus.PENDING
        self.idempotency_key = idempotency_key
        self.execution_result: Optional[Dict[str, Any]] = None

    def is_expired(self) -> bool:
        return datetime.datetime.now(datetime.timezone.utc) > self.expires_at


class OTPService:
    def __init__(self):
        self._challenges: Dict[str, OTPChallenge] = {}
        self._lock = threading.Lock()

    def _hash_otp(self, otp: str, salt: str) -> str:
        """Computes salted SHA-256 hash of OTP."""
        return hashlib.sha256(f"{salt}:{otp}".encode("utf-8")).hexdigest()

    def create_challenge(
        self,
        customer_id: int,
        customer_email: str,
        customer_name: str,
        transaction_type: TransactionType,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> Tuple[OTPChallenge, str]:
        """
        Creates a new cryptographically secure 6-digit OTP challenge,
        hashes the OTP, stores the challenge, and dispatches the OTP email.
        """
        # 1. Generate secure 6-digit OTP (000000 to 999999)
        raw_otp = f"{secrets.randbelow(1_000_000):06d}"
        salt = secrets.token_hex(16)
        otp_hash = self._hash_otp(raw_otp, salt)
        
        challenge_id = f"ch_{uuid.uuid4().hex[:16]}"
        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now + datetime.timedelta(seconds=settings.OTP_EXPIRY_SECONDS)

        challenge = OTPChallenge(
            challenge_id=challenge_id,
            customer_id=customer_id,
            customer_email=customer_email,
            customer_name=customer_name,
            transaction_type=transaction_type,
            payload=payload,
            otp_hash=otp_hash,
            salt=salt,
            expires_at=expires_at,
            max_attempts=settings.OTP_MAX_ATTEMPTS,
            idempotency_key=idempotency_key
        )

        with self._lock:
            self._challenges[challenge_id] = challenge

        # Send email
        self._send_otp_email(
            to_email=customer_email,
            customer_name=customer_name,
            otp=raw_otp,
            transaction_type=transaction_type,
            payload=payload,
            challenge_id=challenge_id
        )

        return challenge, raw_otp

    def verify_otp(
        self,
        challenge_id: str,
        otp_input: str
    ) -> Tuple[bool, str, Optional[OTPChallenge]]:
        """
        Verifies the user-supplied OTP against the stored challenge.
        Returns (success: bool, message: str, challenge: Optional[OTPChallenge]).
        """
        clean_otp = str(otp_input).strip()
        with self._lock:
            challenge = self._challenges.get(challenge_id)
            if not challenge:
                return False, f"Invalid or unknown challenge ID '{challenge_id}'.", None

            if challenge.status == TransactionStatus.COMPLETED:
                return False, "This OTP challenge has already been verified and completed.", challenge

            if challenge.status == TransactionStatus.LOCKED:
                return False, "This OTP challenge is locked due to exceeding the maximum allowed verification attempts.", challenge

            if challenge.is_expired():
                challenge.status = TransactionStatus.EXPIRED
                return False, "This OTP challenge has expired (validity is 5 minutes). Please initiate a new transaction.", challenge

            # Check attempt limit
            challenge.attempt_count += 1
            expected_hash = challenge.otp_hash
            input_hash = self._hash_otp(clean_otp, challenge.salt)

            if not hmac.compare_digest(input_hash, expected_hash):
                remaining = max(0, challenge.max_attempts - challenge.attempt_count)
                if remaining == 0:
                    challenge.status = TransactionStatus.LOCKED
                    return False, "Incorrect OTP. Maximum attempts exceeded. This security challenge has been locked.", challenge
                return False, f"Incorrect OTP. You have {remaining} attempt(s) remaining.", challenge

            # Successful verification
            challenge.status = TransactionStatus.COMPLETED
            return True, "OTP verified successfully.", challenge

    def get_challenge(self, challenge_id: str) -> Optional[OTPChallenge]:
        with self._lock:
            return self._challenges.get(challenge_id)

    def _send_otp_email(
        self,
        to_email: str,
        customer_name: str,
        otp: str,
        transaction_type: TransactionType,
        payload: Dict[str, Any],
        challenge_id: str
    ) -> None:
        """
        Dispatches the transaction authorization OTP via Resend or console fallback.
        """
        amount = payload.get("amount")
        currency = payload.get("currency", "INR")
        
        if transaction_type == TransactionType.TRANSFER:
            dest_name = payload.get("beneficiary_name", "Beneficiary")
            dest_acc = mask_identifier(payload.get("beneficiary_account_number", ""))
            src_acc = mask_identifier(payload.get("source_account", ""))
            action_desc = f"Fund Transfer of {currency} {amount:,.2f} to {dest_name} ({dest_acc}) from account {src_acc}"
        elif transaction_type == TransactionType.CARD_PAYMENT:
            card_acc = mask_identifier(payload.get("card_account_number", ""))
            src_acc = mask_identifier(payload.get("source_account", ""))
            action_desc = f"Credit Card Payment of {currency} {amount:,.2f} for card {card_acc} from account {src_acc}"
        elif transaction_type == TransactionType.LIMIT_UPDATE:
            new_limit = payload.get("new_limit", 0.0)
            action_desc = f"Update Transaction Security Limit to {currency} {new_limit:,.2f}"
        else:
            action_desc = f"Transaction authorization for {currency} {amount}"

        subject = f"BankPilot Security Code: {otp} for your {transaction_type.value.replace('_', ' ')}"
        
        text_body = f"""Hi {customer_name},

Your one-time authorization code (OTP) for the following operation is:

OTP: {otp}

Operation Details:
- Action: {action_desc}
- Challenge ID: {challenge_id}
- Validity: 5 minutes

If you did not initiate this request, please contact BankPilot security immediately.

Thank you,
BankPilot Security Team"""

        html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>BankPilot Security Verification</title></head>
<body style="margin: 0; padding: 0; background-color: #f5f7fb; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #334155;">
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f5f7fb; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #E5E7EB;">
          <tr>
            <td align="center" style="background: linear-gradient(135deg, #1a1f71 0%, #312e81 100%); padding: 28px;">
              <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 800;">BankPilot</h1>
              <p style="margin: 4px 0 0 0; color: #E3F2FD; font-size: 14px;">Secure Transaction Verification</p>
            </td>
          </tr>
          <tr>
            <td style="padding: 32px; font-size: 15px; line-height: 1.6;">
              <p style="margin: 0 0 16px 0;">Hi <strong>{customer_name}</strong>,</p>
              <p style="margin: 0 0 20px 0;">Please use the following One-Time Password (OTP) to authorize your pending action:</p>
              
              <!-- OTP Box -->
              <div style="text-align: center; margin: 28px 0; background-color: #f8fafc; border: 2px dashed #1a1f71; padding: 20px; border-radius: 10px;">
                <span style="font-family: monospace; font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #1a1f71;">{otp}</span>
                <p style="margin: 8px 0 0 0; font-size: 12px; color: #64748b; text-transform: uppercase;">Valid for 5 minutes &bull; Max 3 attempts</p>
              </div>

              <!-- Transaction Summary -->
              <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; border-radius: 8px; border: 1px solid #E5E7EB; margin-bottom: 24px;">
                <tr>
                  <td style="padding: 12px 16px; font-size: 13px; color: #64748b; border-bottom: 1px solid #E5E7EB;"><strong>Action:</strong></td>
                  <td style="padding: 12px 16px; font-size: 13px; color: #0f172a; border-bottom: 1px solid #E5E7EB;">{action_desc}</td>
                </tr>
                <tr>
                  <td style="padding: 12px 16px; font-size: 13px; color: #64748b;"><strong>Challenge ID:</strong></td>
                  <td style="padding: 12px 16px; font-size: 13px; color: #0f172a; font-family: monospace;">{challenge_id}</td>
                </tr>
              </table>

              <p style="margin: 0 0 12px 0; font-size: 13px; color: #ef4444; background: #fef2f2; border: 1px solid #fee2e2; padding: 10px; border-radius: 6px;">
                ⚠️ <strong>Security Notice:</strong> Never share this OTP with anyone, including bank representatives. BankPilot staff will never ask for your verification code.
              </p>
            </td>
          </tr>
          <tr>
            <td style="background: #f8fafc; border-top: 1px solid #E5E7EB; padding: 18px; text-align: center; font-size: 11px; color: #94a3b8;">
              BankPilot Automated Transaction Security System &bull; FastMCP Protection
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

        # Log outbox notification
        print("\n" + "="*50)
        print(f"TRANSACTION OTP OUTBOX TRIGGERED FOR: {to_email}")
        print(f"SUBJECT: {subject}")
        print(f"OTP: {otp} | CHALLENGE: {challenge_id}")
        print("-"*50)
        print(text_body)
        print("="*50 + "\n")

        # Dispatch via Resend (Sole real-world delivery method)
        resend_api_key = settings.RESEND_API_KEY or os.getenv("RESEND_API_KEY")
        if resend_api_key:
            try:
                import resend
                resend.api_key = resend_api_key
                reply_to_addr = settings.ADMIN_EMAIL or os.getenv("ADMIN_EMAIL", "souravmaiti1997@gmail.com")
                email_from = settings.EMAIL_FROM or os.getenv("EMAIL_FROM", "BankPilot <onboarding@resend.dev>")
                
                payload = {
                    "from": email_from,
                    "to": [to_email],
                    "subject": subject,
                    "text": text_body,
                    "reply_to": reply_to_addr
                }
                if html_body:
                    payload["html"] = html_body

                resend.Emails.send(payload)
                logger.info("Transaction OTP email successfully sent via Resend Python SDK to %s", to_email)
                return
            except Exception as e:
                logger.error("Failed to deliver OTP email via Resend Python SDK to %s: %s", to_email, e)
        else:
            logger.info("Resend API key not configured. Printed OTP to console fallback for %s.", to_email)


otp_service = OTPService()
