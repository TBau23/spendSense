"""
Persona Evaluators

Functions to evaluate whether a user matches each persona's criteria
and compute severity scores for prioritization.
"""

from typing import Dict, Tuple, List
from .metadata import PERSONA_METADATA


def evaluate_persona_1(features: Dict) -> Tuple[bool, float, Dict]:
    """
    Persona 1: High Utilization
    
    Criteria (ANY of):
    - Any card utilization ≥50%
    - Interest charges present
    - Minimum-payment-only detected
    - Any card overdue
    
    Args:
        features: Dict containing credit features
        
    Returns:
        (matched: bool, severity: float, details: dict)
    """
    credit = features.get('credit', {})
    
    max_util = credit.get('max_utilization', 0.0)
    interest_charges = credit.get('interest_charges_present', False)
    min_payment_only = credit.get('minimum_payment_only', False)
    is_overdue = credit.get('is_overdue', False)
    
    # Check criteria (ANY condition triggers match)
    triggers = []
    if max_util is not None and max_util >= 0.50:
        triggers.append('max_utilization')
    if interest_charges:
        triggers.append('interest_charges')
    if min_payment_only:
        triggers.append('minimum_payment_only')
    if is_overdue:
        triggers.append('is_overdue')
    
    matched = len(triggers) > 0
    
    # Severity = max utilization (higher = worse)
    severity = max_util if max_util is not None else 0.0
    
    details = {
        'criteria': {
            'max_utilization': max_util,
            'threshold': 0.50,
            'interest_charges': interest_charges,
            'minimum_payment_only': min_payment_only,
            'is_overdue': is_overdue
        },
        'triggered_by': triggers
    }
    
    return matched, severity, details


def evaluate_persona_2(features: Dict) -> Tuple[bool, float, Dict]:
    """
    Persona 2: Variable Income Budgeter
    
    Criteria (ALL of):
    - Median pay gap > 45 days
    - Cash-flow buffer < 1 month
    
    Args:
        features: Dict containing income features
        
    Returns:
        (matched: bool, severity: float, details: dict)
    """
    income = features.get('income', {})
    
    median_pay_gap = income.get('median_pay_gap_days', 0.0)
    cash_flow_buffer = income.get('cash_flow_buffer_months', float('inf'))
    
    # Check criteria (ALL conditions must be true)
    pay_gap_ok = median_pay_gap > 45
    buffer_low = cash_flow_buffer < 1.0
    
    matched = pay_gap_ok and buffer_low
    
    # Severity = normalized pay gap (higher = worse)
    severity = median_pay_gap / 45.0 if matched else 0.0
    
    triggers = []
    if matched:
        triggers = ['median_pay_gap_days', 'cash_flow_buffer_months']
    
    details = {
        'criteria': {
            'median_pay_gap_days': median_pay_gap,
            'threshold_pay_gap': 45,
            'cash_flow_buffer_months': cash_flow_buffer,
            'threshold_buffer': 1.0
        },
        'triggered_by': triggers
    }
    
    return matched, severity, details


def evaluate_persona_3(features: Dict) -> Tuple[bool, float, Dict]:
    """
    Persona 3: Subscription-Heavy
    
    Criteria (ALL of):
    - Recurring merchants ≥3
    - At least ONE of:
      - Monthly recurring spend ≥$50 (in 30d window)
      - Subscription spend share ≥10%
    
    Args:
        features: Dict containing subscription features
        
    Returns:
        (matched: bool, severity: float, details: dict)
    """
    subscriptions = features.get('subscriptions', {})
    
    recurring_count = subscriptions.get('recurring_merchant_count', 0)
    monthly_spend = subscriptions.get('monthly_recurring_spend', 0.0)
    sub_share = subscriptions.get('subscription_share', 0.0)
    
    # Check criteria
    has_merchants = recurring_count >= 3
    spend_high = monthly_spend >= 50.0
    share_high = sub_share >= 0.10
    
    matched = has_merchants and (spend_high or share_high)
    
    # Severity = subscription share (higher = worse)
    severity = sub_share if matched else 0.0
    
    triggers = []
    if matched:
        triggers.append('recurring_merchant_count')
        if spend_high:
            triggers.append('monthly_recurring_spend')
        if share_high:
            triggers.append('subscription_share')
    
    details = {
        'criteria': {
            'recurring_merchant_count': recurring_count,
            'threshold_count': 3,
            'monthly_recurring_spend': monthly_spend,
            'threshold_spend': 50.0,
            'subscription_share': sub_share,
            'threshold_share': 0.10
        },
        'triggered_by': triggers
    }
    
    return matched, severity, details


