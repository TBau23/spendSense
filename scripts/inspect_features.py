"""
Inspect computed features to debug archetype detection
"""

import sys
from pathlib import Path
import pandas as pd

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from features.storage import load_features_from_parquet

# Set pandas display options
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

print("=" * 80)
print("Credit Features (180d window)")
print("=" * 80)
credit_df = load_features_from_parquet('credit', 'data/features')
credit_180 = credit_df[credit_df['window_days'] == 180]
print(f"\nTotal users: {len(credit_180)}")
print(f"\nMax utilization statistics:")
print(credit_180['max_utilization'].describe())
print(f"\nUsers with has_high_utilization=True: {credit_180['has_high_utilization'].sum()}")
print(f"\nSample of users with highest utilization:")
print(credit_180.nlargest(5, 'max_utilization')[['user_id', 'max_utilization', 'has_high_utilization']])

print("\n" + "=" * 80)
print("Subscription Features (180d window)")
print("=" * 80)
sub_df = load_features_from_parquet('subscriptions', 'data/features')
sub_180 = sub_df[sub_df['window_days'] == 180]
print(f"\nTotal users: {len(sub_180)}")
print(f"\nRecurring merchant count statistics:")
print(sub_180['recurring_merchant_count'].describe())
print(f"\nUsers with ≥3 recurring merchants: {(sub_180['recurring_merchant_count'] >= 3).sum()}")
print(f"\nSample of users with most recurring merchants:")
print(sub_180.nlargest(5, 'recurring_merchant_count')[['user_id', 'recurring_merchant_count', 'monthly_recurring_spend']])

print("\n" + "=" * 80)
print("Cash Flow Features (180d window)")
print("=" * 80)
cash_df = load_features_from_parquet('cash_flow', 'data/features')
cash_180 = cash_df[cash_df['window_days'] == 180]
print(f"\nTotal users: {len(cash_180)}")
print(f"\nPct days below $100 statistics:")
print(cash_180['pct_days_below_100'].describe())
print(f"\nUsers with ≥30% days below $100: {(cash_180['pct_days_below_100'] >= 0.30).sum()}")
print(f"\nSample of users with highest low balance frequency:")
print(cash_180.nlargest(5, 'pct_days_below_100')[['user_id', 'pct_days_below_100', 'balance_volatility', 'avg_balance']])

print("\n" + "=" * 80)
print("Savings Features (180d window)")
print("=" * 80)
savings_df = load_features_from_parquet('savings', 'data/features')
savings_180 = savings_df[savings_df['window_days'] == 180]
print(f"\nTotal users: {len(savings_180)}")
print(f"\nGrowth rate statistics:")
print(savings_180['growth_rate'].describe())
print(f"\nUsers with positive growth: {(savings_180['growth_rate'] > 0).sum()}")
print(f"\nSample of users with highest growth:")
print(savings_180.nlargest(5, 'growth_rate')[['user_id', 'growth_rate', 'net_inflow']])

