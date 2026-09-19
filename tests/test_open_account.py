"""Tests for account opening."""

from decimal import Decimal

from banking.enums import AccountType


def test_open_account_links_owner_and_unique_number(bank):
    bank.create_customer("Sara", "Karimi", "3344556677")

    account_a = bank.open_account(
        "3344556677",
        AccountType.SAVINGS,
        initial_balance=Decimal("100.00"),
    )
    account_b = bank.open_account(
        "3344556677",
        AccountType.CHECKING,
        initial_balance=Decimal("50.00"),
    )

    assert account_a.account_number != account_b.account_number
    assert account_a.owner.national_id == "3344556677"
    assert account_b.owner.national_id == "3344556677"

    customer = bank.get_customer("3344556677")
    assert account_a.account_number in customer.account_numbers
    assert account_b.account_number in customer.account_numbers
    assert bank.get_account(account_a.account_number) is account_a
