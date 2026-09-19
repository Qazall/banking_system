"""Shared pytest fixtures."""

from decimal import Decimal
from pathlib import Path

import pytest

from banking.bank import Bank
from banking.enums import AccountType


@pytest.fixture
def bank(tmp_path: Path) -> Bank:
    Bank.reset_instance()
    instance = Bank.get_instance(
        state_path=tmp_path / "bank_state.json",
        log_path=tmp_path / "transactions.log",
    )
    yield instance
    Bank.reset_instance()


@pytest.fixture
def seeded_bank(bank: Bank) -> Bank:
    bank.create_customer("Test", "User", "1234567890")
    bank.create_customer("Other", "Person", "0987654321")
    savings = bank.open_account(
        "1234567890",
        AccountType.SAVINGS,
        initial_balance=Decimal("1000.00"),
    )
    checking = bank.open_account(
        "1234567890",
        AccountType.CHECKING,
        initial_balance=Decimal("500.00"),
        withdrawal_fee=Decimal("2.00"),
    )
    other = bank.open_account(
        "0987654321",
        AccountType.SAVINGS,
        initial_balance=Decimal("300.00"),
    )
    bank._seeded_accounts = {
        "savings": savings.account_number,
        "checking": checking.account_number,
        "other": other.account_number,
    }
    return bank
