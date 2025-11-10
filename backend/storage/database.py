"""
Database connection and initialization utilities for SpendSense
Handles SQLite database setup and connection management
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


def get_db_path(db_name: str = "spendsense.db") -> str:
    """
    Get the database file path
    
    Args:
        db_name: Name of the database file
        
    Returns:
        Full path to the database file
    """
    # Get project root (3 levels up from this file)
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)
    
    return str(data_dir / db_name)


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Get a database connection
    
    Args:
        db_path: Optional path to database file. If None, uses default.
        
    Returns:
        SQLite connection object
    """
    if db_path is None:
        db_path = get_db_path()
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")
    
    return conn


@contextmanager
def db_session(db_path: Optional[str] = None):
    """
    Context manager for database sessions
    
    Usage:
        with db_session() as conn:
            # do database operations
            pass
    
    Args:
        db_path: Optional path to database file
        
    Yields:
        SQLite connection object
    """
    conn = get_db_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database(db_path: Optional[str] = None, reset: bool = False) -> str:
    """
    Initialize the database with all tables
    
    Args:
        db_path: Optional path to database file. If None, uses default.
        reset: If True, drops existing tables before creating
        
    Returns:
        Path to the initialized database
    """
    from .schemas import create_tables, drop_all_tables
    
    if db_path is None:
        db_path = get_db_path()
    
    conn = get_db_connection(db_path)
    
    try:
        if reset:
            drop_all_tables(conn)
        
        # Create core tables (users, accounts, transactions, liabilities)
        create_tables(conn)
        
        # Create Epic 3 tables (persona assignments)
        try:
            from ..personas.storage import create_persona_assignments_table
        except ImportError:
            from personas.storage import create_persona_assignments_table
        create_persona_assignments_table(db_path)
        
        # Create Epic 4 tables (recommendations, content, offers)
        try:
            from ..recommend.storage import create_recommendation_tables
        except ImportError:
            from recommend.storage import create_recommendation_tables
        create_recommendation_tables(db_path)
        
        # Create Epic 5 tables (decision traces)
        try:
            from .migrations import create_decision_traces_table
        except ImportError:
            from storage.migrations import create_decision_traces_table
        create_decision_traces_table(conn)
        
        conn.commit()
        print(f"Database initialized at: {db_path}")
        
    finally:
        conn.close()
    
    return db_path


def database_exists(db_path: Optional[str] = None) -> bool:
    """
    Check if database file exists
    
    Args:
        db_path: Optional path to database file
        
    Returns:
        True if database file exists
    """
    if db_path is None:
        db_path = get_db_path()
    
    return os.path.exists(db_path)

