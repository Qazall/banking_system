"""Thread-safe singleton Bank facade coordinating banking services."""

from __future__ import annotations

import threading
from decimal import Decimal
from pathlib import Path

from banking.enums import AccountType
from banking.exceptions import PersistenceError
from banking.models.account import Account
from banking.models.customer import Customer
from banking.models.transaction import Transaction
from banking.observers.console_observer import ConsoleTransactionObserver
from banking.observers.subject import TransactionObserver, TransactionSubject
from banking.persistence.state_repository import StateRepository
from banking.services.account_service import AccountService
from banking.services.customer_service import CustomerService
from banking.services.transfer_service import TransferService


class Bank:
    """Central banking system entry point (thread-safe Singleton)."""

    _instance: Bank | None = None
    _instance_lock = threading.Lock()

    def __init__(
        self,
        state_path: str | Path = "data/bank_state.json",
        log_path: str | Path = "transactions.log",
    ) -> None:
        self._state_path = Path(state_path)
        self._log_path = Path(log_path)
        self._subject = TransactionSubject()
        self._customer_service = CustomerService()
        self._account_service = AccountService(
            self._customer_service,
            self._subject,
            log_path=str(self._log_path),
        )
        self._transfer_service = TransferService(
            self._account_service,
            self._subject,
            log_path=str(self._log_path),
        )
        self._repository = StateRepository(self._state_path)

    @classmethod
    def get_instance(
        cls,
        state_path: str | Path = "data/bank_state.json",
        log_path: str | Path = "transactions.log",
    ) -> Bank:
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls(state_path=state_path, log_path=log_path)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton for testing."""
        with cls._instance_lock:
            cls._instance = None

    def attach_observer(self, observer: TransactionObserver) -> None:
        self._subject.attach(observer)

    def detach_observer(self, observer: TransactionObserver) -> None:
        self._subject.detach(observer)

    def create_customer(self, first_name: str, last_name: str, national_id: str) -> Customer:
        return self._customer_service.create_customer(first_name, last_name, national_id)

    def get_customer(self, national_id: str) -> Customer:
        return self._customer_service.get_customer(national_id)

    def open_account(
        self,
        national_id: str,
        account_type: AccountType,
        initial_balance: Decimal = Decimal("0"),
        **kwargs,
    ) -> Account:
        return self._account_service.open_account(
            national_id,
            account_type,
            initial_balance=initial_balance,
            **kwargs,
        )

    def get_account(self, account_number: str) -> Account:
        return self._account_service.get_account(account_number)

    def deposit(self, account_number: str, amount: Decimal, description: str = "") -> Transaction:
        return self._account_service.deposit(account_number, amount, description=description)

    def withdraw(self, account_number: str, amount: Decimal, description: str = "") -> Transaction:
        return self._account_service.withdraw(account_number, amount, description=description)

    def transfer(
        self,
        source_account_number: str,
        destination_account_number: str,
        amount: Decimal,
        description: str = "",
    ) -> Transaction:
        return self._transfer_service.transfer(
            source_account_number,
            destination_account_number,
            amount,
            description=description,
        )

    def save_state(self) -> None:
        self._repository.save(self._customer_service, self._account_service)

    def load_state(self) -> None:
        self._repository.load(self._customer_service, self._account_service)

    def get_transaction_from_log(self, transaction_id: str) -> dict | None:
        """Retrieve historical transaction data directly from the log file by ID."""
        from banking.logging.transaction_logger import find_transaction_in_log
        return find_transaction_in_log(transaction_id, log_path=self._log_path)

    @property
    def customer_service(self) -> CustomerService:
        return self._customer_service

    @property
    def account_service(self) -> AccountService:
        return self._account_service

    def apply_periodic_interest(self, account_number: str) -> Transaction:
        """Execute and commit time-based simple interest via the account service layer."""
        return self._account_service.apply_periodic_interest(account_number)

    def get_transaction_from_log(self, transaction_id: str) -> dict | None:
        """Retrieve historical transaction data directly from the log file by ID."""
        return self._account_service.get_transaction_from_log(transaction_id)