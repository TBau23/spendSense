"""
Eligibility Checker

Rules-based eligibility checking for partner offers with credit score estimation.
"""

from typing import Dict, Any, Tuple, List, Optional
import sqlite3


def estimate_credit_score(credit_features: Dict[str, Any]) -> int:
    """
    Estimate credit score from utilization and payment behavior.
    
    NOTE: This is a simplified heuristic for demo purposes only.
    Real credit scores are calculated using proprietary algorithms.
    
    Args:
        credit_features: Dictionary with credit metrics
    
    Returns:
        Estimated credit score (300-850 range)
    """
    base_score = 750
    
    # Utilization penalty (35% of credit score)
    max_util = credit_features.get('max_utilization', 0.0)
    if max_util >= 0.90:
        base_score -= 120
    elif max_util >= 0.80:
        base_score -= 100
    elif max_util >= 0.70:
        base_score -= 75
    elif max_util >= 0.50:
        base_score -= 50
    elif max_util >= 0.30:
        base_score -= 20
    
    # Payment behavior (35% of credit score)
    if credit_features.get('is_overdue', False):
        base_score -= 100  # Severe penalty for late payments
    
    if credit_features.get('minimum_payment_only', False):
        base_score -= 30  # Moderate penalty for minimum payments only
    
    # Interest charges (indicator of high utilization or late payments)
    if credit_features.get('interest_charges_present', False):
        base_score -= 10  # Mild penalty
    
    # Clamp to valid range
    return max(300, min(850, base_score))


def check_eligibility(
    user_id: str,
    offer: Dict[str, Any],
    features: Dict[str, Any],
    db_path: str
) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if user is eligible for a partner offer.
    
    Args:
        user_id: User identifier
        offer: Partner offer dictionary with eligibility_rules
        features: User's computed features (credit, income, savings, etc.)
        db_path: Path to SQLite database
    
    Returns:
        Tuple of (eligible: bool, criteria_details: dict)
    """
    rules = offer.get('eligibility_rules', {})
    
    if not rules:
        # No rules = everyone eligible
        return True, {'no_rules': True}
    
    criteria_results = {}
    
    # Credit score check
    if 'min_estimated_credit_score' in rules:
        credit_features = features.get('credit', {})
        estimated_score = estimate_credit_score(credit_features)
        min_required = rules['min_estimated_credit_score']
        
        criteria_results['estimated_credit_score'] = estimated_score
        criteria_results['min_credit_score_required'] = min_required
        criteria_results['credit_score_met'] = estimated_score >= min_required
    
    # Credit utilization checks
    if 'max_credit_utilization' in rules:
        max_util = features.get('credit', {}).get('max_utilization', 0.0)
        max_allowed = rules['max_credit_utilization']
        
        criteria_results['user_max_utilization'] = max_util
        criteria_results['max_utilization_allowed'] = max_allowed
        criteria_results['utilization_check'] = max_util <= max_allowed
    
    if 'min_credit_utilization' in rules:
        max_util = features.get('credit', {}).get('max_utilization', 0.0)
        min_required = rules['min_credit_utilization']
        
        criteria_results['user_max_utilization'] = max_util
        criteria_results['min_utilization_required'] = min_required
        criteria_results['min_utilization_met'] = max_util >= min_required
    
    # Balance/debt checks
    if 'min_credit_card_balance' in rules:
        # Estimate total balance from utilization (rough approximation)
        credit = features.get('credit', {})
        # This is a simplification - in reality we'd need actual balance data
        has_balance = credit.get('max_utilization', 0) > 0
        
        criteria_results['has_credit_card_balance'] = has_balance
        criteria_results['min_balance_required'] = rules['min_credit_card_balance']
        criteria_results['balance_check'] = has_balance
    
    # Income checks
    if 'min_monthly_income' in rules:
        income_features = features.get('income', {})
        # Estimate from payroll count and buffer
        payroll_count = income_features.get('payroll_count', 0)
        has_income = payroll_count > 0
        
        criteria_results['has_regular_income'] = has_income
        criteria_results['min_monthly_income_required'] = rules['min_monthly_income']
        criteria_results['income_check'] = has_income
    
    # Savings checks
    if 'min_savings_balance' in rules:
        savings = features.get('savings', {})
        # Use emergency fund coverage as proxy
        coverage = savings.get('emergency_fund_coverage_months', 0)
        has_savings = coverage > 0
        
        criteria_results['has_savings'] = has_savings
        criteria_results['min_savings_required'] = rules['min_savings_balance']
        criteria_results['savings_check'] = has_savings
    
    # Existing account checks
    if 'exclude_if_has_account_type' in rules:
        account_type = rules['exclude_if_has_account_type']
        has_account = _has_account_type(user_id, account_type, db_path)
        
        criteria_results['has_existing_account_type'] = account_type
        criteria_results['user_has_account'] = has_account
        criteria_results['account_check'] = not has_account  # Pass if they DON'T have it
    
    # Check for specific savings account
    if 'has_savings_account' in rules:
        required = rules['has_savings_account']
        has_savings_account = _has_account_type(user_id, 'savings', db_path)
        
        criteria_results['user_has_savings_account'] = has_savings_account
        criteria_results['savings_account_required'] = required
        criteria_results['savings_account_check'] = has_savings_account == required
    
    # Card count checks
    if 'max_existing_cards' in rules:
        card_count = _count_credit_cards(user_id, db_path)
        max_allowed = rules['max_existing_cards']
        
        criteria_results['user_card_count'] = card_count
        criteria_results['max_cards_allowed'] = max_allowed
        criteria_results['card_count_check'] = card_count <= max_allowed
    
    # Checking balance checks
    if 'min_checking_balance' in rules:
        # Use cash flow features as proxy
        cash_flow = features.get('cash_flow', {})
        avg_balance = cash_flow.get('avg_balance', 0)
        min_required = rules['min_checking_balance']
        
        criteria_results['avg_checking_balance'] = avg_balance
        criteria_results['min_balance_required'] = min_required
        criteria_results['checking_balance_check'] = avg_balance >= min_required
    
    # All criteria must pass
    check_keys = [k for k in criteria_results.keys() if k.endswith('_check') or k.endswith('_met')]
    if check_keys:
        eligible = all(criteria_results[k] for k in check_keys)
    else:
        # No checks performed = eligible
        eligible = True
    
    criteria_results['eligible'] = eligible
    criteria_results['checks_performed'] = len(check_keys)
    criteria_results['checks_passed'] = sum(1 for k in check_keys if criteria_results[k])
    
    return eligible, criteria_results


def _has_account_type(user_id: str, account_type: str, db_path: str) -> bool:
    """
    Check if user has an account of specified type.
    
    Args:
        user_id: User identifier
        account_type: Account type to check (e.g., 'savings', 'high_yield_savings')
    
    Returns:
        True if user has account of this type
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Map product types to account types
    type_mapping = {
        'high_yield_savings': 'savings',
        'checking': 'checking',
        'savings': 'savings',
        'money_market': 'money_market'
    }
    
    db_account_type = type_mapping.get(account_type, account_type)
    
    cursor.execute('''
        SELECT COUNT(*) FROM accounts
        WHERE user_id = ? AND account_type = ?
    ''', (user_id, db_account_type))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0


