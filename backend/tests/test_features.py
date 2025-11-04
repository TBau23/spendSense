"""
Tests for feature engineering module
Tests all 5 signal types and end-to-end computation
"""

import pytest
from datetime import date, timedelta
import pandas as pd
from pathlib import Path
import sys

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from features.subscriptions import detect_subscription_cadence, compute_subscription_features
from features.savings import compute_savings_features
from features.credit import compute_credit_features
from features.income import calculate_median_pay_gap, compute_income_features
from features.cash_flow import reconstruct_daily_balances, compute_cash_flow_features
from features.storage import save_features_to_parquet, load_features_from_parquet
from features.compute import compute_all_features


class TestSubscriptionDetection:
    """Test subscription detection with cadence analysis"""
    
    def test_monthly_cadence_detection(self):
        """Test detection of monthly recurring transactions"""
        base_date = date(2025, 1, 1)
        dates = [
            base_date,
            base_date + timedelta(days=30),
            base_date + timedelta(days=61),
            base_date + timedelta(days=91)
        ]
        
        is_subscription, cadence = detect_subscription_cadence(dates, tolerance_days=2)
        
        assert is_subscription is True
        assert cadence == 'monthly'
    
    def test_weekly_cadence_detection(self):
        """Test detection of weekly recurring transactions"""
        base_date = date(2025, 1, 1)
        dates = [
            base_date,
            base_date + timedelta(days=7),
            base_date + timedelta(days=14),
            base_date + timedelta(days=21)
        ]
        
        is_subscription, cadence = detect_subscription_cadence(dates, tolerance_days=2)
        
        assert is_subscription is True
        assert cadence == 'weekly'
    
    def test_irregular_pattern_not_detected(self):
        """Test that irregular patterns are not detected as subscriptions"""
        base_date = date(2025, 1, 1)
        dates = [
            base_date,
            base_date + timedelta(days=5),
            base_date + timedelta(days=25),
            base_date + timedelta(days=90)
        ]
        
        is_subscription, cadence = detect_subscription_cadence(dates, tolerance_days=2)
        
        assert is_subscription is False
        assert cadence == 'none'
    
    def test_insufficient_transactions(self):
        """Test that < 3 transactions are not detected"""
        base_date = date(2025, 1, 1)
        dates = [base_date, base_date + timedelta(days=30)]
        
        is_subscription, cadence = detect_subscription_cadence(dates, tolerance_days=2)
        
        assert is_subscription is False


class TestSavingsMetrics:
    """Test savings growth and emergency fund calculations"""
    
    def test_positive_growth_rate(self):
        """Test calculation of positive savings growth"""
        # Create test data
        accounts_df = pd.DataFrame([
            {
                'user_id': 'user1',
                'account_id': 'sav1',
                'account_type': 'depository',
                'account_subtype': 'savings',
                'balance_current': 1100.0
            }
        ])
        
        # Transactions showing $100 inflow (negative in Plaid convention)
        transactions_df = pd.DataFrame([
            {
                'user_id': 'user1',
                'account_id': 'sav1',
                'date': date(2025, 10, 15),
                'amount': -100.0  # Deposits are negative in Plaid convention
            }
        ])
        
        result = compute_savings_features(
            accounts_df,
            transactions_df,
            'user1',
            date(2025, 11, 4),
            30
        )
        
        assert result['net_inflow'] == 100.0  # After sign correction, positive = money in
        assert result['growth_rate'] > 0  # Should show positive growth
    
    def test_no_savings_account(self):
        """Test user with no savings accounts"""
        accounts_df = pd.DataFrame([
            {
                'user_id': 'user1',
                'account_id': 'chk1',
                'account_type': 'depository',
                'account_subtype': 'checking',
                'balance_current': 500.0
            }
        ])
        
        transactions_df = pd.DataFrame()
        
        result = compute_savings_features(
            accounts_df,
            transactions_df,
            'user1',
            date(2025, 11, 4),
            30
        )
        
        assert result['net_inflow'] == 0.0
        assert result['growth_rate'] == 0.0


class TestCreditUtilization:
    """Test credit utilization threshold detection"""
    
    def test_high_utilization_detection(self):
        """Test detection of ≥50% utilization"""
        accounts_df = pd.DataFrame([
            {
                'user_id': 'user1',
                'account_id': 'cc1',
                'account_type': 'credit',
                'account_subtype': 'credit_card',
                'balance_current': 2500.0,
                'balance_limit': 5000.0
            }
        ])
        
        liabilities_df = pd.DataFrame([
            {
                'user_id': 'user1',
                'account_id': 'cc1',
                'minimum_payment_amount': 50.0,
                'last_payment_amount': 51.0,
                'is_overdue': False
            }
        ])
        
        transactions_df = pd.DataFrame()
        
        result = compute_credit_features(
            accounts_df,
            liabilities_df,
            transactions_df,
            'user1',
            date(2025, 11, 4),
            30
        )
        
        assert result['max_utilization'] == 0.5
        assert result['has_high_utilization'] is True
    
    def test_utilization_thresholds(self):
        """Test 30%, 50%, 80% utilization flags"""
        # 80% utilization
        accounts_df = pd.DataFrame([
            {
                'user_id': 'user1',
                'account_id': 'cc1',
                'account_type': 'credit',
                'account_subtype': 'credit_card',
                'balance_current': 4000.0,
                'balance_limit': 5000.0
            }
        ])
        
        result = compute_credit_features(
            accounts_df,
            pd.DataFrame(),
            pd.DataFrame(),
            'user1',
            date(2025, 11, 4),
            30
        )
        
        assert result['max_utilization'] == 0.8
        assert result['has_high_utilization'] is True


