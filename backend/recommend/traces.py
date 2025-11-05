"""
Decision Trace Generation

Generate explanatory traces for why recommendations were made
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import logging
import sys
import os

# Add backend to path to import personas module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from personas.metadata import get_persona_name

logger = logging.getLogger(__name__)


def _format_persona_list(persona_ids: List[int]) -> str:
    """
    Convert list of persona IDs to human-readable names
    
    Args:
        persona_ids: List of persona IDs (e.g., [3, 1])
        
    Returns:
        Comma-separated persona names (e.g., "Subscription-Heavy, High Utilization")
    """
    if not persona_ids:
        return "None"
    
    names = []
    for pid in persona_ids:
        name = get_persona_name(pid)
        if name:
            names.append(name)
        else:
            names.append(f"Unknown ({pid})")
    
    return ", ".join(names)


def get_threshold_for_criterion(criterion: str, criteria_values: dict = None) -> str:
    """
    Map criterion name to human-readable threshold description
    
    Args:
        criterion: Criterion key from persona evaluation
        criteria_values: Dictionary of criteria values with thresholds
        
    Returns:
        Human-readable threshold description
    """
    threshold_map = {
        # Persona 1: High Utilization
        'max_utilization': 'Utilization ≥50%',
        'interest_charges': 'Interest charges present',
        'minimum_payment_only': 'Minimum payment only',
        'is_overdue': 'Overdue payment',
        
        # Persona 2: Variable Income
        'median_pay_gap_days': 'Pay gap >45 days',
        'cash_flow_buffer_months': 'Cash flow buffer <1 month',
        
        # Persona 3: Subscription-Heavy
        'recurring_merchant_count': 'Recurring merchants ≥3',
        'monthly_recurring_spend': 'Monthly recurring spend ≥$50',
        'subscription_share': 'Subscription share ≥10%',
        
        # Persona 4: Savings Builder
        'growth_rate': 'Savings growth ≥2%',
        'net_inflow': 'Net savings inflow ≥$200/month',
        'net_inflow_monthly': 'Net savings inflow ≥$200/month',
        'max_utilization_ok': 'All cards <30% utilization',
        
        # Persona 5: Cash Flow Stressed
        'pct_days_below_100': 'Days below $100 ≥30%',
        'balance_volatility': 'Balance volatility >1.0',
    }
    
    return threshold_map.get(criterion, criterion.replace('_', ' ').title())


def generate_persona_trace(
    user_id: str,
    window_days: int,
    persona_assignment: Dict[str, Any],
    db_path: str
) -> Dict[str, Any]:
    """
    Generate trace explaining why a persona was assigned
    
    Args:
        user_id: User identifier
        window_days: Time window (30 or 180)
        persona_assignment: Persona assignment dictionary
        db_path: Path to SQLite database
        
    Returns:
        Trace dictionary
    """
    trace = {
        'trace_type': 'persona_assignment',
        'user_id': user_id,
        'window_days': window_days,
        'primary_persona_id': persona_assignment.get('primary_persona_id'),
        'primary_persona_name': persona_assignment.get('primary_persona_name'),
        'status': persona_assignment.get('status'),
        'rationale': None,
        'criteria_met': {},
        'feature_values_cited': {}
    }
    
    # Parse assignment trace if available
    if 'assignment_trace' in persona_assignment and persona_assignment['assignment_trace']:
        try:
            assignment_trace = json.loads(persona_assignment['assignment_trace'])
            
            # New structure: parse evaluations to extract criteria_met
            evaluations = assignment_trace.get('evaluations', {})
            primary_id = persona_assignment.get('primary_persona_id')
            
            if primary_id and f'persona_{primary_id}' in evaluations:
                persona_eval = evaluations[f'persona_{primary_id}']
                triggered_by = persona_eval.get('triggered_by', [])
                criteria = persona_eval.get('criteria', {})
                
                # Build criteria_met dict from triggered_by
                trace['criteria_met'] = {criterion: True for criterion in triggered_by}
                
                # Extract feature values from criteria
                trace['feature_values_cited'] = criteria
            else:
                # Fallback to old structure if present
                trace['criteria_met'] = assignment_trace.get('criteria_met', {})
                trace['feature_values_cited'] = assignment_trace.get('feature_values', {})
                
        except json.JSONDecodeError:
            logger.warning(f"Could not parse assignment_trace for user {user_id}")
    
    # Generate structured rationale with criteria details
    if trace['status'] == 'STABLE':
        trace['rationale'] = {
            'summary': "User did not meet criteria for any persona. Financial situation appears stable.",
            'criteria_details': []
        }
    elif trace['primary_persona_id']:
        persona_name = trace['primary_persona_name']
        
        # Build criteria details list
        criteria_list = []
        for criterion, met in trace['criteria_met'].items():
            if met:  # Only include met criteria
                threshold = get_threshold_for_criterion(criterion, trace['feature_values_cited'])
                # Get actual value from feature_values_cited
                actual_value = trace['feature_values_cited'].get(criterion)
                
                # Format actual value nicely
                if actual_value is not None:
                    if isinstance(actual_value, float):
                        # Check if it's a percentage (between 0 and 1)
                        if 0 < actual_value < 1 and criterion in ['growth_rate', 'subscription_share', 'max_utilization']:
                            actual_str = f"{actual_value*100:.1f}%"
                        elif criterion in ['monthly_recurring_spend', 'net_inflow_monthly']:
                            actual_str = f"${actual_value:.2f}"
                        else:
                            actual_str = f"{actual_value:.1f}"
                    elif isinstance(actual_value, (int, float)) and criterion == 'recurring_merchant_count':
                        actual_str = f"{int(actual_value)} services"
                    elif isinstance(actual_value, bool):
                        actual_str = "Yes" if actual_value else "No"
                    else:
                        actual_str = str(actual_value)
                else:
                    actual_str = "Met"
                
                criteria_list.append({
                    'criterion': criterion,
                    'threshold': threshold,
                    'actual': actual_str
                })
        
        trace['rationale'] = {
            'summary': f"Met {len(criteria_list)} criteria for {persona_name}",
            'criteria_details': criteria_list
        }
    else:
        trace['rationale'] = {
            'summary': "Persona could not be determined.",
            'criteria_details': []
        }
    
    return trace


def generate_content_selection_trace(
    recommendation: Dict[str, Any],
    educational_items: List[Dict[str, Any]],
    partner_offers: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate trace explaining why specific content was selected
    
    Args:
        recommendation: Recommendation dictionary
        educational_items: List of educational content items
        partner_offers: List of partner offers
        
    Returns:
        Trace dictionary
    """
    trace = {
        'trace_type': 'content_selection',
        'recommendation_id': recommendation.get('recommendation_id'),
        'target_personas': recommendation.get('target_personas'),
        'educational_items': [],
        'partner_offers': []
    }
    
    # Educational item selection reasons
    target_personas = recommendation.get('target_personas', [])
    persona_names = _format_persona_list(target_personas)
    
    for item in educational_items:
        trace['educational_items'].append({
            'content_id': item.get('content_id'),
            'title': item.get('title'),
            'selected_reason': f"Primary relevance to persona(s): {persona_names}",
            'persona_tags': item.get('persona_tags', [])
        })
    
    # Partner offer selection reasons
    for offer in partner_offers:
        eligibility_details = {}
        if offer.get('eligibility_details'):
            try:
                eligibility_details = json.loads(offer['eligibility_details']) if isinstance(offer['eligibility_details'], str) else offer['eligibility_details']
            except json.JSONDecodeError:
                pass
        
        trace['partner_offers'].append({
            'offer_id': offer.get('offer_id'),
            'title': offer.get('offer_title'),
            'selected_reason': "Eligible based on credit score and utilization checks",
            'eligibility_passed': offer.get('eligibility_passed', False),
            'eligibility_details': eligibility_details
        })
    
    return trace


