"""Observer pattern for transaction event notifications."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from banking.enums import TransactionStatus, TransactionType
from banking.models.transaction import Transaction


@dataclass(frozen=True)
class TransactionEvent:
    """Event payload sent to observers after a banking operation."""

    transaction: Transaction
    message: str = ""


class TransactionObserver(ABC):
    """Observer interface for transaction events."""

    @abstractmethod
    def on_transaction(self, event: TransactionEvent) -> None:
        """Handle a transaction event."""


class TransactionSubject:
    """Subject that notifies attached observers of transaction events."""

    def __init__(self) -> None:
        self._observers: list[TransactionObserver] = []

    def attach(self, observer: TransactionObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: TransactionObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event: TransactionEvent) -> None:
        for observer in list(self._observers):
            try:
                observer.on_transaction(event)
            except Exception:
                # Observer failures must not disrupt banking operations.
                continue
