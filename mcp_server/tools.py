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
PROJECT_DATASET_CREDIT_CARDS = "banking-agent-adk-mcp.banking_data.credit_cards"


def _get_bq_client():
    """Return a BigQuery client (uses ADC or path set in env var)."""
    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if key_path:
        return bigquery.Client.from_service_account_json(key_path)
    return bigquery.Client(project="banking-agent-adk-mcp")


def _fetch_account(client: bigquery.Client, account_number: str) -> Optional[Dict[str, Any]]:
    # Query for the CURRENT active version of the account
    query = f"SELECT * FROM `{PROJECT_DATASET_ACCOUNTS}` WHERE account_number = @anum AND is_current = true LIMIT 1"
    job = client.query(query, job_config=bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("anum", "STRING", account_number)]
    ))
    rows = list(job.result())
    if not rows:
        return None
    row = rows[0]
    return dict(row.items())


def _update_account_balance(client: bigquery.Client, account_number: str, new_balance: float):
    # BigQuery UPDATE on the current version
    query = f"UPDATE `{PROJECT_DATASET_ACCOUNTS}` SET balance = @bal WHERE account_number = @anum AND is_current = true"
    job = client.query(query, job_config=bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("bal", "FLOAT64", new_balance),
            bigquery.ScalarQueryParameter("anum", "STRING", account_number),
        ]
    ))
    job.result()


def _fetch_credit_card(client: bigquery.Client, card_account_number: str) -> Optional[Dict[str, Any]]:
    query = f"SELECT * FROM `{PROJECT_DATASET_CREDIT_CARDS}` WHERE card_account_number = @canum AND is_current = true LIMIT 1"
    job = client.query(query, job_config=bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("canum", "STRING", card_account_number)]
    ))
    rows = list(job.result())
    if not rows:
        return None
    return dict(rows[0].items())


def _insert_transaction(client: bigquery.Client, tx: Dict[str, Any]):
    table_ref = client.get_table(PROJECT_DATASET_TRANSACTIONS)
    client.insert_rows_json(table_ref, [tx])


def make_transaction(from_account_number: str, to_account_number: str, amount: float, confirm: bool = False) -> Dict[str, Any]:
    """Move money between accounts using account numbers and ledger-style double entry.

    Steps:
    - Validate both accounts exist and are active.
    - Check `from_account` has sufficient balance.
    - If `confirm` is False: return a confirmation message with details.
    - If `confirm` is True: perform the transfer by inserting TWO transaction rows
      (DEBIT for sender, CREDIT for receiver) and updating balances.
    """
    client = _get_bq_client()

    from_acc = _fetch_account(client, from_account_number)
    to_acc = _fetch_account(client, to_account_number)

    if from_acc is None:
        return {"success": False, "message": f"From account {from_account_number} not found"}
    if to_acc is None:
        return {"success": False, "message": f"To account {to_account_number} not found"}

    if from_acc["account_status"].upper() != "ACTIVE":
        return {"success": False, "message": f"From account {from_account_number} is not active"}
    if to_acc["account_status"].upper() != "ACTIVE":
        return {"success": False, "message": f"To account {to_account_number} is not active"}

    amt = float(amount)
    if amt <= 0:
        return {"success": False, "message": "Amount must be > 0"}

    if from_acc["account_type"].upper() not in ("SAVINGS", "CURRENT", "SALARY"):
        return {"success": False, "message": "Can only send money from SAVINGS, CURRENT or SALARY accounts"}

    if from_acc["balance"] < amt:
        return {"success": False, "message": "Insufficient balance"}

    if not confirm:
        return {
            "success": True,
            "confirm_required": True,
            "message": (
                f"Transfer {amt:.2f} {from_acc['currency']} from account {from_account_number} "
                f"to account {to_account_number}."
            ),
        }

    # Perform transfer
    new_from_balance = float(from_acc["balance"]) - amt
    new_to_balance = float(to_acc["balance"]) + amt
    
    _update_account_balance(client, from_account_number, new_from_balance)
    _update_account_balance(client, to_account_number, new_to_balance)

    ref_id = f"REF_{date.today().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
    timestamp = datetime.now().isoformat()

    # Row 1: DEBIT
    tx_debit = {
        "transaction_id": f"TXN_{random.randint(10**11, 10**12-1)}",
        "reference_id": ref_id,
        "account_number": from_account_number,
        "counterparty_account_number": to_account_number,
        "transaction_type": "TRANSFER",
        "currency": from_acc["currency"],
        "direction": "DEBIT",
        "amount": amt,
        "merchant_name": None,
        "category": "BANKING",
        "description": f"Transfer to {to_account_number}",
        "transaction_timestamp": timestamp,
    }
    _insert_transaction(client, tx_debit)

    # Row 2: CREDIT
    tx_credit = {
        "transaction_id": f"TXN_{random.randint(10**11, 10**12-1)}",
        "reference_id": ref_id,
        "account_number": to_account_number,
        "counterparty_account_number": from_account_number,
        "transaction_type": "TRANSFER",
        "currency": to_acc["currency"],
        "direction": "CREDIT",
        "amount": amt,
        "merchant_name": None,
        "category": "BANKING",
        "description": f"Transfer from {from_account_number}",
        "transaction_timestamp": timestamp,
    }
    _insert_transaction(client, tx_credit)

    return {
        "success": True,
        "message": "Transfer completed",
        "reference_id": ref_id,
        "from_new_balance": new_from_balance,
        "to_new_balance": new_to_balance,
    }


def credit_card_payment(cc_account_number: str, from_account_number: str, option: str = "full", amount: Optional[float] = None, confirm: bool = False) -> Dict[str, Any]:
    """Pay a credit card bill from a savings/current account."""
    client = _get_bq_client()
    cc_acc = _fetch_credit_card(client, cc_account_number)
    from_acc = _fetch_account(client, from_account_number)

    if cc_acc is None:
        return {"success": False, "message": f"Credit card {cc_account_number} not found"}
    if from_acc is None:
        return {"success": False, "message": f"From account {from_account_number} not found"}

    pay_amount = 0.0
    if option == "full":
        pay_amount = float(cc_acc["outstanding_balance"])
    elif option == "minimum":
        pay_amount = float(cc_acc["minimum_due_amount"])
    else:
        if amount is None: return {"success": False, "message": "Amount required for custom payment"}
        pay_amount = float(amount)

    if not confirm:
        return {"success": True, "confirm_required": True, "payment_amount": pay_amount}

    # Execute payment
    new_from_balance = float(from_acc["balance"]) - pay_amount
    _update_account_balance(client, from_account_number, new_from_balance)
    
    # Update CC balance
    new_cc_balance = float(cc_acc["outstanding_balance"]) - pay_amount
    query = f"UPDATE `{PROJECT_DATASET_CREDIT_CARDS}` SET outstanding_balance = @bal, available_credit = credit_limit - @bal WHERE card_account_number = @anum AND is_current = true"
    client.query(query, job_config=bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("bal", "FLOAT64", new_cc_balance),
            bigquery.ScalarQueryParameter("anum", "STRING", cc_account_number),
        ]
    )).result()

    return {"success": True, "message": "CC Payment completed", "amount_paid": pay_amount}
