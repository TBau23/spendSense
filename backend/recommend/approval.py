"""
Recommendation Approval Management

Handles operator actions: approve, flag, and (future) override recommendations
"""

import sqlite3
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def approve_recommendation(
    rec_id: str,
    db_path: str,
    reviewer_notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Approve a recommendation for delivery to user
    
    Args:
        rec_id: Recommendation identifier
        db_path: Path to SQLite database
        reviewer_notes: Optional notes from operator
        
    Returns:
        Updated recommendation dictionary
        
    Raises:
        ValueError: If recommendation does not exist
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if recommendation exists
        cursor.execute(
            "SELECT recommendation_id, user_id, status FROM recommendations WHERE recommendation_id = ?",
            (rec_id,)
        )
        row = cursor.fetchone()
        
        if row is None:
            raise ValueError(f"Recommendation {rec_id} not found")
        
        old_status = row['status']
        
        # Update status
        cursor.execute("""
            UPDATE recommendations
            SET status = 'APPROVED',
                reviewed_at = CURRENT_TIMESTAMP,
                reviewer_notes = ?
            WHERE recommendation_id = ?
        """, (reviewer_notes, rec_id))
        
        conn.commit()
        
        logger.info(f"Recommendation {rec_id} approved (was {old_status})")
        
        # Return updated recommendation
        cursor.execute(
            "SELECT * FROM recommendations WHERE recommendation_id = ?",
            (rec_id,)
        )
        updated_row = cursor.fetchone()
        
        return dict(updated_row)
        
    finally:
        conn.close()


def flag_recommendation(
    rec_id: str,
    db_path: str,
    reviewer_notes: str
) -> Dict[str, Any]:
    """
    Flag a recommendation as problematic (blocked from delivery)
    
    Args:
        rec_id: Recommendation identifier
        db_path: Path to SQLite database
        reviewer_notes: Required notes explaining why flagged
        
    Returns:
        Updated recommendation dictionary
        
    Raises:
        ValueError: If recommendation does not exist or notes not provided
    """
    if not reviewer_notes or not reviewer_notes.strip():
        raise ValueError("Reviewer notes are required when flagging a recommendation")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if recommendation exists
        cursor.execute(
            "SELECT recommendation_id, user_id, status FROM recommendations WHERE recommendation_id = ?",
            (rec_id,)
        )
        row = cursor.fetchone()
        
        if row is None:
            raise ValueError(f"Recommendation {rec_id} not found")
        
        old_status = row['status']
        
        # Update status
        cursor.execute("""
            UPDATE recommendations
            SET status = 'FLAGGED',
                reviewed_at = CURRENT_TIMESTAMP,
                reviewer_notes = ?
            WHERE recommendation_id = ?
        """, (reviewer_notes, rec_id))
        
        conn.commit()
        
        logger.warning(f"Recommendation {rec_id} flagged (was {old_status}): {reviewer_notes}")
        
        # Return updated recommendation
        cursor.execute(
            "SELECT * FROM recommendations WHERE recommendation_id = ?",
            (rec_id,)
        )
        updated_row = cursor.fetchone()
        
        return dict(updated_row)
        
    finally:
        conn.close()


# def override_recommendation(
#     rec_id: str,
#     db_path: str,
#     overrides: Dict[str, Any],
#     reviewer_notes: Optional[str] = None
# ) -> Dict[str, Any]:
#     """
#     Override recommendation content before approving
#     
#     Placeholder for Epic 6+
#     
#     Args:
#         rec_id: Recommendation identifier
#         db_path: Path to SQLite database
#         overrides: Dictionary of fields to override
#         reviewer_notes: Optional notes explaining override
#         
#     Returns:
#         Updated recommendation dictionary
#     """
#     # TODO: Implement in Epic 6
#     # - Allow operator to edit educational items, actionable items, rationales
#     # - Track that recommendation was overridden (add 'overridden_by' field?)
#     # - Auto-approve after override, or require separate approval?
#     # - Store original version for audit trail?
#     raise NotImplementedError("Override functionality coming in Epic 6")


def get_recommendations_by_status(
    status: str,
    db_path: str,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get all recommendations with a specific status
    
    Args:
        status: Status filter ('PENDING_REVIEW', 'APPROVED', 'FLAGGED')
        db_path: Path to SQLite database
        limit: Optional limit on number of results
        
    Returns:
        List of recommendation dictionaries
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT * FROM recommendations 
            WHERE status = ?
            ORDER BY generated_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (status,))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
        
    finally:
        conn.close()


def get_user_recommendations(
    user_id: str,
    db_path: str,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get all recommendations for a specific user
    
    Args:
        user_id: User identifier
        db_path: Path to SQLite database
        status: Optional status filter
        
    Returns:
        List of recommendation dictionaries
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        if status:
            cursor.execute("""
                SELECT * FROM recommendations
                WHERE user_id = ? AND status = ?
                ORDER BY generated_at DESC
            """, (user_id, status))
        else:
            cursor.execute("""
                SELECT * FROM recommendations
                WHERE user_id = ?
                ORDER BY generated_at DESC
            """, (user_id,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
        
    finally:
        conn.close()


def get_recommendation_with_items(rec_id: str, db_path: str) -> Dict[str, Any]:
    """
    Get full recommendation with all items (educational, actionable, partner offers)
    
    Args:
        rec_id: Recommendation identifier
        db_path: Path to SQLite database
        
    Returns:
        Dictionary with recommendation and nested items
        
    Raises:
        ValueError: If recommendation does not exist
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Get recommendation
        cursor.execute(
            "SELECT * FROM recommendations WHERE recommendation_id = ?",
            (rec_id,)
        )
        rec_row = cursor.fetchone()
        
        if rec_row is None:
            raise ValueError(f"Recommendation {rec_id} not found")
        
        recommendation = dict(rec_row)
        
        # Get all items
        cursor.execute("""
            SELECT * FROM recommendation_items
            WHERE recommendation_id = ?
            ORDER BY item_type, item_order
        """, (rec_id,))
        
        items_rows = cursor.fetchall()
        
        # Organize items by type
        educational_items = []
        actionable_items = []
        partner_offers = []
        
        for item_row in items_rows:
            item = dict(item_row)
            if item['item_type'] == 'educational':
                educational_items.append(item)
            elif item['item_type'] == 'actionable':
                actionable_items.append(item)
            elif item['item_type'] == 'partner_offer':
                partner_offers.append(item)
        
        recommendation['educational_items'] = educational_items
        recommendation['actionable_items'] = actionable_items
        recommendation['partner_offers'] = partner_offers
        
        return recommendation
        
    finally:
        conn.close()

