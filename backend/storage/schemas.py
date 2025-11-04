"""
Database schema definitions for SpendSense
Creates 4 core tables: users, accounts, transactions, liabilities
"""

import sqlite3
from typing import Optional


def create_tables(conn: sqlite3.Connection) -> None:
    """
    Create all database tables if they don't exist
    
    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()
    
    # Users table - core user data with consent tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            consent_status BOOLEAN NOT NULL,
            consent_updated_at TIMESTAMP
        )
    """)
    
    # Accounts table - checking, savings, credit, etc.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            account_type TEXT NOT NULL,
            account_subtype TEXT,
            balance_available REAL,
            balance_current REAL,
            balance_limit REAL,
            iso_currency_code TEXT DEFAULT 'USD',
            holder_category TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Transactions table - transaction history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            date DATE NOT NULL,
            amount REAL NOT NULL,
            merchant_name TEXT,
            payment_channel TEXT,
            category_primary TEXT,
            category_detailed TEXT,
            pending BOOLEAN DEFAULT 0,
            FOREIGN KEY (account_id) REFERENCES accounts(account_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Create index on transactions for efficient queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_user_date 
        ON transactions(user_id, date)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_account 
        ON transactions(account_id)
    """)
    
    # Liabilities table - credit cards, loans, mortgages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS liabilities (
            liability_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            liability_type TEXT NOT NULL,
            apr_percentage REAL,
            apr_type TEXT,
            minimum_payment_amount REAL,
            last_payment_amount REAL,
            is_overdue BOOLEAN DEFAULT 0,
            next_payment_due_date DATE,
            last_statement_balance REAL,
            interest_rate REAL,
            FOREIGN KEY (account_id) REFERENCES accounts(account_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    conn.commit()


def get_table_counts(conn: sqlite3.Connection) -> dict:
    """
    Get row counts for all tables
    
    Args:
        conn: SQLite database connection
        
    Returns:
        Dictionary with table names and row counts
    """
    cursor = conn.cursor()
    counts = {}
    
    for table in ['users', 'accounts', 'transactions', 'liabilities']:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        counts[table] = cursor.fetchone()[0]
    
    return counts


def drop_all_tables(conn: sqlite3.Connection) -> None:
    """
    Drop all tables (useful for testing/reset)
    
    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS liabilities")
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("DROP TABLE IF EXISTS accounts")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    conn.commit()

