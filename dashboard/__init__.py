"""Flask admin dashboard for banking system management."""

from flask import Flask
from banking.bank import Bank
from banking.observers.console_observer import ConsoleTransactionObserver


def create_app():
    """Application factory for Flask dashboard."""
    app = Flask(__name__, template_folder='templates')
    app.config['SECRET_KEY'] = 'dev-key-banking-dashboard'
    
    # Initialize bank singleton
    bank = Bank.get_instance()
    bank.attach_observer(ConsoleTransactionObserver())
    
    # Load existing state or seed demo data
    try:
        bank.load_state()
    except Exception:
        from decimal import Decimal
        from banking.enums import AccountType
        
        # Seed demo data
        alice = bank.create_customer("Alice", "Smith", "1111111111")
        bob = bank.create_customer("Bob", "Jones", "2222222222")
        
        bank.open_account(
            alice.national_id,
            AccountType.SAVINGS,
            initial_balance=Decimal("1000.00"),
        )
        bank.open_account(
            alice.national_id,
            AccountType.CHECKING,
            initial_balance=Decimal("500.00"),
            withdrawal_fee=Decimal("2.00"),
        )
        bank.open_account(
            bob.national_id,
            AccountType.SAVINGS,
            initial_balance=Decimal("800.00"),
        )
    
    # Store bank reference in app context
    app.bank = bank
    
    # Register blueprints
    from dashboard.routes import dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    return app
