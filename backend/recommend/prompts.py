"""
Prompt Templates

Structured prompts for LLM generation of rationales, actionable items,
and partner offer relevance explanations.
"""

import json
from typing import Dict, Any


def build_rationale_prompt(
    user_context: Dict[str, Any],
    persona_name: str,
    content_title: str,
    content_snippet: str
) -> tuple[str, str]:
    """
    Build prompt for generating educational content rationale.
    
    Args:
        user_context: Dictionary with user-specific metrics
        persona_name: Name of user's persona
        content_title: Title of educational content
        content_snippet: Brief description of content
    
    Returns:
        Tuple of (system_message, user_prompt)
    """
    system_message = """You are a financial education assistant. Generate clear, empowering rationales for why recommended content is relevant to users.

Guidelines:
- Use empowering, non-judgmental language
- Cite specific user data (percentages, amounts, counts)
- Focus on opportunities and benefits, not problems
- Keep under 100 words
- Avoid words like "overspending", "bad", "poor"
- Use phrases like "we noticed", "you could", "this might help"
- Never use "you should" - instead say "you might consider"
"""
    
    user_prompt = f"""Generate a rationale for why this content is relevant to the user.

User Persona: {persona_name}

User Metrics:
{json.dumps(user_context, indent=2)}

Recommended Content:
Title: "{content_title}"
Description: {content_snippet}

Generate a brief, empowering rationale that:
1. References specific numbers from the user metrics
2. Explains how this content relates to their situation
3. Focuses on potential benefits and opportunities

Rationale:"""
    
    return system_message, user_prompt


def build_actionable_items_prompt(
    user_context: Dict[str, Any],
    persona_name: str,
    personas_list: list[int],
    count: int = 2
) -> tuple[str, str]:
    """
    Build prompt for generating actionable items.
    
    Args:
        user_context: Dictionary with user-specific metrics
        persona_name: Primary persona name
        personas_list: List of persona IDs being targeted (for cross-window)
        count: Number of items to generate (1-3)
    
    Returns:
        Tuple of (system_message, user_prompt)
    """
    system_message = """You are a financial education assistant. Generate specific, actionable next steps that users can take.

Guidelines:
- Make actions SPECIFIC and MEASURABLE (e.g., "Pay $150 toward...", not "Pay more")
- Cite actual user data in rationales
- Focus on small, achievable steps
- Use empowering language
- Each action should be under 50 words
- Never use "you should" - say "you might consider", "you could", etc.
- Return ONLY valid JSON, no other text

Output format:
[
  {
    "text": "Specific action the user can take",
    "rationale": "Why this action helps, citing specific user data"
  }
]
"""
    
    personas_context = ""
    if len(personas_list) > 1:
        personas_context = f"\n\nNote: User has different personas across time windows. Address the most urgent behaviors from both patterns."
    
    user_prompt = f"""Generate {count} specific, actionable next steps for this user.

User Persona: {persona_name}
Target Personas: {personas_list}{personas_context}

User Metrics:
{json.dumps(user_context, indent=2)}

Requirements for each action:
1. Must be specific and measurable (include actual numbers when possible)
2. Must cite user's actual data in the rationale
3. Must be achievable (small steps, not overwhelming)
4. Must use empowering language

Generate exactly {count} actions as a JSON array:"""
    
    return system_message, user_prompt


def build_offer_relevance_prompt(
    user_context: Dict[str, Any],
    persona_name: str,
    offer_name: str,
    offer_description: str,
    offer_benefits: list[str]
) -> tuple[str, str]:
    """
    Build prompt for explaining why a partner offer is relevant.
    
    Args:
        user_context: Dictionary with user-specific metrics
        persona_name: Name of user's persona
        offer_name: Name of partner offer
        offer_description: Description of the offer
        offer_benefits: List of benefit strings
    
    Returns:
        Tuple of (system_message, user_prompt)
    """
    system_message = """You are a financial education assistant. Explain why financial products might be relevant to users based on their situation.

Guidelines:
- Keep under 80 words
- Cite specific user data
- Focus on how the product addresses their situation
- Use empowering language
- Say "might help", "could", never "should"
- Don't oversell - be realistic about benefits
"""
    
    benefits_text = "\n".join([f"- {b}" for b in offer_benefits])
    
    user_prompt = f"""Explain why this product is relevant to the user's situation.

User Persona: {persona_name}

User Metrics:
{json.dumps(user_context, indent=2)}

Product:
Name: {offer_name}
Description: {offer_description}

Benefits:
{benefits_text}

Generate a brief explanation (under 80 words) of how this product relates to the user's specific financial situation. Cite actual numbers from their metrics.

Explanation:"""
    
    return system_message, user_prompt


