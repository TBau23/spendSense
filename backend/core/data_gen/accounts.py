"""
Account generation for SpendSense
Generates checking, savings, credit card, and other account types based on archetypes
"""

import sqlite3
from typing import List, Dict, Any
from faker import Faker
from datetime import datetime
from .archetypes import Archetype


fake = Faker()
Faker.seed(42)  # For reproducibility


def generate_account_id() -> str:
    """Generate a Plaid-style account ID"""
    return f"acc_{fake.uuid4()[:8]}"


def generate_user_accounts(
    user_id: str,
    archetype: Archetype,
    conn: sqlite3.Connection
) -> List[str]:
    """
    Generate accounts for a user based on their archetype
    
    Args:
        user_id: User ID
        archetype: User's archetype definition
        conn: Database connection
        
    Returns:
        List of account IDs created
    """
    cursor = conn.cursor()
    account_ids = []
    
    # Always create a checking account
    checking_id = generate_account_id()
    cursor.execute("""
        INSERT INTO accounts (
            account_id, user_id, account_type, account_subtype,
            balance_available, balance_current, balance_limit,
            iso_currency_code, holder_category
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        checking_id,
        user_id,
        "depository",
        "checking",
        archetype.starting_checking_balance,
        archetype.starting_checking_balance,
        None,
        "USD",
        "personal"
    ))
    account_ids.append(checking_id)
    
    # Create savings account if archetype has one
    if archetype.has_savings_account:
        savings_id = generate_account_id()
        
        # Determine starting savings balance based on behavior
        if archetype.savings_behavior == "aggressive":
            starting_savings = archetype.income_range[0] * 3  # 3 months income
        elif archetype.savings_behavior == "consistent":
            starting_savings = archetype.income_range[0] * 1.5  # 1.5 months income
        elif archetype.savings_behavior == "minimal":
            starting_savings = 500
        else:
            starting_savings = 100
        
        cursor.execute("""
            INSERT INTO accounts (
                account_id, user_id, account_type, account_subtype,
                balance_available, balance_current, balance_limit,
                iso_currency_code, holder_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            savings_id,
            user_id,
            "depository",
            "savings",
            starting_savings,
            starting_savings,
            None,
            "USD",
            "personal"
        ))
        account_ids.append(savings_id)
    
    # Create credit card accounts
    for i in range(archetype.credit_card_count):
        credit_id = generate_account_id()
        
        # Determine credit limit based on income
        avg_income = sum(archetype.income_range) / 2
        credit_limit = avg_income * 2  # 2x monthly income is typical
        
        # Calculate current balance based on target utilization
        current_balance = credit_limit * archetype.credit_utilization_target
        available = credit_limit - current_balance
        
        cursor.execute("""
            INSERT INTO accounts (
                account_id, user_id, account_type, account_subtype,
                balance_available, balance_current, balance_limit,
                iso_currency_code, holder_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            credit_id,
            user_id,
            "credit",
            "credit_card",
            available,
            current_balance,
            credit_limit,
            "USD",
            "personal"
        ))
        account_ids.append(credit_id)
    
    conn.commit()
    return account_ids


def get_checking_account(user_id: str, conn: sqlite3.Connection) -> str:
    """
    Get the checking account ID for a user
    
    Args:
        user_id: User ID
        conn: Database connection
        
    Returns:
        Checking account ID
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT account_id FROM accounts
        WHERE user_id = ? AND account_subtype = 'checking'
        LIMIT 1
    """, (user_id,))
    
    result = cursor.fetchone()
    return result[0] if result else None


def get_savings_account(user_id: str, conn: sqlite3.Connection) -> str:
    """
    Get the savings account ID for a user
    
    Args:
        user_id: User ID
        conn: Database connection
        
    Returns:
        Savings account ID or None
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT account_id FROM accounts
        WHERE user_id = ? AND account_subtype = 'savings'
        LIMIT 1
    """, (user_id,))
    
    result = cursor.fetchone()
    return result[0] if result else None


def get_credit_accounts(user_id: str, conn: sqlite3.Connection) -> List[str]:
    """
    Get all credit card account IDs for a user
    
    Args:
        user_id: User ID
        conn: Database connection
        
    Returns:
        List of credit card account IDs
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT account_id FROM accounts
        WHERE user_id = ? AND account_type = 'credit'
    """, (user_id,))
    
    return [row[0] for row in cursor.fetchall()]


def update_account_balance(
    account_id: str,
    new_balance: float,
    conn: sqlite3.Connection
) -> None:
    """
    Update an account's balance
    
    Args:
        account_id: Account ID
        new_balance: New balance amount
        conn: Database connection
    """
    cursor = conn.cursor()
    
    # For credit cards, also update available balance
    cursor.execute("""
        SELECT account_type, balance_limit FROM accounts WHERE account_id = ?
    """, (account_id,))
    result = cursor.fetchone()
    
    if result and result[0] == 'credit':
        limit = result[1]
        available = limit - new_balance
        cursor.execute("""
            UPDATE accounts
            SET balance_current = ?, balance_available = ?
            WHERE account_id = ?
        """, (new_balance, available, account_id))
    else:
        cursor.execute("""
            UPDATE accounts
            SET balance_current = ?, balance_available = ?
            WHERE account_id = ?
        """, (new_balance, new_balance, account_id))
    
    conn.commit()


def get_account_balance(account_id: str, conn: sqlite3.Connection) -> float:
    """
    Get current balance for an account
    
    Args:
        account_id: Account ID
        conn: Database connection
        
    Returns:
        Current balance
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT balance_current FROM accounts WHERE account_id = ?
    """, (account_id,))
    
    result = cursor.fetchone()
    return result[0] if result else 0.0

