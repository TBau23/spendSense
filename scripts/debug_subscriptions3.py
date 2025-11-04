"""
Step-by-step debugging of subscription detection
"""

import sys
from pathlib import Path
from datetime import date, timedelta

backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from features.subscriptions import detect_subscription_cadence
from features.utils import calculate_window_dates, filter_transactions_by_window
from features.compute import load_data_from_db

# Load data
users_df, accounts_df, transactions_df, liabilities_df = load_data_from_db("data/spendsense.db")

test_user = 'user_0ab54bde'
as_of_date = date(2025, 11, 4)
window_days = 90

# Manual step-by-step
start_date, end_date = calculate_window_dates(as_of_date, window_days)
user_txns = filter_transactions_by_window(transactions_df, test_user, start_date, end_date)

print(f"User: {test_user}")
print(f"Window: {start_date} to {end_date}")
print(f"Total transactions: {len(user_txns)}")
print()

# Filter to outflows only
outflows = user_txns[user_txns['amount'] < 0]
print(f"Outflow transactions: {len(outflows)}")
print()

# Group by merchant
merchant_groups = outflows.groupby('merchant_name')

print("Checking each merchant:")
print("=" * 80)

for merchant_name, merchant_txns in merchant_groups:
    if len(merchant_txns) < 3:
        continue
    
    print(f"\nMerchant: {merchant_name}")
    print(f"  Count: {len(merchant_txns)}")
    
    # Get dates
    txn_dates = merchant_txns['date'].tolist()
    print(f"  Dates (unsorted): {txn_dates}")
    print(f"  Date types: {[type(d) for d in txn_dates[:3]]}")
    
    txn_dates_sorted = sorted(txn_dates)
    print(f"  Dates (sorted): {txn_dates_sorted}")
    
    # Calculate gaps
    if len(txn_dates_sorted) >= 2:
        gaps = []
        for i in range(1, len(txn_dates_sorted)):
            gap = (txn_dates_sorted[i] - txn_dates_sorted[i-1]).days
            gaps.append(gap)
        print(f"  Gaps: {gaps}")
        
        # Check cadence
        is_subscription, cadence_type = detect_subscription_cadence(txn_dates_sorted)
        print(f"  Detection: is_subscription={is_subscription}, cadence={cadence_type}")

