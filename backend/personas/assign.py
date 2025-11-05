"""
Persona Assignment Orchestrator

Main logic for assigning personas to users based on computed features.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from .evaluators import (
    evaluate_persona_1,
    evaluate_persona_2,
    evaluate_persona_3,
    evaluate_persona_4,
    evaluate_persona_5
)
from .prioritize import sort_matched_personas, select_primary_and_secondary
from .trace import generate_assignment_trace


def load_features_for_user(
    user_id: str,
    window_days: int,
    as_of_date: str,
    features_dir: str
) -> Dict:
    """
    Load all features for a specific user/window from Parquet files.
    
    Args:
        user_id: User identifier
        window_days: Time window (30 or 180)
        as_of_date: Date string (YYYY-MM-DD)
        features_dir: Directory containing feature Parquet files
        
    Returns:
        Dict mapping feature type to feature dict
    """
    from datetime import datetime
    
    features = {}
    feature_types = ['subscriptions', 'savings', 'credit', 'income', 'cash_flow']
    
    # Convert string date to datetime.date for comparison
    date_obj = datetime.strptime(as_of_date, '%Y-%m-%d').date()
    
    for feature_type in feature_types:
        parquet_path = Path(features_dir) / f'{feature_type}.parquet'
        
        if not parquet_path.exists():
            print(f"Warning: {parquet_path} not found, skipping {feature_type} features")
            features[feature_type] = {}
            continue
        
        try:
            df = pd.read_parquet(parquet_path)
            
            # Filter for this user/window
            user_features = df[
                (df['user_id'] == user_id) & 
                (df['window_days'] == window_days) &
                (df['as_of_date'] == date_obj)
            ]
            
            if len(user_features) > 0:
                features[feature_type] = user_features.iloc[0].to_dict()
            else:
                features[feature_type] = {}
                
        except Exception as e:
            print(f"Warning: Error loading {feature_type} for user {user_id}: {e}")
            features[feature_type] = {}
    
    return features


def assign_personas_for_user(
    user_id: str,
    window_days: int,
    as_of_date: str,
    features: Dict
) -> Dict:
    """
    Assign personas for a single user/window.
    
    Args:
        user_id: User identifier
        window_days: Time window (30 or 180)
        as_of_date: Date string (YYYY-MM-DD)
        features: Dict containing all feature types
        
    Returns:
        Dict with assignment result:
        {
            'user_id': str,
            'window_days': int,
            'as_of_date': str,
            'primary': dict or None,
            'secondary': dict or None,
            'status': 'ASSIGNED' or 'STABLE',
            'assignment_trace': str (JSON)
        }
    """
    # Evaluate all 5 personas
    evaluations = {}
    matched_personas = []
    
    evaluators = [
        (1, evaluate_persona_1),
        (2, evaluate_persona_2),
        (3, evaluate_persona_3),
        (4, evaluate_persona_4),
        (5, evaluate_persona_5),
    ]
    
    for persona_id, evaluator_func in evaluators:
        matched, severity, details = evaluator_func(features)
        evaluations[persona_id] = (matched, severity, details)
        
        if matched:
            from .metadata import get_persona_info
            persona_info = get_persona_info(persona_id)
            matched_personas.append({
                'persona_id': persona_id,
                'persona_name': persona_info['name'],
                'priority': persona_info['priority'],
                'severity': severity,
                'details': details
            })
    
    # Handle no matches (STABLE status)
    if len(matched_personas) == 0:
        assignment_trace = generate_assignment_trace(
            user_id=user_id,
            window_days=window_days,
            as_of_date=as_of_date,
            all_evaluations=evaluations,
            primary=None,
            secondary=None,
            status='STABLE'
        )
        
        return {
            'user_id': user_id,
            'window_days': window_days,
            'as_of_date': as_of_date,
            'primary': None,
            'secondary': None,
            'status': 'STABLE',
            'assignment_trace': assignment_trace
        }
    
    # Sort and select primary/secondary
    sorted_personas = sort_matched_personas(matched_personas)
    primary, secondary = select_primary_and_secondary(sorted_personas)
    
    # Generate audit trace
    assignment_trace = generate_assignment_trace(
        user_id=user_id,
        window_days=window_days,
        as_of_date=as_of_date,
        all_evaluations=evaluations,
        primary=primary,
        secondary=secondary,
        status='ASSIGNED'
    )
    
    return {
        'user_id': user_id,
        'window_days': window_days,
        'as_of_date': as_of_date,
        'primary': primary,
        'secondary': secondary,
        'status': 'ASSIGNED',
        'assignment_trace': assignment_trace
    }


def assign_all_personas(
    db_path: str,
    features_dir: str,
    windows: List[int],
    as_of_date: str
) -> List[Dict]:
    """
    Assign personas for all users across all windows.
    
    Args:
        db_path: Path to SQLite database (to get user list)
        features_dir: Directory containing feature Parquet files
        windows: List of window sizes (e.g., [30, 180])
        as_of_date: Date string (YYYY-MM-DD)
        
    Returns:
        List of assignment dicts
    """
    import sqlite3
    
    # Get all user IDs from database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users ORDER BY user_id')
    user_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print(f"\n=== Assigning Personas ===")
    print(f"Users: {len(user_ids)}")
    print(f"Windows: {windows}")
    print(f"As of date: {as_of_date}")
    
    assignments = []
    
    for user_id in user_ids:
        for window_days in windows:
            # Load features
            features = load_features_for_user(
                user_id=user_id,
                window_days=window_days,
                as_of_date=as_of_date,
                features_dir=features_dir
            )
            
            # Assign personas
            assignment = assign_personas_for_user(
                user_id=user_id,
                window_days=window_days,
                as_of_date=as_of_date,
                features=features
            )
            
            assignments.append(assignment)
            
            # Progress indicator
            if len(assignments) % 10 == 0:
                print(f"  Processed {len(assignments)} assignments...")
    
    print(f"✓ Completed {len(assignments)} persona assignments")
    
    # Summary statistics
    assigned_count = sum(1 for a in assignments if a['status'] == 'ASSIGNED')
    stable_count = sum(1 for a in assignments if a['status'] == 'STABLE')
    
    print(f"\nSummary:")
    print(f"  ASSIGNED: {assigned_count}")
    print(f"  STABLE: {stable_count}")
    
    # Count by primary persona
    persona_counts = {}
    for assignment in assignments:
        if assignment['primary']:
            name = assignment['primary']['persona_name']
            persona_counts[name] = persona_counts.get(name, 0) + 1
    
    if persona_counts:
        print(f"\nBy Primary Persona:")
        for name, count in sorted(persona_counts.items(), key=lambda x: -x[1]):
            print(f"  {name}: {count}")
    
    return assignments


def validate_assignments(assignments: List[Dict], db_path: str) -> Dict:
    """
    Validate persona assignments against Epic 1 archetypes.
    
    Args:
        assignments: List of assignment dicts
        db_path: Path to SQLite database
        
    Returns:
        Dict with validation results
    """
    import sqlite3
    
    print(f"\n=== Validating Persona Assignments ===")
    
    # Get user archetypes from data generation (if stored)
    # For now, just do basic validation
    
    total = len(assignments)
    assigned = sum(1 for a in assignments if a['status'] == 'ASSIGNED')
    stable = sum(1 for a in assignments if a['status'] == 'STABLE')
    
    # Check for dual windows (each user should have 2 assignments)
    user_window_counts = {}
    for assignment in assignments:
        user_id = assignment['user_id']
        user_window_counts[user_id] = user_window_counts.get(user_id, 0) + 1
    
    users_with_both_windows = sum(1 for count in user_window_counts.values() if count == 2)
    total_users = len(user_window_counts)
    
    # Check persona distribution
    persona_counts = {}
    for assignment in assignments:
        if assignment['primary']:
            persona_id = assignment['primary']['persona_id']
            persona_counts[persona_id] = persona_counts.get(persona_id, 0) + 1
    
    all_personas_represented = len(persona_counts) >= 5
    
    validation = {
        'total_assignments': total,
        'assigned_count': assigned,
        'stable_count': stable,
        'total_users': total_users,
        'users_with_both_windows': users_with_both_windows,
        'coverage_100_percent': users_with_both_windows == total_users,
        'persona_counts': persona_counts,
        'all_personas_represented': all_personas_represented,
        'validation_passed': (
            total > 0 and
            users_with_both_windows == total_users and
            len(persona_counts) >= 1  # At least some personas assigned
        )
    }
    
    print(f"Total assignments: {total}")
    print(f"  ASSIGNED: {assigned}")
    print(f"  STABLE: {stable}")
    print(f"Total users: {total_users}")
    print(f"Users with both windows (30d + 180d): {users_with_both_windows}/{total_users}")
    print(f"Coverage 100%: {'✓' if validation['coverage_100_percent'] else '✗'}")
    print(f"All 5 personas represented: {'✓' if all_personas_represented else '✗'}")
    
    if persona_counts:
        print(f"\nPersona distribution:")
        for persona_id in sorted(persona_counts.keys()):
            from .metadata import get_persona_name
            name = get_persona_name(persona_id)
            count = persona_counts[persona_id]
            print(f"  Persona {persona_id} ({name}): {count}")
    
    print(f"\nValidation: {'✓ PASSED' if validation['validation_passed'] else '✗ FAILED'}")
    
    return validation

