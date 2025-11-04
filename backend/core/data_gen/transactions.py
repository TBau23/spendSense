"""
Transaction generation for SpendSense
Generates realistic transaction patterns chronologically with running balance tracking
"""

import sqlite3
import random
from typing import List, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from faker import Faker

from .archetypes import Archetype
from .accounts import (
    get_checking_account,
    get_savings_account,
    get_credit_accounts,
    update_account_balance,
    get_account_balance
)


fake = Faker()
Faker.seed(42)


# Subscription merchants (recurring)
SUBSCRIPTION_MERCHANTS = [
    ("Netflix", 15.99, "ENTERTAINMENT", "Video"),
    ("Spotify", 10.99, "ENTERTAINMENT", "Music"),
    ("Amazon Prime", 14.99, "GENERAL_SERVICES", "Subscription"),
    ("Gym Membership", 45.00, "RECREATION", "Gyms and Fitness Centers"),
    ("NYT Subscription", 17.00, "ENTERTAINMENT", "News"),
    ("iCloud Storage", 2.99, "GENERAL_SERVICES", "Cloud Storage"),
    ("Disney+", 7.99, "ENTERTAINMENT", "Video"),
    ("Meal Kit", 69.99, "FOOD_AND_DRINK", "Meal Delivery"),
]

# Regular expense merchants
EXPENSE_MERCHANTS = [
    # Groceries
    ("Whole Foods", (50, 150), "FOOD_AND_DRINK", "Supermarkets and Groceries"),
    ("Safeway", (40, 120), "FOOD_AND_DRINK", "Supermarkets and Groceries"),
    ("Trader Joe's", (35, 100), "FOOD_AND_DRINK", "Supermarkets and Groceries"),
    
    # Dining
    ("Local Restaurant", (25, 80), "FOOD_AND_DRINK", "Restaurants"),
    ("Coffee Shop", (5, 15), "FOOD_AND_DRINK", "Coffee Shop"),
    ("Fast Food", (10, 25), "FOOD_AND_DRINK", "Fast Food"),
    
    # Gas
    ("Shell Station", (40, 70), "TRANSPORTATION", "Gas Stations"),
    ("Chevron", (40, 70), "TRANSPORTATION", "Gas Stations"),
    
    # Utilities
    ("Electric Company", (80, 150), "GENERAL_SERVICES", "Utilities"),
    ("Internet Provider", (60, 100), "GENERAL_SERVICES", "Telecommunications"),
    ("Water Utility", (30, 60), "GENERAL_SERVICES", "Utilities"),
    
    # Shopping
    ("Amazon", (20, 150), "GENERAL_MERCHANDISE", "Online Shopping"),
    ("Target", (30, 120), "GENERAL_MERCHANDISE", "Superstores"),
    ("Walmart", (25, 100), "GENERAL_MERCHANDISE", "Superstores"),
    
    # Healthcare
    ("Pharmacy", (15, 80), "MEDICAL", "Pharmacies"),
    ("Doctor Visit", (30, 200), "MEDICAL", "Healthcare Services"),
    
    # Rent/Mortgage
    ("Rent Payment", None, "LOAN_PAYMENTS", "Rent"),  # Will be calculated
]


def generate_transaction_id() -> str:
    """Generate a Plaid-style transaction ID"""
    return f"txn_{fake.uuid4()[:12]}"


def generate_payroll_transaction(
    account_id: str,
    user_id: str,
    trans_date: date,
    amount: float,
    conn: sqlite3.Connection
) -> None:
    """Generate a payroll deposit transaction"""
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO transactions (
            transaction_id, account_id, user_id, date, amount,
            merchant_name, payment_channel, category_primary, category_detailed, pending
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        generate_transaction_id(),
        account_id,
        user_id,
        trans_date,
        -amount,  # Negative = deposit in Plaid convention
        "PAYROLL DEPOSIT",
        "ach",
        "INCOME",
        "Payroll",
        False
    ))


def generate_expense_transaction(
    account_id: str,
    user_id: str,
    trans_date: date,
    merchant: str,
    amount: float,
    category_primary: str,
    category_detailed: str,
    conn: sqlite3.Connection
) -> None:
    """Generate an expense transaction"""
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO transactions (
            transaction_id, account_id, user_id, date, amount,
            merchant_name, payment_channel, category_primary, category_detailed, pending
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        generate_transaction_id(),
        account_id,
        user_id,
        trans_date,
        amount,  # Positive = expense
        merchant,
        "online" if "Amazon" in merchant or "Netflix" in merchant else "in store",
        category_primary,
        category_detailed,
        False
    ))


