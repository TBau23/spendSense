"""
Savings metrics computation
Tracks savings growth, inflows, and emergency fund coverage
"""

from datetime import date
from typing import Dict
import pandas as pd
from .utils import filter_transactions_by_window, calculate_window_dates, calculate_average_monthly_expenses


SAVINGS_ACCOUNT_SUBTYPES = ['savings', 'money_market', 'hsa']


def compute_savings_features(
    accounts_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    user_id: str,
    as_of_date: date,
    window_days: int
) -> Dict[str, any]:
    """
    Compute savings features for a user
    
    Args:
        accounts_df: All accounts DataFrame
        transactions_df: All transactions DataFrame
        user_id: User ID
        as_of_date: End date for window
        window_days: Window size in days
        
    Returns:
        Dictionary with savings features
    """
    # Get savings-type accounts for user
    user_savings_accounts = accounts_df[
        (accounts_df['user_id'] == user_id) &
        (accounts_df['account_type'] == 'depository') &
        (accounts_df['account_subtype'].isin(SAVINGS_ACCOUNT_SUBTYPES))
    ]
    
    if user_savings_accounts.empty:
        return {
            'user_id': user_id,
            'window_days': window_days,
            'as_of_date': as_of_date,
            'net_inflow': 0.0,
            'growth_rate': 0.0,
            'emergency_fund_coverage_months': 0.0,
            'avg_monthly_expenses': 0.0
        }
    
    # Get current total savings balance (end of window)
    current_savings_balance = user_savings_accounts['balance_current'].sum()
    
    # Get transactions in window for savings accounts
    start_date, end_date = calculate_window_dates(as_of_date, window_days)
    
    savings_account_ids = user_savings_accounts['account_id'].tolist()
    savings_txns = transactions_df[
        (transactions_df['user_id'] == user_id) &
        (transactions_df['account_id'].isin(savings_account_ids)) &
        (transactions_df['date'] > start_date) &
        (transactions_df['date'] <= end_date)
    ]
    
    # Calculate net inflow (negate to convert Plaid convention to semantic meaning)
    # In Plaid: deposits are negative, withdrawals are positive
    # We want: positive net_inflow = money coming in
    net_inflow = -savings_txns['amount'].sum() if not savings_txns.empty else 0.0
    
    # Calculate growth rate
    # Start balance = Current balance - Net inflow
    start_balance = current_savings_balance - net_inflow
    
    growth_rate = 0.0
    if start_balance > 0:
        growth_rate = (current_savings_balance - start_balance) / start_balance
    
    # Calculate average monthly expenses (from all transactions)
    user_all_txns = filter_transactions_by_window(transactions_df, user_id, start_date, end_date)
    avg_monthly_expenses = calculate_average_monthly_expenses(user_all_txns, window_days)
    
    # Calculate emergency fund coverage
    emergency_fund_coverage_months = 0.0
    if avg_monthly_expenses > 0:
        emergency_fund_coverage_months = current_savings_balance / avg_monthly_expenses
    
    return {
        'user_id': user_id,
        'window_days': window_days,
        'as_of_date': as_of_date,
        'net_inflow': round(net_inflow, 2),
        'growth_rate': round(growth_rate, 4),
        'emergency_fund_coverage_months': round(emergency_fund_coverage_months, 2),
        'avg_monthly_expenses': round(avg_monthly_expenses, 2)
    }

