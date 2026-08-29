import datetime
import logging
import threading
import uuid
from typing import Optional, Dict, Any, List
from google.cloud import bigquery
from app.config import settings
from app.schemas import TransactionStatus, TransactionStatusResponse

logger = logging.getLogger(__name__)


class LedgerError(Exception):
    """Raised when ledger balance or constraint validation fails."""
    pass


class LedgerService:
    def __init__(self, bq_client: Optional[bigquery.Client] = None):
        self._bq_client = bq_client
        self._idempotency_store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    @property
    def bq(self) -> bigquery.Client:
        if self._bq_client is None:
            self._bq_client = bigquery.Client(
                project=settings.GOOGLE_CLOUD_PROJECT,
                location=settings.GOOGLE_CLOUD_LOCATION
            )
        return self._bq_client

    def get_idempotent_result(self, key: Optional[str]) -> Optional[Dict[str, Any]]:
        if not key:
            return None
        with self._lock:
            return self._idempotency_store.get(key)

    def record_idempotent_result(self, key: Optional[str], result: Dict[str, Any]) -> None:
        if not key:
            return
        with self._lock:
            self._idempotency_store[key] = result

    def execute_transfer(
        self,
        customer_id: int,
        source_account_number: str,
        beneficiary_name: str,
        beneficiary_account_number: str,
        beneficiary_bank: str,
        beneficiary_ifsc: str,
        amount: float,
        currency: str = "INR",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes an authorized fund transfer. Enforces SCD Type 2 balance updates
        and ledger entries.
        """
        cached = self.get_idempotent_result(idempotency_key)
        if cached:
            logger.info("Returning cached idempotent result for key: %s", idempotency_key)
            return cached

        accounts_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.accounts"
        transactions_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.transactions"

        # 1. Fetch current source account record
        fetch_acc_query = f"""
            SELECT account_number, customer_id, account_type, account_status, balance, currency, ifsc_code, branch_name, created_at, record_version
            FROM `{accounts_table}`
            WHERE account_number = @acc AND is_current = TRUE
        """
        acc_rows = list(self.bq.query(
            fetch_acc_query,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("acc", "STRING", source_account_number)]
            )
        ))
        if not acc_rows:
            raise LedgerError(f"Active source account '{source_account_number}' was not found.")

        src_acc = acc_rows[0]
        if src_acc.customer_id != customer_id:
            raise LedgerError("Unauthorized: Account does not belong to the authenticated customer.")
        if str(src_acc.account_status).upper() != "ACTIVE":
            raise LedgerError(f"Source account is {src_acc.account_status}. Only ACTIVE accounts can make transfers.")

        current_balance = float(src_acc.balance)
        if current_balance < amount:
            raise LedgerError(
                f"Insufficient funds in account {source_account_number}. "
                f"Available balance: {currency} {current_balance:,.2f}, Required: {currency} {amount:,.2f}."
            )

        new_source_balance = round(current_balance - amount, 2)
        old_version = int(src_acc.record_version)
        new_version = old_version + 1

        ref_id = f"REF_{uuid.uuid4().hex[:12].upper()}"
        txn_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # 2. SCD Type 2 update on source account
        update_src_sql = f"""
            UPDATE `{accounts_table}`
            SET is_current = FALSE, eff_end_ts = CURRENT_TIMESTAMP()
            WHERE account_number = @acc AND is_current = TRUE
        """
        self.bq.query(
            update_src_sql,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("acc", "STRING", source_account_number)]
            )
        ).result()

        insert_src_sql = f"""
            INSERT INTO `{accounts_table}` (
                account_number, customer_id, account_type, account_status,
                balance, currency, ifsc_code, branch_name, created_at,
                eff_start_ts, eff_end_ts, is_current, record_version
            ) VALUES (
                @acc, @cid, @type, @status,
                @bal, @curr, @ifsc, @branch, @created_at,
                CURRENT_TIMESTAMP(), NULL, TRUE, @ver
            )
        """
        self.bq.query(
            insert_src_sql,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("acc", "STRING", src_acc.account_number),
                    bigquery.ScalarQueryParameter("cid", "INTEGER", src_acc.customer_id),
                    bigquery.ScalarQueryParameter("type", "STRING", src_acc.account_type),
                    bigquery.ScalarQueryParameter("status", "STRING", src_acc.account_status),
                    bigquery.ScalarQueryParameter("bal", "FLOAT", new_source_balance),
                    bigquery.ScalarQueryParameter("curr", "STRING", src_acc.currency),
                    bigquery.ScalarQueryParameter("ifsc", "STRING", src_acc.ifsc_code),
                    bigquery.ScalarQueryParameter("branch", "STRING", src_acc.branch_name),
                    bigquery.ScalarQueryParameter("created_at", "DATE", str(src_acc.created_at)),
                    bigquery.ScalarQueryParameter("ver", "INTEGER", new_version),
                ]
            )
        ).result()

        # 3. Insert Outflow (DEBIT) transaction record
        insert_txn_sql = f"""
            INSERT INTO `{transactions_table}` (
                transaction_id, reference_id, account_number, counterparty_account_number,
                transaction_type, currency, direction, amount, merchant_name,
                category, description, transaction_timestamp
            ) VALUES (
                @tid, @rid, @acc, @counter_acc,
                'TRANSFER', @curr, @direction, @amt, @merchant,
                'BANKING', @desc, CURRENT_TIMESTAMP()
            )
        """
        self.bq.query(
            insert_txn_sql,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("tid", "STRING", txn_id),
                    bigquery.ScalarQueryParameter("rid", "STRING", ref_id),
                    bigquery.ScalarQueryParameter("acc", "STRING", source_account_number),
                    bigquery.ScalarQueryParameter("counter_acc", "STRING", beneficiary_account_number),
                    bigquery.ScalarQueryParameter("curr", "STRING", currency),
                    bigquery.ScalarQueryParameter("direction", "STRING", "DEBIT"),
                    bigquery.ScalarQueryParameter("amt", "FLOAT", amount),
                    bigquery.ScalarQueryParameter("merchant", "STRING", beneficiary_bank),
                    bigquery.ScalarQueryParameter("desc", "STRING", f"Transfer to {beneficiary_name} ({beneficiary_account_number})"),
                ]
            )
        ).result()

        # 4. If destination account is an internal account in our bank, credit it as well
        dest_acc_rows = list(self.bq.query(
            fetch_acc_query,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("acc", "STRING", beneficiary_account_number)]
            )
        ))
        if dest_acc_rows:
            dest_acc = dest_acc_rows[0]
            new_dest_balance = round(float(dest_acc.balance) + amount, 2)
            dest_txn_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
            
            # SCD Type 2 update on destination
            self.bq.query(
                update_src_sql,
                job_config=bigquery.QueryJobConfig(
                    query_parameters=[bigquery.ScalarQueryParameter("acc", "STRING", beneficiary_account_number)]
                )
            ).result()

            self.bq.query(
                insert_src_sql,
                job_config=bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("acc", "STRING", dest_acc.account_number),
                        bigquery.ScalarQueryParameter("cid", "INTEGER", dest_acc.customer_id),
                        bigquery.ScalarQueryParameter("type", "STRING", dest_acc.account_type),
                        bigquery.ScalarQueryParameter("status", "STRING", dest_acc.account_status),
                        bigquery.ScalarQueryParameter("bal", "FLOAT", new_dest_balance),
                        bigquery.ScalarQueryParameter("curr", "STRING", dest_acc.currency),
                        bigquery.ScalarQueryParameter("ifsc", "STRING", dest_acc.ifsc_code),
                        bigquery.ScalarQueryParameter("branch", "STRING", dest_acc.branch_name),
                        bigquery.ScalarQueryParameter("created_at", "DATE", str(dest_acc.created_at)),
                        bigquery.ScalarQueryParameter("ver", "INTEGER", int(dest_acc.record_version) + 1),
                    ]
                )
            ).result()

            # Insert CREDIT transaction leg
            self.bq.query(
                insert_txn_sql,
                job_config=bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("tid", "STRING", dest_txn_id),
                        bigquery.ScalarQueryParameter("rid", "STRING", ref_id),
                        bigquery.ScalarQueryParameter("acc", "STRING", beneficiary_account_number),
                        bigquery.ScalarQueryParameter("counter_acc", "STRING", source_account_number),
                        bigquery.ScalarQueryParameter("curr", "STRING", currency),
                        bigquery.ScalarQueryParameter("direction", "STRING", "CREDIT"),
                        bigquery.ScalarQueryParameter("amt", "FLOAT", amount),
                        bigquery.ScalarQueryParameter("merchant", "STRING", "BankPilot Direct Transfer"),
                        bigquery.ScalarQueryParameter("desc", "STRING", f"Transfer received from account {source_account_number}"),
                    ]
                )
            ).result()

        result = {
            "status": "COMPLETED",
            "transaction_id": txn_id,
            "reference_id": ref_id,
            "source_account": source_account_number,
            "beneficiary_name": beneficiary_name,
            "beneficiary_account": beneficiary_account_number,
            "amount": amount,
            "currency": currency,
            "remaining_balance": new_source_balance,
            "message": f"Successfully transferred {currency} {amount:,.2f} to {beneficiary_name}. Reference ID: {ref_id}."
        }
        self.record_idempotent_result(idempotency_key, result)
        return result

    def execute_credit_card_payment(
        self,
        customer_id: int,
        source_account_number: str,
        card_account_number: str,
        amount: float,
        currency: str = "INR",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes an authorized credit card bill payment.
        Debits the source bank account and credits the card balance with SCD Type 2 updates.
        """
        cached = self.get_idempotent_result(idempotency_key)
        if cached:
            return cached

        accounts_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.accounts"
        cards_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.credit_cards"
        transactions_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.transactions"

        # 1. Fetch source account
        fetch_acc_query = f"""
            SELECT account_number, customer_id, account_type, account_status, balance, currency, ifsc_code, branch_name, created_at, record_version
            FROM `{accounts_table}`
            WHERE account_number = @acc AND is_current = TRUE
        """
        acc_rows = list(self.bq.query(
            fetch_acc_query,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("acc", "STRING", source_account_number)]
            )
        ))
        if not acc_rows:
            raise LedgerError(f"Active source account '{source_account_number}' not found.")
        src_acc = acc_rows[0]
        if src_acc.customer_id != customer_id:
            raise LedgerError("Unauthorized: Source account does not belong to authenticated customer.")
        
        current_balance = float(src_acc.balance)
        if current_balance < amount:
            raise LedgerError(
                f"Insufficient funds in account {source_account_number}. "
                f"Available balance: {currency} {current_balance:,.2f}, Payment amount: {currency} {amount:,.2f}."
            )

        # 2. Fetch credit card
        fetch_card_query = f"""
            SELECT card_account_number, customer_id, card_number, card_type, credit_limit, available_credit,
                   outstanding_balance, statement_amount, minimum_due_amount, payment_due_date,
                   statement_date, utilization_percentage, status, created_at, record_version
            FROM `{cards_table}`
            WHERE card_account_number = @card_acc AND is_current = TRUE
        """
        card_rows = list(self.bq.query(
            fetch_card_query,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("card_acc", "STRING", card_account_number)]
            )
        ))
        if not card_rows:
            raise LedgerError(f"Credit card account '{card_account_number}' not found.")
        card = card_rows[0]
        if card.customer_id != customer_id:
            raise LedgerError("Unauthorized: Credit card does not belong to authenticated customer.")

        # Compute updated numbers
        new_source_balance = round(current_balance - amount, 2)
        credit_limit = float(card.credit_limit)
        old_outstanding = float(card.outstanding_balance)
        old_available = float(card.available_credit)

        new_outstanding = round(max(0.0, old_outstanding - amount), 2)
        new_available = round(min(credit_limit, old_available + amount), 2)
        new_util = round((new_outstanding / credit_limit) * 100.0, 2) if credit_limit > 0 else 0.0

        ref_id = f"REF_{uuid.uuid4().hex[:12].upper()}"
        txn_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
        card_number_masked = f"****{str(card.card_number)[-4:]}"

        # 3. SCD Type 2 update on source account
        update_src_sql = f"UPDATE `{accounts_table}` SET is_current = FALSE, eff_end_ts = CURRENT_TIMESTAMP() WHERE account_number = @acc AND is_current = TRUE"
        self.bq.query(update_src_sql, job_config=bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("acc", "STRING", source_account_number)])).result()

        insert_src_sql = f"""
            INSERT INTO `{accounts_table}` (
                account_number, customer_id, account_type, account_status,
                balance, currency, ifsc_code, branch_name, created_at,
                eff_start_ts, eff_end_ts, is_current, record_version
            ) VALUES (
                @acc, @cid, @type, @status,
                @bal, @curr, @ifsc, @branch, @created_at,
                CURRENT_TIMESTAMP(), NULL, TRUE, @ver
            )
        """
        self.bq.query(insert_src_sql, job_config=bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("acc", "STRING", src_acc.account_number),
            bigquery.ScalarQueryParameter("cid", "INTEGER", src_acc.customer_id),
            bigquery.ScalarQueryParameter("type", "STRING", src_acc.account_type),
            bigquery.ScalarQueryParameter("status", "STRING", src_acc.account_status),
            bigquery.ScalarQueryParameter("bal", "FLOAT", new_source_balance),
            bigquery.ScalarQueryParameter("curr", "STRING", src_acc.currency),
            bigquery.ScalarQueryParameter("ifsc", "STRING", src_acc.ifsc_code),
            bigquery.ScalarQueryParameter("branch", "STRING", src_acc.branch_name),
            bigquery.ScalarQueryParameter("created_at", "DATE", str(src_acc.created_at)),
            bigquery.ScalarQueryParameter("ver", "INTEGER", int(src_acc.record_version) + 1),
        ])).result()

        # 4. SCD Type 2 update on credit card
        update_card_sql = f"UPDATE `{cards_table}` SET is_current = FALSE, eff_end_ts = CURRENT_TIMESTAMP() WHERE card_account_number = @card_acc AND is_current = TRUE"
        self.bq.query(update_card_sql, job_config=bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("card_acc", "STRING", card_account_number)])).result()

        insert_card_sql = f"""
            INSERT INTO `{cards_table}` (
                card_account_number, customer_id, card_number, card_type,
                credit_limit, available_credit, outstanding_balance, statement_amount,
                minimum_due_amount, payment_due_date, statement_date, utilization_percentage,
                status, created_at, eff_start_ts, eff_end_ts, is_current, record_version
            ) VALUES (
                @card_acc, @cid, @card_num, @card_type,
                @lim, @avail, @out, @stmt_amt,
                @min_due, @due_dt, @stmt_dt, @util,
                @status, @created_at, CURRENT_TIMESTAMP(), NULL, TRUE, @ver
            )
        """
        self.bq.query(insert_card_sql, job_config=bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("card_acc", "STRING", card.card_account_number),
            bigquery.ScalarQueryParameter("cid", "INTEGER", card.customer_id),
            bigquery.ScalarQueryParameter("card_num", "STRING", card.card_number),
            bigquery.ScalarQueryParameter("card_type", "STRING", card.card_type),
            bigquery.ScalarQueryParameter("lim", "FLOAT", credit_limit),
            bigquery.ScalarQueryParameter("avail", "FLOAT", new_available),
            bigquery.ScalarQueryParameter("out", "FLOAT", new_outstanding),
            bigquery.ScalarQueryParameter("stmt_amt", "FLOAT", float(card.statement_amount)),
            bigquery.ScalarQueryParameter("min_due", "FLOAT", float(card.minimum_due_amount)),
            bigquery.ScalarQueryParameter("due_dt", "DATE", str(card.payment_due_date)),
            bigquery.ScalarQueryParameter("stmt_dt", "DATE", str(card.statement_date)),
            bigquery.ScalarQueryParameter("util", "FLOAT", new_util),
            bigquery.ScalarQueryParameter("status", "STRING", card.status),
            bigquery.ScalarQueryParameter("created_at", "DATE", str(card.created_at)),
            bigquery.ScalarQueryParameter("ver", "INTEGER", int(card.record_version) + 1),
        ])).result()

        # 5. Insert transaction log entries (both DEBIT on bank account and CREDIT on credit card account)
        insert_txn_sql = f"""
            INSERT INTO `{transactions_table}` (
                transaction_id, reference_id, account_number, counterparty_account_number,
                transaction_type, currency, direction, amount, merchant_name,
                category, description, transaction_timestamp
            ) VALUES (
                @tid, @rid, @acc, @counter_acc,
                'CARD_PAYMENT', @curr, @direction, @amt, 'BankPilot Card Services',
                'BANKING', @desc, CURRENT_TIMESTAMP()
            )
        """
        # Debit leg on source bank account
        self.bq.query(insert_txn_sql, job_config=bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("tid", "STRING", txn_id),
            bigquery.ScalarQueryParameter("rid", "STRING", ref_id),
            bigquery.ScalarQueryParameter("acc", "STRING", source_account_number),
            bigquery.ScalarQueryParameter("counter_acc", "STRING", card_account_number),
            bigquery.ScalarQueryParameter("curr", "STRING", currency),
            bigquery.ScalarQueryParameter("direction", "STRING", "DEBIT"),
            bigquery.ScalarQueryParameter("amt", "FLOAT", amount),
            bigquery.ScalarQueryParameter("desc", "STRING", f"Payment towards credit card {card_number_masked}"),
        ])).result()

        # Credit leg on credit card account
        card_txn_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
        self.bq.query(insert_txn_sql, job_config=bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("tid", "STRING", card_txn_id),
            bigquery.ScalarQueryParameter("rid", "STRING", ref_id),
            bigquery.ScalarQueryParameter("acc", "STRING", card_account_number),
            bigquery.ScalarQueryParameter("counter_acc", "STRING", source_account_number),
            bigquery.ScalarQueryParameter("curr", "STRING", currency),
            bigquery.ScalarQueryParameter("direction", "STRING", "CREDIT"),
            bigquery.ScalarQueryParameter("amt", "FLOAT", amount),
            bigquery.ScalarQueryParameter("desc", "STRING", f"Bill payment received from account {source_account_number}"),
        ])).result()

        result = {
            "status": "COMPLETED",
            "transaction_id": txn_id,
            "reference_id": ref_id,
            "source_account": source_account_number,
            "card_account_number": card_account_number,
            "card_number_masked": card_number_masked,
            "amount": amount,
            "currency": currency,
            "remaining_account_balance": new_source_balance,
            "new_outstanding_balance": new_outstanding,
            "new_available_credit": new_available,
            "message": f"Successfully paid {currency} {amount:,.2f} to credit card {card_number_masked}. Reference ID: {ref_id}."
        }
        self.record_idempotent_result(idempotency_key, result)
        return result

    def get_transaction_status(self, identifier: str) -> TransactionStatusResponse:
        """
        Retrieves status of a transaction by transaction_id, reference_id, or challenge_id.
        """
        clean_id = identifier.strip()

        # 1. Check if it's an OTP challenge
        from app.otp_service import otp_service
        challenge = otp_service.get_challenge(clean_id)
        if challenge:
            payload = challenge.payload
            return TransactionStatusResponse(
                status=challenge.status,
                identifier=clean_id,
                transaction_type=challenge.transaction_type.value,
                amount=payload.get("amount") or payload.get("new_limit"),
                currency=payload.get("currency", "INR"),
                source_account=payload.get("source_account"),
                destination=payload.get("beneficiary_name") or payload.get("card_account_number"),
                timestamp=challenge.created_at.isoformat(),
                details={"attempt_count": challenge.attempt_count, "expires_at": challenge.expires_at.isoformat()}
            )

        # 2. Check BigQuery transactions table
        transactions_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.transactions"
        query = f"""
            SELECT transaction_id, reference_id, account_number, counterparty_account_number,
                   transaction_type, currency, direction, amount, merchant_name, category, description, transaction_timestamp
            FROM `{transactions_table}`
            WHERE transaction_id = @id OR reference_id = @id
            LIMIT 1
        """
        rows = list(self.bq.query(
            query,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("id", "STRING", clean_id)]
            )
        ))
        if rows:
            r = rows[0]
            return TransactionStatusResponse(
                status=TransactionStatus.COMPLETED,
                identifier=clean_id,
                transaction_type=str(r.transaction_type),
                amount=float(r.amount),
                currency=str(r.currency),
                source_account=str(r.account_number),
                destination=str(r.counterparty_account_number or r.merchant_name or ""),
                timestamp=str(r.transaction_timestamp),
                details={"direction": str(r.direction), "description": str(r.description), "reference_id": str(r.reference_id)}
            )

        return TransactionStatusResponse(
            status=TransactionStatus.FAILED,
            identifier=clean_id,
            details={"error": f"No transaction or challenge found matching identifier '{identifier}'."}
        )

    def add_beneficiary(
        self,
        customer_id: int,
        beneficiary_name: str,
        beneficiary_account_number: str,
        bank_name: str,
        ifsc_code: str
    ) -> Dict[str, Any]:
        """
        Inserts a new beneficiary into the BigQuery beneficiaries table for the customer.
        """
        beneficiaries_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.beneficiaries"

        # 1. Check if beneficiary account is already registered for this customer
        check_sql = f"""
            SELECT beneficiary_id, beneficiary_name, status
            FROM `{beneficiaries_table}`
            WHERE customer_id = @cid AND beneficiary_account_number = @acc AND status = 'ACTIVE'
            LIMIT 1
        """
        existing_rows = list(self.bq.query(
            check_sql,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("cid", "INTEGER", customer_id),
                    bigquery.ScalarQueryParameter("acc", "STRING", beneficiary_account_number),
                ]
            )
        ))
        if existing_rows:
            r = existing_rows[0]
            raise LedgerError(
                f"Beneficiary with account number '{beneficiary_account_number}' is already registered as '{r.beneficiary_name}'."
            )

        # 2. Determine next beneficiary_id
        id_query = f"SELECT COALESCE(MAX(beneficiary_id), 5000) + 1 AS next_id FROM `{beneficiaries_table}`"
        id_rows = list(self.bq.query(id_query))
        next_id = int(id_rows[0].next_id) if id_rows and getattr(id_rows[0], "next_id", None) is not None else 5001

        # 3. Insert beneficiary record
        insert_sql = f"""
            INSERT INTO `{beneficiaries_table}` (
                beneficiary_id, customer_id, beneficiary_name,
                beneficiary_account_number, bank_name, ifsc_code,
                status, created_at
            ) VALUES (
                @bid, @cid, @name,
                @acc, @bank, @ifsc,
                'ACTIVE', CURRENT_TIMESTAMP()
            )
        """
        self.bq.query(
            insert_sql,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("bid", "INTEGER", next_id),
                    bigquery.ScalarQueryParameter("cid", "INTEGER", customer_id),
                    bigquery.ScalarQueryParameter("name", "STRING", beneficiary_name),
                    bigquery.ScalarQueryParameter("acc", "STRING", beneficiary_account_number),
                    bigquery.ScalarQueryParameter("bank", "STRING", bank_name),
                    bigquery.ScalarQueryParameter("ifsc", "STRING", ifsc_code),
                ]
            )
        ).result()

        return {
            "status": "COMPLETED",
            "beneficiary_id": next_id,
            "beneficiary_name": beneficiary_name,
            "beneficiary_account_number": beneficiary_account_number,
            "bank_name": bank_name,
            "ifsc_code": ifsc_code,
            "message": f"Successfully registered beneficiary '{beneficiary_name}' (Account: {beneficiary_account_number}, Bank: {bank_name}, IFSC: {ifsc_code}) with ID {next_id}."
        }



ledger_service = LedgerService()