class TestIncomeStability:
    """Test income frequency and pay gap calculations"""
    
    def test_median_pay_gap_calculation(self):
        """Test median pay gap for biweekly payroll"""
        dates = [
            date(2025, 1, 1),
            date(2025, 1, 15),
            date(2025, 1, 29),
            date(2025, 2, 12)
        ]
        
        median_gap = calculate_median_pay_gap(dates)
        
        assert median_gap == 14.0  # Median of [14, 14, 14]
    
    def test_variable_income_detection(self):
        """Test detection of irregular payment patterns"""
        dates = [
            date(2025, 1, 1),
            date(2025, 2, 20),  # 50 day gap
            date(2025, 3, 5),   # 13 day gap
            date(2025, 5, 1)    # 57 day gap
        ]
        
        median_gap = calculate_median_pay_gap(dates)
        
        # Median of [50, 13, 57] = 50
        assert median_gap == 50.0


class TestCashFlowReconstruction:
    """Test daily balance reconstruction"""
    
    def test_daily_balance_reconstruction(self):
        """Test reconstruction of daily balances from transactions"""
        transactions_df = pd.DataFrame([
            {
                'account_id': 'chk1',
                'date': date(2025, 10, 10),
                'amount': 1000.0
            },
            {
                'account_id': 'chk1',
                'date': date(2025, 10, 15),
                'amount': -500.0
            },
            {
                'account_id': 'chk1',
                'date': date(2025, 10, 20),
                'amount': -300.0
            }
        ])
        
        # Current balance is 700 (1000 - 500 - 300 + starting balance)
        daily_balances = reconstruct_daily_balances(
            transactions_df,
            'chk1',
            date(2025, 10, 5),
            date(2025, 10, 25),
            700.0
        )
        
        # Should have 20 days of balances
        assert len(daily_balances) == 20
        
        # Final balance should be 700
        assert daily_balances[-1] == 700.0
    
    def test_low_balance_frequency(self):
        """Test detection of frequent low balances"""
        # Create checking account with low balance
        accounts_df = pd.DataFrame([
            {
                'user_id': 'user1',
                'account_id': 'chk1',
                'account_type': 'depository',
                'account_subtype': 'checking',
                'balance_current': 50.0
            }
        ])
        
        # Transactions that keep balance low
        transactions_df = pd.DataFrame([
            {
                'user_id': 'user1',
                'account_id': 'chk1',
                'date': date(2025, 10, 10),
                'amount': -20.0
            }
        ])
        
        result = compute_cash_flow_features(
            accounts_df,
            transactions_df,
            'user1',
            date(2025, 11, 4),
            30
        )
        
        # With balance at 50, should have high % of days below 100
        assert result['pct_days_below_100'] > 0.5


class TestParquetStorage:
    """Test Parquet read/write operations"""
    
    def test_parquet_round_trip(self):
        """Test writing and reading Parquet files"""
        # Create test DataFrame
        test_df = pd.DataFrame([
            {
                'user_id': 'user1',
                'window_days': 30,
                'as_of_date': date(2025, 11, 4),
                'test_value': 123.45
            }
        ])
        
        # Write to Parquet
        output_path = save_features_to_parquet(
            test_df,
            'test_features',
            'data/features/test'
        )
        
        assert output_path.exists()
        
        # Read back
        loaded_df = load_features_from_parquet('test_features', 'data/features/test')
        
        assert loaded_df is not None
        assert len(loaded_df) == 1
        assert loaded_df.iloc[0]['user_id'] == 'user1'
        
        # Cleanup
        output_path.unlink()


class TestEndToEndComputation:
    """Test end-to-end feature computation"""
    
    def test_full_feature_computation(self):
        """Test computing all features for all users"""
        # This uses the actual database from Epic 1
        summary = compute_all_features(
            db_path="data/spendsense.db",
            output_dir="data/features",
            as_of_date=date(2025, 11, 4),
            windows=[30, 180]
        )
        
        # Verify summary
        assert summary['user_count'] == 75
        assert summary['windows'] == [30, 180]
        
        # Verify features were created (75 users × 2 windows = 150 rows each)
        assert summary['features_computed']['subscriptions'] == 150
        assert summary['features_computed']['savings'] == 150
        assert summary['features_computed']['credit'] == 150
        assert summary['features_computed']['income'] == 150
        assert summary['features_computed']['cash_flow'] == 150
        
        # Verify Parquet files exist
        assert Path('data/features/subscriptions.parquet').exists()
        assert Path('data/features/savings.parquet').exists()
        assert Path('data/features/credit.parquet').exists()
        assert Path('data/features/income.parquet').exists()
        assert Path('data/features/cash_flow.parquet').exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

