from decimal import Decimal

from banking.bank import Bank
from banking.enums import AccountType
from banking.observers.console_observer import ConsoleTransactionObserver
from simulation.atm_simulator import run_atm_simulation


def seed_demo_data(bank: Bank) -> list[str]:
    """Seed initial data for testing if no previous bank state is found."""
    alice = bank.create_customer("Alice", "Smith", "1111111111")
    bob = bank.create_customer("Bob", "Jones", "2222222222")

    savings = bank.open_account(
        alice.national_id,
        AccountType.SAVINGS,
        initial_balance=Decimal("1000.00"),
    )

    checking = bank.open_account(
        alice.national_id,
        AccountType.CHECKING,
        initial_balance=Decimal("500.00"),
        withdrawal_fee=Decimal("2.00"),
    )

    bob_savings = bank.open_account(
        bob.national_id,
        AccountType.SAVINGS,
        initial_balance=Decimal("800.00"),
    )

    return [
        savings.account_number,
        checking.account_number,
        bob_savings.account_number,
    ]


def print_accounts(bank: Bank) -> None:
    """Display all active bank accounts and their currently settled balances."""
    print("\n--- Accounts ---")

    accounts = bank.account_service.accounts

    if not accounts:
        print("No accounts found.")
        return

    for account_number, account in accounts.items():
        print(
            f"{account_number} | "
            f"{account.account_type.value:<8} | "
            f"balance={account.get_balance():.2f}"
        )


def create_customer(bank: Bank) -> None:
    """Collect details and create a new Customer profile."""
    print("\n--- Create Customer ---")

    first_name = input("First name: ")
    last_name = input("Last name: ")
    national_id = input("National ID: ")

    customer = bank.create_customer(first_name, last_name, national_id)

    print(f"Customer created: {customer.first_name} {customer.last_name}")


def create_account(bank: Bank) -> None:
    """Open a new Savings or Checking account for an existing Customer without asking for interest metrics."""
    print("\n--- Open Account ---")

    national_id = input("Customer national ID: ")

    print("1. Savings")
    print("2. Checking")
    choice = input("Choose account type: ")

    initial_balance = Decimal(input("Initial balance: "))

    if choice == "1":
        account = bank.open_account(
            national_id, 
            AccountType.SAVINGS, 
            initial_balance=initial_balance
        )

    elif choice == "2":
        withdrawal_fee = Decimal(input("Enter withdrawal fee (e.g. 2.00): "))
        account = bank.open_account(
            national_id, 
            AccountType.CHECKING, 
            initial_balance=initial_balance, 
            withdrawal_fee=withdrawal_fee
        )

    else:
        print("Invalid choice.")
        return

    print(f"Account created successfully: {account.account_number}")


def process_balance_inquiry(bank: Bank) -> None:
    """Check and display the balance of a specific account dynamically."""
    print("\n--- Balance Inquiry ---")
    account_number = input("Enter account number: ").strip()
    
    current_balance = bank.account_service.get_balance(account_number)
    print(f"Account: {account_number}")
    print(f"Current Balance: {current_balance:.2f}")


def process_deposit(bank: Bank) -> None:
    """Execute a thread-safe deposit process on a specific account."""
    print("\n--- Deposit Funds ---")
    account_number = input("Enter account number: ").strip()
    amount = Decimal(input("Enter deposit amount: "))
    description = input("Enter description (optional): ").strip()

    try:
        transaction = bank.account_service.deposit(
            account_number=account_number, 
            amount=amount, 
            description=description or "Manual Deposit"
        )
        print(f"Deposit successful. Transaction ID: {transaction.transaction_id}")
    except Exception as e:
        print(f"Transaction Failed! {e}")


def process_withdrawal(bank: Bank) -> None:
    """Execute a thread-safe withdrawal process with applied fees if applicable."""
    print("\n--- Withdraw Funds ---")
    account_number = input("Enter account number: ").strip()
    amount = Decimal(input("Enter withdrawal amount: "))
    description = input("Enter description (optional): ").strip()

    try:
        transaction = bank.account_service.withdraw(
            account_number=account_number, 
            amount=amount, 
            description=description or "Manual Withdrawal"
        )
        print(f"Withdrawal successful. Transaction ID: {transaction.transaction_id}")
    except Exception as e:
        print(f"Transaction Failed! {e}")


def process_transfer(bank: Bank) -> None:
    """Execute an atomic, deadlock-free transfer between two specific accounts."""
    print("\n--- Transfer Funds ---")
    source_number = input("Enter source account number: ").strip()
    destination_number = input("Enter destination account number: ").strip()
    amount = Decimal(input("Enter transfer amount: "))
    description = input("Enter description (optional): ").strip()

    try:
        transaction = bank.transfer(
            source_account_number=source_number,
            destination_account_number=destination_number,
            amount=amount,
            description=description or f"Transfer from {source_number[:8]} to {destination_number[:8]}"
        )
        print(f"Transfer successful. Transaction ID: {transaction.transaction_id}")
    except Exception as e:
        print(f"Transaction Failed! {e}")


