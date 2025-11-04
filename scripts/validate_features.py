"""
Validate computed features against Epic 1 archetypes
Checks that feature values align with archetype expectations
"""

import sys
import json
import sqlite3
from pathlib import Path
import pandas as pd

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from features.storage import load_features_from_parquet


def load_user_archetypes(db_path: str = "data/spendsense.db") -> dict:
    """Load user IDs and their archetypes from database"""
    # We need to infer archetypes from data since they weren't explicitly stored
    # For validation, we'll check feature patterns match expected behavior
    conn = sqlite3.connect(db_path)
    users_df = pd.read_sql_query("SELECT user_id, name FROM users", conn)
    conn.close()
    return users_df


def validate_high_utilization_users():
    """Validate High Utilization archetype users"""
    credit_df = load_features_from_parquet('credit', 'data/features')
    
    # Filter for 180-day window
    credit_180 = credit_df[credit_df['window_days'] == 180]
    
    # Count users with high utilization (≥50%)
    high_util_users = credit_180[credit_180['has_high_utilization'] == True]
    
    print(f"\n✓ High Utilization Users: {len(high_util_users)}")
    print(f"  - Expected: ≥5 users with utilization ≥50%")
    print(f"  - Actual: {len(high_util_users)} users")
    
    if len(high_util_users) >= 5:
        print(f"  - ✓ PASS: Sufficient high utilization users detected")
        return True
    else:
        print(f"  - ✗ FAIL: Need at least 5 high utilization users")
        return False


def validate_subscription_heavy_users():
    """Validate Subscription Heavy archetype users"""
    sub_df = load_features_from_parquet('subscriptions', 'data/features')
    
    # Filter for 180-day window (uses 90-day detection but reported with 180)
    sub_180 = sub_df[sub_df['window_days'] == 180]
    
    # Count users with ≥3 recurring merchants
    sub_heavy_users = sub_180[sub_180['recurring_merchant_count'] >= 3]
    
    print(f"\n✓ Subscription Heavy Users: {len(sub_heavy_users)}")
    print(f"  - Expected: ≥5 users with ≥3 recurring merchants")
    print(f"  - Actual: {len(sub_heavy_users)} users")
    
    if len(sub_heavy_users) >= 5:
        print(f"  - ✓ PASS: Sufficient subscription heavy users detected")
        return True
    else:
        print(f"  - ✗ FAIL: Need at least 5 subscription heavy users")
        return False


def validate_savings_builder_users():
    """Validate Savings Builder archetype users"""
    savings_df = load_features_from_parquet('savings', 'data/features')
    credit_df = load_features_from_parquet('credit', 'data/features')
    
    # Filter for 180-day window
    savings_180 = savings_df[savings_df['window_days'] == 180]
    credit_180 = credit_df[credit_df['window_days'] == 180]
    
    # Merge to get both savings and credit data
    merged = savings_180.merge(credit_180, on='user_id', suffixes=('_sav', '_crd'))
    
    # Savings builder: positive growth OR net inflow ≥$200/month, AND low utilization
    savings_builders = merged[
        ((merged['growth_rate'] > 0) | (merged['net_inflow'] >= 200)) &
        (merged['max_utilization'] < 0.30)
    ]
    
    print(f"\n✓ Savings Builder Users: {len(savings_builders)}")
    print(f"  - Expected: ≥5 users with positive savings & low utilization")
    print(f"  - Actual: {len(savings_builders)} users")
    
    if len(savings_builders) >= 5:
        print(f"  - ✓ PASS: Sufficient savings builder users detected")
        return True
    else:
        print(f"  - ✗ FAIL: Need at least 5 savings builder users")
        return False


def validate_variable_income_users():
    """Validate Variable Income archetype users"""
    income_df = load_features_from_parquet('income', 'data/features')
    
    # Filter for 180-day window
    income_180 = income_df[income_df['window_days'] == 180]
    
    # Variable income: median pay gap >45 days AND cash buffer <1 month
    variable_income_users = income_180[
        (income_180['median_pay_gap_days'] > 45) &
        (income_180['cash_flow_buffer_months'] < 1)
    ]
    
    print(f"\n✓ Variable Income Users: {len(variable_income_users)}")
    print(f"  - Expected: ≥5 users with pay gap >45 days & buffer <1 month")
    print(f"  - Actual: {len(variable_income_users)} users")
    
    if len(variable_income_users) >= 5:
        print(f"  - ✓ PASS: Sufficient variable income users detected")
        return True
    else:
        print(f"  - ✗ FAIL: Need at least 5 variable income users")
        return False


def validate_cash_flow_stressed_users():
    """Validate Cash Flow Stressed archetype users"""
    cash_flow_df = load_features_from_parquet('cash_flow', 'data/features')
    
    # Filter for 180-day window
    cash_flow_180 = cash_flow_df[cash_flow_df['window_days'] == 180]
    
    # Cash flow stressed: ≥30% days below $100 AND high volatility
    cash_stressed_users = cash_flow_180[
        (cash_flow_180['pct_days_below_100'] >= 0.30)
    ]
    
    print(f"\n✓ Cash Flow Stressed Users: {len(cash_stressed_users)}")
    print(f"  - Expected: ≥5 users with ≥30% days below $100")
    print(f"  - Actual: {len(cash_stressed_users)} users")
    
    if len(cash_stressed_users) >= 5:
        print(f"  - ✓ PASS: Sufficient cash flow stressed users detected")
        return True
    else:
        print(f"  - ✗ FAIL: Need at least 5 cash flow stressed users")
        return False


def validate_feature_coverage():
    """Validate that all users have features computed"""
    users_df = load_user_archetypes()
    
    sub_df = load_features_from_parquet('subscriptions', 'data/features')
    
    total_users = len(users_df)
    
    # Check 30-day window
    sub_30 = sub_df[sub_df['window_days'] == 30]
    users_with_30d = len(sub_30)
    
    # Check 180-day window
    sub_180 = sub_df[sub_df['window_days'] == 180]
    users_with_180d = len(sub_180)
    
    print(f"\n✓ Feature Coverage:")
    print(f"  - Total users: {total_users}")
    print(f"  - Users with 30d features: {users_with_30d}")
    print(f"  - Users with 180d features: {users_with_180d}")
    
    coverage_pass = (users_with_30d == total_users and users_with_180d == total_users)
    
    if coverage_pass:
        print(f"  - ✓ PASS: 100% coverage for both windows")
        return True
    else:
        print(f"  - ✗ FAIL: Missing features for some users")
        return False


def main():
    """Run all validations"""
    print("=" * 60)
    print("Epic 2 Feature Validation")
    print("=" * 60)
    
    results = {
        'coverage': validate_feature_coverage(),
        'high_utilization': validate_high_utilization_users(),
        'subscription_heavy': validate_subscription_heavy_users(),
        'savings_builder': validate_savings_builder_users(),
        'variable_income': validate_variable_income_users(),
        'cash_flow_stressed': validate_cash_flow_stressed_users()
    }
    
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n  Total: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n✓ All archetype validations PASSED!")
        print("=" * 60)
        return 0
    else:
        print(f"\n✗ {total - passed} validation(s) FAILED")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())

