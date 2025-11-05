#!/usr/bin/env python3
"""
Persona Assignment Script

Assigns personas to all users based on computed behavioral features.
Creates SQLite table and exports to Parquet.

Usage:
    python scripts/assign_personas.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from personas.storage import (
    create_persona_assignments_table,
    batch_insert_persona_assignments,
    export_to_parquet,
    get_assignment_summary
)
from personas.assign import assign_all_personas, validate_assignments


def load_config(config_path: str = 'config.json') -> dict:
    """Load configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    """Main execution function"""
    print("=" * 60)
    print("PERSONA ASSIGNMENT")
    print("=" * 60)
    
    # Load config
    config = load_config()
    db_path = config['database']['path']
    features_dir = config['features']['output_dir']
    windows = config['personas']['windows']
    as_of_date = config['personas']['as_of_date']
    output_parquet = config['personas']['output_parquet']
    
    # Use current date if as_of_date is null
    if as_of_date is None:
        as_of_date = datetime.now().strftime('%Y-%m-%d')
        print(f"Using current date as as_of_date: {as_of_date}")
    
    # Verify database exists
    if not Path(db_path).exists():
        print(f"✗ Error: Database not found at {db_path}")
        print("  Run 'python scripts/generate_data.py' first")
        sys.exit(1)
    
    # Verify features exist
    feature_types = ['subscriptions', 'savings', 'credit', 'income', 'cash_flow']
    missing_features = []
    for feature_type in feature_types:
        feature_path = Path(features_dir) / f'{feature_type}.parquet'
        if not feature_path.exists():
            missing_features.append(feature_type)
    
    if missing_features:
        print(f"✗ Error: Missing feature files: {', '.join(missing_features)}")
        print("  Run 'python scripts/compute_features.py' first")
        sys.exit(1)
    
    print(f"\nConfiguration:")
    print(f"  Database: {db_path}")
    print(f"  Features: {features_dir}")
    print(f"  Windows: {windows}")
    print(f"  As of date: {as_of_date}")
    
    # Step 1: Create table
    print(f"\n{'-' * 60}")
    print("Step 1: Create persona_assignments table")
    print(f"{'-' * 60}")
    create_persona_assignments_table(db_path)
    
    # Step 2: Assign personas
    print(f"\n{'-' * 60}")
    print("Step 2: Assign personas to all users")
    print(f"{'-' * 60}")
    assignments = assign_all_personas(
        db_path=db_path,
        features_dir=features_dir,
        windows=windows,
        as_of_date=as_of_date
    )
    
    # Step 3: Insert into database
    print(f"\n{'-' * 60}")
    print("Step 3: Insert assignments into SQLite")
    print(f"{'-' * 60}")
    batch_insert_persona_assignments(db_path, assignments)
    
    # Step 4: Export to Parquet
    print(f"\n{'-' * 60}")
    print("Step 4: Export to Parquet")
    print(f"{'-' * 60}")
    export_to_parquet(db_path, output_parquet)
    
    # Step 5: Validation
    print(f"\n{'-' * 60}")
    print("Step 5: Validate assignments")
    print(f"{'-' * 60}")
    validation = validate_assignments(assignments, db_path)
    
    # Step 6: Summary
    print(f"\n{'-' * 60}")
    print("Step 6: Summary statistics")
    print(f"{'-' * 60}")
    summary = get_assignment_summary(db_path)
    
    print(f"\nTotal assignments: {summary['total_assignments']}")
    print(f"\nBy status:")
    for status, count in summary['by_status'].items():
        print(f"  {status}: {count}")
    
    print(f"\nBy primary persona:")
    for persona_name, count in summary['by_persona'].items():
        print(f"  {persona_name}: {count}")
    
    print(f"\nBy window:")
    for window, count in summary['by_window'].items():
        print(f"  {window} days: {count}")
    
    # Final status
    print(f"\n{'=' * 60}")
    if validation['validation_passed']:
        print("✓ PERSONA ASSIGNMENT COMPLETE")
        print(f"{'=' * 60}")
        print(f"\nOutputs:")
        print(f"  SQLite: {db_path} (persona_assignments table)")
        print(f"  Parquet: {output_parquet}")
        print(f"\nNext steps:")
        print(f"  - Review assignments in database")
        print(f"  - Check audit traces for specific users")
        print(f"  - Proceed to Epic 4: Recommendation Engine")
    else:
        print("✗ VALIDATION FAILED")
        print(f"{'=' * 60}")
        print(f"Please review validation errors above")
        sys.exit(1)


if __name__ == '__main__':
    main()

