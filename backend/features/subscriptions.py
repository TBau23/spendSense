"""
Subscription detection from recurring merchant transactions
Detects monthly and weekly recurring payment patterns
"""

from datetime import date
from typing import Dict, List, Tuple
import pandas as pd
from .utils import filter_transactions_by_window, calculate_window_dates


def detect_subscription_cadence(transaction_dates: List[date], tolerance_days: int = 2) -> Tuple[bool, str]:
    """
    Detect if transactions follow a monthly or weekly cadence
    
    Args:
        transaction_dates: Sorted list of transaction dates
        tolerance_days: Allowed deviation from expected cadence (±days)
        
    Returns:
        Tuple of (is_subscription, cadence_type)
        cadence_type is 'monthly', 'weekly', or 'none'
    """
    if len(transaction_dates) < 3:
        return False, 'none'
    
    # Calculate gaps between consecutive transactions
    gaps = []
    for i in range(1, len(transaction_dates)):
        gap = (transaction_dates[i] - transaction_dates[i-1]).days
        gaps.append(gap)
    
    if not gaps:
        return False, 'none'
    
    # Check monthly cadence (28-32 days = 30 ± 2)
    monthly_min = 30 - tolerance_days
    monthly_max = 30 + tolerance_days
    monthly_matches = sum(1 for gap in gaps if monthly_min <= gap <= monthly_max)
    monthly_ratio = monthly_matches / len(gaps)
    
    if monthly_ratio >= 0.7:  # 70% threshold
        return True, 'monthly'
    
    # Check weekly cadence (5-9 days = 7 ± 2)
    weekly_min = 7 - tolerance_days
    weekly_max = 7 + tolerance_days
    weekly_matches = sum(1 for gap in gaps if weekly_min <= gap <= weekly_max)
    weekly_ratio = weekly_matches / len(gaps)
    
    if weekly_ratio >= 0.7:  # 70% threshold
        return True, 'weekly'
    
    return False, 'none'


def compute_subscription_features(
    transactions_df: pd.DataFrame,
    user_id: str,
    as_of_date: date,
    window_days: int = 90
) -> Dict[str, any]:
    """
    Compute subscription features for a user
    
    Args:
        transactions_df: All transactions DataFrame
        user_id: User ID
        as_of_date: End date for window
        window_days: Window size (default 90 for subscription detection)
        
    Returns:
        Dictionary with subscription features
    """
    # Get transactions in window
    start_date, end_date = calculate_window_dates(as_of_date, window_days)
    user_txns = filter_transactions_by_window(transactions_df, user_id, start_date, end_date)
    
    if user_txns.empty:
        return {
            'user_id': user_id,
            'window_days': window_days,
            'as_of_date': as_of_date,
            'recurring_merchant_count': 0,
            'monthly_recurring_spend': 0.0,
            'subscription_share': 0.0
        }
    
    # Calculate total spend (all outflows - POSITIVE amounts in Epic 1 data)
    total_spend = abs(user_txns[user_txns['amount'] > 0]['amount'].sum())
    
    # Group by merchant and count occurrences
    merchant_groups = user_txns[user_txns['amount'] > 0].groupby('merchant_name')
    
    recurring_merchants = []
    total_recurring_spend = 0.0
    
    for merchant_name, merchant_txns in merchant_groups:
        # Need at least 3 occurrences
        if len(merchant_txns) < 3:
            continue
        
        # Get sorted transaction dates
        txn_dates = sorted(merchant_txns['date'].tolist())
        
        # Check if it follows a subscription cadence
        is_subscription, cadence_type = detect_subscription_cadence(txn_dates)
        
        if is_subscription:
            recurring_merchants.append({
                'merchant': merchant_name,
                'cadence': cadence_type,
                'count': len(merchant_txns),
                'total_amount': abs(merchant_txns['amount'].sum())
            })
            total_recurring_spend += abs(merchant_txns['amount'].sum())
    
    # Calculate subscription share
    subscription_share = 0.0
    if total_spend > 0:
        subscription_share = total_recurring_spend / total_spend
    
    # Calculate monthly recurring spend (annualize to monthly)
    monthly_recurring_spend = total_recurring_spend / (window_days / 30.0)
    
    return {
        'user_id': user_id,
        'window_days': window_days,
        'as_of_date': as_of_date,
        'recurring_merchant_count': len(recurring_merchants),
        'monthly_recurring_spend': round(monthly_recurring_spend, 2),
        'subscription_share': round(subscription_share, 4)
    }

