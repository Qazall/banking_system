"""Customer model representing a bank client."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Customer:
    """A bank customer who may own multiple accounts."""

    first_name: str
    last_name: str
    national_id: str
    account_numbers: list[str] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def add_account(self, account_number: str) -> None:
        if account_number not in self.account_numbers:
            self.account_numbers.append(account_number)

    def to_dict(self) -> dict:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "national_id": self.national_id,
            "account_numbers": list(self.account_numbers),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Customer:
        return cls(
            first_name=data["first_name"],
            last_name=data["last_name"],
            national_id=data["national_id"],
            account_numbers=list(data.get("account_numbers", [])),
        )
