"""Multi-threaded ATM simulation for concurrent banking operations."""

from __future__ import annotations

import random
import threading
from decimal import Decimal

from banking.bank import Bank


class ATMThread(threading.Thread):
    """Simulates an ATM performing random banking operations."""

    def __init__(
        self,
        atm_id: int,
        bank: Bank,
        account_numbers: list[str],
        operations_per_atm: int = 20,
    ) -> None:
        super().__init__(name=f"ATM-{atm_id}", daemon=True)
        self._atm_id = atm_id
        self._bank = bank
        self._account_numbers = account_numbers
        self._operations = operations_per_atm
        self.errors: list[str] = []

    def run(self) -> None:
        for _ in range(self._operations):
            operation = random.choice(["deposit", "withdraw", "transfer"])
            try:
                if operation == "deposit":
                    account = random.choice(self._account_numbers)
                    amount = Decimal(str(random.randint(1, 50)))
                    self._bank.deposit(account, amount, description=f"ATM-{self._atm_id} deposit")
                elif operation == "withdraw":
                    account = random.choice(self._account_numbers)
                    amount = Decimal(str(random.randint(1, 20)))
                    self._bank.withdraw(account, amount, description=f"ATM-{self._atm_id} withdrawal")
                else:
                    source, destination = random.sample(self._account_numbers, 2)
                    amount = Decimal(str(random.randint(1, 30)))
                    self._bank.transfer(
                        source,
                        destination,
                        amount,
                        description=f"ATM-{self._atm_id} transfer",
                    )
            except Exception as exc:
                self.errors.append(str(exc))


def run_atm_simulation(
    bank: Bank,
    account_numbers: list[str],
    num_atms: int = 5,
    operations_per_atm: int = 20,
) -> list[ATMThread]:
    """Start and wait for concurrent ATM threads."""
    threads = [
        ATMThread(i + 1, bank, account_numbers, operations_per_atm=operations_per_atm)
        for i in range(num_atms)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return threads
