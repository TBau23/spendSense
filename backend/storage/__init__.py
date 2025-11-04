"""
Storage module for SpendSense
Handles database connections and schema definitions
"""

from .database import get_db_connection, initialize_database, get_db_path
from .schemas import create_tables

__all__ = [
    'get_db_connection',
    'initialize_database',
    'get_db_path',
    'create_tables'
]