def generate_transfer_transaction(
    account_id: str,
    user_id: str,
    trans_date: date,
    amount: float,
    is_deposit: bool,
    conn: sqlite3.Connection
) -> None:
    """Generate a transfer transaction (e.g., savings transfer)"""
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO transactions (
            transaction_id, account_id, user_id, date, amount,
            merchant_name, payment_channel, category_primary, category_detailed, pending
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        generate_transaction_id(),
        account_id,
        user_id,
        trans_date,
        -amount if is_deposit else amount,
        "TRANSFER" if is_deposit else "TRANSFER OUT",
        "ach",
        "TRANSFER_IN" if is_deposit else "TRANSFER_OUT",
        "Savings" if is_deposit else "Transfer",
        False
    ))


def calculate_payroll_dates(
    start_date: date,
    end_date: date,
    frequency: str,
    variability: float
) -> List[date]:
    """
    Calculate payroll dates based on frequency and variability
    
    Args:
        start_date: Start of period
        end_date: End of period
        frequency: "biweekly", "monthly", "irregular"
        variability: 0.0 to 1.0 (higher = more irregular)
        
    Returns:
        List of payroll dates
    """
    dates = []
    current = start_date
    
    if frequency == "biweekly":
        base_interval = 14
    elif frequency == "monthly":
        base_interval = 30
    else:  # irregular
        base_interval = 35  # Average, but will vary significantly
    
    while current <= end_date:
        dates.append(current)
        
        # Add variability to interval
        if variability > 0.5:  # High variability (for variable income)
            # Can have gaps >45 days for Persona 2
            interval = int(base_interval * random.uniform(0.7, 2.5))
        else:
            # Low variability
            interval = int(base_interval * random.uniform(0.95, 1.05))
        
        current = current + timedelta(days=interval)
    
    return dates


