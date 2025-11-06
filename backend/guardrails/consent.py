"""
Consent Enforcement Utilities

Ensures that user consent is checked before processing data
and that non-consented users are filtered from operator views.
"""

import sqlite3
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ConsentError(Exception):
    """Raised when attempting to access data for non-consented user"""
    pass


def check_consent(user_id: str, db_path: str) -> bool:
    """
    Verify that user has consented to data processing
    
    Args:
        user_id: User identifier
        db_path: Path to SQLite database
        
    Returns:
        True if user has consented
        
    Raises:
        ConsentError: If user has not consented or does not exist
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT consent_status FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        
        if row is None:
            logger.warning(f"User {user_id} not found")
            raise ConsentError(f"User {user_id} does not exist")
        
        consent_status = bool(row['consent_status'])
        
        if not consent_status:
            logger.info(f"Consent check failed for user {user_id}")
            raise ConsentError(f"User {user_id} has not consented to data processing")
        
        logger.debug(f"Consent verified for user {user_id}")
        return True
        
    finally:
        conn.close()


def get_consented_users(db_path: str) -> List[Dict]:
    """
    Get list of all users who have consented to data processing
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        List of user dictionaries with basic information
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                user_id,
                name,
                created_at,
                consent_status,
                consent_updated_at
            FROM users
            WHERE consent_status = 1
            ORDER BY name
        """)
        
        rows = cursor.fetchall()
        users = [dict(row) for row in rows]
        
        logger.info(f"Retrieved {len(users)} consented users")
        return users
        
    finally:
        conn.close()


def get_consent_status(user_id: str, db_path: str) -> Optional[bool]:
    """
    Get consent status for a specific user
    
    Args:
        user_id: User identifier
        db_path: Path to SQLite database
        
    Returns:
        True if consented, False if not consented, None if user not found
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT consent_status FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return bool(row['consent_status'])
        
    finally:
        conn.close()


def update_consent(user_id: str, consent: bool, db_path: str) -> None:
    """
    Update consent status for a user
    
    Note: This will be used in Epic 6 for user-facing consent management.
    For now, it's a utility function for testing/admin purposes.
    
    Args:
        user_id: User identifier
        consent: New consent status (True = consented, False = revoked)
        db_path: Path to SQLite database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE users 
            SET consent_status = ?, 
                consent_updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (1 if consent else 0, user_id))
        
        conn.commit()
        
        status_text = "granted" if consent else "revoked"
        logger.info(f"Consent {status_text} for user {user_id}")
        
    finally:
        conn.close()


def grant_consent(user_id: str, db_path: str) -> bool:
    """
    Grant consent for a user (Epic 6 - Consent Management)
    
    Updates user consent status to true. Recommendation generation
    should be triggered separately by the API endpoint.
    
    Args:
        user_id: User identifier
        db_path: Path to SQLite database
        
    Returns:
        True if consent granted successfully
        
    Raises:
        ValueError: If user does not exist
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone() is None:
            raise ValueError(f"User {user_id} does not exist")
        
        # Update consent status
        cursor.execute("""
            UPDATE users 
            SET consent_status = 1, 
                consent_updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (user_id,))
        
        conn.commit()
        logger.info(f"Consent granted for user {user_id}")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error granting consent for user {user_id}: {e}")
        raise
    finally:
        conn.close()


def revoke_consent(user_id: str, db_path: str) -> bool:
    """
    Revoke consent for a user (Epic 6 - Consent Management)
    
    Updates user consent status to false and soft deletes all
    recommendations by setting their status to 'DELETED'.
    
    Args:
        user_id: User identifier
        db_path: Path to SQLite database
        
    Returns:
        True if consent revoked successfully
        
    Raises:
        ValueError: If user does not exist
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone() is None:
            raise ValueError(f"User {user_id} does not exist")
        
        # Update consent status
        cursor.execute("""
            UPDATE users 
            SET consent_status = 0, 
                consent_updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (user_id,))
        
        # Soft delete all recommendations for this user
        cursor.execute("""
            UPDATE recommendations 
            SET status = 'DELETED',
                reviewed_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            AND status != 'DELETED'
        """, (user_id,))
        
        deleted_count = cursor.rowcount
        
        conn.commit()
        logger.info(f"Consent revoked for user {user_id}, soft deleted {deleted_count} recommendations")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error revoking consent for user {user_id}: {e}")
        raise
    finally:
        conn.close()

