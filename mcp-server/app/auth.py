import base64
import json
import logging
import os
from typing import Optional, List, Dict, Any
from google.cloud import bigquery
from app.config import settings
from app.schemas import (
    CustomerAuthContext,
    AuthorizedAccountInfo,
    AuthorizedCardInfo,
    AuthorizedBeneficiaryInfo,
)

logger = logging.getLogger(__name__)

# Context variable for holding active auth token in the current async context if injected
import contextvars
active_auth_token: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("active_auth_token", default=None)


class AuthError(Exception):
    """Raised when authentication or authorization fails."""
    pass


class AuthManager:
    def __init__(self, bq_client: Optional[bigquery.Client] = None):
        self._bq_client = bq_client

    @property
    def bq(self) -> bigquery.Client:
        if self._bq_client is None:
            self._bq_client = bigquery.Client(
                project=settings.GOOGLE_CLOUD_PROJECT,
                location=settings.GOOGLE_CLOUD_LOCATION
            )
        return self._bq_client

    def extract_token_from_headers(self, headers: Dict[str, str]) -> Optional[str]:
        """Extracts Bearer token or custom auth token from headers."""
        if not headers:
            return None
        
        # Check standard Authorization header
        auth_header = headers.get("authorization") or headers.get("Authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                return parts[1]
            return auth_header

        # Check custom headers
        for h in ["x-firebase-id-token", "x-auth-token", "X-Firebase-Id-Token", "X-Auth-Token"]:
            if h in headers:
                return headers[h]
        return None

    def resolve_token(self, token: Optional[str] = None) -> str:
        """Resolves token from argument, context variable, or fallback."""
        if token:
            return token
        ctx_token = active_auth_token.get()
        if ctx_token:
            return ctx_token
        raise AuthError("No authentication token provided or found in context.")

    def decode_token_payload(self, token: str) -> Dict[str, Any]:
        """
        Decodes token payload. Supports Firebase JWT and mock tokens for test/dev.
        """
        if not token:
            raise AuthError("Authentication token is empty.")

        # Dev mock token handling: "mock-token:<email_or_uid>"
        if token.startswith("mock-token:"):
            val = token.split(":", 1)[1].strip()
            if "@" in val:
                return {"email": val, "firebase_uid": f"mock-uid-{val}"}
            else:
                return {"firebase_uid": val}
        if token == "mock-token":
            fallback_email = os.getenv("CUSTOMER_EMAIL_ID", "souravmaiti1997@gmail.com")
            return {"email": fallback_email, "firebase_uid": "mock-uid-default"}
        if token.startswith("mock-uid-"):
            return {"firebase_uid": token}

        # JWT decode without signature verification for payload extraction
        # (Firebase verification can be performed when credentials configured)
        try:
            parts = token.split(".")
            if len(parts) >= 2:
                payload_b64 = parts[1]
                # Pad base64
                rem = len(payload_b64) % 4
                if rem > 0:
                    payload_b64 += "=" * (4 - rem)
                payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode("utf-8")
                return json.loads(payload_json)
        except Exception as e:
            logger.warning("Could not decode JWT payload directly: %s", e)

        # Fallback treat as identifier
        if "@" in token:
            return {"email": token}
        return {"firebase_uid": token}

    def get_auth_context(self, token: Optional[str] = None) -> CustomerAuthContext:
        """
        Resolves customer ID, demographics, authorized accounts, credit cards,
        and beneficiaries from the BigQuery store based on the authenticated token.
        """
        resolved_token = self.resolve_token(token)
        payload = self.decode_token_payload(resolved_token)
        
        email = payload.get("email")
        firebase_uid = payload.get("uid") or payload.get("user_id") or payload.get("firebase_uid") or payload.get("sub")
        
        mapping_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.customer_identity_mapping"
        customers_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.customers"
        accounts_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.accounts"
        cards_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.credit_cards"
        beneficiaries_table = f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.beneficiaries"

        # 1. Resolve customer_id and customer_email
        customer_id: Optional[int] = None
        customer_email: Optional[str] = email if email and "@" in str(email) else None

        # 1a. Try customer-identity-service endpoint if available
        identity_url = getattr(settings, "IDENTITY_SERVICE_URL", "http://localhost:8001").rstrip("/")
        if identity_url and resolved_token:
            try:
                import httpx
                headers = {"Authorization": f"Bearer {resolved_token}"}
                resp = httpx.get(f"{identity_url}/api/v1/mcp/customer-context", headers=headers, timeout=2.0)
                if resp.status_code == 200:
                    data = resp.json()
                    cid = data.get("customer_id")
                    c_email = data.get("email") or data.get("email_id")
                    if cid is not None:
                        customer_id = cid
                    if c_email:
                        customer_email = c_email
            except Exception as e:
                logger.debug("Could not resolve context via customer-identity-service: %s", e)

        # 1b. Resolve customer_id from mapping table in BigQuery
        if customer_id is None and email and "@" in str(email):
            query = f"SELECT customer_id, email_id, firebase_uid FROM `{mapping_table}` WHERE LOWER(email_id) = LOWER(@email)"
            job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", email)]
            )
            rows = list(self.bq.query(query, job_config=job_config))
            if rows:
                customer_id = rows[0].customer_id
                customer_email = rows[0].email_id or customer_email

        if customer_id is None and firebase_uid:
            # Check mock-uid-<id> pattern where <id> is an integer customer_id
            if str(firebase_uid).startswith("mock-uid-"):
                try:
                    candidate_id = int(str(firebase_uid).split("-")[-1])
                    query = f"SELECT customer_id, email_id, firebase_uid FROM `{mapping_table}` WHERE customer_id = @cid"
                    job_config = bigquery.QueryJobConfig(
                        query_parameters=[bigquery.ScalarQueryParameter("cid", "INTEGER", candidate_id)]
                    )
                    rows = list(self.bq.query(query, job_config=job_config))
                    if rows:
                        customer_id = rows[0].customer_id
                        customer_email = rows[0].email_id
                except ValueError:
                    pass

            # Direct firebase_uid lookup
            if customer_id is None:
                query = f"SELECT customer_id, email_id, firebase_uid FROM `{mapping_table}` WHERE firebase_uid = @uid"
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[bigquery.ScalarQueryParameter("uid", "STRING", str(firebase_uid))]
                )
                rows = list(self.bq.query(query, job_config=job_config))
                if rows:
                    customer_id = rows[0].customer_id
                    customer_email = rows[0].email_id

            # Also check if raw_uid (with 'mock-uid-' stripped) exists in mapping
            if customer_id is None and str(firebase_uid).startswith("mock-uid-"):
                raw_uid = str(firebase_uid).replace("mock-uid-", "")
                query = f"SELECT customer_id, email_id, firebase_uid FROM `{mapping_table}` WHERE firebase_uid = @uid"
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[bigquery.ScalarQueryParameter("uid", "STRING", raw_uid)]
                )
                rows = list(self.bq.query(query, job_config=job_config))
                if rows:
                    customer_id = rows[0].customer_id
                    customer_email = rows[0].email_id

        # Fallback if mock_auth_bypass is enabled
        mock_auth_bypass = os.getenv("MOCK_AUTH_BYPASS", "false").lower() == "true"
        if customer_id is None and mock_auth_bypass:
            fallback_email = os.getenv("CUSTOMER_EMAIL_ID", "souravmaiti1997@gmail.com")
            query = f"SELECT customer_id, email_id, firebase_uid FROM `{mapping_table}` WHERE LOWER(email_id) = LOWER(@email)"
            job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", fallback_email)]
            )
            rows = list(self.bq.query(query, job_config=job_config))
            if rows:
                customer_id = rows[0].customer_id
                customer_email = rows[0].email_id

        if customer_id is None:
            raise AuthError(f"Unauthorized: No valid customer record found for token identity (email: {email}, uid: {firebase_uid}).")

        # 2. Fetch customer profile details
        cust_query = f"""
            SELECT customer_id, name, email, customer_status, customer_segment, kyc_status
            FROM `{customers_table}`
            WHERE customer_id = @cid AND is_current = TRUE
        """
        cust_rows = list(self.bq.query(
            cust_query,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("cid", "INTEGER", customer_id)]
            )
        ))
        
        name = "Valued Customer"
        kyc_status = "VERIFIED"
        customer_segment = "RETAIL"
        if cust_rows:
            r = cust_rows[0]
            name = r.name or name
            customer_email = r.email or customer_email
            kyc_status = r.kyc_status or kyc_status
            customer_segment = r.customer_segment or customer_segment

        # 3. Fetch authorized deposit accounts
        acc_query = f"""
            SELECT account_number, account_type, account_status, balance, currency
            FROM `{accounts_table}`
            WHERE customer_id = @cid AND is_current = TRUE
        """
        acc_rows = list(self.bq.query(
            acc_query,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("cid", "INTEGER", customer_id)]
            )
        ))
        accounts = [
            AuthorizedAccountInfo(
                account_number=str(r.account_number),
                account_type=str(r.account_type),
                account_status=str(r.account_status),
                balance=float(r.balance or 0.0),
                currency=str(r.currency or "INR")
            )
            for r in acc_rows
        ]

        # 4. Fetch authorized credit cards
        card_query = f"""
            SELECT card_account_number, card_number, card_type, credit_limit, available_credit, outstanding_balance, status
            FROM `{cards_table}`
            WHERE customer_id = @cid AND is_current = TRUE
        """
        card_rows = list(self.bq.query(
            card_query,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("cid", "INTEGER", customer_id)]
            )
        ))
        credit_cards = [
            AuthorizedCardInfo(
                card_account_number=str(r.card_account_number),
                card_number=str(r.card_number),
                card_type=str(r.card_type),
                credit_limit=float(r.credit_limit or 0.0),
                available_credit=float(r.available_credit or 0.0),
                outstanding_balance=float(r.outstanding_balance or 0.0),
                status=str(r.status or "ACTIVE")
            )
            for r in card_rows
        ]

        # 5. Fetch authorized beneficiaries
        ben_query = f"""
            SELECT beneficiary_id, beneficiary_name, beneficiary_account_number, bank_name, ifsc_code, status
            FROM `{beneficiaries_table}`
            WHERE customer_id = @cid
        """
        ben_rows = list(self.bq.query(
            ben_query,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("cid", "INTEGER", customer_id)]
            )
        ))
        beneficiaries = [
            AuthorizedBeneficiaryInfo(
                beneficiary_id=int(r.beneficiary_id),
                beneficiary_name=str(r.beneficiary_name),
                beneficiary_account_number=str(r.beneficiary_account_number),
                bank_name=str(r.bank_name),
                ifsc_code=str(r.ifsc_code),
                status=str(r.status or "ACTIVE")
            )
            for r in ben_rows
        ]

        return CustomerAuthContext(
            customer_id=customer_id,
            email=customer_email or (email if email and "@" in str(email) else None) or "unknown@bankpilot.dev",
            name=name,
            firebase_uid=firebase_uid,
            kyc_status=kyc_status,
            customer_segment=customer_segment,
            accounts=accounts,
            credit_cards=credit_cards,
            beneficiaries=beneficiaries
        )

    def resolve_source_account(
        self,
        context: CustomerAuthContext,
        requested_account: Optional[str] = None
    ) -> AuthorizedAccountInfo:
        """
        Resolves and verifies that the source account belongs to the customer
        and is currently ACTIVE.
        """
        active_accounts = [
            a for a in context.accounts
            if a.account_status.upper() == "ACTIVE"
        ]
        if not active_accounts:
            raise AuthError("No active accounts found for this customer.")

        if requested_account:
            clean_req = requested_account.strip()
            # Match exact or last 4 digits
            matched = [
                a for a in active_accounts
                if a.account_number == clean_req or a.account_number.endswith(clean_req)
            ]
            if not matched:
                raise AuthError(f"Account '{requested_account}' is not an authorized active account for this customer.")
            return matched[0]

        # Default to primary SAVINGS or CURRENT account
        savings = [a for a in active_accounts if a.account_type.upper() in ["SAVINGS", "CURRENT", "SALARY"]]
        if savings:
            return savings[0]
        return active_accounts[0]

    def resolve_beneficiary(
        self,
        context: CustomerAuthContext,
        beneficiary_identifier: str
    ) -> AuthorizedBeneficiaryInfo:
        """
        Resolves beneficiary by ID, exact name, partial name, or account number.
        Enforces that only ACTIVE beneficiaries mapped to this customer are allowed.
        """
        clean_ident = beneficiary_identifier.strip().lower()
        active_bens = [b for b in context.beneficiaries if b.status.upper() == "ACTIVE"]

        if not active_bens:
            raise AuthError("No active beneficiaries registered for this customer. Please register a beneficiary first.")

        # Try match by ID
        try:
            ben_id = int(clean_ident)
            for b in active_bens:
                if b.beneficiary_id == ben_id:
                    return b
        except ValueError:
            pass

        # Try match by account number
        for b in active_bens:
            if b.beneficiary_account_number.lower() == clean_ident or b.beneficiary_account_number.endswith(clean_ident):
                return b

        # Try match by exact name
        for b in active_bens:
            if b.beneficiary_name.lower() == clean_ident:
                return b

        # Try match by name substring
        name_matches = [b for b in active_bens if clean_ident in b.beneficiary_name.lower()]
        if len(name_matches) == 1:
            return name_matches[0]
        elif len(name_matches) > 1:
            names = ", ".join([f"'{b.beneficiary_name}' (ID: {b.beneficiary_id})" for b in name_matches])
            raise AuthError(f"Multiple beneficiaries match '{beneficiary_identifier}': {names}. Please specify exact beneficiary name or ID.")

        raise AuthError(f"Beneficiary '{beneficiary_identifier}' was not found in your registered payees list.")

    def resolve_credit_card(
        self,
        context: CustomerAuthContext,
        card_identifier: str
    ) -> AuthorizedCardInfo:
        """
        Resolves credit card by account number, card number, or last 4 digits.
        """
        clean_ident = card_identifier.strip()
        active_cards = [c for c in context.credit_cards if c.status.upper() == "ACTIVE"]

        if not active_cards:
            raise AuthError("No active credit cards found for this customer.")

        # Match exact card_account_number or card_number
        for c in active_cards:
            if c.card_account_number == clean_ident or c.card_number == clean_ident:
                return c

        # Match last 4 digits
        last4_matches = [
            c for c in active_cards
            if c.card_number.replace("-", "").endswith(clean_ident) or c.card_account_number.endswith(clean_ident)
        ]
        if len(last4_matches) == 1:
            return last4_matches[0]
        elif len(last4_matches) > 1:
            cards = ", ".join([f"Card ending {c.card_number[-4:]} ({c.card_account_number})" for c in last4_matches])
            raise AuthError(f"Multiple credit cards match '{card_identifier}': {cards}. Please specify exact card account number.")

        # If user passed a generic reference and only 1 active card exists
        generic_terms = ["", "card", "my card", "credit card", "primary", "default", "my credit card"]
        if clean_ident.lower() in generic_terms and len(active_cards) == 1:
            return active_cards[0]

        raise AuthError(f"Credit card '{card_identifier}' was not found among your active cards.")


auth_manager = AuthManager()