def generate_user_transactions(
    user_id: str,
    archetype: Archetype,
    account_ids: List[str],
    start_date: date,
    end_date: date,
    conn: sqlite3.Connection
) -> int:
    """
    Generate all transactions for a user chronologically with balance tracking
    
    Args:
        user_id: User ID
        archetype: User's archetype
        account_ids: List of account IDs for the user
        start_date: Start of transaction period
        end_date: End of transaction period
        conn: Database connection
        
    Returns:
        Number of transactions generated
    """
    transaction_count = 0
    
    # Get account IDs
    checking_id = get_checking_account(user_id, conn)
    savings_id = get_savings_account(user_id, conn)
    credit_ids = get_credit_accounts(user_id, conn)
    
    if not checking_id:
        return 0
    
    # Calculate payroll schedule
    avg_income = sum(archetype.income_range) / 2
    payroll_dates = calculate_payroll_dates(
        start_date,
        end_date,
        archetype.payroll_frequency,
        archetype.payroll_variability
    )
    
    # Select subscriptions for this user
    num_subscriptions = archetype.subscription_count
    user_subscriptions = random.sample(SUBSCRIPTION_MERCHANTS, min(num_subscriptions, len(SUBSCRIPTION_MERCHANTS)))
    
    # Calculate monthly rent/mortgage
    monthly_rent = avg_income * 0.30  # 30% of income
    
    # Track balance day-by-day for Cash Flow Stressed validation
    daily_balances = []
    current_balance = archetype.starting_checking_balance
    
    # Generate transactions chronologically
    current_date = start_date
    payroll_index = 0
    subscription_day_of_month = random.randint(1, 28)
    
    while current_date <= end_date:
        # Check if it's a payroll date
        if payroll_index < len(payroll_dates) and current_date == payroll_dates[payroll_index]:
            # Payroll deposit
            payroll_amount = avg_income * random.uniform(0.95, 1.05)
            generate_payroll_transaction(checking_id, user_id, current_date, payroll_amount, conn)
            current_balance += payroll_amount
            transaction_count += 1
            payroll_index += 1
            
            # Pay rent/mortgage a few days after payroll
            if random.random() < 0.5:  # 50% chance to pay rent right after payroll
                rent_date = current_date + timedelta(days=random.randint(1, 3))
                if rent_date <= end_date:
                    generate_expense_transaction(
                        checking_id, user_id, rent_date,
                        "Rent Payment", monthly_rent,
                        "LOAN_PAYMENTS", "Rent", conn
                    )
                    current_balance -= monthly_rent
                    transaction_count += 1
        
        # Subscriptions (monthly on specific day)
        if current_date.day == subscription_day_of_month:
            for merchant, amount, category_primary, category_detailed in user_subscriptions:
                generate_expense_transaction(
                    checking_id, user_id, current_date,
                    merchant, amount, category_primary, category_detailed, conn
                )
                current_balance -= amount
                transaction_count += 1
        
        # Regular expenses (groceries, dining, gas, etc.) - random days
        if random.random() < 0.3:  # 30% chance of expense each day
            merchant_data = random.choice([m for m in EXPENSE_MERCHANTS if m[0] not in ["Rent Payment", "Electric Company", "Internet Provider", "Water Utility"]])
            merchant, amount_range, category_primary, category_detailed = merchant_data
            
            if isinstance(amount_range, tuple):
                amount = random.uniform(*amount_range)
            else:
                amount = amount_range
            
            # Use credit card for some purchases if available
            if credit_ids and random.random() < 0.4:  # 40% of expenses on credit
                account_for_transaction = random.choice(credit_ids)
            else:
                account_for_transaction = checking_id
            
            generate_expense_transaction(
                account_for_transaction, user_id, current_date,
                merchant, amount, category_primary, category_detailed, conn
            )
            
            if account_for_transaction == checking_id:
                current_balance -= amount
            
            transaction_count += 1
        
        # Utilities (monthly on specific days)
        if current_date.day == 15:  # Mid-month utilities
            for utility in ["Electric Company", "Internet Provider", "Water Utility"]:
                merchant_data = next(m for m in EXPENSE_MERCHANTS if m[0] == utility)
                _, amount_range, category_primary, category_detailed = merchant_data
                amount = random.uniform(*amount_range)
                
                generate_expense_transaction(
                    checking_id, user_id, current_date,
                    utility, amount, category_primary, category_detailed, conn
                )
                current_balance -= amount
                transaction_count += 1
        
        # Savings transfers (for savings builders)
        if savings_id and archetype.savings_behavior in ["consistent", "aggressive"]:
            # Transfer to savings after payroll
            if payroll_index > 0 and current_date == payroll_dates[payroll_index - 1] + timedelta(days=2):
                if archetype.savings_behavior == "aggressive":
                    transfer_amount = avg_income * 0.20  # 20% of income
                else:
                    transfer_amount = avg_income * 0.10  # 10% of income
                
                # Transfer from checking
                generate_transfer_transaction(checking_id, user_id, current_date, transfer_amount, False, conn)
                current_balance -= transfer_amount
                transaction_count += 1
                
                # Transfer to savings
                generate_transfer_transaction(savings_id, user_id, current_date, transfer_amount, True, conn)
                transaction_count += 1
        
        # For Cash Flow Stressed, ensure frequent low balance days
        if archetype.target_low_balance_days_pct > 0.25 and current_balance > 100:
            # Add extra expenses to drive balance down
            if random.random() < 0.2:  # 20% chance
                amount = random.uniform(20, 80)
                merchant = random.choice(["Coffee Shop", "Fast Food", "Local Restaurant"])
                generate_expense_transaction(
                    checking_id, user_id, current_date,
                    merchant, amount, "FOOD_AND_DRINK", "Restaurants", conn
                )
                current_balance -= amount
                transaction_count += 1
        
        # Track daily balance
        daily_balances.append(current_balance)
        
        # Prevent negative balances
        if current_balance < 0:
            current_balance = 10  # Emergency floor
        
        current_date += timedelta(days=1)
    
    # Update final checking account balance
    update_account_balance(checking_id, current_balance, conn)
    
    # Update credit card balances to reflect target utilization
    for credit_id in credit_ids:
        cursor = conn.cursor()
        
        # Get credit limit
        cursor.execute("""
            SELECT balance_limit FROM accounts WHERE account_id = ?
        """, (credit_id,))
        limit = cursor.fetchone()[0]
        
        # Set final balance to match target utilization
        # This ensures archetype patterns are preserved
        target_balance = limit * archetype.credit_utilization_target
        update_account_balance(credit_id, target_balance, conn)
    
    conn.commit()
    return transaction_count

