"""
Feature computation orchestrator
Coordinates computation of all feature types across time windows
"""

from datetime import date, datetime
from typing import Optional, List
import pandas as pd
import sqlite3
from pathlib import Path

from .subscriptions import compute_subscription_features
from .savings import compute_savings_features
from .credit import compute_credit_features
from .income import compute_income_features
from .cash_flow import compute_cash_flow_features
from .storage import save_features_to_parquet, ensure_features_directory


def load_data_from_db(db_path: str) -> tuple:
    """
    Load all necessary data from SQLite database
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Tuple of (users_df, accounts_df, transactions_df, liabilities_df)
    """
    conn = sqlite3.connect(db_path)
    
    # Load all tables
    users_df = pd.read_sql_query("SELECT * FROM users", conn)
    accounts_df = pd.read_sql_query("SELECT * FROM accounts", conn)
    transactions_df = pd.read_sql_query("SELECT * FROM transactions", conn)
    liabilities_df = pd.read_sql_query("SELECT * FROM liabilities", conn)
    
    # Convert date columns
    transactions_df['date'] = pd.to_datetime(transactions_df['date']).dt.date
    
    conn.close()
    
    return users_df, accounts_df, transactions_df, liabilities_df


def compute_all_features(
    db_path: str = "data/spendsense.db",
    output_dir: str = "data/features",
    as_of_date: Optional[date] = None,
    windows: List[int] = [30, 180]
) -> dict:
    """
    Compute all features for all users across specified time windows
    
    Args:
        db_path: Path to SQLite database
        output_dir: Output directory for Parquet files
        as_of_date: End date for windows (defaults to today)
        windows: List of window sizes in days (default [30, 180])
        
    Returns:
        Dictionary with computation summary
    """
    # Set default as_of_date to today
    if as_of_date is None:
        as_of_date = date.today()
    
    # Ensure output directory exists
    ensure_features_directory(output_dir)
    
    # Load data
    print(f"Loading data from {db_path}...")
    users_df, accounts_df, transactions_df, liabilities_df = load_data_from_db(db_path)
    
    print(f"Computing features for {len(users_df)} users as of {as_of_date}")
    print(f"Windows: {windows} days")
    
    # Initialize feature DataFrames
    subscription_features = []
    savings_features = []
    credit_features = []
    income_features = []
    cash_flow_features = []
    
    # Compute features for each user and each window
    for _, user in users_df.iterrows():
        user_id = user['user_id']
        
        for window_days in windows:
            # Subscriptions (use 90-day window for detection)
            sub_features = compute_subscription_features(
                transactions_df,
                user_id,
                as_of_date,
                window_days=90  # Always use 90 days for subscription detection
            )
            # But report with the target window
            sub_features['window_days'] = window_days
            subscription_features.append(sub_features)
            
            # Savings
            savings_features.append(
                compute_savings_features(
                    accounts_df,
                    transactions_df,
                    user_id,
                    as_of_date,
                    window_days
                )
            )
            
            # Credit
            credit_features.append(
                compute_credit_features(
                    accounts_df,
                    liabilities_df,
                    transactions_df,
                    user_id,
                    as_of_date,
                    window_days
                )
            )
            
            # Income
            income_features.append(
                compute_income_features(
                    accounts_df,
                    transactions_df,
                    user_id,
                    as_of_date,
                    window_days
                )
            )
            
            # Cash Flow
            cash_flow_features.append(
                compute_cash_flow_features(
                    accounts_df,
                    transactions_df,
                    user_id,
                    as_of_date,
                    window_days
                )
            )
    
    # Convert to DataFrames
    print("\nCreating feature DataFrames...")
    subscriptions_df = pd.DataFrame(subscription_features)
    savings_df = pd.DataFrame(savings_features)
    credit_df = pd.DataFrame(credit_features)
    income_df = pd.DataFrame(income_features)
    cash_flow_df = pd.DataFrame(cash_flow_features)
    
    # Save to Parquet
    print(f"\nSaving features to {output_dir}...")
    save_features_to_parquet(subscriptions_df, 'subscriptions', output_dir)
    save_features_to_parquet(savings_df, 'savings', output_dir)
    save_features_to_parquet(credit_df, 'credit', output_dir)
    save_features_to_parquet(income_df, 'income', output_dir)
    save_features_to_parquet(cash_flow_df, 'cash_flow', output_dir)
    
    # Create summary
    summary = {
        'computation_date': datetime.now().isoformat(),
        'as_of_date': as_of_date.isoformat(),
        'user_count': len(users_df),
        'windows': windows,
        'features_computed': {
            'subscriptions': len(subscriptions_df),
            'savings': len(savings_df),
            'credit': len(credit_df),
            'income': len(income_df),
            'cash_flow': len(cash_flow_df)
        },
        'output_directory': output_dir
    }
    
    print("\n✓ Feature computation complete!")
    print(f"  - {len(users_df)} users")
    print(f"  - {len(windows)} windows")
    print(f"  - {len(subscriptions_df)} feature rows per signal type")
    
    return summary

