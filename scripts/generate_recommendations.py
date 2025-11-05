#!/usr/bin/env python3
"""
Generate Recommendations Script

CLI tool to generate recommendations for users.
Supports single-user and batch modes.
"""

import sys
import os
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.recommend.generator import (
    generate_recommendation,
    generate_batch_recommendations
)
from backend.recommend.storage import export_recommendations_to_parquet


def main():
    parser = argparse.ArgumentParser(
        description='Generate personalized recommendations for users'
    )
    
    parser.add_argument(
        '--user-id',
        type=str,
        help='Generate recommendation for a specific user'
    )
    
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Generate recommendations for all users with persona assignments'
    )
    
    parser.add_argument(
        '--as-of-date',
        type=str,
        help='Date for reproducible generation (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--export-parquet',
        action='store_true',
        help='Export recommendations to Parquet after generation'
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default='data/spendsense.db',
        help='Path to SQLite database (default: data/spendsense.db)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.user_id and not args.batch:
        parser.error("Either --user-id or --batch must be specified")
    
    if args.user_id and args.batch:
        parser.error("Cannot specify both --user-id and --batch")
    
    # Check database exists
    if not os.path.exists(args.db_path):
        print(f"Error: Database not found at {args.db_path}")
        sys.exit(1)
    
    try:
        if args.user_id:
            # Single user generation
            print(f"\nGenerating recommendation for user: {args.user_id}\n")
            
            recommendation = generate_recommendation(
                user_id=args.user_id,
                as_of_date=args.as_of_date
            )
            
            if 'error' in recommendation:
                print(f"\n✗ Failed: {recommendation['error']}")
                sys.exit(1)
            else:
                print(f"\n✓ Successfully generated recommendation")
                print(f"   Recommendation ID: {recommendation['recommendation_id']}")
                print(f"   Educational items: {len(recommendation['educational_content'])}")
                print(f"   Actionable items: {len(recommendation['actionable_items'])}")
                print(f"   Partner offers: {len(recommendation['partner_offers'])}")
                print(f"   Generation time: {recommendation['generation_latency_seconds']:.2f}s")
        
        elif args.batch:
            # Batch generation
            print(f"\nGenerating recommendations for all users...\n")
            
            results = generate_batch_recommendations(
                user_ids=None,  # All users
                as_of_date=args.as_of_date
            )
            
            if results['failed'] > 0:
                print(f"\n⚠ Some users failed:")
                for error in results['errors'][:5]:  # Show first 5
                    print(f"   - {error['user_id']}: {error['error']}")
                if len(results['errors']) > 5:
                    print(f"   ... and {len(results['errors']) - 5} more")
        
        # Export to Parquet if requested
        if args.export_parquet:
            print(f"\nExporting to Parquet...")
            output_path = 'data/features/recommendations.parquet'
            export_recommendations_to_parquet(args.db_path, output_path)
            print(f"✓ Exported to {output_path}")
        
        print("\n✓ Generation complete!\n")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

