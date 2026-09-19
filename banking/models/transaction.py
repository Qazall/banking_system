"""Transaction model representing a banking operation record."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from banking.enums import TransactionStatus, TransactionType


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Transaction:
    """Immutable record of a banking transaction."""

    transaction_type: TransactionType
    amount: Decimal
    status: TransactionStatus
    source_account: str | None = None
    destination_account: str | None = None
    description: str = ""
    transaction_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "transaction_type": self.transaction_type.value,
            "amount": str(self.amount),
            "timestamp": self.timestamp.isoformat(),
            "source_account": self.source_account,
            "destination_account": self.destination_account,
            "status": self.status.value,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Transaction:
        return cls(
            transaction_id=data["transaction_id"],
            transaction_type=TransactionType(data["transaction_type"]),
            amount=Decimal(data["amount"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source_account=data.get("source_account"),
            destination_account=data.get("destination_account"),
            status=TransactionStatus(data["status"]),
            description=data.get("description", ""),
        )

    
