"""Customer management service."""

from __future__ import annotations

import threading

from banking.exceptions import CustomerNotFoundError, DuplicateCustomerError
from banking.models.customer import Customer


class CustomerService:
    """Handles customer registration and lookup."""

    def __init__(self) -> None:
        self._customers: dict[str, Customer] = {}
        self._lock = threading.Lock()

    def create_customer(self, first_name: str, last_name: str, national_id: str) -> Customer:
        with self._lock:
            if national_id in self._customers:
                raise DuplicateCustomerError(
                    f"Customer with national ID {national_id} already exists"
                )
            customer = Customer(
                first_name=first_name,
                last_name=last_name,
                national_id=national_id,
            )
            self._customers[national_id] = customer
            return customer

    def get_customer(self, national_id: str) -> Customer:
        with self._lock:
            customer = self._customers.get(national_id)
            if customer is None:
                raise CustomerNotFoundError(
                    f"Customer with national ID {national_id} not found"
                )
            return customer

    def list_customers(self) -> list[Customer]:
        with self._lock:
            return list(self._customers.values())

    @property
    def customers(self) -> dict[str, Customer]:
        with self._lock:
            return dict(self._customers)

    def load_customers(self, customers: dict[str, Customer]) -> None:
        with self._lock:
            self._customers = customers
