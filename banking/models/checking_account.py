"""Checking account with a 4% dynamic transaction fee policy."""

from __future__ import annotations

from decimal import Decimal

from banking.enums import AccountType, TransactionStatus, TransactionType
from banking.exceptions import InsufficientFundsError
from banking.models.account import Account
from banking.models.customer import Customer
from banking.models.transaction import Transaction


class CheckingAccount(Account):
    """A checking account that charges a dynamic 4% fee on withdrawals and transfers."""

    def __init__(
        self,
        owner: Customer,
        withdrawal_fee: Decimal = Decimal("0.04"), # Core multiplier tracking rate (4%)
        account_number: str | None = None,
        initial_balance: Decimal = Decimal("0"),
    ) -> None:
        super().__init__(owner, account_number, initial_balance)
        # Ensure the fee rate default or passed argument represents the percentage modifier
        self._withdrawal_fee = Decimal("0.04")

    @property
    def account_type(self) -> AccountType:
        return AccountType.CHECKING

    @property
    def withdrawal_fee(self) -> Decimal:
        return self._withdrawal_fee

    def _calculate_fee(self, amount: Decimal) -> Decimal:
        """Calculate dynamic 4% fee rounded strictly to two decimal places."""
        return (amount * self._withdrawal_fee).quantize(Decimal("0.01"))

    def _total_debit(self, amount: Decimal) -> Decimal:
        """Calculate the complete debit impact: principal + dynamic fee."""
        return amount + self._calculate_fee(amount)

    def withdraw(self, amount: Decimal, description: str = "") -> Transaction:
        amount = Decimal(str(amount))
        self._validate_amount(amount)
        with self._lock:
            dynamic_fee = self._calculate_fee(amount)
            total_debit = amount + dynamic_fee
            
            if self._balance < total_debit:
                self._record_transaction(
                    TransactionType.WITHDRAWAL,
                    amount,
                    TransactionStatus.FAILED,
                    description=description or "Withdrawal failed: insufficient funds",
                )
                raise InsufficientFundsError(
                    f"Account {self._account_number} has insufficient funds "
                    f"for withdrawal of {amount} plus 4% fee {dynamic_fee}"
                ) from None

            self._balance -= total_debit
            withdrawal_tx = self._record_transaction(
                TransactionType.WITHDRAWAL,
                amount,
                TransactionStatus.SUCCESS,
                description=description or "Withdrawal",
            )
            
            if dynamic_fee > Decimal("0"):
                self._record_transaction(
                    TransactionType.FEE,
                    dynamic_fee,
                    TransactionStatus.SUCCESS,
                    description="Withdrawal percentage fee (4%)",
                )
            return withdrawal_tx

    def debit(self, amount: Decimal, transaction_type: TransactionType, description: str) -> Transaction:
        """Deduct transaction amount AND the dynamic 4% fee from balance."""
        amount = Decimal(str(amount))
        self._validate_amount(amount)
        
        if not self._lock._is_owned():
            raise RuntimeError(f"Internal banking error: Lock must be acquired before calling debit on {self._account_number}")
            
        dynamic_fee = self._calculate_fee(amount)
        total_debit = amount + dynamic_fee

        if self._balance < total_debit:
            self._record_transaction(
                transaction_type,
                amount,
                TransactionStatus.FAILED,
                description=f"{description} failed: insufficient funds"
            )
            raise InsufficientFundsError(
                f"Account {self._account_number} has insufficient funds "
                f"for debit of {amount} (required with 4% fee: {total_debit}, balance: {self._balance})"
            )
            
        self._balance -= total_debit
        
        transfer_tx = self._record_transaction(
            transaction_type,
            amount,
            TransactionStatus.SUCCESS,
            description=description
        )
        
        if dynamic_fee > Decimal("0"):
            self._record_transaction(
                TransactionType.FEE,
                dynamic_fee,
                TransactionStatus.SUCCESS,
                description="Transfer percentage fee (4%)",
            )
            
        return transfer_tx

    def _extra_fields(self) -> dict:
        return {"withdrawal_fee": str(self._withdrawal_fee)}