def store_trace(
    trace: Dict[str, Any],
    db_path: str
) -> str:
    """
    Store a decision trace in the database
    
    Args:
        trace: Trace dictionary
        db_path: Path to SQLite database
        
    Returns:
        Trace ID
    """
    trace_id = f"trace_{uuid.uuid4().hex[:12]}"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO decision_traces (
                trace_id,
                user_id,
                recommendation_id,
                trace_type,
                trace_content,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            trace_id,
            trace['user_id'],
            trace.get('recommendation_id'),
            trace['trace_type'],
            json.dumps(trace),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        logger.debug(f"Stored trace {trace_id} for user {trace['user_id']}")
        
        return trace_id
        
    finally:
        conn.close()


def generate_and_store_traces(
    user_id: str,
    recommendation: Dict[str, Any],
    educational_items: List[Dict[str, Any]],
    partner_offers: List[Dict[str, Any]],
    db_path: str
) -> List[str]:
    """
    Generate and store all traces for a recommendation
    
    Should be called during recommendation generation (Epic 4 integration point)
    
    Args:
        user_id: User identifier
        recommendation: Recommendation dictionary
        educational_items: List of educational content items
        partner_offers: List of partner offers
        db_path: Path to SQLite database
        
    Returns:
        List of trace IDs
    """
    trace_ids = []
    
    # Get persona assignments for trace generation
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Generate persona assignment traces (30d and 180d)
        for window_days in [30, 180]:
            cursor.execute("""
                SELECT * FROM persona_assignments
                WHERE user_id = ? AND window_days = ?
                ORDER BY computed_at DESC
                LIMIT 1
            """, (user_id, window_days))
            
            row = cursor.fetchone()
            if row:
                persona_assignment = dict(row)
                persona_trace = generate_persona_trace(user_id, window_days, persona_assignment, db_path)
                trace_id = store_trace(persona_trace, db_path)
                trace_ids.append(trace_id)
        
        # Generate content selection trace
        content_trace = generate_content_selection_trace(recommendation, educational_items, partner_offers)
        content_trace['user_id'] = user_id
        trace_id = store_trace(content_trace, db_path)
        trace_ids.append(trace_id)
        
        logger.info(f"Generated {len(trace_ids)} traces for user {user_id}")
        return trace_ids
        
    finally:
        conn.close()


def get_traces(
    user_id: str,
    db_path: str,
    recommendation_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get all decision traces for a user
    
    Args:
        user_id: User identifier
        db_path: Path to SQLite database
        recommendation_id: Optional filter by recommendation
        
    Returns:
        List of trace dictionaries
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        if recommendation_id:
            cursor.execute("""
                SELECT * FROM decision_traces
                WHERE user_id = ? AND recommendation_id = ?
                ORDER BY created_at DESC
            """, (user_id, recommendation_id))
        else:
            cursor.execute("""
                SELECT * FROM decision_traces
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
        
        rows = cursor.fetchall()
        
        traces = []
        for row in rows:
            trace_dict = dict(row)
            # Parse trace_content JSON
            try:
                trace_dict['trace_content'] = json.loads(trace_dict['trace_content'])
            except json.JSONDecodeError:
                logger.warning(f"Could not parse trace_content for trace {trace_dict['trace_id']}")
            
            traces.append(trace_dict)
        
        logger.debug(f"Retrieved {len(traces)} traces for user {user_id}")
        return traces
        
    finally:
        conn.close()


def get_latest_persona_traces(user_id: str, db_path: str) -> Dict[str, Any]:
    """
    Get the latest persona assignment traces (30d and 180d)
    
    Convenience method for operator dashboard display
    
    Args:
        user_id: User identifier
        db_path: Path to SQLite database
        
    Returns:
        Dictionary with 30d and 180d persona traces
    """
    traces = get_traces(user_id, db_path)
    
    persona_traces_30d = None
    persona_traces_180d = None
    
    for trace in traces:
        if trace['trace_type'] == 'persona_assignment':
            trace_content = trace['trace_content']
            window_days = trace_content.get('window_days')
            
            if window_days == 30 and persona_traces_30d is None:
                persona_traces_30d = trace_content
            elif window_days == 180 and persona_traces_180d is None:
                persona_traces_180d = trace_content
    
    return {
        'window_30d': persona_traces_30d,
        'window_180d': persona_traces_180d
    }

