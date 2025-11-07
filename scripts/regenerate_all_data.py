#!/usr/bin/env python3
"""
Master Data Regeneration Script

This script regenerates ALL synthetic data from scratch:
1. Wipes existing database and features
2. Generates new synthetic data (users, accounts, transactions)
3. Computes all features (credit, savings, cash flow, subscriptions, income)
4. Assigns personas (30d and 180d windows)
5. Generates decision traces for explainability

Usage:
    python scripts/regenerate_all_data.py [--users N] [--skip-validation]

Options:
    --users N           Number of users to generate (default: 75)
    --skip-validation   Skip feature validation step (faster)
    --seed N           Random seed for reproducibility (default: 42)
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
import sqlite3
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.storage.database import get_db_path
from backend.storage.schemas import create_tables
from backend.personas.storage import create_persona_assignments_table
from backend.recommend.storage import create_recommendation_tables
from backend.storage.migrations import create_decision_traces_table


def print_header(title: str):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def wipe_existing_data(db_path: str, features_dir: Path):
    """Wipe existing database and feature files"""
    print_header("STEP 1: Cleaning Existing Data")
    
    # Delete database
    if Path(db_path).exists():
        print(f"🗑️  Deleting existing database: {db_path}")
        Path(db_path).unlink()
    else:
        print(f"✓ No existing database found")
    
    # Delete feature parquet files
    if features_dir.exists():
        print(f"🗑️  Deleting existing feature files in: {features_dir}")
        for file in features_dir.glob("*.parquet"):
            file.unlink()
            print(f"   - Deleted: {file.name}")
        
        # Delete computation summary
        summary_file = features_dir / "computation_summary.json"
        if summary_file.exists():
            summary_file.unlink()
            print(f"   - Deleted: computation_summary.json")
    else:
        print(f"✓ No existing feature directory found")
    
    print("\n✅ Data cleanup complete\n")


def create_database_schema(db_path: str):
    """Create fresh database with all tables"""
    print_header("STEP 2: Creating Database Schema")
    
    conn = sqlite3.connect(db_path)
    
    print("📋 Creating core tables...")
    create_tables(conn)
    
    print("📋 Creating persona tables...")
    create_persona_assignments_table(db_path)
    
    print("📋 Creating recommendation tables...")
    create_recommendation_tables(db_path)
    
    print("📋 Creating decision traces table...")
    create_decision_traces_table(conn)
    
    conn.close()
    print("\n✅ Database schema created\n")


def generate_synthetic_data(num_users: int, seed: int, config_path: str):
    """Generate synthetic user data"""
    print_header(f"STEP 3: Generating Synthetic Data ({num_users} users)")
    
    # Update config.json with desired user count and seed
    import json
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Update generation settings
    config['data_generation']['user_count'] = num_users
    config['data_generation']['seed'] = seed
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"📝 Updated config: {num_users} users, seed={seed}")
    
    # Import here to avoid circular dependencies
    from scripts.generate_data import main as generate_data_main
    
    # Temporarily modify sys.argv for the generation script
    original_argv = sys.argv
    sys.argv = ['generate_data.py', '--reset']
    
    try:
        generate_data_main()
    finally:
        sys.argv = original_argv
    
    print("\n✅ Synthetic data generation complete\n")


def compute_features(skip_validation: bool):
    """Compute all features"""
    print_header("STEP 4: Computing Features")
    
    from scripts.compute_features import main as compute_features_main
    
    # Temporarily modify sys.argv
    original_argv = sys.argv
    if skip_validation:
        sys.argv = ['compute_features.py', '--skip-validation']
    else:
        sys.argv = ['compute_features.py']
    
    try:
        compute_features_main()
    finally:
        sys.argv = original_argv
    
    print("\n✅ Feature computation complete\n")


def assign_personas():
    """Assign personas for all users"""
    print_header("STEP 5: Assigning Personas")
    
    from scripts.assign_personas import main as assign_personas_main
    
    # Temporarily modify sys.argv
    original_argv = sys.argv
    sys.argv = ['assign_personas.py']
    
    try:
        assign_personas_main()
    finally:
        sys.argv = original_argv
    
    print("\n✅ Persona assignment complete\n")


def print_summary(db_path: str):
    """Print summary statistics"""
    print_header("REGENERATION SUMMARY")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # User counts
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE consent_status = 1")
    consented_users = cursor.fetchone()[0]
    
    print(f"\n👥 Users:")
    print(f"   Total: {total_users}")
    print(f"   Consented: {consented_users}")
    
    # Transaction counts
    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_transactions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM accounts WHERE account_type = 'credit'")
    credit_accounts = cursor.fetchone()[0]
    
    print(f"\n💳 Accounts & Transactions:")
    print(f"   Total transactions: {total_transactions:,}")
    print(f"   Credit card accounts: {credit_accounts}")
    
    # Persona distribution
    cursor.execute("""
        SELECT 
            primary_persona_id,
            primary_persona_name,
            status,
            COUNT(*) as count
        FROM persona_assignments
        WHERE window_days = 30
        GROUP BY primary_persona_id, primary_persona_name, status
        ORDER BY primary_persona_id
    """)
    
    print(f"\n🎭 Persona Distribution (30-day window):")
    for row in cursor.fetchall():
        persona_id, persona_name, status, count = row
        if status == 'STABLE':
            print(f"   STABLE (no persona): {count} users")
        else:
            print(f"   Persona {persona_id} ({persona_name}): {count} users")
    
    # Coverage
    cursor.execute("""
        SELECT COUNT(DISTINCT pa.user_id) as count
        FROM persona_assignments pa
        JOIN users u ON pa.user_id = u.user_id
        WHERE u.consent_status = 1 
        AND pa.status = 'ASSIGNED'
        AND pa.window_days = 30
    """)
    users_with_persona = cursor.fetchone()[0]
    
    if consented_users > 0:
        coverage_pct = (users_with_persona / consented_users) * 100
        print(f"\n📊 Coverage:")
        print(f"   Consented users with personas: {users_with_persona}/{consented_users} ({coverage_pct:.1f}%)")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✅ DATA REGENERATION COMPLETE!")
    print("="*80)
    print(f"\nGenerated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nDatabase: {db_path}")
    print(f"Features: {Path(db_path).parent / 'features'}")
    print("\n💡 Next steps:")
    print("   - Start backend: cd backend && source venv/bin/activate && uvicorn api.main:app --reload")
    print("   - Generate recommendations: python scripts/generate_recommendations.py")
    print("\n")


def main():
    """Main regeneration pipeline"""
    parser = argparse.ArgumentParser(
        description='Regenerate all synthetic data from scratch',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--users', type=int, default=75,
                       help='Number of users to generate (default: 75)')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip feature validation step (faster)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')
    
    args = parser.parse_args()
    
    # Confirm before wiping data
    print("\n⚠️  WARNING: This will DELETE all existing data and regenerate from scratch!")
    print(f"   - Users to generate: {args.users}")
    print(f"   - Random seed: {args.seed}")
    print(f"   - Validation: {'Skipped' if args.skip_validation else 'Enabled'}")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Aborted by user")
        return
    
    # Start timer
    start_time = datetime.now()
    
    try:
        # Get paths
        db_path = get_db_path()
        features_dir = Path(db_path).parent / "features"
        config_path = project_root / "config.json"
        
        # Execute pipeline
        wipe_existing_data(db_path, features_dir)
        create_database_schema(db_path)
        generate_synthetic_data(args.users, args.seed, str(config_path))
        compute_features(args.skip_validation)
        assign_personas()
        
        # Print summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print_summary(db_path)
        print(f"⏱️  Total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

