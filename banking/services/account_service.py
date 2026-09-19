"""Account management and financial operations service."""

from __future__ import annotations

import threading
from decimal import Decimal
from uuid import uuid4

from banking.enums import AccountType, TransactionStatus, TransactionType
from banking.exceptions import AccountNotFoundError
from banking.logging.transaction_logger import log_transaction
from banking.models.account import Account
from banking.models.checking_account import CheckingAccount
from banking.models.customer import Customer
from banking.models.savings_account import SavingsAccount
from banking.models.transaction import Transaction
from banking.observers.subject import TransactionEvent, TransactionSubject
from banking.services.customer_service import CustomerService


class AccountService:
    """Handles account lifecycle and single-account operations."""

    def __init__(
        self,
        customer_service: CustomerService,
        subject: TransactionSubject,
        log_path: str = "transactions.log",
    ) -> None:
        self._customer_service = customer_service
        self._accounts: dict[str, Account] = {}
        self._subject = subject
        self._log_path = log_path
        self._lock = threading.Lock()

    def open_account(
        self,
        national_id: str,
        account_type: AccountType,
        initial_balance: Decimal = Decimal("0"),
        **kwargs,
    ) -> Account:
        customer = self._customer_service.get_customer(national_id)
        account_number = str(uuid4())

        if account_type == AccountType.SAVINGS:
            account: Account = SavingsAccount(
                owner=customer,
                account_number=account_number,
                initial_balance=initial_balance,
            )
        elif account_type == AccountType.CHECKING:
            withdrawal_fee = kwargs.get("withdrawal_fee", Decimal("1.00"))
            account = CheckingAccount(
                owner=customer,
                withdrawal_fee=withdrawal_fee,
                account_number=account_number,
                initial_balance=initial_balance,
            )
        else:
            raise ValueError(f"Unsupported account type: {account_type}")

        with self._lock:
            if account_number in self._accounts:
                raise ValueError(f"Account number {account_number} already exists")
            self._accounts[account_number] = account
        customer.add_account(account_number)
        return account

    def get_account(self, account_number: str) -> Account:
        with self._lock:
            account = self._accounts.get(account_number)
        if account is None:
            raise AccountNotFoundError(f"Account {account_number} not found")
        return account

    def deposit(self, account_number: str, amount: Decimal, description: str = "") -> Transaction:
        account = self.get_account(account_number)
        try:
            transaction = account.deposit(amount, description=description)
            self._publish(transaction, f"Deposit to {account_number}")
            return transaction
        except Exception as exc:
            failed = self._failed_transaction(
                TransactionType.DEPOSIT,
                amount,
                account_number,
                None,
                str(exc),
            )
            self._publish(failed, str(exc))
            raise

    def withdraw(self, account_number: str, amount: Decimal, description: str = "") -> Transaction:
        account = self.get_account(account_number)
        try:
            # 1. Execute the withdrawal operation
            transaction = account.withdraw(amount, description=description)
            self._publish(transaction, f"Withdrawal from {account_number}")
            
            print(f"\n[DATA MOVEMENT] Successful withdrawal of {amount:.2f} executed on account {account_number}.")
            
            # 2. Check and publish if a structural fee was appended
            with account.lock:
                if len(account.transactions) >= 2:
                    potential_fee_tx = account.transactions[-1]
                    if potential_fee_tx.transaction_type == TransactionType.FEE:
                        self._publish(potential_fee_tx, f"Withdrawal processing fee collected from {account_number}")
                        print(f"[DATA MOVEMENT] Policy Fee Added: {potential_fee_tx.amount:.2f} deducted from account {account_number}.")

            return transaction
        except Exception as exc:
            # Generate the structured failure transaction (it automatically gets a unique ID on creation)
            failed = self._failed_transaction(
                TransactionType.WITHDRAWAL,
                amount,
                account_number,
                None,
                str(exc),
            )
            # CRUCIAL: Publish it so it gets written to transactions.log for Option 9 lookup
            self._publish(failed, str(exc))
            
            print(f"\n[DATA MOVEMENT TRANSACTION FAILED] Attempted withdrawal of {amount:.2f} from {account_number} rejected: {exc}")
            print(f"Failed Transaction ID: {failed.transaction_id}") # <--- Prints the ID for tracking
            raise

    def get_transaction_from_log(self, transaction_id: str) -> dict | None:
        """Retrieve historical transaction data directly from the log file by ID."""
        from banking.logging.transaction_logger import find_transaction_in_log
        return find_transaction_in_log(transaction_id, log_path=self._log_path)

    def get_balance(self, account_number: str) -> Decimal:
        """Fetch balance safely, capturing the inquiry within transactions and notifications."""
        account = self.get_account(account_number)
        try:
            balance_value = account.get_balance()
            if account.transactions:
                last_tx = account.transactions[-1]
                if last_tx.transaction_type == TransactionType.BALANCE_INQUIRY:
                    self._publish(last_tx, f"Balance check on {account_number}")
            return balance_value
        except Exception as exc:
            failed = self._failed_transaction(
                TransactionType.BALANCE_INQUIRY,
                Decimal("0"),
                account_number,
                None,
                str(exc),
            )
            self._publish(failed, str(exc))
            raise

    def _publish(self, transaction: Transaction, message: str = "") -> None:
        log_transaction(transaction, self._log_path)
        self._subject.notify(TransactionEvent(transaction=transaction, message=message))

    @staticmethod
    def _failed_transaction(
        transaction_type: TransactionType,
        amount: Decimal,
        source: str | None,
        destination: str | None,
        description: str,
    ) -> Transaction:
        return Transaction(
            transaction_type=transaction_type,
            amount=amount,
            status=TransactionStatus.FAILED,
            source_account=source,
            destination_account=destination,
            description=description,
        )

    @property
    def accounts(self) -> dict[str, Account]:
        with self._lock:
            return dict(self._accounts)

    def load_accounts(self, accounts: dict[str, Account]) -> None:
        with self._lock:
            self._accounts = accounts