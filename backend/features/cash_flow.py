"""
Cash flow analysis with daily balance reconstruction
Detects low balance frequency and balance volatility
"""

from datetime import date, timedelta
from typing import Dict, List
import pandas as pd
import statistics
from .utils import calculate_window_dates, get_primary_checking_account


def reconstruct_daily_balances(
    transactions_df: pd.DataFrame,
    account_id: str,
    start_date: date,
    end_date: date,
    current_balance: float
) -> List[float]:
    """
    Reconstruct daily balances by replaying transactions chronologically
    
    Args:
        transactions_df: All transactions DataFrame
        account_id: Account ID
        start_date: Window start date (exclusive)
        end_date: Window end date (inclusive)
        current_balance: Current account balance (as of end_date)
        
    Returns:
        List of daily balances for each day in window
    """
    # Get transactions for this account in window (and beyond for calculation)
    account_txns = transactions_df[
        (transactions_df['account_id'] == account_id) &
        (transactions_df['date'] <= end_date)
    ].sort_values('date')
    
    # Work backwards from current balance to calculate start balance
    # Sum all transactions from start_date (exclusive) to end_date (inclusive)
    window_txns = account_txns[
        (account_txns['date'] > start_date) &
        (account_txns['date'] <= end_date)
    ]
    
    net_change = window_txns['amount'].sum() if not window_txns.empty else 0.0
    start_balance = current_balance - net_change
    
    # Build daily balances array
    daily_balances = []
    running_balance = start_balance
    
    # Create date range for all days in window
    current_date = start_date + timedelta(days=1)  # Start day after start_date
    
    while current_date <= end_date:
        # Get transactions for this specific date
        day_txns = window_txns[window_txns['date'] == current_date]
        
        # Apply transactions
        if not day_txns.empty:
            day_change = day_txns['amount'].sum()
            running_balance += day_change
        
        daily_balances.append(running_balance)
        current_date += timedelta(days=1)
    
    return daily_balances


def compute_cash_flow_features(
    accounts_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    user_id: str,
    as_of_date: date,
    window_days: int,
    low_balance_threshold: float = 100.0
) -> Dict[str, any]:
    """
    Compute cash flow features for a user
    
    Args:
        accounts_df: All accounts DataFrame
        transactions_df: All transactions DataFrame
        user_id: User ID
        as_of_date: End date for window
        window_days: Window size in days
        low_balance_threshold: Threshold for low balance detection (default $100)
        
    Returns:
        Dictionary with cash flow features
    """
    # Get primary checking account
    primary_checking_id = get_primary_checking_account(accounts_df, transactions_df, user_id)
    
    if not primary_checking_id:
        return {
            'user_id': user_id,
            'window_days': window_days,
            'as_of_date': as_of_date,
            'pct_days_below_100': 0.0,
            'balance_volatility': 0.0,
            'min_balance': 0.0,
            'max_balance': 0.0,
            'avg_balance': 0.0
        }
    
    # Get current balance
    checking_account = accounts_df[accounts_df['account_id'] == primary_checking_id]
    current_balance = checking_account.iloc[0]['balance_current'] or 0.0
    
    # Reconstruct daily balances
    start_date, end_date = calculate_window_dates(as_of_date, window_days)
    daily_balances = reconstruct_daily_balances(
        transactions_df,
        primary_checking_id,
        start_date,
        end_date,
        current_balance
    )
    
    if not daily_balances:
        return {
            'user_id': user_id,
            'window_days': window_days,
            'as_of_date': as_of_date,
            'pct_days_below_100': 0.0,
            'balance_volatility': 0.0,
            'min_balance': current_balance,
            'max_balance': current_balance,
            'avg_balance': current_balance
        }
    
    # Calculate metrics
    min_balance = min(daily_balances)
    max_balance = max(daily_balances)
    avg_balance = statistics.mean(daily_balances)
    
    # Calculate % days below threshold
    days_below_threshold = sum(1 for balance in daily_balances if balance < low_balance_threshold)
    pct_days_below_100 = days_below_threshold / len(daily_balances) if daily_balances else 0.0
    
    # Calculate balance volatility (std_dev / mean)
    balance_volatility = 0.0
    if len(daily_balances) > 1 and avg_balance > 0:
        std_dev = statistics.stdev(daily_balances)
        balance_volatility = std_dev / avg_balance
    
    return {
        'user_id': user_id,
        'window_days': window_days,
        'as_of_date': as_of_date,
        'pct_days_below_100': round(pct_days_below_100, 4),
        'balance_volatility': round(balance_volatility, 4),
        'min_balance': round(min_balance, 2),
        'max_balance': round(max_balance, 2),
        'avg_balance': round(avg_balance, 2)
    }

