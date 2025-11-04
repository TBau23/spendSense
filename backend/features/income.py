"""
Income stability detection
Tracks payroll frequency and cash-flow buffer
"""

from datetime import date
from typing import Dict, List
import pandas as pd
import statistics
from .utils import (
    filter_transactions_by_window,
    calculate_window_dates,
    calculate_average_monthly_expenses,
    get_primary_checking_account
)


def detect_payroll_transactions(transactions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter transactions to find payroll deposits
    
    Args:
        transactions_df: Transactions DataFrame
        
    Returns:
        DataFrame with only payroll transactions
    """
    # Payroll deposits are NEGATIVE in Epic 1 data (reversed convention)
    payroll_txns = transactions_df[
        ((transactions_df['merchant_name'] == 'PAYROLL DEPOSIT') |
         (transactions_df['category_primary'] == 'INCOME')) &
        (transactions_df['amount'] < 0)
    ]
    return payroll_txns


def calculate_median_pay_gap(payroll_dates: List[date]) -> float:
    """
    Calculate median gap between consecutive payroll deposits
    
    Args:
        payroll_dates: Sorted list of payroll deposit dates
        
    Returns:
        Median pay gap in days
    """
    if len(payroll_dates) < 2:
        return 0.0
    
    gaps = []
    for i in range(1, len(payroll_dates)):
        gap = (payroll_dates[i] - payroll_dates[i-1]).days
        gaps.append(gap)
    
    if not gaps:
        return 0.0
    
    return statistics.median(gaps)


def compute_income_features(
    accounts_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    user_id: str,
    as_of_date: date,
    window_days: int
) -> Dict[str, any]:
    """
    Compute income stability features for a user
    
    Args:
        accounts_df: All accounts DataFrame
        transactions_df: All transactions DataFrame
        user_id: User ID
        as_of_date: End date for window
        window_days: Window size in days
        
    Returns:
        Dictionary with income features
    """
    # Get transactions in window
    start_date, end_date = calculate_window_dates(as_of_date, window_days)
    user_txns = filter_transactions_by_window(transactions_df, user_id, start_date, end_date)
    
    # Detect payroll transactions
    payroll_txns = detect_payroll_transactions(user_txns)
    payroll_count = len(payroll_txns)
    
    # Calculate median pay gap
    median_pay_gap_days = 0.0
    if payroll_count >= 2:
        payroll_dates = sorted(payroll_txns['date'].tolist())
        median_pay_gap_days = calculate_median_pay_gap(payroll_dates)
    
    # Calculate cash-flow buffer
    # Get primary checking account balance
    primary_checking_id = get_primary_checking_account(accounts_df, transactions_df, user_id)
    
    checking_balance = 0.0
    if primary_checking_id:
        checking_account = accounts_df[accounts_df['account_id'] == primary_checking_id]
        if not checking_account.empty:
            checking_balance = checking_account.iloc[0]['balance_current'] or 0.0
    
    # Calculate average monthly expenses
    avg_monthly_expenses = calculate_average_monthly_expenses(user_txns, window_days)
    
    # Calculate cash-flow buffer in months
    cash_flow_buffer_months = 0.0
    if avg_monthly_expenses > 0:
        cash_flow_buffer_months = checking_balance / avg_monthly_expenses
    
    return {
        'user_id': user_id,
        'window_days': window_days,
        'as_of_date': as_of_date,
        'payroll_count': payroll_count,
        'median_pay_gap_days': round(median_pay_gap_days, 1),
        'cash_flow_buffer_months': round(cash_flow_buffer_months, 2),
        'avg_monthly_expenses': round(avg_monthly_expenses, 2)
    }