def extract_persona_specific_metrics(
    features: Dict[str, Any],
    persona_id: int
) -> Dict[str, Any]:
    """
    Extract the most relevant metrics for a persona to include in prompts.
    
    Args:
        features: Full features dictionary for user
        persona_id: Persona ID (1-5)
    
    Returns:
        Dictionary with persona-specific metrics
    """
    if persona_id == 1:
        # High Utilization - focus on credit metrics
        credit = features.get('credit', {})
        return {
            'persona': 'High Utilization',
            'max_utilization': credit.get('max_utilization', 0),
            'avg_utilization': credit.get('avg_utilization', 0),
            'interest_charges_present': credit.get('interest_charges_present', False),
            'minimum_payment_only': credit.get('minimum_payment_only', False),
            'is_overdue': credit.get('is_overdue', False)
        }
    
    elif persona_id == 2:
        # Variable Income - focus on income and buffer metrics
        income = features.get('income', {})
        return {
            'persona': 'Variable Income Budgeter',
            'median_pay_gap_days': income.get('median_pay_gap_days', 0),
            'cash_flow_buffer_months': income.get('cash_flow_buffer_months', 0),
            'payroll_count': income.get('payroll_count', 0),
            'avg_monthly_expenses': income.get('avg_monthly_expenses', 0)
        }
    
    elif persona_id == 3:
        # Subscription-Heavy - focus on subscription metrics
        subs = features.get('subscriptions', {})
        return {
            'persona': 'Subscription-Heavy',
            'recurring_merchant_count': subs.get('recurring_merchant_count', 0),
            'monthly_recurring_spend': subs.get('monthly_recurring_spend', 0),
            'subscription_share': subs.get('subscription_share', 0)
        }
    
    elif persona_id == 4:
        # Savings Builder - focus on savings metrics
        savings = features.get('savings', {})
        credit = features.get('credit', {})
        return {
            'persona': 'Savings Builder',
            'net_inflow': savings.get('net_inflow', 0),
            'growth_rate': savings.get('growth_rate', 0),
            'emergency_fund_coverage_months': savings.get('emergency_fund_coverage_months', 0),
            'max_utilization': credit.get('max_utilization', 0)
        }
    
    elif persona_id == 5:
        # Cash Flow Stressed - focus on cash flow metrics
        cash_flow = features.get('cash_flow', {})
        return {
            'persona': 'Cash Flow Stressed',
            'pct_days_below_100': cash_flow.get('pct_days_below_100', 0),
            'balance_volatility': cash_flow.get('balance_volatility', 0),
            'min_balance': cash_flow.get('min_balance', 0),
            'avg_balance': cash_flow.get('avg_balance', 0)
        }
    
    else:
        # Stable or unknown
        return {'persona': 'Stable'}


def build_cross_window_context(
    features_30d: Dict[str, Any],
    features_180d: Dict[str, Any],
    persona_30d_id: int,
    persona_180d_id: int
) -> Dict[str, Any]:
    """
    Build combined context when user has different personas across windows.
    
    Args:
        features_30d: Features for 30-day window
        features_180d: Features for 180-day window
        persona_30d_id: 30-day persona ID
        persona_180d_id: 180-day persona ID
    
    Returns:
        Combined context dictionary with both persona metrics
    """
    context_30d = extract_persona_specific_metrics(features_30d, persona_30d_id)
    context_180d = extract_persona_specific_metrics(features_180d, persona_180d_id)
    
    return {
        'recent_30d': context_30d,
        'long_term_180d': context_180d,
        'note': 'User shows different patterns in recent vs long-term behavior'
    }