def evaluate_persona_4(features: Dict) -> Tuple[bool, float, Dict]:
    """
    Persona 4: Savings Builder
    
    Criteria (ALL of):
    - (Savings growth rate ≥2% over window OR net savings inflow ≥$200/month)
    - ALL card utilizations < 30% (or no credit cards)
    
    Args:
        features: Dict containing savings and credit features
        
    Returns:
        (matched: bool, severity: float, details: dict)
    """
    savings = features.get('savings', {})
    credit = features.get('credit', {})
    
    # Savings criteria
    growth_rate = savings.get('growth_rate', 0.0)
    net_inflow = savings.get('net_inflow', 0.0)
    window_days = savings.get('window_days', 30)
    net_inflow_monthly = net_inflow / (window_days / 30.0) if window_days > 0 else 0.0
    
    savings_ok = (growth_rate >= 0.02) or (net_inflow_monthly >= 200.0)
    
    # Credit criteria - NULL/None means no credit cards (auto-pass)
    max_util = credit.get('max_utilization')
    credit_ok = (max_util is None) or (max_util < 0.30)
    
    matched = savings_ok and credit_ok
    
    # Severity = growth rate (higher = better, but still used for tie-breaking)
    severity = growth_rate if matched else 0.0
    
    triggers = []
    if matched:
        if growth_rate >= 0.02:
            triggers.append('growth_rate')
        if net_inflow_monthly >= 200.0:
            triggers.append('net_inflow')
        triggers.append('max_utilization_ok')
    
    details = {
        'criteria': {
            'growth_rate': growth_rate,
            'threshold_growth': 0.02,
            'net_inflow_monthly': net_inflow_monthly,
            'threshold_inflow': 200.0,
            'max_utilization': max_util,
            'threshold_utilization': 0.30,
            'no_credit_cards': max_util is None
        },
        'triggered_by': triggers
    }
    
    return matched, severity, details


def evaluate_persona_5(features: Dict) -> Tuple[bool, float, Dict]:
    """
    Persona 5: Cash Flow Stressed
    
    Criteria (ALL of):
    - Checking balance <$100 on ≥20% of days in window (adjusted from 30%)
    - Balance volatility > 0.15 (adjusted from 1.0 for low-balance accounts)
    
    Args:
        features: Dict containing cash_flow features
        
    Returns:
        (matched: bool, severity: float, details: dict)
    """
    cash_flow = features.get('cash_flow', {})
    
    pct_days_below = cash_flow.get('pct_days_below_100', 0.0)
    balance_volatility = cash_flow.get('balance_volatility', 0.0)
    
    # Check criteria (ALL conditions must be true)
    low_balance_frequent = pct_days_below >= 0.20  # Lowered from 0.30 to 0.20
    volatility_high = balance_volatility > 0.15  # Lowered from 1.0 to 0.15
    
    matched = low_balance_frequent and volatility_high
    
    # Severity = % days below threshold (higher = worse)
    severity = pct_days_below if matched else 0.0
    
    triggers = []
    if matched:
        triggers = ['pct_days_below_100', 'balance_volatility']
    
    details = {
        'criteria': {
            'pct_days_below_100': pct_days_below,
            'threshold_pct': 0.20,  # Updated from 0.30 to 0.20
            'balance_volatility': balance_volatility,
            'threshold_volatility': 0.15  # Updated threshold
        },
        'triggered_by': triggers
    }
    
    return matched, severity, details


def evaluate_all_personas(features: Dict) -> List[Dict]:
    """
    Evaluate all 5 personas for given features.
    
    Args:
        features: Dict containing all feature types (subscriptions, savings, credit, income, cash_flow)
        
    Returns:
        List of dicts for matched personas with structure:
        {
            'persona_id': int,
            'persona_name': str,
            'priority': str,
            'severity': float,
            'details': dict
        }
    """
    matched_personas = []
    
    # Evaluate each persona
    evaluators = [
        (1, evaluate_persona_1),
        (2, evaluate_persona_2),
        (3, evaluate_persona_3),
        (4, evaluate_persona_4),
        (5, evaluate_persona_5),
    ]
    
    for persona_id, evaluator_func in evaluators:
        matched, severity, details = evaluator_func(features)
        
        if matched:
            persona_info = PERSONA_METADATA[persona_id]
            matched_personas.append({
                'persona_id': persona_id,
                'persona_name': persona_info['name'],
                'priority': persona_info['priority'],
                'severity': severity,
                'details': details
            })
    
    return matched_personas

