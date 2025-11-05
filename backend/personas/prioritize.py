"""
Persona Prioritization

Handles sorting and tie-breaking logic for persona assignment.
"""

from typing import List, Dict
from .metadata import PRIORITY_ORDER


def sort_matched_personas(matched_personas: List[Dict]) -> List[Dict]:
    """
    Sort matched personas by priority level, then severity, then persona_id.
    
    Priority order: CRITICAL > HIGH > MEDIUM > LOW
    Within same priority: Higher severity wins
    If severity equal: Lower persona_id wins (stable tie-breaker)
    
    Args:
        matched_personas: List of persona dicts with keys:
            - persona_id: int
            - priority: str (CRITICAL, HIGH, MEDIUM, LOW)
            - severity: float
            
    Returns:
        Sorted list (highest priority first)
    """
    return sorted(
        matched_personas,
        key=lambda p: (
            PRIORITY_ORDER[p['priority']],  # Lower number = higher priority
            -p['severity'],                  # Higher severity first (negative for descending)
            p['persona_id']                  # Stable tie-breaker (lower ID wins)
        )
    )


def select_primary_and_secondary(sorted_personas: List[Dict]) -> tuple:
    """
    Select primary and secondary personas from sorted list.
    
    Args:
        sorted_personas: List sorted by priority/severity
        
    Returns:
        (primary_dict, secondary_dict)
        Either can be None if no matches or only one match
    """
    primary = sorted_personas[0] if len(sorted_personas) > 0 else None
    secondary = sorted_personas[1] if len(sorted_personas) > 1 else None
    
    return primary, secondary


def format_persona_reasoning(persona_dict: Dict) -> str:
    """
    Generate human-readable reasoning string for a persona match.
    
    Args:
        persona_dict: Dict with persona_name, severity, priority, and details
        
    Returns:
        String explaining why this persona was assigned
    """
    name = persona_dict['persona_name']
    severity = persona_dict['severity']
    priority = persona_dict['priority']
    details = persona_dict.get('details', {})
    triggered_by = details.get('triggered_by', [])
    criteria = details.get('criteria', {})
    
    # Build trigger explanation
    trigger_parts = []
    for trigger in triggered_by:
        if trigger in criteria:
            value = criteria[trigger]
            threshold_key = f"threshold_{trigger.split('_')[-1]}"
            if threshold_key in criteria:
                threshold = criteria[threshold_key]
                trigger_parts.append(f"{trigger} ({value} vs {threshold} threshold)")
            else:
                trigger_parts.append(f"{trigger} ({value})")
    
    trigger_text = ", ".join(trigger_parts) if trigger_parts else "criteria met"
    
    return f"Matched on {trigger_text}. Severity: {severity:.3f}. Priority: {priority}."

