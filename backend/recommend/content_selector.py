"""
Content Selector

Selects educational content from catalog based on persona relevance.
Handles single-persona and cross-window (multi-persona) selection strategies.
"""

import random
from typing import List, Dict, Any, Optional


def select_educational_content(
    db_path: str,
    target_personas: List[int],
    count: int = 5,
    prioritize_primary: bool = True
) -> List[Dict[str, Any]]:
    """
    Select educational content items based on target personas.
    
    Args:
        db_path: Path to SQLite database
        target_personas: List of persona IDs to target (e.g., [5, 1] for cross-window)
        count: Number of items to select (typically 3-5)
        prioritize_primary: If True, select more items for first persona in list
    
    Returns:
        List of content items (dicts with content_id, title, snippet, etc.)
    """
    from .storage import load_content_catalog
    
    # Load all content
    catalog = load_content_catalog(db_path)
    
    if not target_personas:
        # Fallback: stable user or error case
        return _select_stable_content(catalog, count)
    
    if len(target_personas) == 1:
        # Single persona - straightforward selection
        return _select_single_persona_content(catalog, target_personas[0], count)
    else:
        # Cross-window: multiple personas
        return _select_cross_window_content(
            catalog, 
            target_personas, 
            count,
            prioritize_primary
        )


def _select_single_persona_content(
    catalog: List[Dict[str, Any]],
    persona_id: int,
    count: int
) -> List[Dict[str, Any]]:
    """
    Select content for a single persona.
    
    Strategy:
    - Prioritize items where persona_id is in primary persona_tags
    - Fall back to secondary_tags if needed
    - Ensure variety (don't pick only articles if guides/tools available)
    """
    # Filter by primary relevance
    primary_matches = [
        item for item in catalog
        if persona_id in item.get('persona_tags', [])
    ]
    
    # Filter by secondary relevance
    secondary_matches = [
        item for item in catalog
        if persona_id in item.get('secondary_tags', [])
        and item not in primary_matches
    ]
    
    selected = []
    
    # Select from primary matches first
    if len(primary_matches) >= count:
        # Have enough primary matches
        selected = _diverse_sample(primary_matches, count)
    else:
        # Use all primary matches + some secondary
        selected = primary_matches.copy()
        remaining = count - len(selected)
        if secondary_matches and remaining > 0:
            selected.extend(_diverse_sample(secondary_matches, remaining))
    
    # If still not enough, pad with generic content
    if len(selected) < count:
        generic = [item for item in catalog if 0 in item.get('persona_tags', [])]
        remaining = count - len(selected)
        selected.extend(_diverse_sample(generic, remaining))
    
    return selected[:count]


