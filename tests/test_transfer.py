"""Tests for transfer operations."""

from decimal import Decimal

import pytest

from banking.exceptions import InvalidAmountError, TransferToSameAccountError


def test_successful_transfer(seeded_bank):
    source = seeded_bank._seeded_accounts["savings"]
    destination = seeded_bank._seeded_accounts["other"]
    source_before = seeded_bank.get_account(source).get_balance()
    dest_before = seeded_bank.get_account(destination).get_balance()
    amount = Decimal("150.00")

    tx = seeded_bank.transfer(source, destination, amount)

    assert tx.status.value == "SUCCESS"
    assert seeded_bank.get_account(source).get_balance() == source_before - amount
    assert seeded_bank.get_account(destination).get_balance() == dest_before + amount


def test_transfer_to_same_account_raises(seeded_bank):
    account_number = seeded_bank._seeded_accounts["savings"]
    with pytest.raises(TransferToSameAccountError):
        seeded_bank.transfer(account_number, account_number, Decimal("10.00"))


def test_invalid_transfer_amount(seeded_bank):
    source = seeded_bank._seeded_accounts["savings"]
    destination = seeded_bank._seeded_accounts["other"]
    with pytest.raises(InvalidAmountError):
        seeded_bank.transfer(source, destination, Decimal("0"))
