"""Tests for customer registration."""

import pytest

from banking.exceptions import DuplicateCustomerError


def test_create_customer_success(bank):
    customer = bank.create_customer("Ali", "Rezaei", "1122334455")

    assert customer.national_id == "1122334455"
    assert customer.full_name == "Ali Rezaei"
    assert bank.get_customer("1122334455") is customer


def test_create_customer_duplicate_raises(bank):
    bank.create_customer("First", "User", "5566778899")

    with pytest.raises(DuplicateCustomerError):
        bank.create_customer("Second", "User", "5566778899")
