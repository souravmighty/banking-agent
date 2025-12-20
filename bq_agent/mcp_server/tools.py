"""BigQuery-backed tools for MCP server.

This module implements two tools:
- make_transaction(...)
- credit_card_payment(...)

Notes/assumptions:
- Uses Google BigQuery via `google.cloud.bigquery.Client`.
- If `GOOGLE_APPLICATION_CREDENTIALS` is set it will be used. Otherwise
  the client will try default application credentials.
- The credit-card-related fields (latest_statement_balance, minimum_due,
  statement_date, due_date) are not present in the schema; this implementation
  derives sensible defaults where necessary and documents assumptions.
"""
from typing import Optional, Dict, Any
import os
from datetime import date, timedelta

from google.cloud import bigquery

PROJECT_DATASET_ACCOUNTS = "banking-agent-adk-mcp.banking_data.accounts"
PROJECT_DATASET_TRANSACTIONS = "banking-agent-adk-mcp.banking_data.transactions"


def _get_bq_client():
    """Return a BigQuery client (uses ADC or path set in env var)."""
    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if key_path:
        return bigquery.Client.from_service_account_json(key_path)
    return bigquery.Client(project="banking-agent-adk-mcp")


def _fetch_account(client: bigquery.Client, account_id: int) -> Optional[Dict[str, Any]]:
    query = f"SELECT * FROM `{PROJECT_DATASET_ACCOUNTS}` WHERE account_id = @aid LIMIT 1"
    job = client.query(query, job_config=bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("aid", "INT64", account_id)]
    ))
    rows = list(job.result())
    if not rows:
        return None
    row = rows[0]
    return dict(row.items())


def _update_account_balance(client: bigquery.Client, account_id: int, new_balance: float):
    # BigQuery is not an OLTP DB; perform a simple UPDATE statement.
    query = f"UPDATE `{PROJECT_DATASET_ACCOUNTS}` SET balance = @bal WHERE account_id = @aid"
    job = client.query(query, job_config=bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("bal", "FLOAT64", new_balance),
            bigquery.ScalarQueryParameter("aid", "INT64", account_id),
        ]
    ))
    job.result()


def _next_transaction_id(client: bigquery.Client) -> int:
    query = f"SELECT IFNULL(MAX(transaction_id), 0) as mx FROM `{PROJECT_DATASET_TRANSACTIONS}`"
    rows = list(client.query(query).result())
    return int(rows[0]["mx"]) + 1


def _insert_transaction(client: bigquery.Client, tx: Dict[str, Any]):
    table_ref = client.get_table(PROJECT_DATASET_TRANSACTIONS)
    client.insert_rows_json(table_ref, [tx])


def make_transaction(from_account_id: int, to_account_id: int, amount: float, confirm: bool = False) -> Dict[str, Any]:
    """Move money between accounts.

    Steps:
    - Validate both accounts exist and are active.
    - Check `from_account` has sufficient balance (for CHECKING/SAVINGS).
    - If `confirm` is False: return a confirmation message with details.
    - If `confirm` is True: perform the transfer by inserting a transaction row
      and updating the `accounts` table for the from-account balance.

    Returns a dict with `success`, `message`, and additional fields.
    """
    client = _get_bq_client()

    from_acc = _fetch_account(client, from_account_id)
    to_acc = _fetch_account(client, to_account_id)

    if from_acc is None:
        return {"success": False, "message": f"From account {from_account_id} not found"}
    if to_acc is None:
        return {"success": False, "message": f"To account {to_account_id} not found"}

    if from_acc["status"].upper() != "ACTIVE":
        return {"success": False, "message": f"From account {from_account_id} is not active"}
    if to_acc["status"].upper() != "ACTIVE":
        return {"success": False, "message": f"To account {to_account_id} is not active"}

    amt = float(amount)
    if amt <= 0:
        return {"success": False, "message": "Amount must be > 0"}

    # Only CHECKING/SAVINGS can be debited in this implementation
    if from_acc["account_type"].upper() not in ("CHECKING", "SAVINGS"):
        return {"success": False, "message": "Can only send money from CHECKING or SAVINGS accounts"}

    if from_acc["balance"] < amt:
        return {"success": False, "message": "Insufficient balance"}

    # If confirmation not provided, ask for confirmation
    if not confirm:
        return {
            "success": True,
            "confirm_required": True,
            "message": (
                f"Transfer {amt:.2f} {from_acc['currency']} from account {from_account_id} "
                f"(balance: {from_acc['balance']:.2f}) to account {to_account_id} (type: {to_acc['account_type']})."
            ),
        }

    # Perform transfer: subtract from from_acc and (optionally) add to to_acc
    new_from_balance = float(from_acc["balance"]) - amt
    # Update balances
    _update_account_balance(client, from_account_id, new_from_balance)

    # If to account is CHECKING/SAVINGS, add amount; if CREDIT CARD, reduce outstanding (i.e., subtract payment)
    if to_acc["account_type"].upper() in ("CHECKING", "SAVINGS"):
        new_to_balance = float(to_acc["balance"]) + amt
        _update_account_balance(client, to_account_id, new_to_balance)
    else:
        # For CREDIT CARD, we interpret positive balance as amount owed; paying reduces balance
        new_to_balance = float(to_acc["balance"]) - amt
        _update_account_balance(client, to_account_id, new_to_balance)

    tx_id = _next_transaction_id(client)
    tx = {
        "transaction_id": tx_id,
        "from_account_id": from_account_id,
        "to_account_id": to_account_id,
        "amount": amt,
        "type": "TRANSFER",
        "status": "COMPLETED",
        "merchant_name": None,
        "mcc": None,
        "merchant_location": None,
        "timestamp": date.today().isoformat(),
    }
    _insert_transaction(client, tx)

    return {
        "success": True,
        "message": "Transfer completed",
        "transaction": tx,
        "from_new_balance": new_from_balance,
        "to_new_balance": new_to_balance,
    }


