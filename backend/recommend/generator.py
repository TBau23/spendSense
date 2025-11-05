"""
Recommendation Generator

Main orchestrator for generating personalized recommendation packages.
Coordinates content selection, LLM generation, eligibility checking, and package assembly.
"""

import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .persona_handler import get_persona_context, format_persona_summary
from .content_selector import select_educational_content
from .eligibility import select_eligible_offers
from .llm_client import LLMClient
from .prompts import (
    build_rationale_prompt,
    build_actionable_items_prompt,
    build_offer_relevance_prompt,
    extract_persona_specific_metrics,
    build_cross_window_context
)
from .storage import insert_recommendation
from .traces import generate_and_store_traces


def load_config(config_path: str = 'config.json') -> Dict[str, Any]:
    """Load configuration from file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def load_user_features(user_id: str, db_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load all computed features for a user.
    
    Args:
        user_id: User identifier
        db_path: Path to SQLite database
    
    Returns:
        Dictionary with feature types as keys (credit, income, savings, etc.)
    """
    import pandas as pd
    
    features = {}
    feature_dir = Path('data/features')
    
    # Load each feature type
    for feature_type in ['credit', 'income', 'savings', 'subscriptions', 'cash_flow']:
        parquet_path = feature_dir / f'{feature_type}.parquet'
        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
            # Get 30-day window features for this user
            user_df = df[(df['user_id'] == user_id) & (df['window_days'] == 30)]
            if not user_df.empty:
                features[feature_type] = user_df.iloc[0].to_dict()
    
    return features


