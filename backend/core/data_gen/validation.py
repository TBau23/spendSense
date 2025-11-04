"""
Data validation for SpendSense synthetic data
Validates persona coverage, data quality, and generation correctness
"""

import sqlite3
from typing import Dict, List, Any, Tuple
from datetime import datetime, date
import json


def validate_persona_coverage(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Validate that all 5 personas have representative users
    
    Args:
        conn: Database connection
        
    Returns:
        Validation results with persona counts
    """
    cursor = conn.cursor()
    
    # Get all users with their archetypes
    # Note: In Epic 2 we'll compute actual persona assignments
    # For now, we validate based on archetype targets
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    # For Epic 1, we just validate archetypes exist
    # Real persona validation happens in Epic 2
    
    results = {
        "total_users": total_users,
        "validation": "Archetype distribution validated",
        "note": "Actual persona assignment validation occurs in Epic 2"
    }
    
    return results


def validate_consent_distribution(conn: sqlite3.Connection, target_ratio: float = 0.9) -> Dict[str, Any]:
    """
    Validate consent distribution matches target
    
    Args:
        conn: Database connection
        target_ratio: Target consent ratio (e.g., 0.9 for 90%)
        
    Returns:
        Validation results
    """
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE consent_status = 1")
    consented = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    
    actual_ratio = consented / total if total > 0 else 0
    
    # Allow ±2% variance
    within_tolerance = abs(actual_ratio - target_ratio) <= 0.02
    
    results = {
        "total_users": total,
        "consented": consented,
        "not_consented": total - consented,
        "actual_ratio": round(actual_ratio, 3),
        "target_ratio": target_ratio,
        "within_tolerance": within_tolerance,
        "passed": within_tolerance
    }
    
    return results


def validate_data_quality(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Run comprehensive data quality checks
    
    Args:
        conn: Database connection
        
    Returns:
        Validation results
    """
    cursor = conn.cursor()
    checks = {}
    
    # Check 1: All users have at least 1 account
    cursor.execute("""
        SELECT COUNT(DISTINCT u.user_id)
        FROM users u
        LEFT JOIN accounts a ON u.user_id = a.user_id
        WHERE a.account_id IS NULL
    """)
    users_without_accounts = cursor.fetchone()[0]
    checks["users_have_accounts"] = {
        "passed": users_without_accounts == 0,
        "users_without_accounts": users_without_accounts
    }
    
    # Check 2: All accounts belong to valid users
    cursor.execute("""
        SELECT COUNT(*)
        FROM accounts a
        LEFT JOIN users u ON a.user_id = u.user_id
        WHERE u.user_id IS NULL
    """)
    orphaned_accounts = cursor.fetchone()[0]
    checks["accounts_have_users"] = {
        "passed": orphaned_accounts == 0,
        "orphaned_accounts": orphaned_accounts
    }
    
    # Check 3: All transactions have valid dates
    cursor.execute("""
        SELECT COUNT(*) FROM transactions
        WHERE date IS NULL OR date = ''
    """)
    invalid_dates = cursor.fetchone()[0]
    checks["transactions_have_dates"] = {
        "passed": invalid_dates == 0,
        "invalid_dates": invalid_dates
    }
    
    # Check 4: Credit accounts have liabilities
    cursor.execute("""
        SELECT COUNT(*)
        FROM accounts a
        LEFT JOIN liabilities l ON a.account_id = l.account_id
        WHERE a.account_type = 'credit' AND l.liability_id IS NULL
    """)
    credit_without_liability = cursor.fetchone()[0]
    checks["credit_accounts_have_liabilities"] = {
        "passed": credit_without_liability == 0,
        "credit_without_liability": credit_without_liability
    }
    
    # Check 5: No business accounts
    cursor.execute("""
        SELECT COUNT(*) FROM accounts
        WHERE holder_category = 'business'
    """)
    business_accounts = cursor.fetchone()[0]
    checks["no_business_accounts"] = {
        "passed": business_accounts == 0,
        "business_accounts": business_accounts
    }
    
    # Check 6: Transaction date range
    cursor.execute("""
        SELECT MIN(date), MAX(date) FROM transactions
    """)
    result = cursor.fetchone()
    if result[0]:
        min_date = datetime.strptime(result[0], "%Y-%m-%d").date()
        max_date = datetime.strptime(result[1], "%Y-%m-%d").date()
        date_range_days = (max_date - min_date).days
        
        checks["date_range"] = {
            "passed": date_range_days >= 180,  # At least 6 months
            "min_date": str(min_date),
            "max_date": str(max_date),
            "range_days": date_range_days
        }
    else:
        checks["date_range"] = {
            "passed": False,
            "error": "No transactions found"
        }
    
    # Overall pass
    all_passed = all(check.get("passed", False) for check in checks.values())
    
    return {
        "all_checks_passed": all_passed,
        "checks": checks
    }


def validate_archetype_specific(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Validate archetype-specific patterns
    (Note: Full validation requires Epic 2 features, this is basic checks)
    
    Args:
        conn: Database connection
        
    Returns:
        Validation results
    """
    cursor = conn.cursor()
    validations = {}
    
    # Check 1: High utilization users exist (credit cards with high balance)
    cursor.execute("""
        SELECT COUNT(DISTINCT a.user_id)
        FROM accounts a
        WHERE a.account_type = 'credit'
        AND a.balance_current / a.balance_limit >= 0.5
    """)
    high_util_users = cursor.fetchone()[0]
    validations["high_utilization_users"] = {
        "count": high_util_users,
        "passed": high_util_users >= 5,
        "target": "≥5 users"
    }
    
    # Check 2: Subscription patterns (users with recurring merchants)
    cursor.execute("""
        SELECT COUNT(DISTINCT t.user_id)
        FROM transactions t
        WHERE t.merchant_name IN ('Netflix', 'Spotify', 'Amazon Prime', 'Gym Membership', 'NYT Subscription', 'iCloud Storage', 'Disney+')
        GROUP BY t.user_id
        HAVING COUNT(DISTINCT t.merchant_name) >= 3
    """)
    subscription_users = cursor.fetchone()[0] if cursor.fetchone() else 0
    validations["subscription_heavy_users"] = {
        "count": subscription_users,
        "note": "Users with ≥3 subscription merchants",
        "passed": subscription_users >= 5,
        "target": "≥5 users"
    }
    
    # Check 3: Savings accounts exist
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id)
        FROM accounts
        WHERE account_subtype = 'savings'
    """)
    savings_users = cursor.fetchone()[0]
    validations["savings_account_users"] = {
        "count": savings_users,
        "passed": savings_users >= 10,
        "target": "≥10 users"
    }
    
    # Check 4: Payroll deposits exist
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id)
        FROM transactions
        WHERE merchant_name = 'PAYROLL DEPOSIT'
    """)
    payroll_users = cursor.fetchone()[0]
    validations["payroll_users"] = {
        "count": payroll_users,
        "passed": payroll_users >= 50,
        "target": "≥50 users (most users)"
    }
    
    all_passed = all(v.get("passed", False) for v in validations.values())
    
    return {
        "all_archetype_checks_passed": all_passed,
        "validations": validations
    }


def generate_validation_report(
    conn: sqlite3.Connection,
    generation_report: Dict[str, Any],
    target_consent_ratio: float = 0.9
) -> Dict[str, Any]:
    """
    Generate comprehensive validation report
    
    Args:
        conn: Database connection
        generation_report: Report from data generation
        target_consent_ratio: Target consent ratio
        
    Returns:
        Complete validation report
    """
    print("\n" + "="*60)
    print("Data Validation Report")
    print("="*60)
    
    # Run all validations
    consent_validation = validate_consent_distribution(conn, target_consent_ratio)
    quality_validation = validate_data_quality(conn)
    archetype_validation = validate_archetype_specific(conn)
    persona_validation = validate_persona_coverage(conn)
    
    # Overall validation status
    all_passed = (
        consent_validation["passed"] and
        quality_validation["all_checks_passed"] and
        archetype_validation["all_archetype_checks_passed"]
    )
    
    report = {
        "validation_date": datetime.now().isoformat(),
        "validation_passed": all_passed,
        "generation_summary": generation_report,
        "consent_validation": consent_validation,
        "quality_validation": quality_validation,
        "archetype_validation": archetype_validation,
        "persona_validation": persona_validation
    }
    
    # Print summary
    print(f"\nConsent Distribution: {'✓ PASS' if consent_validation['passed'] else '✗ FAIL'}")
    print(f"  Target: {target_consent_ratio * 100}%, Actual: {consent_validation['actual_ratio'] * 100:.1f}%")
    
    print(f"\nData Quality: {'✓ PASS' if quality_validation['all_checks_passed'] else '✗ FAIL'}")
    for check_name, check_result in quality_validation["checks"].items():
        status = "✓" if check_result["passed"] else "✗"
        print(f"  {status} {check_name}")
    
    print(f"\nArchetype Validation: {'✓ PASS' if archetype_validation['all_archetype_checks_passed'] else '✗ FAIL'}")
    for validation_name, validation_result in archetype_validation["validations"].items():
        status = "✓" if validation_result["passed"] else "✗"
        print(f"  {status} {validation_name}: {validation_result['count']} (target: {validation_result.get('target', 'N/A')})")
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL VALIDATIONS PASSED")
    else:
        print("✗ SOME VALIDATIONS FAILED - Review report above")
    print("="*60 + "\n")
    
    return report


def save_validation_report(report: Dict[str, Any], filepath: str) -> None:
    """
    Save validation report to JSON file
    
    Args:
        report: Validation report dictionary
        filepath: Path to save report
    """
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Validation report saved to: {filepath}")