def _count_credit_cards(user_id: str, db_path: str) -> int:
    """
    Count number of credit cards user has.
    
    Args:
        user_id: User identifier
        db_path: Path to SQLite database
    
    Returns:
        Number of credit cards
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM accounts
        WHERE user_id = ? AND account_type = 'credit_card'
    ''', (user_id,))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count


def select_eligible_offers(
    user_id: str,
    personas: List[int],
    features: Dict[str, Any],
    db_path: str,
    max_offers: int = 2
) -> List[Dict[str, Any]]:
    """
    Select partner offers that user is eligible for.
    
    Args:
        user_id: User identifier
        personas: List of persona IDs
        features: User's computed features
        db_path: Path to SQLite database
        max_offers: Maximum number of offers to return
    
    Returns:
        List of eligible offers with eligibility details
    """
    from .storage import load_partner_offers
    
    # Load all offers
    all_offers = load_partner_offers(db_path)
    
    # Filter by persona relevance
    relevant_offers = [
        offer for offer in all_offers
        if any(p in offer.get('persona_relevance', []) for p in personas)
    ]
    
    # Check eligibility for each
    eligible_offers = []
    for offer in relevant_offers:
        is_eligible, criteria = check_eligibility(user_id, offer, features, db_path)
        
        if is_eligible:
            offer_with_eligibility = offer.copy()
            offer_with_eligibility['eligibility_passed'] = True
            offer_with_eligibility['eligibility_details'] = criteria
            eligible_offers.append(offer_with_eligibility)
    
    # Limit to max_offers
    return eligible_offers[:max_offers]


def get_eligibility_summary(
    user_id: str,
    features: Dict[str, Any],
    db_path: str
) -> Dict[str, Any]:
    """
    Get eligibility summary across all offers.
    
    Args:
        user_id: User identifier
        features: User's computed features
        db_path: Path to SQLite database
    
    Returns:
        Summary dict with estimated score, eligible offer count, etc.
    """
    from .storage import load_partner_offers
    
    # Estimate credit score
    credit_features = features.get('credit', {})
    estimated_score = estimate_credit_score(credit_features)
    
    # Check all offers
    all_offers = load_partner_offers(db_path)
    eligible_count = 0
    ineligible_reasons = []
    
    for offer in all_offers:
        is_eligible, criteria = check_eligibility(user_id, offer, features, db_path)
        if is_eligible:
            eligible_count += 1
        else:
            # Identify why ineligible
            failed_checks = [
                k for k in criteria.keys()
                if (k.endswith('_check') or k.endswith('_met')) and not criteria[k]
            ]
            if failed_checks:
                ineligible_reasons.append({
                    'offer': offer['product_name'],
                    'reasons': failed_checks
                })
    
    return {
        'estimated_credit_score': estimated_score,
        'total_offers': len(all_offers),
        'eligible_offers': eligible_count,
        'ineligible_offers': len(all_offers) - eligible_count,
        'eligibility_rate': eligible_count / len(all_offers) if all_offers else 0,
        'sample_ineligible_reasons': ineligible_reasons[:3]  # First 3 for brevity
    }

