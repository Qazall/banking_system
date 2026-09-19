# 🏦 Enterprise Banking System Simulation

A robust, thread-safe, and object-oriented banking system framework developed in Pure Python. This project simulates a real-world enterprise banking environment, focusing on concurrent transaction management, data integrity, and advanced software design patterns.

## ✨ Key Features

- **High-Concurrency (Thread-Safe):** Utilizes Python's `threading` module and `RLock` to simulate multiple ATMs executing transactions simultaneously without race conditions.
- **Precision Financial Math:** Employs the `Decimal` library for exact financial calculations, entirely preventing floating-point inaccuracies.
- **State Persistence:** Features a custom data persistence layer using JSON to securely store, update, and retrieve account states and transaction histories.
- **Event-Driven Architecture:** Implements the **Observer** design pattern for real-time, decoupled, and structured transaction logging.
- **Custom Exception Handling:** Robust error management customized for financial operations (e.g., `InsufficientFundsError`, `ConcurrencyLockError`).

## 🏗 Architecture & Design Patterns

- **Singleton Facade:** Provides a unified, thread-safe entry point to manage the entire banking subsystem globally.
- **Abstract Base Classes (ABC):** Defines strict, standard interfaces for extending various account types (e.g., Savings, Checking).
- **Observer Pattern:** Decouples core financial logic from side-effect operations like logging and notifications.

## 🛠 Tech Stack

- **Language:** Pure Python (No external frameworks like Django/Flask used)
- **Core Modules:** `threading`, `decimal`, `json`, `abc`, `logging`

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher

### Installation
1. Clone the repository:
   ```bash
   git clone [https://github.com/Qazall/banking_system.git](https://github.com/Qazall/banking_system.git)