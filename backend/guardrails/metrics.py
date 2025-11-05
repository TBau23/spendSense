"""
Metrics Computation

Compute aggregate and per-user metrics for operator dashboard
"""

import sqlite3
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Cache for aggregate metrics
_metrics_cache = {}
_cache_timestamp = None
CACHE_TTL_SECONDS = 60


def compute_operator_metrics(db_path: str, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Compute aggregate metrics for operator dashboard main page
    
    Cached for 60 seconds to improve performance.
    
    Args:
        db_path: Path to SQLite database
        force_refresh: If True, bypass cache and recompute
        
    Returns:
        Dictionary with aggregate metrics
    """
    global _metrics_cache, _cache_timestamp
    
    # Check cache
    if not force_refresh and _cache_timestamp is not None:
        age = (datetime.now() - _cache_timestamp).total_seconds()
        if age < CACHE_TTL_SECONDS:
            logger.debug(f"Returning cached metrics (age: {age:.1f}s)")
            return _metrics_cache
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Total consented users
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE consent_status = 1")
        total_consented_users = cursor.fetchone()['count']
        
        # Total recommendations generated
        cursor.execute("SELECT COUNT(*) as count FROM recommendations")
        total_recommendations = cursor.fetchone()['count']
        
        # Recommendation counts by status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM recommendations 
            GROUP BY status
        """)
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        pending_count = status_counts.get('PENDING_REVIEW', 0)
        approved_count = status_counts.get('APPROVED', 0)
        flagged_count = status_counts.get('FLAGGED', 0)
        
        # Users with pending recommendations
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as count 
            FROM recommendations 
            WHERE status = 'PENDING_REVIEW'
        """)
        users_with_pending = cursor.fetchone()['count']
        
        # Approval rate
        reviewed_total = approved_count + flagged_count
        approval_rate = (approved_count / reviewed_total) if reviewed_total > 0 else 0
        
        # Average recommendations per user
        avg_recs_per_user = (total_recommendations / total_consented_users) if total_consented_users > 0 else 0
        
        # Coverage: % of consented users with persona assignment
        cursor.execute("""
            SELECT COUNT(DISTINCT pa.user_id) as count
            FROM persona_assignments pa
            JOIN users u ON pa.user_id = u.user_id
            WHERE u.consent_status = 1 
            AND pa.status = 'ASSIGNED'
            AND pa.window_days = 30
        """)
        users_with_persona = cursor.fetchone()['count']
        coverage_pct = (users_with_persona / total_consented_users) if total_consented_users > 0 else 0
        
        metrics = {
            'total_consented_users': total_consented_users,
            'total_recommendations_generated': total_recommendations,
            'users_with_pending_recs': users_with_pending,
            'pending_count': pending_count,
            'approved_count': approved_count,
            'flagged_count': flagged_count,
            'approval_rate': round(approval_rate, 3),
            'avg_recs_per_user': round(avg_recs_per_user, 2),
            'coverage_pct': round(coverage_pct, 3),
            'computed_at': datetime.now().isoformat()
        }
        
        # Update cache
        _metrics_cache = metrics
        _cache_timestamp = datetime.now()
        
        logger.info(f"Computed operator metrics: {metrics}")
        return metrics
        
    finally:
        conn.close()


def get_user_metrics(user_id: str, db_path: str) -> Dict[str, Any]:
    """
    Compute detailed metrics for a specific user (User Detail Page)
    
    Args:
        user_id: User identifier
        db_path: Path to SQLite database
        
    Returns:
        Dictionary with user-specific metrics
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Get persona assignments (30d and 180d)
        personas = {}
        for window_days in [30, 180]:
            cursor.execute("""
                SELECT 
                    primary_persona_id,
                    primary_persona_name,
                    primary_priority,
                    secondary_persona_id,
                    secondary_persona_name,
                    status,
                    computed_at
                FROM persona_assignments
                WHERE user_id = ? AND window_days = ?
                ORDER BY computed_at DESC
                LIMIT 1
            """, (user_id, window_days))
            
            row = cursor.fetchone()
            if row:
                personas[f'window_{window_days}d'] = {
                    'primary_persona_id': row['primary_persona_id'],
                    'primary_persona_name': row['primary_persona_name'],
                    'primary_priority': row['primary_priority'],
                    'secondary_persona_id': row['secondary_persona_id'],
                    'secondary_persona_name': row['secondary_persona_name'],
                    'status': row['status'],
                    'computed_at': row['computed_at']
                }
            else:
                personas[f'window_{window_days}d'] = None
        
        # Get account counts
        cursor.execute("""
            SELECT 
                account_type,
                COUNT(*) as count
            FROM accounts
            WHERE user_id = ?
            GROUP BY account_type
        """, (user_id,))
        
        account_counts = {row['account_type']: row['count'] for row in cursor.fetchall()}
        
        accounts = {
            'checking_count': account_counts.get('depository', 0),
            'savings_count': sum(account_counts.get(t, 0) for t in ['savings', 'money_market', 'cash_management']),
            'credit_card_count': account_counts.get('credit', 0)
        }
        
        # Get recommendation counts by status
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM recommendations
            WHERE user_id = ?
            GROUP BY status
        """, (user_id,))
        
        rec_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        recommendations = {
            'total_generated': sum(rec_counts.values()),
            'pending': rec_counts.get('PENDING_REVIEW', 0),
            'approved': rec_counts.get('APPROVED', 0),
            'flagged': rec_counts.get('FLAGGED', 0)
        }
        
        # Get latest feature values (from parquet, but we'll use placeholder for now)
        # In a full implementation, this would read from the features parquet files
        features = _get_user_features_placeholder(user_id, db_path)
        
        return {
            'user_id': user_id,
            'personas': personas,
            'accounts': accounts,
            'recommendations': recommendations,
            'features': features,
            'computed_at': datetime.now().isoformat()
        }
        
    finally:
        conn.close()


def _get_user_features_placeholder(user_id: str, db_path: str) -> Dict[str, Any]:
    """
    Placeholder for feature loading
    
    In full implementation, this would load from parquet files.
    For now, returns basic computed values.
    
    Args:
        user_id: User identifier
        db_path: Path to SQLite database
        
    Returns:
        Dictionary with key feature metrics
    """
    try:
        # Try to load from parquet files
        from pathlib import Path
        project_root = Path(db_path).parent.parent
        features_dir = project_root / "data" / "features"
        
        features = {}
        
        # Load credit features
        credit_path = features_dir / "credit.parquet"
        if credit_path.exists():
            df_credit = pd.read_parquet(credit_path)
            user_credit = df_credit[df_credit['user_id'] == user_id]
            if not user_credit.empty:
                latest = user_credit.iloc[0]
                features['credit_utilization'] = round(latest.get('max_utilization', 0), 3)
                features['total_credit_balance'] = round(latest.get('total_balance', 0), 2)
        
        # Load savings features
        savings_path = features_dir / "savings.parquet"
        if savings_path.exists():
            df_savings = pd.read_parquet(savings_path)
            user_savings = df_savings[df_savings['user_id'] == user_id]
            if not user_savings.empty:
                latest = user_savings.iloc[0]
                features['savings_growth_rate'] = round(latest.get('growth_rate', 0), 3)
                features['emergency_fund_months'] = round(latest.get('emergency_fund_months', 0), 2)
        
        # Load cash flow features
        cash_flow_path = features_dir / "cash_flow.parquet"
        if cash_flow_path.exists():
            df_cash = pd.read_parquet(cash_flow_path)
            user_cash = df_cash[df_cash['user_id'] == user_id]
            if not user_cash.empty:
                latest = user_cash.iloc[0]
                features['pct_days_below_100'] = round(latest.get('pct_days_below_100', 0), 3)
                features['balance_volatility'] = round(latest.get('balance_volatility', 0), 2)
        
        return features if features else {'note': 'Features not yet computed'}
        
    except Exception as e:
        logger.warning(f"Could not load features for user {user_id}: {e}")
        return {'note': 'Features not available'}


def get_user_list_with_status(
    db_path: str,
    persona_filter: Optional[int] = None,
    status_filter: Optional[str] = None,
    sort_by: str = 'name'
) -> list:
    """
    Get list of consented users with recommendation status info
    
    Used by operator dashboard main page for user list.
    
    Args:
        db_path: Path to SQLite database
        persona_filter: Filter by primary persona ID (30d window)
        status_filter: Filter by recommendation status
        sort_by: Sort order ('name', 'date', 'persona')
        
    Returns:
        List of user dictionaries with status information
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        # Build query
        query = """
            SELECT 
                u.user_id,
                u.name,
                pa.primary_persona_id,
                pa.primary_persona_name,
                COUNT(DISTINCT r.recommendation_id) as rec_count,
                SUM(CASE WHEN r.status = 'PENDING_REVIEW' THEN 1 ELSE 0 END) as pending_count,
                MAX(r.generated_at) as last_rec_date
            FROM users u
            LEFT JOIN persona_assignments pa 
                ON u.user_id = pa.user_id AND pa.window_days = 30
            LEFT JOIN recommendations r 
                ON u.user_id = r.user_id
            WHERE u.consent_status = 1
        """
        
        params = []
        
        # Add filters
        if persona_filter is not None:
            query += " AND pa.primary_persona_id = ?"
            params.append(persona_filter)
        
        if status_filter:
            query += " AND r.status = ?"
            params.append(status_filter)
        
        # Group by user
        query += " GROUP BY u.user_id, u.name, pa.primary_persona_id, pa.primary_persona_name"
        
        # Sort
        if sort_by == 'name':
            query += " ORDER BY u.name"
        elif sort_by == 'date':
            query += " ORDER BY last_rec_date DESC NULLS LAST"
        elif sort_by == 'persona':
            query += " ORDER BY pa.primary_persona_id"
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row['user_id'],
                'name': row['name'],
                'primary_persona_id': row['primary_persona_id'],
                'primary_persona_name': row['primary_persona_name'],
                'rec_count': row['rec_count'] or 0,
                'has_pending_recs': (row['pending_count'] or 0) > 0,
                'pending_count': row['pending_count'] or 0,
                'last_rec_date': row['last_rec_date']
            })
        
        logger.info(f"Retrieved {len(users)} users with filters: persona={persona_filter}, status={status_filter}")
        return users
        
    finally:
        conn.close()

