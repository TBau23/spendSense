"""
Debug subscription detection to find the issue
"""

import sys
from pathlib import Path
from datetime import date, timedelta

backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from features.subscriptions import compute_subscription_features, detect_subscription_cadence
from features.compute import load_data_from_db

# Load data
users_df, accounts_df, transactions_df, liabilities_df = load_data_from_db("data/spendsense.db")

# Test with user_ecab3301 who we know has Electric Company on the 15th
test_user = 'user_ecab3301'
as_of_date = date(2025, 11, 4)

print(f"Testing subscription detection for {test_user}")
print(f"As of date: {as_of_date}")
print()

# Get their transactions
user_txns = transactions_df[transactions_df['user_id'] == test_user]
print(f"Total transactions: {len(user_txns)}")
print()

# Check Electric Company specifically
electric_txns = user_txns[user_txns['merchant_name'] == 'Electric Company']
print(f"Electric Company transactions: {len(electric_txns)}")
print("Dates:", electric_txns['date'].tolist())
print()

if len(electric_txns) >= 3:
    dates = sorted(electric_txns['date'].tolist())
    is_sub, cadence = detect_subscription_cadence(dates, tolerance_days=2)
    print(f"Detection result: is_subscription={is_sub}, cadence={cadence}")
    
    # Calculate gaps
    gaps = []
    for i in range(1, len(dates)):
        gap = (dates[i] - dates[i-1]).days
        gaps.append(gap)
    print(f"Gaps between transactions: {gaps}")
    print(f"Gap analysis: monthly (28-32 days), actual gaps: {gaps}")
    
    # Check 70% threshold
    monthly_matches = sum(1 for gap in gaps if 28 <= gap <= 32)
    print(f"Gaps matching monthly (28-32): {monthly_matches}/{len(gaps)} = {monthly_matches/len(gaps)*100:.1f}%")
print()

# Run full subscription detection
result = compute_subscription_features(transactions_df, test_user, as_of_date, window_days=90)
print("Full subscription detection result:")
print(result)

