"""
Cross-Window Persona Handler

Determines target personas when user has different personas across 30d and 180d windows.
"""

from typing import List, Dict, Any, Optional, Tuple
import sqlite3


def load_persona_assignments(
    user_id: str,
    db_path: str
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Load persona assignments for both 30d and 180d windows.
    
    Args:
        user_id: User identifier
        db_path: Path to SQLite database
    
    Returns:
        Tuple of (assignments_30d, assignments_180d)
        Each is a dict or None if not found
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Load 30d assignment
    cursor.execute('''
        SELECT * FROM persona_assignments
        WHERE user_id = ? AND window_days = 30
        ORDER BY computed_at DESC
        LIMIT 1
    ''', (user_id,))
    row_30d = cursor.fetchone()
    assignments_30d = dict(row_30d) if row_30d else None
    
    # Load 180d assignment
    cursor.execute('''
        SELECT * FROM persona_assignments
        WHERE user_id = ? AND window_days = 180
        ORDER BY computed_at DESC
        LIMIT 1
    ''', (user_id,))
    row_180d = cursor.fetchone()
    assignments_180d = dict(row_180d) if row_180d else None
    
    conn.close()
    
    return assignments_30d, assignments_180d


def determine_target_personas(
    assignments_30d: Optional[Dict[str, Any]],
    assignments_180d: Optional[Dict[str, Any]]
) -> List[int]:
    """
    Determine which persona(s) to target for recommendations.
    
    Strategy:
    - If same persona both windows: target single persona
    - If different personas: target both, prioritize 30d (recent behavior)
    - If one STABLE and one ASSIGNED: use the assigned persona
    - If both STABLE: return [0] for stable content
    - If missing data: return empty list
    
    Args:
        assignments_30d: 30-day persona assignment dict
        assignments_180d: 180-day persona assignment dict
    
    Returns:
        List of persona IDs ordered by priority [primary, secondary]
    """
    # Handle missing data
    if not assignments_30d or not assignments_180d:
        if assignments_30d:
            return _extract_personas(assignments_30d)
        elif assignments_180d:
            return _extract_personas(assignments_180d)
        else:
            return []  # No persona data
    
    # Check status
    status_30d = assignments_30d.get('status')
    status_180d = assignments_180d.get('status')
    
    # Both stable
    if status_30d == 'STABLE' and status_180d == 'STABLE':
        return [0]  # Stable user
    
    # One stable, one assigned
    if status_30d == 'STABLE' and status_180d == 'ASSIGNED':
        return _extract_personas(assignments_180d)
    if status_30d == 'ASSIGNED' and status_180d == 'STABLE':
        return _extract_personas(assignments_30d)
    
    # Both assigned - check if same persona
    persona_30d = assignments_30d.get('primary_persona_id')
    persona_180d = assignments_180d.get('primary_persona_id')
    
    if persona_30d == persona_180d:
        # Same persona both windows - target single persona
        return [persona_30d] if persona_30d is not None else []
    else:
        # Different personas - include both, prioritize 30d (recent behavior)
        personas = []
        if persona_30d is not None:
            personas.append(persona_30d)
        if persona_180d is not None and persona_180d not in personas:
            personas.append(persona_180d)
        return personas


def _extract_personas(assignment: Dict[str, Any]) -> List[int]:
    """Extract persona IDs from assignment (primary only for now)."""
    if assignment.get('status') == 'STABLE':
        return [0]
    
    persona_id = assignment.get('primary_persona_id')
    if persona_id is not None:
        return [persona_id]
    return []


def get_persona_context(
    user_id: str,
    db_path: str
) -> Dict[str, Any]:
    """
    Get full persona context for recommendation generation.
    
    Args:
        user_id: User identifier
        db_path: Path to SQLite database
    
    Returns:
        Context dictionary with:
            - target_personas: List[int]
            - assignments_30d: dict
            - assignments_180d: dict
            - strategy: str (single_persona, cross_window, stable, missing)
            - persona_names: List[str]
    """
    from backend.personas.metadata import PERSONA_METADATA
    
    assignments_30d, assignments_180d = load_persona_assignments(user_id, db_path)
    target_personas = determine_target_personas(assignments_30d, assignments_180d)
    
    # Determine strategy
    if not target_personas:
        strategy = 'missing'
    elif target_personas == [0]:
        strategy = 'stable'
    elif len(target_personas) == 1:
        strategy = 'single_persona'
    else:
        strategy = 'cross_window'
    
    # Get persona names
    persona_names = []
    for pid in target_personas:
        if pid == 0:
            persona_names.append('Stable')
        elif pid in PERSONA_METADATA:
            persona_names.append(PERSONA_METADATA[pid]['name'])
        else:
            persona_names.append(f'Unknown-{pid}')
    
    return {
        'target_personas': target_personas,
        'assignments_30d': assignments_30d,
        'assignments_180d': assignments_180d,
        'strategy': strategy,
        'persona_names': persona_names,
        'primary_persona_name': persona_names[0] if persona_names else None
    }


def should_include_cross_window_context(context: Dict[str, Any]) -> bool:
    """
    Determine if recommendation should include cross-window context.
    
    Args:
        context: Context from get_persona_context()
    
    Returns:
        True if recommendations should address both window personas
    """
    return context['strategy'] == 'cross_window'


def get_persona_weights(context: Dict[str, Any]) -> Dict[int, float]:
    """
    Get weights for each persona for content selection.
    
    Args:
        context: Context from get_persona_context()
    
    Returns:
        Dict mapping persona_id to weight (0.0-1.0)
    """
    personas = context['target_personas']
    strategy = context['strategy']
    
    if not personas:
        return {}
    
    if strategy == 'single_persona' or strategy == 'stable':
        # Full weight to single persona
        return {personas[0]: 1.0}
    
    elif strategy == 'cross_window':
        # 60/40 split: prioritize recent (30d) over long-term (180d)
        weights = {}
        if len(personas) >= 1:
            weights[personas[0]] = 0.6  # Primary (30d)
        if len(personas) >= 2:
            weights[personas[1]] = 0.4  # Secondary (180d)
        return weights
    
    else:
        return {}


def format_persona_summary(context: Dict[str, Any]) -> str:
    """
    Format a human-readable summary of persona context.
    
    Args:
        context: Context from get_persona_context()
    
    Returns:
        Summary string
    """
    strategy = context['strategy']
    names = context['persona_names']
    
    if strategy == 'missing':
        return "No persona data available"
    elif strategy == 'stable':
        return "User shows stable financial behavior"
    elif strategy == 'single_persona':
        return f"Persona: {names[0]}"
    elif strategy == 'cross_window':
        return f"Recent (30d): {names[0]}, Long-term (180d): {names[1]}"
    else:
        return "Unknown strategy"


def validate_persona_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that persona context is complete and ready for recommendation generation.
    
    Args:
        context: Context from get_persona_context()
    
    Returns:
        Validation result dict with 'valid' and 'issues' keys
    """
    issues = []
    
    # Check strategy
    if context['strategy'] == 'missing':
        issues.append("No persona assignments found")
    
    # Check target personas
    if not context['target_personas']:
        issues.append("No target personas identified")
    
    # Check assignments
    if context['strategy'] != 'missing':
        if not context['assignments_30d'] and not context['assignments_180d']:
            issues.append("No assignment data available")
    
    # Check persona names
    if context['target_personas'] and not context['persona_names']:
        issues.append("Persona names not resolved")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'strategy': context['strategy'],
        'persona_count': len(context['target_personas'])
    }

