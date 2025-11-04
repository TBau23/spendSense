"""
Liability generation for SpendSense
Generates credit card and loan liability details (APRs, payment history, etc.)
"""

import sqlite3
import random
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
from faker import Faker

from .archetypes import Archetype
from .accounts import get_credit_accounts, get_account_balance


fake = Faker()
Faker.seed(42)


def generate_liability_id() -> str:
    """Generate a unique liability ID"""
    return f"liab_{fake.uuid4()[:8]}"


def generate_credit_card_liability(
    account_id: str,
    user_id: str,
    archetype: Archetype,
    conn: sqlite3.Connection
) -> str:
    """
    Generate liability details for a credit card
    
    Args:
        account_id: Credit card account ID
        user_id: User ID
        archetype: User's archetype
        conn: Database connection
        
    Returns:
        Liability ID
    """
    cursor = conn.cursor()
    
    # Get current credit card balance
    current_balance = get_account_balance(account_id, conn)
    
    # Get credit limit
    cursor.execute("""
        SELECT balance_limit FROM accounts WHERE account_id = ?
    """, (account_id,))
    result = cursor.fetchone()
    credit_limit = result[0] if result else 5000
    
    # APR based on archetype (higher utilization often correlates with higher APR)
    if archetype.credit_utilization_target > 0.5:
        apr = random.uniform(18.0, 25.0)  # High APR for high utilization
    elif archetype.credit_utilization_target > 0.3:
        apr = random.uniform(14.0, 20.0)  # Medium APR
    else:
        apr = random.uniform(10.0, 16.0)  # Low APR for low utilization
    
    apr_type = "variable" if random.random() < 0.7 else "fixed"
    
    # Calculate minimum payment (typically 2-3% of balance or $25, whichever is higher)
    minimum_payment = max(25, current_balance * 0.025)
    
    # Last payment based on payment behavior
    if archetype.payment_behavior == "minimum":
        last_payment = minimum_payment
    elif archetype.payment_behavior == "full":
        last_payment = current_balance * 0.9  # Most of balance
    else:  # mixed
        last_payment = random.uniform(minimum_payment, current_balance * 0.5)
    
    # Is overdue? (High utilization users more likely to be overdue)
    is_overdue = (
        archetype.credit_utilization_target > 0.7 and 
        random.random() < 0.2  # 20% chance if high utilization
    )
    
    # Payment due date (typically 21-25 days from now)
    next_payment_due = date.today() + timedelta(days=random.randint(21, 25))
    
    # Last statement balance (slightly higher than current if paying down)
    last_statement_balance = current_balance * random.uniform(1.0, 1.2)
    
    liability_id = generate_liability_id()
    
    cursor.execute("""
        INSERT INTO liabilities (
            liability_id, account_id, user_id, liability_type,
            apr_percentage, apr_type, minimum_payment_amount, last_payment_amount,
            is_overdue, next_payment_due_date, last_statement_balance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        liability_id,
        account_id,
        user_id,
        "credit_card",
        apr,
        apr_type,
        minimum_payment,
        last_payment,
        is_overdue,
        next_payment_due,
        last_statement_balance
    ))
    
    conn.commit()
    return liability_id


def generate_user_liabilities(
    user_id: str,
    archetype: Archetype,
    account_ids: List[str],
    conn: sqlite3.Connection
) -> List[str]:
    """
    Generate all liabilities for a user
    
    Args:
        user_id: User ID
        archetype: User's archetype
        account_ids: List of all account IDs for user
        conn: Database connection
        
    Returns:
        List of liability IDs created
    """
    liability_ids = []
    
    # Get credit card accounts
    credit_accounts = get_credit_accounts(user_id, conn)
    
    # Generate liability for each credit card
    for credit_account_id in credit_accounts:
        liability_id = generate_credit_card_liability(
            credit_account_id,
            user_id,
            archetype,
            conn
        )
        liability_ids.append(liability_id)
    
    return liability_ids


def calculate_interest_charges(
    account_id: str,
    conn: sqlite3.Connection
) -> float:
    """
    Calculate estimated monthly interest charges for a credit card
    
    Args:
        account_id: Credit card account ID
        conn: Database connection
        
    Returns:
        Estimated monthly interest charge
    """
    cursor = conn.cursor()
    
    # Get balance and APR
    cursor.execute("""
        SELECT a.balance_current, l.apr_percentage
        FROM accounts a
        JOIN liabilities l ON a.account_id = l.account_id
        WHERE a.account_id = ?
    """, (account_id,))
    
    result = cursor.fetchone()
    if not result:
        return 0.0
    
    balance, apr = result
    
    # Calculate monthly interest
    monthly_interest = (balance * (apr / 100)) / 12
    
    return monthly_interest


def is_minimum_payment_only(
    account_id: str,
    conn: sqlite3.Connection
) -> bool:
    """
    Check if user is making minimum payments only
    
    Args:
        account_id: Credit card account ID
        conn: Database connection
        
    Returns:
        True if making minimum payments only
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT minimum_payment_amount, last_payment_amount
        FROM liabilities
        WHERE account_id = ?
    """, (account_id,))
    
    result = cursor.fetchone()
    if not result:
        return False
    
    minimum, last_payment = result
    
    # Consider it "minimum only" if last payment was within 10% of minimum
    return last_payment < minimum * 1.1

