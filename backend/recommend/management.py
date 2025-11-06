"""
Recommendation Management

Handles generation and deletion of recommendations for Epic 6.
Provides functions for on-demand recommendation generation and soft deletion.
"""

import sqlite3
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_recommendation_for_user(
    user_id: str,
    db_path: str,
    config_path: str = 'config.json'
) -> Dict[str, Any]:
    """
    Generate a new recommendation for a user on-demand.
    
    This function wraps the existing generate_recommendation() from generator.py
    and ensures the recommendation is stored with PENDING_REVIEW status.
    
    Args:
        user_id: User identifier
        db_path: Path to SQLite database
        config_path: Path to configuration file
        
    Returns:
        Dictionary containing the generated recommendation
        
    Raises:
        ValueError: If user does not exist or has not consented
        RuntimeError: If recommendation generation fails
    """
    import json
    from .generator import generate_recommendation
    from ..guardrails.consent import check_consent, ConsentError
    
    try:
        # Verify user has consented
        check_consent(user_id, db_path)
        
        # Load config from file
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Generate recommendation using existing pipeline
        logger.info(f"Generating new recommendation for user {user_id}")
        recommendation = generate_recommendation(
            user_id=user_id,
            config=config
        )
        
        logger.info(f"Successfully generated recommendation {recommendation.get('recommendation_id')} for user {user_id}")
        return recommendation
        
    except ConsentError as e:
        logger.error(f"Consent check failed for user {user_id}: {e}")
        raise ValueError(f"User {user_id} has not consented to data processing")
    except Exception as e:
        logger.error(f"Error generating recommendation for user {user_id}: {e}")
        raise RuntimeError(f"Failed to generate recommendation: {e}")


def soft_delete_recommendation(rec_id: str, db_path: str) -> bool:
    """
    Soft delete a recommendation by setting its status to 'DELETED'.
    
    This preserves the recommendation in the database for audit purposes
    but filters it out from all user-facing and operator queries.
    
    Args:
        rec_id: Recommendation identifier
        db_path: Path to SQLite database
        
    Returns:
        True if successfully deleted
        
    Raises:
        ValueError: If recommendation does not exist
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if recommendation exists
        cursor.execute(
            "SELECT recommendation_id FROM recommendations WHERE recommendation_id = ?",
            (rec_id,)
        )
        if cursor.fetchone() is None:
            raise ValueError(f"Recommendation {rec_id} does not exist")
        
        # Soft delete by updating status
        cursor.execute("""
            UPDATE recommendations 
            SET status = 'DELETED',
                reviewed_at = CURRENT_TIMESTAMP
            WHERE recommendation_id = ?
        """, (rec_id,))
        
        conn.commit()
        logger.info(f"Soft deleted recommendation {rec_id}")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error soft deleting recommendation {rec_id}: {e}")
        raise
    finally:
        conn.close()


def get_recommendation_by_id(rec_id: str, db_path: str) -> Optional[Dict[str, Any]]:
    """
    Get a single recommendation by ID (for operator view).
    
    Args:
        rec_id: Recommendation identifier
        db_path: Path to SQLite database
        
    Returns:
        Recommendation dictionary or None if not found
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM recommendations
            WHERE recommendation_id = ?
        """, (rec_id,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
        
    finally:
        conn.close()


def get_user_recommendations(
    user_id: str,
    db_path: str,
    status_filter: Optional[str] = None,
    exclude_deleted: bool = True
) -> list:
    """
    Get all recommendations for a user.
    
    Args:
        user_id: User identifier
        db_path: Path to SQLite database
        status_filter: Optional status to filter by (e.g., 'APPROVED', 'PENDING_REVIEW')
        exclude_deleted: If True, filter out DELETED recommendations
        
    Returns:
        List of recommendation dictionaries
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        query = "SELECT * FROM recommendations WHERE user_id = ?"
        params = [user_id]
        
        if exclude_deleted:
            query += " AND status != 'DELETED'"
        
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
        
        query += " ORDER BY generated_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
        
    finally:
        conn.close()

