from unittest.mock import MagicMock
import pytest
from app.ledger_service import LedgerService, LedgerError


def test_idempotency_cache():
    service = LedgerService(bq_client=MagicMock())
    service.record_idempotent_result("key_123", {"status": "COMPLETED", "tx_id": "TXN_1"})
    
    assert service.get_idempotent_result("key_123") == {"status": "COMPLETED", "tx_id": "TXN_1"}
    assert service.get_idempotent_result("key_unknown") is None


def test_execute_transfer_insufficient_funds():
    mock_bq = MagicMock()
    # Mock account row with balance = 1000.0
    mock_row = MagicMock()
    mock_row.account_number = "ACC100101"
    mock_row.customer_id = 1001
    mock_row.account_status = "ACTIVE"
    mock_row.balance = 1000.0
    mock_row.currency = "INR"
    mock_row.record_version = 1
    
    mock_bq.query.return_value = [mock_row]
    
    service = LedgerService(bq_client=mock_bq)
    
    with pytest.raises(LedgerError) as exc:
        service.execute_transfer(
            customer_id=1001,
            source_account_number="ACC100101",
            beneficiary_name="Aarav Sharma",
            beneficiary_account_number="ACC200201",
            beneficiary_bank="HDFC",
            beneficiary_ifsc="HDFC0001",
            amount=5000.0,
            currency="INR"
        )
    assert "Insufficient funds" in str(exc.value)


def test_execute_transfer_success():
    mock_bq = MagicMock()
    # Source account row
    mock_src = MagicMock()
    mock_src.account_number = "ACC100101"
    mock_src.customer_id = 1001
    mock_src.account_status = "ACTIVE"
    mock_src.balance = 20000.0
    mock_src.currency = "INR"
    mock_src.ifsc_code = "BANK001"
    mock_src.branch_name = "Main"
    mock_src.created_at = "2024-01-01"
    mock_src.record_version = 1
    
    # Destination account not internal (empty list)
    mock_bq.query.side_effect = [
        [mock_src],   # fetch source
        MagicMock(),  # update old version
        MagicMock(),  # insert new version
        MagicMock(),  # insert txn log
        []            # check if dest account is internal
    ]
    
    service = LedgerService(bq_client=mock_bq)
    res = service.execute_transfer(
        customer_id=1001,
        source_account_number="ACC100101",
        beneficiary_name="Aarav Sharma",
        beneficiary_account_number="ACC200201",
        beneficiary_bank="HDFC",
        beneficiary_ifsc="HDFC0001",
        amount=3000.0,
        currency="INR"
    )
    
    assert res["status"] == "COMPLETED"
    assert res["amount"] == 3000.0
    assert res["remaining_balance"] == 17000.0
    assert res["transaction_id"].startswith("TXN_")
    assert res["reference_id"].startswith("REF_")


def test_execute_transfer_internal_destination_credit():
    mock_bq = MagicMock()
    # Source account row
    mock_src = MagicMock()
    mock_src.account_number = "ACC100101"
    mock_src.customer_id = 1001
    mock_src.account_status = "ACTIVE"
    mock_src.balance = 20000.0
    mock_src.currency = "INR"
    mock_src.ifsc_code = "BANK001"
    mock_src.branch_name = "Main"
    mock_src.created_at = "2024-01-01"
    mock_src.record_version = 1

    # Destination account row (internal)
    mock_dest = MagicMock()
    mock_dest.account_number = "ACC200201"
    mock_dest.customer_id = 2002
    mock_dest.account_status = "ACTIVE"
    mock_dest.balance = 5000.0
    mock_dest.currency = "INR"
    mock_dest.ifsc_code = "BANK001"
    mock_dest.branch_name = "Main"
    mock_dest.created_at = "2024-01-01"
    mock_dest.record_version = 1

    mock_bq.query.side_effect = [
        [mock_src],   # 1. fetch source
        MagicMock(),  # 2. update old source version
        MagicMock(),  # 3. insert new source version
        MagicMock(),  # 4. insert source debit txn log
        [mock_dest],  # 5. check if dest account is internal (found!)
        MagicMock(),  # 6. update old dest version
        MagicMock(),  # 7. insert new dest version
        MagicMock(),  # 8. insert dest credit txn log
    ]

    service = LedgerService(bq_client=mock_bq)
    res = service.execute_transfer(
        customer_id=1001,
        source_account_number="ACC100101",
        beneficiary_name="Aarav Sharma",
        beneficiary_account_number="ACC200201",
        beneficiary_bank="BankPilot",
        beneficiary_ifsc="BANK001",
        amount=3000.0,
        currency="INR"
    )

    assert res["status"] == "COMPLETED"
    assert res["amount"] == 3000.0
    assert res["remaining_balance"] == 17000.0
    assert mock_bq.query.call_count == 8

    # Verify call #4 is DEBIT and call #8 is CREDIT
    call_4_params = {p.name: p.value for p in mock_bq.query.call_args_list[3].kwargs["job_config"].query_parameters}
    assert call_4_params["direction"] == "DEBIT"
    assert call_4_params["acc"] == "ACC100101"

    call_8_params = {p.name: p.value for p in mock_bq.query.call_args_list[7].kwargs["job_config"].query_parameters}
    assert call_8_params["direction"] == "CREDIT"
    assert call_8_params["acc"] == "ACC200201"



