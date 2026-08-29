import logging
from typing import Optional, Dict, Any
from app.schemas import (
    TransferMoneyResponse,
    PayCreditCardResponse,
    VerifyOtpResponse,
    TransactionLimitResponse,
    UpdateLimitResponse,
    TransactionStatusResponse,
    AddBeneficiaryResponse,
    TransactionStatus,
    TransactionType,
)
from app.auth import auth_manager, AuthError
from app.otp_service import otp_service, mask_email, mask_identifier
from app.limit_service import limit_service
from app.ledger_service import ledger_service, LedgerError

logger = logging.getLogger(__name__)


def transfer_money(
    beneficiary: str,
    amount: float,
    currency: str = "INR",
    source_account: Optional[str] = None,
    auth_token: Optional[str] = None,
    idempotency_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transfers money to an existing authorized beneficiary payee.
    
    If the transfer amount exceeds the customer's transaction limit (default INR 5,000),
    a 2-Factor OTP challenge is generated and dispatched to the customer's email.
    
    Args:
        beneficiary: Beneficiary name, ID, or account number (must be in authorized payees).
        amount: Amount to transfer (must be positive).
        currency: Base currency code (default: 'INR').
        source_account: Optional source bank account number. Defaults to primary active account.
        auth_token: Optional authentication token (if not provided via headers/context).
        idempotency_key: Optional unique idempotency key to prevent double execution.
    """
    try:
        if amount <= 0:
            return TransferMoneyResponse(
                status=TransactionStatus.FAILED,
                message="Transfer amount must be strictly greater than zero.",
                amount=amount,
                currency=currency
            ).model_dump()

        # 1. Resolve customer identity context deterministically
        context = auth_manager.get_auth_context(auth_token)
        src_acc = auth_manager.resolve_source_account(context, source_account)
        ben = auth_manager.resolve_beneficiary(context, beneficiary)

        # 2. Check source balance
        if src_acc.balance < amount:
            return TransferMoneyResponse(
                status=TransactionStatus.FAILED,
                message=(
                    f"Insufficient funds in account {src_acc.account_number}. "
                    f"Available balance: {currency} {src_acc.balance:,.2f}, Requested: {currency} {amount:,.2f}."
                ),
                source_account=src_acc.account_number,
                beneficiary_name=ben.beneficiary_name,
                beneficiary_account=ben.beneficiary_account_number,
                amount=amount,
                currency=currency,
                remaining_balance=src_acc.balance
            ).model_dump()

        # 3. Check if amount exceeds customer OTP threshold
        if limit_service.requires_otp(context.customer_id, amount):
            payload = {
                "customer_id": context.customer_id,
                "source_account": src_acc.account_number,
                "beneficiary_name": ben.beneficiary_name,
                "beneficiary_account_number": ben.beneficiary_account_number,
                "beneficiary_bank": ben.bank_name,
                "beneficiary_ifsc": ben.ifsc_code,
                "amount": float(amount),
                "currency": currency
            }
            challenge, _ = otp_service.create_challenge(
                customer_id=context.customer_id,
                customer_email=context.email,
                customer_name=context.name,
                transaction_type=TransactionType.TRANSFER,
                payload=payload,
                idempotency_key=idempotency_key
            )
            masked_e = mask_email(context.email)
            masked_b = mask_identifier(ben.beneficiary_account_number)
            return TransferMoneyResponse(
                status=TransactionStatus.OTP_REQUIRED,
                message=(
                    f"This transfer of {currency} {amount:,.2f} exceeds your security threshold. "
                    f"A 6-digit OTP verification code has been dispatched to {masked_e}. "
                    f"Please prompt the user for the OTP code and call verify_transaction_otp(challenge_id='{challenge.challenge_id}', otp=<code>)."
                ),
                challenge_id=challenge.challenge_id,
                source_account=src_acc.account_number,
                beneficiary_name=ben.beneficiary_name,
                beneficiary_account=masked_b,
                amount=amount,
                currency=currency,
                expires_in_seconds=300
            ).model_dump()

        # 4. Immediate execution below threshold
        exec_res = ledger_service.execute_transfer(
            customer_id=context.customer_id,
            source_account_number=src_acc.account_number,
            beneficiary_name=ben.beneficiary_name,
            beneficiary_account_number=ben.beneficiary_account_number,
            beneficiary_bank=ben.bank_name,
            beneficiary_ifsc=ben.ifsc_code,
            amount=amount,
            currency=currency,
            idempotency_key=idempotency_key
        )
        return TransferMoneyResponse(
            status=TransactionStatus.COMPLETED,
            message=exec_res["message"],
            transaction_id=exec_res["transaction_id"],
            reference_id=exec_res["reference_id"],
            source_account=src_acc.account_number,
            beneficiary_name=ben.beneficiary_name,
            beneficiary_account=ben.beneficiary_account_number,
            amount=amount,
            currency=currency,
            remaining_balance=exec_res["remaining_balance"]
        ).model_dump()

    except (AuthError, LedgerError) as e:
        logger.error("Transfer failed with business error: %s", e)
        return TransferMoneyResponse(
            status=TransactionStatus.FAILED,
            message=str(e),
            amount=amount,
            currency=currency
        ).model_dump()
    except Exception as e:
        logger.exception("Unexpected error in transfer_money: %s", e)
        return TransferMoneyResponse(
            status=TransactionStatus.FAILED,
            message=f"An unexpected internal error occurred during transfer: {str(e)}",
            amount=amount,
            currency=currency
        ).model_dump()


def pay_credit_card(
    card_identifier: str,
    amount: float,
    source_account: Optional[str] = None,
    auth_token: Optional[str] = None,
    idempotency_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Pays an authorized customer's credit card bill from their active deposit account.
    
    If the payment amount exceeds the customer's transaction threshold (default INR 5,000),
    a 2-Factor OTP challenge is generated and dispatched to the customer's email.
    
    Args:
        card_identifier: Card account number, card number, or last 4 digits.
        amount: Payment amount (must be positive).
        source_account: Optional source deposit account. Defaults to primary active account.
        auth_token: Optional authentication token.
        idempotency_key: Optional unique idempotency key.
    """
    try:
        if amount <= 0:
            return PayCreditCardResponse(
                status=TransactionStatus.FAILED,
                message="Payment amount must be strictly greater than zero.",
                amount=amount
            ).model_dump()

        # 1. Resolve customer context & resources
        context = auth_manager.get_auth_context(auth_token)
        src_acc = auth_manager.resolve_source_account(context, source_account)
        card = auth_manager.resolve_credit_card(context, card_identifier)

        # 2. Check source balance
        if src_acc.balance < amount:
            return PayCreditCardResponse(
                status=TransactionStatus.FAILED,
                message=(
                    f"Insufficient funds in account {src_acc.account_number}. "
                    f"Available balance: INR {src_acc.balance:,.2f}, Payment amount: INR {amount:,.2f}."
                ),
                source_account=src_acc.account_number,
                card_account_number=card.card_account_number,
                amount=amount,
                remaining_account_balance=src_acc.balance
            ).model_dump()

        # 3. Check if amount exceeds customer threshold
        if limit_service.requires_otp(context.customer_id, amount):
            payload = {
                "customer_id": context.customer_id,
                "source_account": src_acc.account_number,
                "card_account_number": card.card_account_number,
                "card_number": card.card_number,
                "amount": float(amount),
                "currency": "INR"
            }
            challenge, _ = otp_service.create_challenge(
                customer_id=context.customer_id,
                customer_email=context.email,
                customer_name=context.name,
                transaction_type=TransactionType.CARD_PAYMENT,
                payload=payload,
                idempotency_key=idempotency_key
            )
            masked_e = mask_email(context.email)
            masked_c = mask_identifier(card.card_number)
            return PayCreditCardResponse(
                status=TransactionStatus.OTP_REQUIRED,
                message=(
                    f"This credit card payment of INR {amount:,.2f} exceeds your security threshold. "
                    f"A 6-digit OTP verification code has been dispatched to {masked_e}. "
                    f"Please prompt the user for the OTP code and call verify_transaction_otp(challenge_id='{challenge.challenge_id}', otp=<code>)."
                ),
                challenge_id=challenge.challenge_id,
                source_account=src_acc.account_number,
                card_account_number=card.card_account_number,
                card_number_masked=masked_c,
                amount=amount,
                currency="INR",
                expires_in_seconds=300
            ).model_dump()

        # 4. Immediate execution below threshold
        exec_res = ledger_service.execute_credit_card_payment(
            customer_id=context.customer_id,
            source_account_number=src_acc.account_number,
            card_account_number=card.card_account_number,
            amount=amount,
            currency="INR",
            idempotency_key=idempotency_key
        )
        return PayCreditCardResponse(
            status=TransactionStatus.COMPLETED,
            message=exec_res["message"],
            transaction_id=exec_res["transaction_id"],
            reference_id=exec_res["reference_id"],
            source_account=src_acc.account_number,
            card_account_number=card.card_account_number,
            card_number_masked=exec_res["card_number_masked"],
            amount=amount,
            currency="INR",
            remaining_account_balance=exec_res["remaining_account_balance"],
            new_outstanding_balance=exec_res["new_outstanding_balance"],
            new_available_credit=exec_res["new_available_credit"]
        ).model_dump()

    except (AuthError, LedgerError) as e:
        logger.error("Credit card payment failed with business error: %s", e)
        return PayCreditCardResponse(
            status=TransactionStatus.FAILED,
            message=str(e),
            amount=amount
        ).model_dump()
    except Exception as e:
        logger.exception("Unexpected error in pay_credit_card: %s", e)
        return PayCreditCardResponse(
            status=TransactionStatus.FAILED,
            message=f"An unexpected internal error occurred during payment: {str(e)}",
            amount=amount
        ).model_dump()


def verify_transaction_otp(
    challenge_id: str,
    otp: str
) -> Dict[str, Any]:
    """
    Verifies a transaction-bound OTP challenge and executes the approved operation.
    
    Args:
        challenge_id: The security challenge identifier returned when OTP was triggered.
        otp: The 6-digit code sent to the customer's registered email.
    """
    try:
        success, msg, challenge = otp_service.verify_otp(challenge_id, otp)
        if not success or not challenge:
            rem = None
            if challenge:
                rem = max(0, challenge.max_attempts - challenge.attempt_count)
            return VerifyOtpResponse(
                status=TransactionStatus.FAILED if (not challenge or challenge.status != TransactionStatus.LOCKED) else TransactionStatus.LOCKED,
                message=msg,
                challenge_id=challenge_id,
                transaction_type=challenge.transaction_type if challenge else TransactionType.TRANSFER,
                remaining_attempts=rem
            ).model_dump()

        # Execute the bound transaction atomically
        payload = challenge.payload
        t_type = challenge.transaction_type

        if t_type == TransactionType.TRANSFER:
            exec_res = ledger_service.execute_transfer(
                customer_id=challenge.customer_id,
                source_account_number=payload["source_account"],
                beneficiary_name=payload["beneficiary_name"],
                beneficiary_account_number=payload["beneficiary_account_number"],
                beneficiary_bank=payload["beneficiary_bank"],
                beneficiary_ifsc=payload["beneficiary_ifsc"],
                amount=payload["amount"],
                currency=payload.get("currency", "INR"),
                idempotency_key=challenge.idempotency_key
            )
            challenge.execution_result = exec_res
            return VerifyOtpResponse(
                status=TransactionStatus.COMPLETED,
                message=f"OTP verified successfully. {exec_res['message']}",
                challenge_id=challenge_id,
                transaction_type=t_type,
                details=exec_res
            ).model_dump()

        elif t_type == TransactionType.CARD_PAYMENT:
            exec_res = ledger_service.execute_credit_card_payment(
                customer_id=challenge.customer_id,
                source_account_number=payload["source_account"],
                card_account_number=payload["card_account_number"],
                amount=payload["amount"],
                currency=payload.get("currency", "INR"),
                idempotency_key=challenge.idempotency_key
            )
            challenge.execution_result = exec_res
            return VerifyOtpResponse(
                status=TransactionStatus.COMPLETED,
                message=f"OTP verified successfully. {exec_res['message']}",
                challenge_id=challenge_id,
                transaction_type=t_type,
                details=exec_res
            ).model_dump()

        elif t_type == TransactionType.LIMIT_UPDATE:
            new_lim = limit_service.apply_limit_update(challenge.customer_id, payload["new_limit"])
            details = {
                "customer_id": challenge.customer_id,
                "new_limit": new_lim,
                "currency": payload.get("currency", "INR"),
                "previous_limit": payload.get("previous_limit")
            }
            challenge.execution_result = details
            return VerifyOtpResponse(
                status=TransactionStatus.COMPLETED,
                message=f"OTP verified successfully. Your transaction limit has been updated to INR {new_lim:,.2f}.",
                challenge_id=challenge_id,
                transaction_type=t_type,
                details=details
            ).model_dump()

        else:
            return VerifyOtpResponse(
                status=TransactionStatus.FAILED,
                message=f"Unknown transaction type '{t_type}'.",
                challenge_id=challenge_id,
                transaction_type=t_type
            ).model_dump()

    except Exception as e:
        logger.exception("Error verifying OTP: %s", e)
        return VerifyOtpResponse(
            status=TransactionStatus.FAILED,
            message=f"Error verifying OTP and executing transaction: {str(e)}",
            challenge_id=challenge_id,
            transaction_type=TransactionType.TRANSFER
        ).model_dump()


def get_transaction_limit(
    auth_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Returns the customer's current single transaction limit and bank thresholds.
    """
    try:
        context = auth_manager.get_auth_context(auth_token)
        res = limit_service.get_limit_details(context.customer_id)
        return res.model_dump()
    except Exception as e:
        logger.exception("Error in get_transaction_limit: %s", e)
        return {
            "currency": "INR",
            "default_threshold": 5000.0,
            "customer_limit": 5000.0,
            "effective_limit": 5000.0,
            "max_allowed_limit": 100000.0,
            "requires_otp_above": 5000.0,
            "explanation": f"Unable to fetch personalized limits ({str(e)}). Default threshold is INR 5,000.00."
        }


def update_transaction_limit(
    new_limit: float,
    currency: str = "INR",
    auth_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Requests an update to the customer's single-transaction threshold.
    Because this modifies security policy, it requires OTP step-up verification.
    
    Args:
        new_limit: Requested new limit amount in INR (maximum INR 100,000).
        currency: Currency code (default: 'INR').
        auth_token: Optional authentication token.
    """
    try:
        context = auth_manager.get_auth_context(auth_token)
        res = limit_service.initiate_limit_update(
            customer_id=context.customer_id,
            customer_email=context.email,
            customer_name=context.name,
            new_limit=new_limit,
            currency=currency
        )
        return res.model_dump()
    except Exception as e:
        logger.exception("Error in update_transaction_limit: %s", e)
        return UpdateLimitResponse(
            status=TransactionStatus.FAILED,
            message=f"Failed to initiate limit update: {str(e)}",
            current_limit=5000.0,
            requested_limit=new_limit,
            currency=currency
        ).model_dump()


def get_transaction_status(
    identifier: str
) -> Dict[str, Any]:
    """
    Checks the status of a transaction, challenge, or transfer reference.
    
    Args:
        identifier: A transaction_id (TXN_...), reference_id (REF_...), or challenge_id (ch_...).
    """
    try:
        res = ledger_service.get_transaction_status(identifier)
        return res.model_dump()
    except Exception as e:
        logger.exception("Error in get_transaction_status: %s", e)
        return TransactionStatusResponse(
            status=TransactionStatus.FAILED,
            identifier=identifier,
            details={"error": str(e)}
        ).model_dump()


def add_beneficiary(
    beneficiary_name: str,
    beneficiary_account_number: str,
    bank_name: str,
    ifsc_code: str,
    auth_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Registers a new authorized beneficiary for fund transfers.
    
    Args:
        beneficiary_name: Full name or nickname of the payee.
        beneficiary_account_number: The bank account number of the payee.
        bank_name: Name of the payee's bank (e.g. 'HDFC Bank', 'State Bank of India', 'ICICI Bank').
        ifsc_code: Branch routing IFSC code for the payee bank.
        auth_token: Optional authentication token.
    """
    try:
        clean_name = beneficiary_name.strip()
        clean_acc = beneficiary_account_number.strip()
        clean_bank = bank_name.strip()
        clean_ifsc = ifsc_code.strip().upper()

        if not clean_name:
            return AddBeneficiaryResponse(
                status=TransactionStatus.FAILED,
                message="Beneficiary name cannot be empty."
            ).model_dump()

        if not clean_acc:
            return AddBeneficiaryResponse(
                status=TransactionStatus.FAILED,
                message="Beneficiary account number cannot be empty."
            ).model_dump()

        if not clean_bank:
            return AddBeneficiaryResponse(
                status=TransactionStatus.FAILED,
                message="Bank name cannot be empty."
            ).model_dump()

        if not clean_ifsc:
            return AddBeneficiaryResponse(
                status=TransactionStatus.FAILED,
                message="IFSC code cannot be empty."
            ).model_dump()

        # 1. Resolve customer auth context
        context = auth_manager.get_auth_context(auth_token)

        # 2. Add beneficiary via ledger service
        res = ledger_service.add_beneficiary(
            customer_id=context.customer_id,
            beneficiary_name=clean_name,
            beneficiary_account_number=clean_acc,
            bank_name=clean_bank,
            ifsc_code=clean_ifsc
        )
        return AddBeneficiaryResponse(
            status=TransactionStatus.COMPLETED,
            message=res["message"],
            beneficiary_id=res["beneficiary_id"],
            beneficiary_name=res["beneficiary_name"],
            beneficiary_account_number=res["beneficiary_account_number"],
            bank_name=res["bank_name"],
            ifsc_code=res["ifsc_code"]
        ).model_dump()

    except (AuthError, LedgerError) as e:
        logger.error("Add beneficiary failed: %s", e)
        return AddBeneficiaryResponse(
            status=TransactionStatus.FAILED,
            message=str(e),
            beneficiary_name=beneficiary_name,
            beneficiary_account_number=beneficiary_account_number
        ).model_dump()
    except Exception as e:
        logger.exception("Unexpected error in add_beneficiary: %s", e)
        return AddBeneficiaryResponse(
            status=TransactionStatus.FAILED,
            message=f"An unexpected error occurred while adding beneficiary: {str(e)}"
        ).model_dump()

