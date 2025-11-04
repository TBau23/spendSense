"""
Credit utilization and liability metrics
Tracks credit card usage, payments, and debt status
"""

from datetime import date
from typing import Dict
import pandas as pd
from .utils import filter_transactions_by_window, calculate_window_dates


def compute_credit_features(
    accounts_df: pd.DataFrame,
    liabilities_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    user_id: str,
    as_of_date: date,
    window_days: int
) -> Dict[str, any]:
    """
    Compute credit features for a user
    
    Args:
        accounts_df: All accounts DataFrame
        liabilities_df: All liabilities DataFrame
        transactions_df: All transactions DataFrame
        user_id: User ID
        as_of_date: End date for window
        window_days: Window size in days
        
    Returns:
        Dictionary with credit features
    """
    # Get credit card accounts for user
    user_credit_accounts = accounts_df[
        (accounts_df['user_id'] == user_id) &
        (accounts_df['account_type'] == 'credit') &
        (accounts_df['account_subtype'] == 'credit_card')
    ]
    
    if user_credit_accounts.empty:
        return {
            'user_id': user_id,
            'window_days': window_days,
            'as_of_date': as_of_date,
            'max_utilization': 0.0,
            'min_utilization': 0.0,
            'avg_utilization': 0.0,
            'has_high_utilization': False,
            'minimum_payment_only': False,
            'interest_charges_present': False,
            'is_overdue': False
        }
    
    # Calculate utilization for each card
    utilizations = []
    for _, account in user_credit_accounts.iterrows():
        balance = account['balance_current'] or 0.0
        limit = account['balance_limit'] or 1.0  # Avoid division by zero
        
        if limit > 0:
            utilization = balance / limit
            utilizations.append(utilization)
    
    max_utilization = max(utilizations) if utilizations else 0.0
    min_utilization = min(utilizations) if utilizations else 0.0
    avg_utilization = sum(utilizations) / len(utilizations) if utilizations else 0.0
    
    # Check if any card has high utilization (≥50%)
    has_high_utilization = max_utilization >= 0.50
    
    # Get liabilities for credit cards
    credit_account_ids = user_credit_accounts['account_id'].tolist()
    
    # Handle empty liabilities DataFrame
    if liabilities_df.empty:
        user_liabilities = pd.DataFrame()
    else:
        user_liabilities = liabilities_df[
            (liabilities_df['user_id'] == user_id) &
            (liabilities_df['account_id'].isin(credit_account_ids))
        ]
    
    # Check for minimum payment only
    minimum_payment_only = False
    if not user_liabilities.empty:
        for _, liability in user_liabilities.iterrows():
            min_payment = liability['minimum_payment_amount'] or 0.0
            last_payment = liability['last_payment_amount'] or 0.0
            
            # Within 10% tolerance
            if min_payment > 0 and last_payment > 0:
                if abs(last_payment - min_payment) / min_payment <= 0.10:
                    minimum_payment_only = True
                    break
    
    # Check for interest charges in transactions
    start_date, end_date = calculate_window_dates(as_of_date, window_days)
    
    interest_charges_present = False
    if not transactions_df.empty:
        user_txns = filter_transactions_by_window(transactions_df, user_id, start_date, end_date)
        
        if not user_txns.empty:
            # Interest charges are positive amounts (expenses)
            interest_txns = user_txns[
                (user_txns['category_primary'] == 'BANK_FEES') &
                (user_txns['category_detailed'] == 'Interest') &
                (user_txns['amount'] > 0)
            ]
            interest_charges_present = len(interest_txns) > 0
    
    # Check for overdue status
    is_overdue = False
    if not user_liabilities.empty:
        is_overdue = user_liabilities['is_overdue'].any()
    
    return {
        'user_id': user_id,
        'window_days': window_days,
        'as_of_date': as_of_date,
        'max_utilization': round(max_utilization, 4),
        'min_utilization': round(min_utilization, 4),
        'avg_utilization': round(avg_utilization, 4),
        'has_high_utilization': bool(has_high_utilization),
        'minimum_payment_only': bool(minimum_payment_only),
        'interest_charges_present': bool(interest_charges_present),
        'is_overdue': bool(is_overdue)
    }