def process_log_lookup(bank: Bank) -> None:
    """Find and display details of a transaction directly from the log file."""
    print("\n--- Transaction Lookup (Log File) ---")
    tx_id = input("Enter Transaction ID to search in logs: ").strip()
    
    tx_data = bank.get_transaction_from_log(tx_id)
    if tx_data:
        print("\nRecord Found in transactions.log:")
        print(f"Log Timestamp: {tx_data.get('timestamp')}")
        print(f"ID:            {tx_data.get('transaction_id')}")
        print(f"Type:          {tx_data.get('type')}")
        
        amount_val = tx_data.get('amount')
        if amount_val:
            print(f"Amount:        {Decimal(amount_val):.2f}")
        else:
            print(f"Amount:        N/A")
            
        print(f"Status:        {tx_data.get('status')}")
        print(f"Source:        {tx_data.get('source') or 'N/A'}")
        print(f"Destination:   {tx_data.get('destination') or 'N/A'}")
        print(f"Description:   {tx_data.get('description')}")
    else:
        print("Transaction ID not found in log history.")


def run_simulation(bank: Bank) -> None:
    """Launch multi-threaded ATM simulation to stress-test concurrency protections."""
    account_numbers = list(bank.account_service.accounts.keys())

    if not account_numbers:
        print("No accounts available.")
        return

    print("\nStarting ATM simulation...\n")

    threads = run_atm_simulation(
        bank,
        account_numbers,
        num_atms=5,
        operations_per_atm=15,
    )

    failed_ops = sum(len(thread.errors) for thread in threads)

    print("\nSimulation completed.")
    print(f"Expected failures (e.g. insufficient funds): {failed_ops}")

def process_full_account_data(bank: Bank) -> None:
    """Fetch and print the complete dataset, metadata, and history profile for an account."""
    print("\n--- Inspect Full Account Data ---")
    account_number = input("Enter account number: ").strip()
    
    try:
        account = bank.account_service.get_account(account_number)
        statement = account.get_full_statement()
        
        print("\n==============================================")
        print(f"ACCOUNT NUMBER : {statement['account_number']}")
        print(f"ACCOUNT TYPE   : {statement['account_type']}")
        print(f"CURRENT BALANCE: {statement['balance']:.2f}")
        print("----------------------------------------------")
        print(f"OWNER FULL NAME: {statement['owner_name']}")
        print(f"OWNER NATIONAL ID: {statement['owner_id']}")
        
        if statement['extra']:
            print("EXTRA METRICS  :")
            for key, val in statement['extra'].items():
                # Format fee display if it's our 4% rate configuration
                if key == "withdrawal_fee" and float(val) < 1.0:
                    print(f"  - {key}: {float(val)*100:.0f}% Percentage Fee Policy")
                else:
                    print(f"  - {key}: {val}")
        else:
            print("EXTRA METRICS  : None")
            
        print("----------------------------------------------")
        print(f"TRANSACTION HISTORY ({len(statement['transactions'])} records):")
        
        if not statement['transactions']:
            print("  No transactions recorded yet.")
        else:
            for idx, tx in enumerate(statement['transactions'], 1):
                print(f"\n  {idx}. [{tx['timestamp']}] ID: {tx['id']}")
                print(f"     TYPE: {tx['type']:<10} | AMOUNT: {tx['amount']:<8.2f} | STATUS: {tx['status']}")
                print(f"     DETAILS: {tx['description']}")
        print("==============================================")
        
    except Exception as e:
        print(f"Failed to fetch data profile: {e}")

def main() -> None:
    """Main lifecycle and interactive services dashboard orchestration."""
    bank = Bank.get_instance()
    bank.attach_observer(ConsoleTransactionObserver())

    try:
        bank.load_state()
        print("Loaded existing bank state.")

    except Exception:
        print("No previous state found.")
        seed_demo_data(bank)
        print("Seeded demo data.")

    while True:
        print("\n========== Banking System ==========")
        print("1. Show accounts")
        print("2. Create customer")
        print("3. Open account")
        print("4. Check specific balance")
        print("5. Deposit funds")
        print("6. Withdraw funds")
        print("7. Transfer funds")
        print("8. Run ATM simulation")
        print("9. Lookup transaction by ID")
        print("10. Save bank state")
        print("11. Get full account data profile") # <--- New Option!
        print("12. Exit")

        choice = input("Choose an option: ")

        try:
            if choice == "1":
                print_accounts(bank)

            elif choice == "2":
                create_customer(bank)

            elif choice == "3":
                create_account(bank)

            elif choice == "4":
                process_balance_inquiry(bank)

            elif choice == "5":
                process_deposit(bank)

            elif choice == "6":
                process_withdrawal(bank)

            elif choice == "7":
                process_transfer(bank)

            elif choice == "8":
                run_simulation(bank)

            elif choice == "9":
                process_log_lookup(bank)

            elif choice == "10":
                bank.save_state()
                print("Bank state saved successfully.")

            elif choice == "11":
                process_full_account_data(bank)

            elif choice == "12":
                bank.save_state()
                print("Goodbye!")
                break

            else:
                print("Invalid option.")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()