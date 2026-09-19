"""Tests for withdrawal operations."""

from decimal import Decimal

import pytest

from banking.exceptions import InsufficientFundsError, InvalidAmountError


def test_successful_withdrawal(seeded_bank):
    account_number = seeded_bank._seeded_accounts["savings"]
    initial = seeded_bank.get_account(account_number).get_balance()

    tx = seeded_bank.withdraw(account_number, Decimal("200.00"))

    assert tx.status.value == "SUCCESS"
    assert seeded_bank.get_account(account_number).get_balance() == initial - Decimal("200.00")


def test_failed_withdrawal_insufficient_funds(seeded_bank):
    account_number = seeded_bank._seeded_accounts["savings"]
    with pytest.raises(InsufficientFundsError):
        seeded_bank.withdraw(account_number, Decimal("5000.00"))


@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-5")])
def test_invalid_withdrawal_amount(seeded_bank, amount):
    account_number = seeded_bank._seeded_accounts["savings"]
    with pytest.raises(InvalidAmountError):
        seeded_bank.withdraw(account_number, amount)
