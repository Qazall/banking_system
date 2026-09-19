"""Console observer that prints transaction events."""

from banking.observers.subject import TransactionEvent, TransactionObserver


class ConsoleTransactionObserver(TransactionObserver):
    """Prints transaction details to the console."""

    def on_transaction(self, event: TransactionEvent) -> None:
        tx = event.transaction
        print(
            f"[OBSERVER] {tx.timestamp.isoformat()} | {tx.transaction_type.value} | "
            f"amount={tx.amount} | status={tx.status.value} | "
            f"src={tx.source_account} | dst={tx.destination_account} | "
            f"{event.message or tx.description}"
        )
