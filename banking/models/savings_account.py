"""Savings account model."""

from __future__ import annotations

from decimal import Decimal
from banking.enums import AccountType
from banking.models.account import Account
from banking.models.customer import Customer


class SavingsAccount(Account):
    """A standard savings account without complex interest tracking metrics."""

    def __init__(
        self,
        owner: Customer,
        account_number: str | None = None,
        initial_balance: Decimal = Decimal("0"),
    ) -> None:
        super().__init__(owner, account_number, initial_balance)

    @property
    def account_type(self) -> AccountType:
        return AccountType.SAVINGS

    def _extra_fields(self) -> dict:
        """No extra metrics needed for standard savings."""
        return {}