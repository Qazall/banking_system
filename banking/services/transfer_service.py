"""Atomic transfer service with ordered locking to prevent deadlocks."""

from __future__ import annotations

from contextlib import ExitStack
from decimal import Decimal

from banking.enums import TransactionStatus, TransactionType
from banking.exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
    TransferToSameAccountError,
)
from banking.logging.transaction_logger import log_transaction
from banking.models.account import Account
from banking.models.transaction import Transaction
from banking.observers.subject import TransactionEvent, TransactionSubject
from banking.services.account_service import AccountService


class TransferService:
    """Performs thread-safe atomic transfers between accounts."""

    def __init__(
        self,
        account_service: AccountService,
        subject: TransactionSubject,
        log_path: str = "transactions.log",
    ) -> None:
        self._account_service = account_service
        self._subject = subject
        self._log_path = log_path

    def transfer(
        self,
        source_account_number: str,
        destination_account_number: str,
        amount: Decimal,
        description: str = "",
    ) -> Transaction:
        if amount <= Decimal("0"):
            raise InvalidAmountError(f"Transfer amount must be positive, got {amount}")

        if source_account_number == destination_account_number:
            failed = Transaction(
                transaction_type=TransactionType.TRANSFER,
                amount=amount,
                status=TransactionStatus.FAILED,
                source_account=source_account_number,
                destination_account=destination_account_number,
                description="Transfer to same account is not allowed",
            )
            self._publish(failed, failed.description)
            print(f"\n[DATA MOVEMENT TRANSACTION FAILED] Transfer rejected: Same account mapping.")
            print(f"Failed Transaction ID: {failed.transaction_id}")
            raise TransferToSameAccountError(
                "Transfer source and destination accounts must be different"
            )

        source = self._account_service.get_account(source_account_number)
        destination = self._account_service.get_account(destination_account_number)

        first, second = self._ordered_accounts(source, destination)
        transfer_description = description or f"Transfer to {destination_account_number}"

        with ExitStack() as stack:
            stack.enter_context(first.lock)
            if first is not second:
                stack.enter_context(second.lock)

            debited = False
            try:
                source.debit(amount, TransactionType.TRANSFER, transfer_description)
                debited = True
                credit_tx = destination.credit(
                    amount,
                    TransactionType.TRANSFER,
                    f"Transfer from {source_account_number}",
                )
                credit_tx.destination_account = destination_account_number
                credit_tx.source_account = source_account_number

                transfer_tx = Transaction(
                    transaction_type=TransactionType.TRANSFER,
                    amount=amount,
                    status=TransactionStatus.SUCCESS,
                    source_account=source_account_number,
                    destination_account=destination_account_number,
                    description=transfer_description,
                )
                self._publish(transfer_tx, "Transfer completed")
                
                print(f"\n[DATA MOVEMENT] Atomic transfer complete: {amount:.2f} moved cleanly from {source_account_number} to {destination_account_number}.")

                if len(source.transactions) >= 1:
                    potential_fee_tx = source.transactions[-1]
                    if potential_fee_tx.transaction_type == TransactionType.FEE:
                        potential_fee_tx.source_account = source_account_number
                        self._publish(
                            potential_fee_tx, 
                            f"Transfer transaction processing fee collected from {source_account_number}"
                        )
                        print(f"[DATA MOVEMENT] Policy Fee Added: {potential_fee_tx.amount:.2f} deducted from source account {source_account_number}.")

                return transfer_tx
            except InsufficientFundsError as exc:
                failed = Transaction(
                    transaction_type=TransactionType.TRANSFER,
                    amount=amount,
                    status=TransactionStatus.FAILED,
                    source_account=source_account_number,
                    destination_account=destination_account_number,
                    description=str(exc),
                )
                self._publish(failed, str(exc))
                print(f"\n[DATA MOVEMENT TRANSACTION FAILED] Transfer failed due to insufficient funds: {exc}")
                print(f"Failed Transaction ID: {failed.transaction_id}") # <--- Prints ID on Insufficient Funds
                raise
            except Exception as exc:
                if debited:
                    source.credit(
                        amount,
                        TransactionType.TRANSFER,
                        "Transfer rollback: compensating failed credit",
                    )
                    print(f"[DATA MOVEMENT ROLLBACK] Compensated debit balance on {source_account_number} due to down-stream credit failure.")
                failed = Transaction(
                    transaction_type=TransactionType.TRANSFER,
                    amount=amount,
                    status=TransactionStatus.FAILED,
                    source_account=source_account_number,
                    destination_account=destination_account_number,
                    description=str(exc),
                )
                self._publish(failed, str(exc))
                print(f"\n[DATA MOVEMENT TRANSACTION FAILED] Transfer encountered a critical error: {exc}")
                print(f"Failed Transaction ID: {failed.transaction_id}") # <--- Prints ID on general unexpected failures
                raise

    def _ordered_accounts(self, first_account: Account, second_account: Account) -> tuple[Account, Account]:
        """Instance method containing explicit self reference to map positional parameters smoothly."""
        if first_account.account_number <= second_account.account_number:
            return first_account, second_account
        return second_account, first_account

    def _publish(self, transaction: Transaction, message: str = "") -> None:
        log_transaction(transaction, self._log_path)
        self._subject.notify(TransactionEvent(transaction=transaction, message=message))