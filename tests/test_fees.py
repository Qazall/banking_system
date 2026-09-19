"""Tests for checking account withdrawal fees."""

from decimal import Decimal

import pytest

from banking.exceptions import InsufficientFundsError


def test_withdrawal_applies_fee(seeded_bank):
    account_number = seeded_bank._seeded_accounts["checking"]
    initial = seeded_bank.get_account(account_number).get_balance()
    amount = Decimal("50.00")
    fee = Decimal("2.00")

    seeded_bank.withdraw(account_number, amount)

    assert seeded_bank.get_account(account_number).get_balance() == initial - amount - fee


def test_withdrawal_checks_amount_plus_fee(seeded_bank):
    account_number = seeded_bank._seeded_accounts["checking"]
    # Balance is 500, trying to withdraw 499 + 2 fee = 501 > 500
    with pytest.raises(InsufficientFundsError):
        seeded_bank.withdraw(account_number, Decimal("499.00"))
