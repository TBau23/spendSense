#!/usr/bin/env python3
"""
SpendSense Synthetic Data Generation Script

Usage:
    python scripts/generate_data.py [--config CONFIG_PATH] [--reset]

Options:
    --config: Path to configuration file (default: config.json)
    --reset: Drop existing tables and regenerate from scratch
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from storage.database import initialize_database, get_db_connection, get_db_path
from core.data_gen.generator import generate_synthetic_data
from core.data_gen.validation import generate_validation_report, save_validation_report


def load_config(config_path: str = "config.json") -> dict:
    """Load configuration from JSON file"""
    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    """Main entry point for data generation"""
    parser = argparse.ArgumentParser(
        description="Generate synthetic SpendSense data"
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to configuration file (default: config.json)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop existing tables and regenerate from scratch"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    print("Loading configuration...")
    config = load_config(args.config)
    
    data_config = config["data_generation"]
    db_config = config["database"]
    output_config = config.get("output", {})
    
    # Get database path
    db_path = db_config.get("path")
    if db_path and not db_path.startswith("/"):
        # Relative path - make it relative to project root
        project_root = Path(__file__).parent.parent
        db_path = str(project_root / db_path)
    
    # Initialize database
    print(f"Initializing database at: {db_path or 'default location'}")
    initialize_database(db_path, reset=args.reset)
    
    # Get database connection
    conn = get_db_connection(db_path)
    
    try:
        # Generate synthetic data
        generation_report = generate_synthetic_data(
            user_count=data_config["user_count"],
            consent_ratio=data_config["consent_ratio"],
            date_range_months=data_config["date_range_months"],
            conn=conn,
            seed=data_config["seed"]
        )
        
        # Validate generated data
        validation_report = generate_validation_report(
            conn=conn,
            generation_report=generation_report,
            target_consent_ratio=data_config["consent_ratio"]
        )
        
        # Save validation report
        report_path = output_config.get("validation_report_path", "data/validation_report.json")
        if not report_path.startswith("/"):
            project_root = Path(__file__).parent.parent
            report_path = str(project_root / report_path)
        
        save_validation_report(validation_report, report_path)
        
        # Summary
        if validation_report["validation_passed"]:
            print("\n✓ Data generation completed successfully!")
            print(f"  Database: {db_path or get_db_path()}")
            print(f"  Validation report: {report_path}")
        else:
            print("\n⚠ Data generation completed with validation warnings")
            print(f"  Review validation report: {report_path}")
        
        # Always return 0 to allow pipeline to continue
        return 0
            
    except Exception as e:
        print(f"\n✗ Error during data generation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

