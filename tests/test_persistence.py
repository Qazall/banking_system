"""Tests for state persistence and recovery."""

from decimal import Decimal
from pathlib import Path

from banking.bank import Bank
from banking.enums import AccountType


def test_save_and_load_preserves_state(seeded_bank, tmp_path: Path):
    state_path = tmp_path / "persist.json"
    log_path = tmp_path / "persist.log"

    savings_number = seeded_bank._seeded_accounts["savings"]
    checking_number = seeded_bank._seeded_accounts["checking"]

    seeded_bank.deposit(savings_number, Decimal("50.00"))
    seeded_bank.withdraw(checking_number, Decimal("25.00"))

    savings_balance = seeded_bank.get_account(savings_number).get_balance()
    checking_balance = seeded_bank.get_account(checking_number).get_balance()
    savings_tx_count = len(seeded_bank.get_account(savings_number).transactions)

    seeded_bank._repository._state_path = state_path
    seeded_bank.save_state()

    Bank.reset_instance()
    restored = Bank.get_instance(state_path=state_path, log_path=log_path)
    restored.load_state()

    restored_savings = restored.get_account(savings_number)
    restored_checking = restored.get_account(checking_number)

    assert restored.get_customer("1234567890").full_name == "Test User"
    assert restored_savings.get_balance() == savings_balance
    assert restored_checking.get_balance() == checking_balance
    assert len(restored_savings.transactions) == savings_tx_count

    restored.open_account("0987654321", AccountType.CHECKING, initial_balance=Decimal("100"))
    assert len(restored.account_service.accounts) == 4
