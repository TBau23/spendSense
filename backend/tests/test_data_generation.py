"""
Tests for synthetic data generation (Epic 1)
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import date, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.database import initialize_database, get_db_connection
from storage.schemas import create_tables, get_table_counts, drop_all_tables
from core.data_gen.archetypes import (
    ARCHETYPES,
    get_archetype_distribution,
    get_archetype_by_name
)
from core.data_gen.generator import generate_users, generate_synthetic_data
from core.data_gen.validation import (
    validate_consent_distribution,
    validate_data_quality,
    validate_archetype_specific
)


@pytest.fixture
def test_db():
    """Create a temporary test database"""
    # Create temporary file
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    # Initialize database
    initialize_database(db_path, reset=True)
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_schema_creation(test_db):
    """Test that database schema is created correctly"""
    conn = get_db_connection(test_db)
    
    # Check that all tables exist
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    assert "users" in tables
    assert "accounts" in tables
    assert "transactions" in tables
    assert "liabilities" in tables
    
    conn.close()


def test_archetype_distribution():
    """Test archetype distribution calculation"""
    distribution = get_archetype_distribution(75)
    
    # Check that total matches
    assert sum(distribution.values()) == 75
    
    # Check that all key archetypes are present
    assert "high_utilizer" in distribution
    assert "cash_flow_stressed" in distribution
    assert "subscription_heavy" in distribution
    assert "savings_builder" in distribution
    assert "variable_income" in distribution
    
    # Check that counts are reasonable
    assert distribution["high_utilizer"] >= 5
    assert distribution["cash_flow_stressed"] >= 5


def test_archetype_definitions():
    """Test that all archetype definitions are valid"""
    # Check that we have all expected archetypes
    assert len(ARCHETYPES) >= 13  # 5 personas + multi + stable + edge cases
    
    # Test getting archetypes
    high_util = get_archetype_by_name("high_utilizer")
    assert high_util.credit_utilization_target >= 0.5
    assert high_util.payment_behavior == "minimum"
    
    cash_flow = get_archetype_by_name("cash_flow_stressed")
    assert cash_flow.target_low_balance_days_pct >= 0.30
    assert cash_flow.checking_balance_volatility == "high"
    
    savings = get_archetype_by_name("savings_builder")
    assert savings.savings_behavior in ["aggressive", "consistent"]
    assert savings.credit_utilization_target < 0.30


def test_user_generation(test_db):
    """Test user generation with consent distribution"""
    conn = get_db_connection(test_db)
    
    # Generate small test set
    archetype_dist = get_archetype_distribution(10)
    users = generate_users(10, 0.9, archetype_dist, conn)
    
    assert len(users) == 10
    
    # Check consent distribution (should be 9 consented, 1 not)
    consented = sum(1 for u in users.values() if u["consent"])
    assert 8 <= consented <= 10  # Allow some variance in small sample
    
    # Verify users in database
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    assert cursor.fetchone()[0] == 10
    
    conn.close()


def test_consent_distribution_validation(test_db):
    """Test consent distribution validation"""
    conn = get_db_connection(test_db)
    
    # Generate users with 90% consent
    archetype_dist = get_archetype_distribution(50)
    users = generate_users(50, 0.9, archetype_dist, conn)
    
    # Validate
    validation = validate_consent_distribution(conn, 0.9)
    
    assert validation["total_users"] == 50
    assert 40 <= validation["consented"] <= 48  # Allow ±10 variance
    assert validation["within_tolerance"] == True
    
    conn.close()


def test_data_quality_validation(test_db):
    """Test data quality validation checks"""
    conn = get_db_connection(test_db)
    
    # Generate complete dataset
    report = generate_synthetic_data(
        user_count=20,
        consent_ratio=0.9,
        date_range_months=7,
        conn=conn,
        seed=42
    )
    
    # Run validation
    validation = validate_data_quality(conn)
    
    # All checks should pass
    assert validation["all_checks_passed"] == True
    assert validation["checks"]["users_have_accounts"]["passed"] == True
    assert validation["checks"]["accounts_have_users"]["passed"] == True
    assert validation["checks"]["transactions_have_dates"]["passed"] == True
    
    conn.close()


def test_end_to_end_generation(test_db):
    """Test complete end-to-end data generation"""
    conn = get_db_connection(test_db)
    
    # Generate complete dataset
    report = generate_synthetic_data(
        user_count=25,
        consent_ratio=0.9,
        date_range_months=7,
        conn=conn,
        seed=42
    )
    
    # Verify report structure
    assert "generation_date" in report
    assert "users" in report["counts"]
    assert "transactions" in report["counts"]
    
    # Verify counts
    assert report["counts"]["users"] == 25
    assert report["counts"]["transactions"] > 0
    assert report["counts"]["accounts"] > 0
    
    # Verify consent distribution
    consented = report["consent_distribution"]["consented"]
    assert 20 <= consented <= 24  # 90% of 25 with variance
    
    # Verify date range
    assert report["date_range"]["months"] == 7
    
    # Verify data in database
    counts = get_table_counts(conn)
    assert counts["users"] == 25
    assert counts["transactions"] > 100  # Should have many transactions
    
    conn.close()


def test_archetype_specific_validation(test_db):
    """Test archetype-specific validation checks"""
    conn = get_db_connection(test_db)
    
    # Generate dataset with enough users for all archetypes
    report = generate_synthetic_data(
        user_count=75,
        consent_ratio=0.9,
        date_range_months=7,
        conn=conn,
        seed=42
    )
    
    # Run archetype validation
    validation = validate_archetype_specific(conn)
    
    # Check that key persona patterns exist
    assert validation["validations"]["high_utilization_users"]["count"] >= 5
    assert validation["validations"]["savings_account_users"]["count"] >= 10
    assert validation["validations"]["payroll_users"]["count"] >= 50
    
    conn.close()


def test_transaction_date_range(test_db):
    """Test that transactions span the correct date range"""
    conn = get_db_connection(test_db)
    
    # Generate dataset
    report = generate_synthetic_data(
        user_count=15,
        consent_ratio=0.9,
        date_range_months=7,
        conn=conn,
        seed=42
    )
    
    # Check transaction date range
    cursor = conn.cursor()
    cursor.execute("SELECT MIN(date), MAX(date) FROM transactions")
    min_date_str, max_date_str = cursor.fetchone()
    
    from datetime import datetime
    min_date = datetime.strptime(min_date_str, "%Y-%m-%d").date()
    max_date = datetime.strptime(max_date_str, "%Y-%m-%d").date()
    
    date_range_days = (max_date - min_date).days
    
    # Should be approximately 7 months (210 days)
    assert 180 <= date_range_days <= 240  # Allow some variance
    
    conn.close()


def test_credit_accounts_have_liabilities(test_db):
    """Test that all credit accounts have corresponding liabilities"""
    conn = get_db_connection(test_db)
    
    # Generate dataset
    report = generate_synthetic_data(
        user_count=20,
        consent_ratio=0.9,
        date_range_months=7,
        conn=conn,
        seed=42
    )
    
    # Check credit accounts vs liabilities
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM accounts WHERE account_type = 'credit'
    """)
    credit_count = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM liabilities WHERE liability_type = 'credit_card'
    """)
    liability_count = cursor.fetchone()[0]
    
    # All credit accounts should have liabilities
    assert credit_count == liability_count
    
    conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

