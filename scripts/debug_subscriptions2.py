"""
Debug why user with 5 subscriptions shows 0
"""

import sys
from pathlib import Path
from datetime import date

backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from features.subscriptions import compute_subscription_features
from features.compute import load_data_from_db

# Load data
users_df, accounts_df, transactions_df, liabilities_df = load_data_from_db("data/spendsense.db")

# Test with user_0ab54bde who we know has 5 subscriptions
test_user = 'user_0ab54bde'
as_of_date = date(2025, 11, 4)

print(f"Testing subscription detection for {test_user}")
print(f"As of date: {as_of_date}")
print(f"90-day window: 2025-08-06 to 2025-11-04")
print()

# Get their transactions in the 90-day window
from datetime import timedelta
start_date = as_of_date - timedelta(days=90)
user_txns = transactions_df[
    (transactions_df['user_id'] == test_user) &
    (transactions_df['date'] > start_date) &
    (transactions_df['date'] <= as_of_date)
]

print(f"Total transactions in 90-day window: {len(user_txns)}")
print()

# Check subscription merchants
sub_merchants = ['Electric Company', 'Gym Membership', 'Internet Provider', 'Netflix', 'Spotify']
for merchant in sub_merchants:
    merchant_txns = user_txns[user_txns['merchant_name'] == merchant]
    print(f"{merchant}: {len(merchant_txns)} transactions")
    if not merchant_txns.empty:
        print(f"  Dates: {sorted(merchant_txns['date'].tolist())}")

print()

# Run full subscription detection
result = compute_subscription_features(transactions_df, test_user, as_of_date, window_days=90)
print("Full subscription detection result:")
for key, value in result.items():
    print(f"  {key}: {value}")

