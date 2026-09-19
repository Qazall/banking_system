"""Abstract base account with thread-safe financial operations."""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from banking.enums import AccountType, TransactionStatus, TransactionType
from banking.exceptions import InsufficientFundsError, InvalidAmountError
from banking.models.transaction import Transaction

if TYPE_CHECKING:
    from banking.models.customer import Customer


class Account(ABC):
    """Base class for all bank account types."""

    def __init__(
        self,
        owner: Customer,
        account_number: str | None = None,
        initial_balance: Decimal = Decimal("0"),
    ) -> None:
        self._account_number = account_number or str(uuid4())
        self._balance = initial_balance
        self._owner = owner
        self._transactions: list[Transaction] = []
        self._lock = threading.RLock()

    @property
    @abstractmethod
    def account_type(self) -> AccountType:
        """Return the concrete account type."""

    @property
    def account_number(self) -> str:
        return self._account_number

    @property
    def owner(self) -> Customer:
        return self._owner

    @property
    def transactions(self) -> list[Transaction]:
        with self._lock:
            return list(self._transactions)

    def get_balance(self) -> Decimal:
        """Retrieve the current balance and record a balance inquiry transaction."""
        with self._lock:
            self._record_transaction(
                transaction_type=TransactionType.BALANCE_INQUIRY,
                amount=Decimal("0"),
                status=TransactionStatus.SUCCESS,
                description=f"Balance inquiry: Current balance is {self._balance}",
            )
            return self._balance

    def deposit(self, amount: Decimal, description: str = "") -> Transaction:
        self._validate_amount(amount)
        with self._lock:
            self._balance += amount
            transaction = self._record_transaction(
                TransactionType.DEPOSIT,
                amount,
                TransactionStatus.SUCCESS,
                description=description or "Deposit",
            )
            return transaction

    def withdraw(self, amount: Decimal, description: str = "") -> Transaction:
        """Withdraw funds. Subclasses may override to apply fees."""
        self._validate_amount(amount)
        with self._lock:
            total_debit = self._total_debit(amount)
            if self._balance < total_debit:
                self._record_transaction(
                    TransactionType.WITHDRAWAL,
                    amount,
                    TransactionStatus.FAILED,
                    description=description or "Withdrawal failed: insufficient funds",
                )
                raise InsufficientFundsError(
                    f"Account {self._account_number} has insufficient funds "
                    f"for withdrawal of {amount} (total debit {total_debit}, "
                    f"balance {self._balance})"
                ) from None
            self._balance -= total_debit
            return self._record_transaction(
                TransactionType.WITHDRAWAL,
                amount,
                TransactionStatus.SUCCESS,
                description=description or "Withdrawal",
            )

    def _total_debit(self, amount: Decimal) -> Decimal:
        """Total amount debited from balance for a withdrawal request."""
        return amount

    def credit(self, amount: Decimal, transaction_type: TransactionType, description: str) -> Transaction:
        """Internal credit used during transfers without re-acquiring lock."""
        self._validate_amount(amount)
        
        if not self._lock._is_owned():
            raise RuntimeError(f"Internal banking error: Lock must be acquired before calling credit on {self._account_number}")
            
        self._balance += amount
        
        return self._record_transaction(
            transaction_type,
            amount,
            TransactionStatus.SUCCESS,
            description=description,
        )

    def debit(self, amount: Decimal, transaction_type: TransactionType, description: str) -> Transaction:
        """Internal debit used during transfers without re-acquiring lock."""
        self._validate_amount(amount)
        
        if not self._lock._is_owned():
            raise RuntimeError(f"Internal banking error: Lock must be acquired before calling debit on {self._account_number}")
            
        total_debit = self._total_debit(amount)
        
        dest_acc = None
        if "to " in description:
            dest_acc = description.split("to ")[-1].strip()

        if self._balance < total_debit:
            self._record_transaction(
                transaction_type,
                amount,
                TransactionStatus.FAILED,
                description=f"{description} failed: insufficient funds",
                destination_account=dest_acc
            )
            raise InsufficientFundsError(
                f"Account {self._account_number} has insufficient funds "
                f"for debit of {amount} (total debit {total_debit})"
            )
        self._balance -= total_debit
        return self._record_transaction(
            transaction_type,
            amount,
            TransactionStatus.SUCCESS,
            description=description,
            destination_account=dest_acc
        )

    def _record_transaction(
        self,
        transaction_type: TransactionType,
        amount: Decimal,
        status: TransactionStatus,
        description: str = "",
        destination_account: str | None = None,
    ) -> Transaction:
        
        src_acc = self._account_number
        dest_acc = destination_account
        
        if transaction_type == TransactionType.TRANSFER:
            if "from " in description:
                src_acc = description.split("from ")[-1].strip()
                dest_acc = self._account_number

        transaction = Transaction(
            transaction_type=transaction_type,
            amount=amount,
            status=status,
            source_account=src_acc,
            destination_account=dest_acc,
            description=description,
        )
        self._transactions.append(transaction)
        return transaction

    @staticmethod
    def _validate_amount(amount: Decimal) -> None:
        if amount <= Decimal("0"):
            raise InvalidAmountError(f"Amount must be positive, got {amount}")

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "account_number": self._account_number,
                "account_type": self.account_type.value,
                "balance": str(self._balance),
                "owner_national_id": self._owner.national_id,
                "transactions": [tx.to_dict() for tx in self._transactions],
                "extra": self._extra_fields(),
            }

    @abstractmethod
    def _extra_fields(self) -> dict:
        """Return type-specific fields for serialization."""

    @property
    def lock(self) -> threading.RLock:
        return self._lock

    def get_full_statement(self) -> dict:
        """Compile complete master data, metrics, and transaction history for this account."""
        with self._lock:
            return {
                "account_number": self._account_number,
                "account_type": self.account_type.value,
                "balance": self._balance,
                "owner_name": f"{self._owner.first_name} {self._owner.last_name}",
                "owner_id": self._owner.national_id,
                "extra": self._extra_fields(),
                "transactions": [
                    {
                        "id": tx.transaction_id,
                        "timestamp": tx.timestamp,
                        "type": tx.transaction_type.value,
                        "amount": tx.amount,
                        "status": tx.status.value,
                        "description": tx.description,
                    }
                    for tx in self._transactions
                ]
            }