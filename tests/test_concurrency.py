"""Tests for concurrent access and race condition prevention."""

import threading
from decimal import Decimal

from banking.enums import AccountType


def test_concurrent_deposits_and_withdrawals(seeded_bank):
    account_number = seeded_bank._seeded_accounts["savings"]
    other = seeded_bank._seeded_accounts["other"]
    num_threads = 20
    operations = 25
    barrier = threading.Barrier(num_threads)

    def worker(index: int) -> None:
        barrier.wait()
        for i in range(operations):
            if (index + i) % 3 == 0:
                try:
                    seeded_bank.transfer(account_number, other, Decimal("1.00"))
                except Exception:
                    pass
            elif (index + i) % 3 == 1:
                seeded_bank.deposit(account_number, Decimal("2.00"))
            else:
                try:
                    seeded_bank.withdraw(account_number, Decimal("1.00"))
                except Exception:
                    pass

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    savings = seeded_bank.get_account(account_number)
    other_account = seeded_bank.get_account(other)

    savings_tx_amount = sum(
        tx.amount
        for tx in savings.transactions
        if tx.status.value == "SUCCESS" and tx.transaction_type.value in {"DEPOSIT", "WITHDRAWAL", "TRANSFER"}
    )
    assert savings.get_balance() >= Decimal("0")
    assert other_account.get_balance() >= Decimal("0")

    # Recompute expected balance from successful transactions on savings account
    expected = Decimal("1000.00")
    for tx in savings.transactions:
        if tx.status.value != "SUCCESS":
            continue
        if tx.transaction_type.value == "DEPOSIT":
            expected += tx.amount
        elif tx.transaction_type.value == "WITHDRAWAL":
            expected -= tx.amount
        elif tx.transaction_type.value == "TRANSFER" and tx.source_account == account_number:
            expected -= tx.amount

    assert savings.get_balance() == expected


def test_concurrent_transfers_preserve_total_funds(seeded_bank):
    account_a = seeded_bank._seeded_accounts["savings"]
    account_b = seeded_bank._seeded_accounts["checking"]
    initial_total = (
        seeded_bank.get_account(account_a).get_balance()
        + seeded_bank.get_account(account_b).get_balance()
    )
    errors: list[str] = []

    def transfer_loop() -> None:
        for _ in range(30):
            try:
                seeded_bank.transfer(account_a, account_b, Decimal("1.00"))
            except Exception as exc:
                errors.append(str(exc))
            try:
                seeded_bank.transfer(account_b, account_a, Decimal("1.00"))
            except Exception as exc:
                errors.append(str(exc))

    threads = [threading.Thread(target=transfer_loop) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    final_total = (
        seeded_bank.get_account(account_a).get_balance()
        + seeded_bank.get_account(account_b).get_balance()
    )
    assert final_total == initial_total
