"""Custom exceptions for the banking system."""


class BankingError(Exception):
    """Base exception for all banking-related errors."""


class InsufficientFundsError(BankingError):
    """Raised when an account has insufficient balance for an operation."""


class InvalidAmountError(BankingError):
    """Raised when a monetary amount is invalid (zero or negative)."""


class AccountNotFoundError(BankingError):
    """Raised when the requested account does not exist."""


class CustomerNotFoundError(BankingError):
    """Raised when the requested customer does not exist."""


class DuplicateCustomerError(BankingError):
    """Raised when attempting to register a duplicate national ID."""


class TransferToSameAccountError(BankingError):
    """Raised when a transfer targets the same source and destination account."""


class PersistenceError(BankingError):
    """Raised when save or load operations fail."""
