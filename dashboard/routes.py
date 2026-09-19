"""Dashboard routes for banking system admin interface."""

from decimal import Decimal
from flask import Blueprint, render_template, current_app
from banking.enums import TransactionType, TransactionStatus

dashboard_bp = Blueprint(
    'dashboard',
    __name__,
    url_prefix='/dashboard',
    template_folder='templates'
)


@dashboard_bp.route('/')
def homepage():
    """Dashboard homepage with statistics."""
    bank = current_app.bank
    account_service = bank.account_service
    customer_service = bank.customer_service
    
    # Get all data
    accounts = account_service.accounts
    customers = customer_service._customers
    
    # Calculate statistics
    total_customers = len(customers)
    total_accounts = len(accounts)
    total_balance = sum(acc.get_balance() for acc in accounts.values())
    
    # Get recent transactions (last 10)
    all_transactions = []
    for account in accounts.values():
        for tx in account.transactions:
            all_transactions.append({
                'transaction_id': tx.transaction_id,
                'account_number': account.account_number[:8] + '...',
                'owner': account.owner.full_name,
                'type': tx.transaction_type.value,
                'amount': f"${tx.amount:.2f}",
                'status': tx.status.value,
                'timestamp': tx.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'description': tx.description,
            })
    
    # Sort by timestamp descending
    all_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_transactions = all_transactions[:10]
    
    # Count transaction types
    success_count = sum(1 for tx in all_transactions if tx['status'] == TransactionStatus.SUCCESS.value)
    failed_count = sum(1 for tx in all_transactions if tx['status'] == TransactionStatus.FAILED.value)
    
    # Count by type
    deposits = sum(1 for tx in all_transactions if tx['type'] == TransactionType.DEPOSIT.value)
    withdrawals = sum(1 for tx in all_transactions if tx['type'] == TransactionType.WITHDRAWAL.value)
    transfers = sum(1 for tx in all_transactions if tx['type'] == TransactionType.TRANSFER.value)
    
    return render_template(
        'dashboard/homepage.html',
        total_customers=total_customers,
        total_accounts=total_accounts,
        total_balance=f"${total_balance:.2f}",
        recent_transactions=recent_transactions,
        success_count=success_count,
        failed_count=failed_count,
        deposits=deposits,
        withdrawals=withdrawals,
        transfers=transfers,
        total_transactions=len(all_transactions),
    )


@dashboard_bp.route('/customers')
def customers_list():
    """List all customers with their accounts."""
    bank = current_app.bank
    account_service = bank.account_service
    customer_service = bank.customer_service
    
    customers = customer_service._customers
    accounts = account_service.accounts
    
    customers_data = []
    for national_id, customer in customers.items():
        customer_accounts = [acc for acc in accounts.values() if acc.owner.national_id == national_id]
        customer_balance = sum(acc.get_balance() for acc in customer_accounts)
        
        customers_data.append({
            'full_name': customer.full_name,
            'national_id': national_id,
            'account_count': len(customer_accounts),
            'total_balance': f"${customer_balance:.2f}",
            'account_numbers': [acc.account_number[:8] + '...' for acc in customer_accounts],
        })
    
    return render_template(
        'dashboard/customers.html',
        customers=customers_data,
        total_customers=len(customers_data),
    )


@dashboard_bp.route('/accounts')
def accounts_list():
    """List all accounts with details."""
    bank = current_app.bank
    account_service = bank.account_service
    
    accounts = account_service.accounts
    
    accounts_data = []
    for account_number, account in accounts.items():
        transactions = account.transactions
        success_txs = sum(1 for tx in transactions if tx.status.value == TransactionStatus.SUCCESS.value)
        
        accounts_data.append({
            'account_number': account_number[:8] + '...',
            'owner_name': account.owner.full_name,
            'account_type': account.account_type.value.capitalize(),
            'balance': f"${account.get_balance():.2f}",
            'transaction_count': len(transactions),
            'successful_transactions': success_txs,
            'full_account_number': account_number,
        })
    
    return render_template(
        'dashboard/accounts.html',
        accounts=accounts_data,
        total_accounts=len(accounts_data),
    )


@dashboard_bp.route('/transactions')
def transactions_list():
    """List all transactions."""
    bank = current_app.bank
    account_service = bank.account_service
    
    accounts = account_service.accounts
    
    all_transactions = []
    for account in accounts.values():
        for tx in account.transactions:
            all_transactions.append({
                'transaction_id': tx.transaction_id,
                'account_number': account.account_number[:8] + '...',
                'owner': account.owner.full_name,
                'type': tx.transaction_type.value.capitalize(),
                'amount': f"${tx.amount:.2f}",
                'status': tx.status.value.capitalize(),
                'timestamp': tx.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'description': tx.description,
                'source': tx.source_account[:8] + '...' if tx.source_account else 'N/A',
                'destination': tx.destination_account[:8] + '...' if tx.destination_account else 'N/A',
            })
    
    # Sort by timestamp descending
    all_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Calculate stats
    total_transactions = len(all_transactions)
    success_txs = sum(1 for tx in all_transactions if tx['status'] == 'Success')
    failed_txs = sum(1 for tx in all_transactions if tx['status'] == 'Failed')
    
    # Count by type
    type_counts = {}
    for tx in all_transactions:
        tx_type = tx['type']
        type_counts[tx_type] = type_counts.get(tx_type, 0) + 1
    
    return render_template(
        'dashboard/transactions.html',
        transactions=all_transactions,
        total_transactions=total_transactions,
        success_transactions=success_txs,
        failed_transactions=failed_txs,
        type_counts=type_counts,
    )
