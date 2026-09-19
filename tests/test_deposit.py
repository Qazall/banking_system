"""Tests for deposit operations."""

from decimal import Decimal

import pytest

from banking.exceptions import InvalidAmountError


def test_valid_deposit_increases_balance(seeded_bank):
    account_number = seeded_bank._seeded_accounts["savings"]
    initial = seeded_bank.get_account(account_number).get_balance()

    tx = seeded_bank.deposit(account_number, Decimal("100.00"))

    assert tx.status.value == "SUCCESS"
    assert seeded_bank.get_account(account_number).get_balance() == initial + Decimal("100.00")


@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-10")])
def test_invalid_deposit_raises(seeded_bank, amount):
    account_number = seeded_bank._seeded_accounts["savings"]
    with pytest.raises(InvalidAmountError):
        seeded_bank.deposit(account_number, amount)