def _select_cross_window_content(
    catalog: List[Dict[str, Any]],
    target_personas: List[int],
    count: int,
    prioritize_primary: bool
) -> List[Dict[str, Any]]:
    """
    Select content when user has different personas across time windows.
    
    Strategy:
    - Allocate more items to primary persona (first in list - typically 30d)
    - Include some items for secondary persona (typically 180d)
    - Example: count=5, personas=[5,1] → 3 items for P5, 2 items for P1
    """
    if len(target_personas) < 2:
        return _select_single_persona_content(catalog, target_personas[0], count)
    
    primary_persona = target_personas[0]
    secondary_persona = target_personas[1]
    
    # Allocate counts based on priority
    if prioritize_primary:
        # 60/40 split approximately
        if count == 5:
            primary_count, secondary_count = 3, 2
        elif count == 4:
            primary_count, secondary_count = 3, 1
        elif count == 3:
            primary_count, secondary_count = 2, 1
        else:
            primary_count = max(1, count * 6 // 10)
            secondary_count = count - primary_count
    else:
        # Even split
        primary_count = count // 2
        secondary_count = count - primary_count
    
    # Select for each persona
    primary_items = _select_single_persona_content(catalog, primary_persona, primary_count)
    secondary_items = _select_single_persona_content(catalog, secondary_persona, secondary_count)
    
    # Ensure no duplicates
    selected = primary_items.copy()
    for item in secondary_items:
        if item['content_id'] not in [s['content_id'] for s in selected]:
            selected.append(item)
    
    return selected[:count]


def _select_stable_content(
    catalog: List[Dict[str, Any]],
    count: int
) -> List[Dict[str, Any]]:
    """
    Select content for stable users (persona_id = 0).
    """
    stable_items = [
        item for item in catalog
        if 0 in item.get('persona_tags', [])
    ]
    
    if not stable_items:
        # Fallback: generic optimization content
        stable_items = [
            item for item in catalog
            if 'optimization' in item.get('topics', [])
            or 'financial_planning' in item.get('topics', [])
        ]
    
    return _diverse_sample(stable_items, min(count, 2))  # Stable users get fewer items


def _diverse_sample(
    items: List[Dict[str, Any]],
    count: int
) -> List[Dict[str, Any]]:
    """
    Sample items with diversity preference (mix of content types).
    
    Args:
        items: List of content items
        count: Number to sample
    
    Returns:
        Sampled list with diversity
    """
    if len(items) <= count:
        return items.copy()
    
    # Group by content type
    by_type = {}
    for item in items:
        content_type = item.get('content_type', 'article')
        by_type.setdefault(content_type, []).append(item)
    
    selected = []
    types = list(by_type.keys())
    
    # Round-robin selection across types
    type_idx = 0
    attempts = 0
    max_attempts = len(items) * 2  # Prevent infinite loop
    
    while len(selected) < count and attempts < max_attempts:
        current_type = types[type_idx % len(types)]
        
        if by_type[current_type]:
            # Pick random item from this type
            item = random.choice(by_type[current_type])
            if item not in selected:
                selected.append(item)
                by_type[current_type].remove(item)
        
        type_idx += 1
        attempts += 1
    
    # If still need more, add any remaining
    if len(selected) < count:
        remaining = [item for item in items if item not in selected]
        selected.extend(remaining[:count - len(selected)])
    
    return selected[:count]


def get_content_by_id(db_path: str, content_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific content item by ID.
    
    Args:
        db_path: Path to SQLite database
        content_id: Content identifier
    
    Returns:
        Content item dict or None if not found
    """
    from .storage import load_content_catalog
    
    catalog = load_content_catalog(db_path)
    for item in catalog:
        if item['content_id'] == content_id:
            return item
    return None


def get_content_by_persona(
    db_path: str,
    persona_id: int,
    include_secondary: bool = True
) -> List[Dict[str, Any]]:
    """
    Get all content items relevant to a persona.
    
    Args:
        db_path: Path to SQLite database
        persona_id: Persona identifier (0-5)
        include_secondary: Include items where persona is in secondary_tags
    
    Returns:
        List of relevant content items
    """
    from .storage import load_content_catalog
    
    catalog = load_content_catalog(db_path)
    
    relevant = []
    for item in catalog:
        if persona_id in item.get('persona_tags', []):
            relevant.append(item)
        elif include_secondary and persona_id in item.get('secondary_tags', []):
            relevant.append(item)
    
    return relevant


def validate_content_selection(
    selected: List[Dict[str, Any]],
    target_personas: List[int],
    min_count: int = 3,
    max_count: int = 5
) -> Dict[str, Any]:
    """
    Validate that content selection meets requirements.
    
    Args:
        selected: List of selected content items
        target_personas: Target persona IDs
        min_count: Minimum number of items required
        max_count: Maximum number of items allowed
    
    Returns:
        Validation result dict with 'valid' and 'issues' keys
    """
    issues = []
    
    # Check count
    if len(selected) < min_count:
        issues.append(f"Too few items: {len(selected)} < {min_count}")
    if len(selected) > max_count:
        issues.append(f"Too many items: {len(selected)} > {max_count}")
    
    # Check for duplicates
    content_ids = [item['content_id'] for item in selected]
    if len(content_ids) != len(set(content_ids)):
        issues.append("Duplicate content IDs found")
    
    # Check persona relevance
    relevant_count = 0
    for item in selected:
        persona_tags = item.get('persona_tags', [])
        secondary_tags = item.get('secondary_tags', [])
        if any(p in persona_tags or p in secondary_tags for p in target_personas):
            relevant_count += 1
    
    if relevant_count == 0 and target_personas:
        issues.append("No content relevant to target personas")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'count': len(selected),
        'relevant_count': relevant_count
    }

