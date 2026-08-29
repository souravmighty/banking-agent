# BankPilot FastMCP Transaction Server

Production-grade FastMCP Transaction Server integrated with Google ADK (Agent Development Kit) for customer-facing banking transactions.

---

## 1. Architecture Overview

```
                      +------------------------------------------------+
                      |         Customer-Facing Root Agent             |
                      |                 (ADK Agent)                    |
                      +-----------------------+------------------------+
                                              |
                                              | call_transaction_agent
                                              v
                      +------------------------------------------------+
                      |           Transaction Sub-Agent                |
                      +-----------------------+------------------------+
                                              |
                                              | FastMCP Tools
                                              v
                      +------------------------------------------------+
                      |         FastMCP Transaction Server             |
                      |     (mcp-server/app/server.py, tools.py)       |
                      +-------+-------------------+--------------------+
                              |                   |
            +-----------------+                   +--------------------+
            v                                                          v
+-----------------------+                                  +-----------------------+
|  Identity & Auth      |                                  |   OTP & Security      |
|  (mcp-server/app/auth)|                                  | (mcp-server/app/otp_*)|
|  - Token Extraction   |                                  |  - 6-digit CSPRNG     |
|  - Resource Auth      |                                  |  - Salted SHA-256     |
+-----------+-----------+                                  |  - Resend Email       |
            |                                              +-----------+-----------+
            |                                                          |
            +-------------------------+--------------------------------+
                                      |
                                      v
                      +------------------------------------------------+
                      |         Ledger & SCD Type 2 Engine             |
                      |     (mcp-server/app/ledger_service.py)         |
                      |   - Atomic Balance Checks                      |
                      |   - SCD Type 2 Accounts & Cards                |
                      |   - Double-entry Transactions Log              |
                      |   - Idempotency Protection                     |
                      +-----------------------+------------------------+
                                              |
                                              v
                                   [ Google BigQuery ]
```

---

## 2. Tools Reference

### 1. `transfer_money`
Transfers money to an existing authorized beneficiary payee.
- **Parameters**: `beneficiary` (str), `amount` (float), `currency` (str = "INR"), `source_account` (Optional[str]), `idempotency_key` (Optional[str]).
- **Behavior**:
  - Validates `amount > 0` and verifies active source account ownership and sufficient balance.
  - Matches beneficiary against the authenticated customer's registered payee list.
  - If `amount > threshold` (default `INR 5,000`): returns `status: OTP_REQUIRED` with `challenge_id` and dispatches a 6-digit OTP to the registered email via Resend.
  - If `amount <= threshold`: executes immediately with SCD Type 2 balance updates in BigQuery.

### 2. `pay_credit_card`
Pays an authorized credit card bill from an active deposit account.
- **Parameters**: `card_identifier` (str), `amount` (float), `source_account` (Optional[str]), `idempotency_key` (Optional[str]).
- **Behavior**:
  - Validates active source balance and matches credit card to customer.
  - If `amount > threshold`: dispatches OTP challenge.
  - If `amount <= threshold`: executes payment immediately, updating account balance, card outstanding balance, available credit, and utilization percentage.

### 3. `verify_transaction_otp`
Verifies a transaction-bound OTP code and completes the transaction upon success.
- **Parameters**: `challenge_id` (str), `otp` (str).
- **Behavior**:
  - Validates challenge status, expiration (5 min TTL), and rate limit (max 3 attempts).
  - Compares salted SHA-256 hash.
  - On success, atomically executes the bound operation and returns confirmation details.

### 4. `get_transaction_limit`
Retrieves customer's single-transaction threshold, effective limit, and bank policies.

### 5. `update_transaction_limit`
Requests an update to the transaction threshold (up to `INR 100,000`).
- **Behavior**: Requires 2FA verification. Creates an OTP challenge that updates the limit upon verification.

### 6. `get_transaction_status`
Retrieves execution status by `transaction_id`, `reference_id`, or `challenge_id`.

### 7. `add_beneficiary`
Registers a new authorized beneficiary for fund transfers.
- **Parameters**: `beneficiary_name` (str), `beneficiary_account_number` (str), `bank_name` (str), `ifsc_code` (str).
- **Behavior**:
  - Validates payee inputs.
  - Ensures payee account is not already registered under active status for the customer.
  - Inserts new payee entry into BigQuery `beneficiaries` table.

---

## 3. Running & Testing

### Running Tests
```bash
# Run unit & integration tests
cd mcp-server && PYTHONPATH=. pytest tests/ -v

# Run customer-identity-service tests
PYTHONPATH=customer-identity-service pytest customer-identity-service/tests/ -v
```

### Running the FastMCP Server Standalone
```bash
cd mcp-server && uv run uvicorn app.server:app --port 8080 --reload
```
