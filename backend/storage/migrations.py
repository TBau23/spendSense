"""
Database migration utilities for SpendSense

Handles schema updates without losing existing data
"""

import sqlite3
from typing import Optional


def migrate_add_recommendation_status(conn: sqlite3.Connection) -> None:
    """
    Add status, reviewed_at, and reviewer_notes columns to recommendations table
    
    Migration for Epic 5: Guardrails & Operator View
    
    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(recommendations)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add status column (default PENDING_REVIEW for existing records)
        if 'status' not in columns:
            cursor.execute("""
                ALTER TABLE recommendations 
                ADD COLUMN status TEXT DEFAULT 'PENDING_REVIEW'
            """)
            print("✓ Added 'status' column to recommendations table")
        else:
            print("- 'status' column already exists")
        
        # Add reviewed_at column
        if 'reviewed_at' not in columns:
            cursor.execute("""
                ALTER TABLE recommendations 
                ADD COLUMN reviewed_at TIMESTAMP NULL
            """)
            print("✓ Added 'reviewed_at' column to recommendations table")
        else:
            print("- 'reviewed_at' column already exists")
        
        # Add reviewer_notes column
        if 'reviewer_notes' not in columns:
            cursor.execute("""
                ALTER TABLE recommendations 
                ADD COLUMN reviewer_notes TEXT NULL
            """)
            print("✓ Added 'reviewer_notes' column to recommendations table")
        else:
            print("- 'reviewer_notes' column already exists")
        
        conn.commit()
        print("\n✓ Migration complete: Recommendation status fields added")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise


def create_decision_traces_table(conn: sqlite3.Connection) -> None:
    """
    Create decision_traces table for storing recommendation rationales
    
    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decision_traces (
            trace_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            recommendation_id TEXT,
            trace_type TEXT NOT NULL,
            trace_content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
        )
    """)
    
    # Create indexes for efficient queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_traces_user 
        ON decision_traces(user_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_traces_recommendation 
        ON decision_traces(recommendation_id)
    """)
    
    conn.commit()
    print("✓ Created decision_traces table with indexes")


def run_all_migrations(db_path: Optional[str] = None) -> None:
    """
    Run all pending migrations
    
    Args:
        db_path: Optional path to database file
    """
    from .database import get_db_connection
    
    if db_path is None:
        from .database import get_db_path
        db_path = get_db_path()
    
    print(f"Running migrations on database: {db_path}\n")
    
    conn = get_db_connection(db_path)
    
    try:
        # Epic 5 migrations
        migrate_add_recommendation_status(conn)
        create_decision_traces_table(conn)
        
        print("\n✓ All migrations completed successfully")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_all_migrations()

