"""JSON persistence for bank state."""

from __future__ import annotations

import json
import threading
from decimal import Decimal
from pathlib import Path

from banking.enums import AccountType
from banking.exceptions import PersistenceError
from banking.models.account import Account
from banking.models.checking_account import CheckingAccount
from banking.models.customer import Customer
from banking.models.savings_account import SavingsAccount
from banking.services.account_service import AccountService
from banking.services.customer_service import CustomerService


class StateRepository:
    """Thread-safe save/load of customers and accounts."""

    def __init__(self, state_path: str | Path = "data/bank_state.json") -> None:
        self._state_path = Path(state_path)
        self._lock = threading.Lock()

    def save(
        self,
        customer_service: CustomerService,
        account_service: AccountService,
    ) -> None:
        with self._lock:
            try:
                payload = {
                    "customers": {
                        national_id: customer.to_dict()
                        for national_id, customer in customer_service.customers.items()
                    },
                    "accounts": {
                        account_number: account.to_dict()
                        for account_number, account in account_service.accounts.items()
                    },
                }
                self._state_path.parent.mkdir(parents=True, exist_ok=True)
                temp_path = self._state_path.with_suffix(".tmp")
                temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                temp_path.replace(self._state_path)
            except OSError as exc:
                raise PersistenceError(f"Failed to save bank state: {exc}") from exc

    def load(
        self,
        customer_service: CustomerService,
        account_service: AccountService,
    ) -> None:
        with self._lock:
            if not self._state_path.exists():
                return

            try:
                payload = json.loads(self._state_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise PersistenceError(f"Failed to load bank state: {exc}") from exc

            customers = {
                national_id: Customer.from_dict(data)
                for national_id, data in payload.get("customers", {}).items()
            }
            customer_service.load_customers(customers)

            accounts: dict[str, Account] = {}
            for account_number, data in payload.get("accounts", {}).items():
                owner = customer_service.get_customer(data["owner_national_id"])
                account = self._deserialize_account(data, owner)
                accounts[account_number] = account

            account_service.load_accounts(accounts)

    @staticmethod
    def _deserialize_account(data: dict, owner: Customer) -> Account:
        account_type = AccountType(data["account_type"])
        balance = Decimal(str(data["balance"]))
        extra = data.get("extra", {})

        if account_type == AccountType.SAVINGS:
            account: Account = SavingsAccount(
                owner=owner,
                account_number=data["account_number"],
                initial_balance=Decimal("0"),
            )
        else:
            fee_value = Decimal(str(extra.get("withdrawal_fee", "1.00")))
            account = CheckingAccount(
                owner=owner,
                withdrawal_fee=fee_value,
                account_number=data["account_number"],
                initial_balance=Decimal("0"),
            )

        from banking.models.transaction import Transaction

        with account.lock:
            account._balance = balance
            account._transactions = [
                Transaction.from_dict(tx_data) for tx_data in data.get("transactions", [])
            ]

        return account