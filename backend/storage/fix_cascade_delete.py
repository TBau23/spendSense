"""
Fix Foreign Key Constraints to Support CASCADE DELETE

SQLite doesn't support ALTER TABLE for foreign keys, so we need to recreate tables.
This script adds ON DELETE CASCADE to recommendation_items and decision_traces.
"""

import sqlite3
import sys
from pathlib import Path


def fix_cascade_delete(db_path: str):
    """
    Add CASCADE DELETE to foreign key constraints
    
    Args:
        db_path: Path to SQLite database
    """
    print(f"Fixing foreign key constraints in {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    try:
        # 1. Backup and recreate recommendation_items with CASCADE
        print("1. Fixing recommendation_items table...")
        
        # Create temporary table with CASCADE
        cursor.execute("""
            CREATE TABLE recommendation_items_new (
                item_id TEXT PRIMARY KEY,
                recommendation_id TEXT NOT NULL,
                item_type TEXT NOT NULL,
                item_order INTEGER,
                
                -- Educational content
                content_id TEXT,
                content_title TEXT,
                content_snippet TEXT,
                rationale TEXT,
                
                -- Actionable items
                action_text TEXT,
                action_rationale TEXT,
                data_cited TEXT,
                generated_by TEXT,
                
                -- Partner offers
                offer_id TEXT,
                offer_title TEXT,
                offer_description TEXT,
                eligibility_passed BOOLEAN,
                eligibility_details TEXT,
                why_relevant TEXT,
                
                FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
                    ON DELETE CASCADE
            )
        """)
        
        # Copy data
        cursor.execute("""
            INSERT INTO recommendation_items_new 
            SELECT * FROM recommendation_items
        """)
        
        # Drop old table and rename
        cursor.execute("DROP TABLE recommendation_items")
        cursor.execute("ALTER TABLE recommendation_items_new RENAME TO recommendation_items")
        
        # Recreate indexes
        cursor.execute("""
            CREATE INDEX idx_rec_items_rec_id 
            ON recommendation_items(recommendation_id)
        """)
        
        print("   ✓ Fixed recommendation_items")
        
        # 2. Backup and recreate decision_traces with CASCADE
        print("2. Fixing decision_traces table...")
        
        cursor.execute("""
            CREATE TABLE decision_traces_new (
                trace_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                recommendation_id TEXT,
                trace_type TEXT NOT NULL,
                trace_content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
                    ON DELETE CASCADE
            )
        """)
        
        # Copy data
        cursor.execute("""
            INSERT INTO decision_traces_new
            SELECT * FROM decision_traces
        """)
        
        # Drop old and rename
        cursor.execute("DROP TABLE decision_traces")
        cursor.execute("ALTER TABLE decision_traces_new RENAME TO decision_traces")
        
        # Recreate indexes
        cursor.execute("""
            CREATE INDEX idx_traces_user 
            ON decision_traces(user_id)
        """)
        cursor.execute("""
            CREATE INDEX idx_traces_recommendation 
            ON decision_traces(recommendation_id)
        """)
        
        print("   ✓ Fixed decision_traces")
        
        conn.commit()
        print("\n✓ All foreign key constraints fixed!")
        print("\nYou can now delete recommendations and child records will be deleted automatically.\n")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # Get database path
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / "data" / "spendsense.db"
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)
    
    # Ask for confirmation
    print("=" * 70)
    print("This script will recreate tables to add CASCADE DELETE constraints")
    print("Your data will be preserved, but this is a structural change.")
    print("=" * 70)
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Aborted.")
        sys.exit(0)
    
    fix_cascade_delete(str(db_path))