def test_execute_credit_card_payment_success():
    mock_bq = MagicMock()
    # Source account row
    mock_src = MagicMock()
    mock_src.account_number = "ACC100101"
    mock_src.customer_id = 1001
    mock_src.account_type = "SAVINGS"
    mock_src.account_status = "ACTIVE"
    mock_src.balance = 20000.0
    mock_src.currency = "INR"
    mock_src.ifsc_code = "BANK001"
    mock_src.branch_name = "Main"
    mock_src.created_at = "2024-01-01"
    mock_src.record_version = 1

    # Credit card row
    mock_card = MagicMock()
    mock_card.card_account_number = "CARD_ACC_1001"
    mock_card.customer_id = 1001
    mock_card.card_number = "4532-1111-2222-3333"
    mock_card.card_type = "Platinum"
    mock_card.credit_limit = 100000.0
    mock_card.available_credit = 80000.0
    mock_card.outstanding_balance = 20000.0
    mock_card.statement_amount = 20000.0
    mock_card.minimum_due_amount = 1000.0
    mock_card.payment_due_date = "2026-09-15"
    mock_card.statement_date = "2026-08-25"
    mock_card.status = "ACTIVE"
    mock_card.created_at = "2024-01-01"
    mock_card.record_version = 1

    mock_bq.query.side_effect = [
        [mock_src],   # 1. fetch source account
        [mock_card],  # 2. fetch credit card
        MagicMock(),  # 3. update old source account SCD
        MagicMock(),  # 3. insert new source account SCD
        MagicMock(),  # 4. update old credit card SCD
        MagicMock(),  # 4. insert new credit card SCD
        MagicMock(),  # 5. insert DEBIT txn log on source account
        MagicMock(),  # 5. insert CREDIT txn log on card account
    ]

    service = LedgerService(bq_client=mock_bq)
    res = service.execute_credit_card_payment(
        customer_id=1001,
        source_account_number="ACC100101",
        card_account_number="CARD_ACC_1001",
        amount=5000.0,
        currency="INR"
    )

    assert res["status"] == "COMPLETED"
    assert res["amount"] == 5000.0
    assert res["remaining_account_balance"] == 15000.0
    assert res["new_outstanding_balance"] == 15000.0
    assert res["new_available_credit"] == 85000.0
    assert res["card_account_number"] == "CARD_ACC_1001"
    assert res["transaction_id"].startswith("TXN_")
    assert res["reference_id"].startswith("REF_")

    # Verify 8 BigQuery queries were executed (including 2 transaction inserts)
    assert mock_bq.query.call_count == 8


def test_add_beneficiary_success():
    mock_bq = MagicMock()
    # 1. check_sql returns [] (not existing)
    # 2. id_query returns next_id 5005
    # 3. insert_sql succeeds
    mock_id_row = MagicMock()
    mock_id_row.next_id = 5005
    mock_bq.query.side_effect = [
        [],                 # check existing
        [mock_id_row],      # next_id
        MagicMock()         # insert record
    ]

    service = LedgerService(bq_client=mock_bq)
    res = service.add_beneficiary(
        customer_id=1001,
        beneficiary_name="Priya Patel",
        beneficiary_account_number="998877665544",
        bank_name="HDFC Bank",
        ifsc_code="HDFC0001234"
    )

    assert res["status"] == "COMPLETED"
    assert res["beneficiary_id"] == 5005
    assert res["beneficiary_name"] == "Priya Patel"
    assert res["beneficiary_account_number"] == "998877665544"
    assert res["bank_name"] == "HDFC Bank"
    assert res["ifsc_code"] == "HDFC0001234"
    assert "Successfully registered" in res["message"]
    assert mock_bq.query.call_count == 3


def test_add_beneficiary_already_exists():
    mock_bq = MagicMock()
    mock_existing = MagicMock()
    mock_existing.beneficiary_name = "Priya Patel"
    mock_bq.query.return_value = [mock_existing]

    service = LedgerService(bq_client=mock_bq)
    with pytest.raises(LedgerError) as exc:
        service.add_beneficiary(
            customer_id=1001,
            beneficiary_name="Priya Patel",
            beneficiary_account_number="998877665544",
            bank_name="HDFC Bank",
            ifsc_code="HDFC0001234"
        )
    assert "already registered" in str(exc.value)