def credit_card_payment(cc_account_id: int, from_account_id: int, option: str = "full", amount: Optional[float] = None, confirm: bool = False) -> Dict[str, Any]:
    """Pay a credit card bill from a checking/savings account.

    option: one of "full", "minimum", "custom".
    - If `confirm` is False, returns details and asks for confirmation.
    - If `confirm` True, delegates to `make_transaction` to perform payment.

    Because the schema lacks statement-specific fields, the function estimates
    statement and minimum amounts using conservative heuristics.
    """
    client = _get_bq_client()
    cc_acc = _fetch_account(client, cc_account_id)
    from_acc = _fetch_account(client, from_account_id)

    if cc_acc is None:
        return {"success": False, "message": f"Credit card account {cc_account_id} not found"}
    if from_acc is None:
        return {"success": False, "message": f"From account {from_account_id} not found"}

    if cc_acc["account_type"].upper() != "CREDIT CARD":
        return {"success": False, "message": f"Account {cc_account_id} is not a credit card"}

    # Interpret cc_acc['balance'] as outstanding balance
    outstanding = float(cc_acc["balance"])
    # Heuristics: latest_statement_balance equals outstanding (best-effort)
    latest_statement_balance = outstanding
    # Minimum due: max(2% of statement, 25)
    min_due = max(round(latest_statement_balance * 0.02, 2), 25.0) if latest_statement_balance > 0 else 0.0
    # Statement and due dates: estimate using today
    statement_date = (date.today() - timedelta(days=30)).isoformat()
    due_date = (date.today() + timedelta(days=10)).isoformat()

    details = {
        "outstanding": outstanding,
        "latest_statement_balance": latest_statement_balance,
        "minimum_due": min_due,
        "statement_date": statement_date,
        "due_date": due_date,
    }

    if option not in ("full", "minimum", "custom"):
        return {"success": False, "message": "option must be one of 'full', 'minimum' or 'custom'"}

    if option == "full":
        pay_amount = latest_statement_balance
    elif option == "minimum":
        pay_amount = min_due
    else:
        if amount is None:
            return {"success": False, "message": "For custom option, provide amount"}
        pay_amount = float(amount)

    if not confirm:
        return {"success": True, "confirm_required": True, "payment_amount": pay_amount, "details": details}

    # Delegate to make_transaction with confirmation
    tx_resp = make_transaction(from_account_id=from_account_id, to_account_id=cc_account_id, amount=pay_amount, confirm=True)
    if not tx_resp.get("success"):
        return {"success": False, "message": "Payment failed: " + tx_resp.get("message", "unknown")}

    return {"success": True, "message": "Payment completed", "transaction": tx_resp.get("transaction"), "details": details}
