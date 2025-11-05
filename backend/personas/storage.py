"""
Persona Assignment Storage

Handles SQLite and Parquet storage for persona assignments.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


def create_persona_assignments_table(db_path: str):
    """
    Create persona_assignments table in SQLite database.
    
    Args:
        db_path: Path to SQLite database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS persona_assignments (
            assignment_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            window_days INTEGER NOT NULL,
            as_of_date DATE NOT NULL,
            
            -- Primary persona
            primary_persona_id INTEGER,
            primary_persona_name TEXT,
            primary_priority TEXT,
            primary_severity REAL,
            
            -- Secondary persona
            secondary_persona_id INTEGER,
            secondary_persona_name TEXT,
            secondary_priority TEXT,
            secondary_severity REAL,
            
            -- Status
            status TEXT NOT NULL,
            
            -- Audit trail (JSON)
            assignment_trace TEXT,
            
            -- Metadata
            computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, window_days, as_of_date)
        )
    ''')
    
    # Create indexes
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_persona_user_window 
        ON persona_assignments(user_id, window_days)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_persona_primary 
        ON persona_assignments(primary_persona_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_persona_status 
        ON persona_assignments(status)
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"✓ Created persona_assignments table in {db_path}")


def insert_persona_assignment(
    db_path: str,
    user_id: str,
    window_days: int,
    as_of_date: str,
    primary: Optional[Dict],
    secondary: Optional[Dict],
    status: str,
    assignment_trace: str
):
    """
    Insert a persona assignment into SQLite.
    
    Args:
        db_path: Path to SQLite database
        user_id: User identifier
        window_days: Time window (30 or 180)
        as_of_date: Date string (YYYY-MM-DD)
        primary: Primary persona dict (or None)
        secondary: Secondary persona dict (or None)
        status: 'ASSIGNED' or 'STABLE'
        assignment_trace: JSON string with audit trail
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Generate assignment ID
    assignment_id = f"assign_{user_id}_{window_days}d_{as_of_date}"
    
    cursor.execute('''
        INSERT OR REPLACE INTO persona_assignments (
            assignment_id, user_id, window_days, as_of_date,
            primary_persona_id, primary_persona_name, primary_priority, primary_severity,
            secondary_persona_id, secondary_persona_name, secondary_priority, secondary_severity,
            status, assignment_trace, computed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        assignment_id,
        user_id,
        window_days,
        as_of_date,
        primary['persona_id'] if primary else None,
        primary['persona_name'] if primary else None,
        primary['priority'] if primary else None,
        primary['severity'] if primary else None,
        secondary['persona_id'] if secondary else None,
        secondary['persona_name'] if secondary else None,
        secondary['priority'] if secondary else None,
        secondary['severity'] if secondary else None,
        status,
        assignment_trace,
        datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()


def batch_insert_persona_assignments(db_path: str, assignments: List[Dict]):
    """
    Batch insert multiple persona assignments.
    
    Args:
        db_path: Path to SQLite database
        assignments: List of assignment dicts with keys:
            - user_id
            - window_days
            - as_of_date
            - primary (dict or None)
            - secondary (dict or None)
            - status
            - assignment_trace
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    rows = []
    for assign in assignments:
        assignment_id = f"assign_{assign['user_id']}_{assign['window_days']}d_{assign['as_of_date']}"
        primary = assign.get('primary')
        secondary = assign.get('secondary')
        
        rows.append((
            assignment_id,
            assign['user_id'],
            assign['window_days'],
            assign['as_of_date'],
            primary['persona_id'] if primary else None,
            primary['persona_name'] if primary else None,
            primary['priority'] if primary else None,
            primary['severity'] if primary else None,
            secondary['persona_id'] if secondary else None,
            secondary['persona_name'] if secondary else None,
            secondary['priority'] if secondary else None,
            secondary['severity'] if secondary else None,
            assign['status'],
            assign['assignment_trace'],
            datetime.now().isoformat()
        ))
    
    cursor.executemany('''
        INSERT OR REPLACE INTO persona_assignments (
            assignment_id, user_id, window_days, as_of_date,
            primary_persona_id, primary_persona_name, primary_priority, primary_severity,
            secondary_persona_id, secondary_persona_name, secondary_priority, secondary_severity,
            status, assignment_trace, computed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', rows)
    
    conn.commit()
    conn.close()
    
    print(f"✓ Inserted {len(assignments)} persona assignments into SQLite")


def export_to_parquet(db_path: str, output_path: str):
    """
    Export persona assignments from SQLite to Parquet.
    
    Note: Excludes assignment_trace column for cleaner analytics.
    
    Args:
        db_path: Path to SQLite database
        output_path: Path to output Parquet file
    """
    conn = sqlite3.connect(db_path)
    
    # Read assignments (exclude trace for analytics)
    query = '''
        SELECT 
            user_id,
            window_days,
            as_of_date,
            primary_persona_id,
            primary_persona_name,
            primary_priority,
            primary_severity,
            secondary_persona_id,
            secondary_persona_name,
            secondary_priority,
            secondary_severity,
            status,
            computed_at
        FROM persona_assignments
        ORDER BY user_id, window_days
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write to Parquet
    df.to_parquet(output_path, index=False)
    
    print(f"✓ Exported {len(df)} persona assignments to {output_path}")


def get_persona_assignment(db_path: str, user_id: str, window_days: int, as_of_date: str) -> Optional[Dict]:
    """
    Retrieve persona assignment for a specific user/window.
    
    Args:
        db_path: Path to SQLite database
        user_id: User identifier
        window_days: Time window (30 or 180)
        as_of_date: Date string (YYYY-MM-DD)
        
    Returns:
        Dict with assignment data, or None if not found
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM persona_assignments
        WHERE user_id = ? AND window_days = ? AND as_of_date = ?
    ''', (user_id, window_days, as_of_date))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_assignments_by_persona(db_path: str, persona_id: int, window_days: int) -> List[Dict]:
    """
    Get all users assigned to a specific persona.
    
    Args:
        db_path: Path to SQLite database
        persona_id: Persona ID (1-5)
        window_days: Time window filter
        
    Returns:
        List of assignment dicts
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM persona_assignments
        WHERE primary_persona_id = ? AND window_days = ?
        ORDER BY primary_severity DESC
    ''', (persona_id, window_days))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_assignment_summary(db_path: str) -> Dict:
    """
    Get summary statistics for persona assignments.
    
    Returns:
        Dict with counts by persona, status, etc.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total assignments
    cursor.execute('SELECT COUNT(*) FROM persona_assignments')
    total = cursor.fetchone()[0]
    
    # By status
    cursor.execute('''
        SELECT status, COUNT(*) as count
        FROM persona_assignments
        GROUP BY status
    ''')
    status_counts = {row[0]: row[1] for row in cursor.fetchall()}
    
    # By primary persona
    cursor.execute('''
        SELECT primary_persona_name, COUNT(*) as count
        FROM persona_assignments
        WHERE status = 'ASSIGNED'
        GROUP BY primary_persona_name
    ''')
    persona_counts = {row[0]: row[1] for row in cursor.fetchall()}
    
    # By window
    cursor.execute('''
        SELECT window_days, COUNT(*) as count
        FROM persona_assignments
        GROUP BY window_days
    ''')
    window_counts = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        'total_assignments': total,
        'by_status': status_counts,
        'by_persona': persona_counts,
        'by_window': window_counts
    }

