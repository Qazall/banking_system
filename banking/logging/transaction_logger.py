"""Transaction logging to transactions.log using the standard logging module."""

from __future__ import annotations

import logging
from pathlib import Path

from banking.models.transaction import Transaction

_LOGGER: logging.Logger | None = None


def get_transaction_logger(log_path: str | Path = "transactions.log") -> logging.Logger:
    global _LOGGER
    path = Path(log_path)
    logger_name = f"banking.transactions.{path.resolve()}"

    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)

    if _LOGGER is None:
        _LOGGER = logger
    return logger


def log_transaction(transaction: Transaction, log_path: str | Path = "transactions.log") -> None:
    """Log a transaction. Failures in logging must not affect banking operations."""
    try:
        logger = get_transaction_logger(log_path)
        logger.info(
            "transaction_id=%s | type=%s | amount=%s | source=%s | "
            "destination=%s | status=%s | description=%s",
            transaction.transaction_id,
            transaction.transaction_type.value,
            transaction.amount,
            transaction.source_account,
            transaction.destination_account,
            transaction.status.value,
            transaction.description,
        )
    except Exception:
        pass

def find_transaction_in_log(transaction_id: str, log_path: str | Path = "transactions.log") -> dict | None:
    """Search through the log file and parse a transaction's data by its ID."""
    path = Path(log_path)
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            for line in file:

                if f"transaction_id={transaction_id}" in line:
                    parts = line.strip().split(" | ")
                    timestamp = parts[0]
                    metadata_str = " | ".join(parts[1:])
                    
                    kv_pairs = metadata_str.split(" | ")
                    data = {"timestamp": timestamp}
                    
                    for kv in kv_pairs:
                        if "=" in kv:
                            key, val = kv.split("=", 1)
                            if val == "None":
                                val = None
                            data[key] = val
                            
                    return data
    except Exception:
        return None
    return None