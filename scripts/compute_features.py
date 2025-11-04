"""
Feature computation CLI script
Computes all behavioral signals and saves to Parquet files
"""

import sys
import json
from pathlib import Path
from datetime import date, datetime

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from features.compute import compute_all_features


def load_config(config_path: str = "config.json") -> dict:
    """Load configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    """Main entry point for feature computation"""
    print("=" * 60)
    print("SpendSense - Feature Computation")
    print("=" * 60)
    
    # Load config
    config = load_config()
    
    # Get feature computation settings
    feature_config = config.get('features', {})
    db_path = config['database']['path']
    output_dir = feature_config.get('output_dir', 'data/features')
    windows = feature_config.get('windows', [30, 180])
    as_of_date_str = feature_config.get('as_of_date')
    
    # Parse as_of_date
    as_of_date = None
    if as_of_date_str:
        as_of_date = datetime.fromisoformat(as_of_date_str).date()
    else:
        as_of_date = date.today()
    
    # Compute features
    summary = compute_all_features(
        db_path=db_path,
        output_dir=output_dir,
        as_of_date=as_of_date,
        windows=windows
    )
    
    # Save summary report
    summary_path = Path(output_dir) / 'computation_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ Summary saved to {summary_path}")
    print("\n" + "=" * 60)
    print("Feature computation complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()