def generate_recommendation(
    user_id: str,
    as_of_date: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate recommendation package for a user.
    
    Args:
        user_id: User identifier
        as_of_date: Optional date for reproducible generation (YYYY-MM-DD)
        config: Optional configuration dictionary (loads from file if None)
    
    Returns:
        Complete recommendation package dictionary
    """
    start_time = time.time()
    
    # Load configuration
    if config is None:
        config = load_config()
    
    db_path = config['database']['path']
    rec_config = config.get('recommendations', {})
    llm_config = config.get('llm', {})
    
    print(f"\n{'='*70}")
    print(f"Generating recommendations for {user_id}")
    print(f"{'='*70}")
    
    # 1. Load persona context
    print("\n1. Loading persona context...")
    persona_context = get_persona_context(user_id, db_path)
    print(f"   Strategy: {persona_context['strategy']}")
    print(f"   Summary: {format_persona_summary(persona_context)}")
    
    # Handle no persona data
    if persona_context['strategy'] == 'missing':
        print("   ⚠ No persona data found, skipping recommendation generation")
        return {
            'user_id': user_id,
            'error': 'No persona data available',
            'generated_at': datetime.now().isoformat()
        }
    
    # Handle stable users
    if persona_context['strategy'] == 'stable':
        print("   → Routing to stable user handler")
        return generate_stable_user_recommendation(user_id, persona_context, config)
    
    # 2. Load user features
    print("\n2. Loading user features...")
    features = load_user_features(user_id, db_path)
    print(f"   Loaded {len(features)} feature types")
    
    # 3. Select educational content
    print("\n3. Selecting educational content...")
    target_personas = persona_context['target_personas']
    content_count = rec_config.get('content_selection', {}).get('educational_items_max', 5)
    
    educational_items = select_educational_content(
        db_path,
        target_personas,
        count=content_count,
        prioritize_primary=True
    )
    print(f"   Selected {len(educational_items)} items")
    
    # 4. Generate rationales for educational content (LLM)
    print("\n4. Generating educational content rationales...")
    educational_items = generate_educational_rationales(
        educational_items,
        persona_context,
        features,
        llm_config
    )
    
    # 5. Generate actionable items (LLM)
    print("\n5. Generating actionable items...")
    action_count = rec_config.get('content_selection', {}).get('actionable_items_max', 3)
    actionable_items = generate_actionable_items_for_user(
        persona_context,
        features,
        count=action_count,
        llm_config=llm_config
    )
    print(f"   Generated {len(actionable_items)} actionable items")
    
    # 6. Select and explain partner offers
    print("\n6. Selecting partner offers...")
    max_offers = rec_config.get('content_selection', {}).get('partner_offers_max', 2)
    partner_offers = select_and_explain_offers(
        user_id,
        target_personas,
        features,
        persona_context,
        db_path,
        max_offers,
        llm_config
    )
    print(f"   Selected {len(partner_offers)} eligible offers")
    
    # 7. Assemble complete package
    print("\n7. Assembling recommendation package...")
    generation_time = time.time() - start_time
    
    recommendation = {
        'recommendation_id': f"rec_{user_id}_{int(time.time())}",
        'user_id': user_id,
        'window_30d_persona_id': persona_context['assignments_30d']['primary_persona_id'] if persona_context['assignments_30d'] else None,
        'window_180d_persona_id': persona_context['assignments_180d']['primary_persona_id'] if persona_context['assignments_180d'] else None,
        'target_personas': target_personas,
        'educational_content': educational_items,
        'actionable_items': actionable_items,
        'partner_offers': partner_offers,
        'generated_at': datetime.now().isoformat(),
        'llm_model': llm_config.get('model', 'gpt-4o-mini'),
        'generation_latency_seconds': generation_time
    }
    
    # 8. Store in database
    print("\n8. Storing recommendation...")
    try:
        insert_recommendation(
            db_path=db_path,
            recommendation_id=recommendation['recommendation_id'],
            user_id=user_id,
            window_30d_persona_id=recommendation['window_30d_persona_id'],
            window_180d_persona_id=recommendation['window_180d_persona_id'],
            target_personas=target_personas,
            educational_items=educational_items,
            actionable_items=actionable_items,
            partner_offers=partner_offers,
            llm_model=recommendation['llm_model'],
            generation_latency_seconds=generation_time
        )
        print(f"   ✓ Stored recommendation {recommendation['recommendation_id']}")
    except Exception as e:
        print(f"   ⚠ Storage failed: {e}")
    
    # 9. Generate and store decision traces
    print("\n9. Generating decision traces...")
    try:
        trace_ids = generate_and_store_traces(
            user_id=user_id,
            recommendation=recommendation,
            educational_items=educational_items,
            partner_offers=partner_offers,
            db_path=db_path
        )
        print(f"   ✓ Stored {len(trace_ids)} decision traces")
    except Exception as e:
        print(f"   ⚠ Trace generation failed: {e}")
    
    print(f"\n{'='*70}")
    print(f"✓ Recommendation generated in {generation_time:.2f}s")
    print(f"{'='*70}\n")
    
    return recommendation


def generate_educational_rationales(
    educational_items: List[Dict[str, Any]],
    persona_context: Dict[str, Any],
    features: Dict[str, Any],
    llm_config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate LLM rationales for each educational content item.
    
    Args:
        educational_items: List of selected content items
        persona_context: Persona context from get_persona_context()
        features: User features dictionary
        llm_config: LLM configuration
    
    Returns:
        Educational items with rationales added
    """
    # Initialize LLM client
    llm_client = LLMClient(llm_config)
    
    # Extract persona-specific metrics
    primary_persona_id = persona_context['target_personas'][0]
    user_context = extract_persona_specific_metrics(features, primary_persona_id)
    
    # Generate rationale for each item
    for item in educational_items:
        system_msg, user_prompt = build_rationale_prompt(
            user_context=user_context,
            persona_name=persona_context['primary_persona_name'],
            content_title=item['title'],
            content_snippet=item['snippet']
        )
        
        result = llm_client.generate(user_prompt, system_msg)
        
        if result['success']:
            item['rationale'] = result['text']
            print(f"   ✓ {item['content_id']}")
        else:
            # Fallback rationale
            item['rationale'] = f"Based on your {persona_context['primary_persona_name']} profile, this content may be helpful for your situation."
            print(f"   ⚠ {item['content_id']} (using fallback)")
    
    return educational_items


def generate_actionable_items_for_user(
    persona_context: Dict[str, Any],
    features: Dict[str, Any],
    count: int,
    llm_config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate actionable items using LLM.
    
    Args:
        persona_context: Persona context
        features: User features
        count: Number of items to generate
        llm_config: LLM configuration
    
    Returns:
        List of actionable items with text and rationales
    """
    # Initialize LLM client
    llm_client = LLMClient(llm_config)
    
    # Extract metrics
    primary_persona_id = persona_context['target_personas'][0]
    user_context = extract_persona_specific_metrics(features, primary_persona_id)
    
    # Build prompt
    system_msg, user_prompt = build_actionable_items_prompt(
        user_context=user_context,
        persona_name=persona_context['primary_persona_name'],
        personas_list=persona_context['target_personas'],
        count=count
    )
    
    # Generate with LLM
    result = llm_client.generate(user_prompt, system_msg, max_tokens=300)
    
    if result['success']:
        try:
            # Try to parse JSON
            items = json.loads(result['text'])
            if isinstance(items, list) and all('text' in item and 'rationale' in item for item in items):
                # Add metadata
                for item in items:
                    item['generated_by'] = 'llm'
                    item['data_cited'] = user_context
                return items[:count]
        except json.JSONDecodeError:
            print(f"   ⚠ LLM returned invalid JSON, using fallback")
    
    # Fallback to template-based items
    return _fallback_actionable_items(persona_context['primary_persona_name'], count)


def select_and_explain_offers(
    user_id: str,
    target_personas: List[int],
    features: Dict[str, Any],
    persona_context: Dict[str, Any],
    db_path: str,
    max_offers: int,
    llm_config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Select eligible offers and generate relevance explanations.
    
    Args:
        user_id: User identifier
        target_personas: List of target persona IDs
        features: User features
        persona_context: Persona context
        db_path: Database path
        max_offers: Maximum number of offers
        llm_config: LLM configuration
    
    Returns:
        List of offers with eligibility details and relevance explanations
    """
    # Select eligible offers
    eligible_offers = select_eligible_offers(
        user_id,
        target_personas,
        features,
        db_path,
        max_offers
    )
    
    if not eligible_offers:
        return []
    
    # Initialize LLM client
    llm_client = LLMClient(llm_config)
    
    # Extract user context
    primary_persona_id = target_personas[0]
    user_context = extract_persona_specific_metrics(features, primary_persona_id)
    
    # Generate relevance explanation for each offer
    for offer in eligible_offers:
        system_msg, user_prompt = build_offer_relevance_prompt(
            user_context=user_context,
            persona_name=persona_context['primary_persona_name'],
            offer_name=offer['product_name'],
            offer_description=offer['short_description'],
            offer_benefits=offer.get('benefits', [])
        )
        
        result = llm_client.generate(user_prompt, system_msg)
        
        if result['success']:
            offer['why_relevant'] = result['text']
        else:
            # Fallback
            offer['why_relevant'] = f"This {offer['product_type']} may help address your current financial situation."
    
    return eligible_offers


def generate_stable_user_recommendation(
    user_id: str,
    persona_context: Dict[str, Any],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate minimal recommendation for stable users.
    
    Args:
        user_id: User identifier
        persona_context: Persona context (should have strategy='stable')
        config: Configuration dictionary
    
    Returns:
        Recommendation package for stable user
    """
    start_time = time.time()
    db_path = config['database']['path']
    llm_config = config.get('llm', {})
    
    print(f"   Generating stable user content...")
    
    # Select stable content (persona_id = 0)
    educational_items = select_educational_content(
        db_path,
        [0],  # Stable persona
        count=2,
        prioritize_primary=True
    )
    
    # Add simple rationales (no LLM needed for stable users)
    for item in educational_items:
        item['rationale'] = "You're demonstrating strong financial behaviors. This content can help you continue optimizing your financial health."
    
    # One simple actionable item
    actionable_items = [
        {
            'text': "Keep up the great work with your financial habits",
            'rationale': "You're demonstrating strong financial behaviors. Maintaining these habits will continue to support your financial well-being.",
            'generated_by': 'template',
            'data_cited': {}
        }
    ]
    
    # No partner offers for stable users
    partner_offers = []
    
    generation_time = time.time() - start_time
    
    recommendation = {
        'recommendation_id': f"rec_{user_id}_{int(time.time())}",
        'user_id': user_id,
        'window_30d_persona_id': 0,
        'window_180d_persona_id': 0,
        'target_personas': [0],
        'educational_content': educational_items,
        'actionable_items': actionable_items,
        'partner_offers': partner_offers,
        'generated_at': datetime.now().isoformat(),
        'llm_model': llm_config.get('model', 'none'),
        'generation_latency_seconds': generation_time
    }
    
    # Store in database
    try:
        insert_recommendation(
            db_path=db_path,
            recommendation_id=recommendation['recommendation_id'],
            user_id=user_id,
            window_30d_persona_id=0,
            window_180d_persona_id=0,
            target_personas=[0],
            educational_items=educational_items,
            actionable_items=actionable_items,
            partner_offers=partner_offers,
            llm_model=recommendation['llm_model'],
            generation_latency_seconds=generation_time
        )
        print(f"   ✓ Stored stable user recommendation")
    except Exception as e:
        print(f"   ⚠ Storage failed: {e}")
    
    return recommendation


def generate_batch_recommendations(
    user_ids: Optional[List[str]] = None,
    as_of_date: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate recommendations for multiple users.
    
    Args:
        user_ids: List of user IDs, or None for all users with persona assignments
        as_of_date: Optional date for reproducible generation
        config: Optional configuration dictionary
    
    Returns:
        Summary dictionary with generation stats
    """
    import sqlite3
    
    # Load configuration
    if config is None:
        config = load_config()
    
    db_path = config['database']['path']
    
    # Get user IDs if not provided
    if user_ids is None:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT user_id FROM persona_assignments
            WHERE status = 'ASSIGNED' OR status = 'STABLE'
        ''')
        user_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
    
    print(f"\n{'='*70}")
    print(f"BATCH RECOMMENDATION GENERATION")
    print(f"{'='*70}")
    print(f"Total users: {len(user_ids)}")
    print(f"{'='*70}\n")
    
    # Generate for each user
    results = {
        'total_users': len(user_ids),
        'successful': 0,
        'failed': 0,
        'errors': [],
        'total_time': 0,
        'avg_time_per_user': 0
    }
    
    start_time = time.time()
    
    for idx, user_id in enumerate(user_ids, 1):
        print(f"\n[{idx}/{len(user_ids)}] Processing {user_id}...")
        
        try:
            recommendation = generate_recommendation(user_id, as_of_date, config)
            
            if 'error' in recommendation:
                results['failed'] += 1
                results['errors'].append({
                    'user_id': user_id,
                    'error': recommendation['error']
                })
            else:
                results['successful'] += 1
        
        except Exception as e:
            print(f"   ✗ Error: {e}")
            results['failed'] += 1
            results['errors'].append({
                'user_id': user_id,
                'error': str(e)
            })
    
    results['total_time'] = time.time() - start_time
    results['avg_time_per_user'] = results['total_time'] / len(user_ids) if user_ids else 0
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"BATCH GENERATION COMPLETE")
    print(f"{'='*70}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Total time: {results['total_time']:.2f}s")
    print(f"Avg time per user: {results['avg_time_per_user']:.2f}s")
    print(f"{'='*70}\n")
    
    return results


def _fallback_actionable_items(persona_name: str, count: int) -> List[Dict[str, str]]:
    """Fallback actionable items when LLM fails."""
    fallbacks = {
        "High Utilization": [
            {
                "text": "Review your credit card statements to identify which cards have the highest interest rates",
                "rationale": "Focusing on high-interest debt first can help you save money on interest charges.",
                "generated_by": "template",
                "data_cited": {}
            },
            {
                "text": "Consider setting up automatic minimum payments to protect your credit score",
                "rationale": "Automating payments helps ensure you never miss a due date.",
                "generated_by": "template",
                "data_cited": {}
            }
        ],
        "Variable Income Budgeter": [
            {
                "text": "Calculate your average monthly income over the past 6 months",
                "rationale": "Understanding your average income helps create a sustainable budget.",
                "generated_by": "template",
                "data_cited": {}
            },
            {
                "text": "Set aside a percentage during high-earning months",
                "rationale": "Building a buffer during good months reduces stress during lean times.",
                "generated_by": "template",
                "data_cited": {}
            }
        ],
        "Subscription-Heavy": [
            {
                "text": "Review your bank statements from the past 3 months to identify all recurring charges",
                "rationale": "A thorough audit often reveals forgotten subscriptions.",
                "generated_by": "template",
                "data_cited": {}
            },
            {
                "text": "Choose 2-3 services you value most and consider canceling the rest",
                "rationale": "Prioritizing helps you cut spending without sacrificing value.",
                "generated_by": "template",
                "data_cited": {}
            }
        ],
        "Savings Builder": [
            {
                "text": "Review your current savings account interest rate",
                "rationale": "High-yield accounts offer significantly better returns.",
                "generated_by": "template",
                "data_cited": {}
            },
            {
                "text": "Set up automatic transfers from checking to savings",
                "rationale": "Automation ensures consistent savings without relying on willpower.",
                "generated_by": "template",
                "data_cited": {}
            }
        ],
        "Cash Flow Stressed": [
            {
                "text": "Try to set aside $25-50 from your next paycheck",
                "rationale": "Even a small buffer can help break the paycheck-to-paycheck cycle.",
                "generated_by": "template",
                "data_cited": {}
            },
            {
                "text": "Create a list of all your bills and their due dates",
                "rationale": "Strategic timing of payments can help maintain higher balances.",
                "generated_by": "template",
                "data_cited": {}
            }
        ]
    }
    
    items = fallbacks.get(persona_name, [
        {
            "text": "Review your financial accounts and recent transactions",
            "rationale": "Understanding your current situation is the first step to improvement.",
            "generated_by": "template",
            "data_cited": {}
        }
    ])
    
    return items[:count]
