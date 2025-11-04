"""
Shared utility functions for feature computation
"""

from datetime import date, timedelta
from typing import Tuple
import pandas as pd


def calculate_window_dates(as_of_date: date, window_days: int) -> Tuple[date, date]:
    """
    Calculate start and end dates for a time window
    
    Args:
        as_of_date: End date of window
        window_days: Number of days in window
        
    Returns:
        Tuple of (start_date, end_date) inclusive
    """
    end_date = as_of_date
    start_date = as_of_date - timedelta(days=window_days)
    return start_date, end_date


def filter_transactions_by_window(
    transactions_df: pd.DataFrame,
    user_id: str,
    start_date: date,
    end_date: date
) -> pd.DataFrame:
    """
    Filter transactions for a specific user and time window
    
    Args:
        transactions_df: All transactions DataFrame
        user_id: User ID to filter
        start_date: Window start date (exclusive)
        end_date: Window end date (inclusive)
        
    Returns:
        Filtered transactions DataFrame
    """
    return transactions_df[
        (transactions_df['user_id'] == user_id) &
        (transactions_df['date'] > start_date) &
        (transactions_df['date'] <= end_date)
    ].copy()


def calculate_average_monthly_expenses(
    transactions_df: pd.DataFrame,
    window_days: int
) -> float:
    """
    Calculate average monthly expenses from transactions
    
    Args:
        transactions_df: Transactions for a user in a window
        window_days: Number of days in window
        
    Returns:
        Average monthly expenses (positive number)
    """
    # Outflow transactions are POSITIVE amounts in Epic 1 data (reversed convention)
    outflows = transactions_df[transactions_df['amount'] > 0]['amount'].sum()
    
    # Already positive, calculate monthly average
    total_expenses = outflows
    months = window_days / 30.0
    
    if months == 0:
        return 0.0
    
    avg_monthly = total_expenses / months
    
    # Return at least $1 to avoid division by zero in other calculations
    return max(avg_monthly, 1.0)


def get_primary_checking_account(
    accounts_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    user_id: str
) -> str:
    """
    Get primary checking account ID for a user
    If multiple checking accounts, return the one with most transactions
    
    Args:
        accounts_df: All accounts DataFrame
        transactions_df: All transactions DataFrame
        user_id: User ID
        
    Returns:
        Primary checking account_id or empty string if none found
    """
    # Get all checking accounts for user
    checking_accounts = accounts_df[
        (accounts_df['user_id'] == user_id) &
        (accounts_df['account_type'] == 'depository') &
        (accounts_df['account_subtype'] == 'checking')
    ]
    
    if checking_accounts.empty:
        return ""
    
    if len(checking_accounts) == 1:
        return checking_accounts.iloc[0]['account_id']
    
    # Multiple checking accounts - find one with most transactions
    account_txn_counts = []
    for account_id in checking_accounts['account_id']:
        txn_count = len(transactions_df[transactions_df['account_id'] == account_id])
        account_txn_counts.append((account_id, txn_count))
    
    # Sort by transaction count descending
    account_txn_counts.sort(key=lambda x: x[1], reverse=True)
    
    return account_txn_counts[0][0]

