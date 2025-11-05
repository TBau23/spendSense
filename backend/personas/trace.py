"""
Assignment Trace Generation

Creates JSON audit trails for persona assignments showing evaluation details
and reasoning for transparency.
"""

import json
from typing import Dict, List
from datetime import datetime


def generate_assignment_trace(
    user_id: str,
    window_days: int,
    as_of_date: str,
    all_evaluations: Dict,
    primary: Dict,
    secondary: Dict,
    status: str
) -> str:
    """
    Generate JSON trace for persona assignment.
    
    Args:
        user_id: User identifier
        window_days: Time window (30 or 180)
        as_of_date: Date string (YYYY-MM-DD)
        all_evaluations: Dict mapping persona_id -> (matched, severity, details)
        primary: Primary persona dict (or None)
        secondary: Secondary persona dict (or None)
        status: 'ASSIGNED' or 'STABLE'
        
    Returns:
        JSON string with complete audit trail
    """
    trace = {
        'user_id': user_id,
        'window_days': window_days,
        'as_of_date': as_of_date,
        'evaluations': {},
        'result': {}
    }
    
    # Build evaluation results for all 5 personas
    for persona_id in [1, 2, 3, 4, 5]:
        if persona_id in all_evaluations:
            matched, severity, details = all_evaluations[persona_id]
            
            from .metadata import get_persona_info
            persona_info = get_persona_info(persona_id)
            
            trace['evaluations'][f'persona_{persona_id}'] = {
                'name': persona_info['name'],
                'matched': matched,
                'criteria': details.get('criteria', {}),
                'triggered_by': details.get('triggered_by', []),
                'severity': severity if matched else None,
                'priority': persona_info['priority'] if matched else None
            }
    
    # Build result section
    if status == 'STABLE':
        trace['result'] = {
            'primary_persona_id': None,
            'primary_persona_name': None,
            'primary_reasoning': 'No personas matched. User has stable financial behavior.',
            'secondary_persona_id': None,
            'secondary_persona_name': None,
            'secondary_reasoning': None,
            'status': 'STABLE'
        }
    else:
        from .prioritize import format_persona_reasoning
        
        trace['result'] = {
            'primary_persona_id': primary['persona_id'] if primary else None,
            'primary_persona_name': primary['persona_name'] if primary else None,
            'primary_reasoning': format_persona_reasoning(primary) if primary else None,
            'secondary_persona_id': secondary['persona_id'] if secondary else None,
            'secondary_persona_name': secondary['persona_name'] if secondary else None,
            'secondary_reasoning': format_persona_reasoning(secondary) if secondary else None,
            'status': 'ASSIGNED'
        }
    
    return json.dumps(trace, indent=2)


def parse_assignment_trace(trace_json: str) -> Dict:
    """
    Parse JSON trace string back to dict.
    
    Args:
        trace_json: JSON string from database
        
    Returns:
        Dict with trace data
    """
    return json.loads(trace_json)

