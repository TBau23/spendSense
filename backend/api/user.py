"""
End User API Endpoints (Epic 6)

Endpoints for end user portal: user selection, recommendations view, insights
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sqlite3
import json
import logging

from backend.storage.database import get_db_path
from backend.recommend.approval import get_user_recommendations

router = APIRouter()
logger = logging.getLogger(__name__)

# Get database path
DB_PATH = get_db_path()


# ========== Helper Functions ==========

def get_all_users_list(db_path: str) -> List[Dict[str, Any]]:
    """
    Get list of all users (for dropdown selection)
    
    Returns:
        List of users with basic info: user_id, name, consent, has_approved_recs
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                u.user_id,
                u.name,
                u.consent_status,
                COUNT(DISTINCT CASE WHEN r.status = 'APPROVED' THEN r.recommendation_id END) as approved_count
            FROM users u
            LEFT JOIN recommendations r ON u.user_id = r.user_id
            GROUP BY u.user_id, u.name, u.consent_status
            ORDER BY u.name
        """)
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row['user_id'],
                'name': row['name'],
                'consent': bool(row['consent_status']),
                'has_approved_recs': (row['approved_count'] or 0) > 0
            })
        
        return users
        
    finally:
        conn.close()


def get_user_basic_info(user_id: str, db_path: str) -> Optional[Dict[str, Any]]:
    """
    Get basic user information (public endpoint)
    
    Returns:
        User info: user_id, name, consent status
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT user_id, name, consent_status
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'user_id': row['user_id'],
                'name': row['name'],
                'consent': bool(row['consent_status'])
            }
        return None
        
    finally:
        conn.close()


# ========== User Endpoints ==========

@router.get("/users")
async def list_users():
    """
    Get list of all users for dropdown selection
    
    Returns list of users with:
    - user_id
    - name
    - consent (boolean)
    - has_approved_recs (boolean)
    """
    try:
        users = get_all_users_list(DB_PATH)
        
        return {
            "users": users,
            "count": len(users)
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {str(e)}")


@router.get("/users/{user_id}")
async def get_user(user_id: str):
    """
    Get basic user information (public endpoint)
    
    Returns:
    - user_id
    - name  
    - consent (boolean)
    
    Returns 404 if user not found
    """
    try:
        user = get_user_basic_info(user_id, DB_PATH)
        
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user: {str(e)}")


@router.get("/users/{user_id}/insights")
async def get_user_insights(user_id: str, days: int = Query(30, description="Time window in days")):
    """
    Get transaction insights for a user (end user view)
    
    Aggregates transaction data to show:
    - Top merchants by spend
    - Top categories by spend
    - Total spend in window
    
    Query Parameters:
    - days: Time window in days (default: 30)
    
    Returns insights if user has consented, empty data if not.
    """
    try:
        # Get user info to verify they exist and check consent
        user = get_user_basic_info(user_id, DB_PATH)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # If user hasn't consented, return empty insights
        if not user['consent']:
            return {
                "user_id": user_id,
                "window_days": days,
                "top_merchants": [],
                "top_categories": [],
                "total_spend": 0,
                "transaction_count": 0,
                "message": "User has not granted consent"
            }
        
        # Query transactions for this user
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Calculate date threshold
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Top merchants by spend
            cursor.execute("""
                SELECT 
                    merchant_name,
                    COUNT(*) as transaction_count,
                    SUM(amount) as total_spend
                FROM transactions
                WHERE user_id = ? 
                AND date >= ?
                AND amount > 0
                GROUP BY merchant_name
                ORDER BY total_spend DESC
                LIMIT 5
            """, (user_id, cutoff_date))
            
            top_merchants = []
            for row in cursor.fetchall():
                top_merchants.append({
                    'merchant_name': row['merchant_name'],
                    'total_spend': float(row['total_spend']),
                    'transaction_count': row['transaction_count']
                })
            
            # Top categories by spend
            cursor.execute("""
                SELECT 
                    category_primary,
                    COUNT(*) as transaction_count,
                    SUM(amount) as total_spend
                FROM transactions
                WHERE user_id = ? 
                AND date >= ?
                AND amount > 0
                GROUP BY category_primary
                ORDER BY total_spend DESC
                LIMIT 5
            """, (user_id, cutoff_date))
            
            top_categories = []
            for row in cursor.fetchall():
                category = row['category_primary'] or 'Other'
                top_categories.append({
                    'category': category,
                    'total_spend': float(row['total_spend']),
                    'transaction_count': row['transaction_count']
                })
            
            # Total spend
            cursor.execute("""
                SELECT 
                    COUNT(*) as transaction_count,
                    SUM(amount) as total_spend
                FROM transactions
                WHERE user_id = ? 
                AND date >= ?
                AND amount > 0
            """, (user_id, cutoff_date))
            
            totals_row = cursor.fetchone()
            total_spend = float(totals_row['total_spend'] or 0)
            transaction_count = totals_row['transaction_count'] or 0
            
            return {
                "user_id": user_id,
                "window_days": days,
                "top_merchants": top_merchants,
                "top_categories": top_categories,
                "total_spend": total_spend,
                "transaction_count": transaction_count
            }
            
        finally:
            conn.close()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve insights for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve insights: {str(e)}")


@router.get("/users/{user_id}/recommendations")
async def get_user_approved_recommendations(user_id: str):
    """
    Get APPROVED recommendations for a user (end user view)
    
    Only returns recommendations with status = APPROVED.
    Returns empty array if user has no approved recommendations.
    
    Does NOT require consent check for this endpoint - consent is enforced
    by only showing approved recommendations.
    """
    try:
        # Get user info to verify they exist
        user = get_user_basic_info(user_id, DB_PATH)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # If user hasn't consented, return empty array
        if not user['consent']:
            return {
                "user_id": user_id,
                "recommendations": [],
                "count": 0,
                "message": "User has not granted consent"
            }
        
        # Get APPROVED recommendations only
        from backend.recommend.approval import get_recommendation_with_items
        
        recommendations = get_user_recommendations(user_id, DB_PATH, status='APPROVED')
        
        # Fetch full details with items for each recommendation
        full_recommendations = []
        for rec in recommendations:
            try:
                full_rec = get_recommendation_with_items(rec['recommendation_id'], DB_PATH)
                full_recommendations.append(full_rec)
            except Exception as e:
                logger.warning(f"Could not fetch items for {rec['recommendation_id']}: {e}")
                full_recommendations.append(rec)
        
        return {
            "user_id": user_id,
            "recommendations": full_recommendations,
            "count": len(full_recommendations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recommendations: {str(e)}")


# ========== Health Check ==========

@router.get("/health")
async def user_api_health():
    """User API health check"""
    try:
        # Quick database connectivity check
        users = get_all_users_list(DB_PATH)
        
        return {
            "status": "healthy",
            "database": "connected",
            "total_users": len(users)
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

