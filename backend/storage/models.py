"""
SQLAlchemy models for SpendSense
Based on Plaid transaction schema
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    Date, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    """
    User model - represents a synthetic user with financial data
    """
    __tablename__ = 'users'
    
    user_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Persona assignment
    primary_persona = Column(String, nullable=True)  # high_utilization, variable_income, etc.
    secondary_persona = Column(String, nullable=True)
    persona_assigned_at = Column(DateTime, nullable=True)
    
    # Relationships
    accounts = relationship('Account', back_populates='user', cascade='all, delete-orphan')
    consent = relationship('Consent', back_populates='user', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<User(user_id='{self.user_id}', name='{self.name}', persona='{self.primary_persona}')>"


class Account(Base):
    """
    Account model - checking, savings, credit cards, etc.
    Based on Plaid Accounts schema
    """
    __tablename__ = 'accounts'
    
    account_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False)
    
    # Account details
    name = Column(String, nullable=False)  # e.g., "Chase Checking"
    type = Column(String, nullable=False)  # checking, savings, credit, etc.
    subtype = Column(String, nullable=True)  # checking, savings, credit card, money market, HSA
    
    # Balances
    available_balance = Column(Float, nullable=True)
    current_balance = Column(Float, nullable=False)
    limit = Column(Float, nullable=True)  # For credit accounts
    
    # Metadata
    iso_currency_code = Column(String, default='USD')
    holder_category = Column(String, default='personal')  # personal/business
    mask = Column(String, nullable=True)  # Last 4 digits, e.g., "4523"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='accounts')
    transactions = relationship('Transaction', back_populates='account', cascade='all, delete-orphan')
    liabilities = relationship('Liability', back_populates='account', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Account(account_id='{self.account_id}', type='{self.type}', balance={self.current_balance})>"


class Transaction(Base):
    """
    Transaction model - individual financial transactions
    Based on Plaid Transactions schema
    """
    __tablename__ = 'transactions'
    
    transaction_id = Column(String, primary_key=True, index=True)
    account_id = Column(String, ForeignKey('accounts.account_id'), nullable=False)
    
    # Transaction details
    date = Column(Date, nullable=False, index=True)
    amount = Column(Float, nullable=False)  # Positive = money out, Negative = money in
    merchant_name = Column(String, nullable=True)
    merchant_entity_id = Column(String, nullable=True)
    
    # Categories
    payment_channel = Column(String, nullable=True)  # online, in store, other
    category_primary = Column(String, nullable=True)  # INCOME, FOOD_AND_DRINK, etc.
    category_detailed = Column(String, nullable=True)  # More specific category
    
    # Status
    pending = Column(Boolean, default=False)
    
    # Metadata
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account = relationship('Account', back_populates='transactions')
    
    def __repr__(self):
        return f"<Transaction(id='{self.transaction_id}', date='{self.date}', amount={self.amount})>"


class Liability(Base):
    """
    Liability model - credit cards, loans, mortgages
    Based on Plaid Liabilities schema
    """
    __tablename__ = 'liabilities'
    
    liability_id = Column(String, primary_key=True, index=True)
    account_id = Column(String, ForeignKey('accounts.account_id'), nullable=False)
    
    # Liability type
    liability_type = Column(String, nullable=False)  # credit, mortgage, student_loan
    
    # Credit card specific
    apr = Column(Float, nullable=True)
    apr_type = Column(String, nullable=True)  # balance_transfer_apr, purchase_apr
    minimum_payment_amount = Column(Float, nullable=True)
    last_payment_amount = Column(Float, nullable=True)
    last_payment_date = Column(Date, nullable=True)
    last_statement_balance = Column(Float, nullable=True)
    is_overdue = Column(Boolean, default=False)
    
    # Loan specific
    interest_rate = Column(Float, nullable=True)
    next_payment_due_date = Column(Date, nullable=True)
    next_payment_minimum = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship('Account', back_populates='liabilities')
    
    def __repr__(self):
        return f"<Liability(id='{self.liability_id}', type='{self.liability_type}', overdue={self.is_overdue})>"


class Consent(Base):
    """
    Consent model - tracks user consent for data processing
    """
    __tablename__ = 'consent'
    
    consent_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.user_id'), unique=True, nullable=False)
    
    # Consent status
    consent_status = Column(Boolean, default=False, nullable=False)
    consent_date = Column(DateTime, nullable=True)
    revoked_date = Column(DateTime, nullable=True)
    
    # Consent details
    consent_type = Column(String, default='data_processing')
    consent_version = Column(String, default='1.0')
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='consent')
    
    def __repr__(self):
        return f"<Consent(user_id='{self.user_id}', status={self.consent_status})>"


# Additional table for storing computed signals (will be added in Epic 2)
class BehavioralSignals(Base):
    """
    Behavioral signals computed from transaction data
    Separate table for easier querying and caching
    """
    __tablename__ = 'behavioral_signals'
    
    signal_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False)
    
    # Window information
    window_days = Column(Integer, nullable=False)  # 30 or 180
    computed_at = Column(DateTime, default=datetime.utcnow)
    
    # Signals stored as JSON for flexibility
    subscription_signals = Column(JSON, nullable=True)
    savings_signals = Column(JSON, nullable=True)
    credit_signals = Column(JSON, nullable=True)
    income_signals = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<BehavioralSignals(user_id='{self.user_id}', window={self.window_days}d)>"

