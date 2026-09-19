"""Tests for transfer rollback on partial failure."""

from decimal import Decimal
from unittest.mock import patch

import pytest

from banking.enums import TransactionType


def test_transfer_rollback_restores_source_balance(seeded_bank):
    source_number = seeded_bank._seeded_accounts["savings"]
    dest_number = seeded_bank._seeded_accounts["other"]
    source = seeded_bank.get_account(source_number)
    dest = seeded_bank.get_account(dest_number)
    amount = Decimal("25.00")
    source_before = source.get_balance()
    dest_before = dest.get_balance()

    with patch.object(
        dest,
        "credit",
        side_effect=RuntimeError("simulated credit failure"),
    ):
        with pytest.raises(RuntimeError, match="simulated credit failure"):
            seeded_bank.transfer(source_number, dest_number, amount)

    assert source.get_balance() == source_before
    assert dest.get_balance() == dest_before

    rollback_txs = [
        tx
        for tx in source.transactions
        if tx.transaction_type == TransactionType.TRANSFER
        and "rollback" in tx.description.lower()
    ]
    assert len(rollback_txs) == 1
