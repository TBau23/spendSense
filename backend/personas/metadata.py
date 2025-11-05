"""
Persona Metadata

Defines all persona properties including names, priorities, focus areas, and risks.
Used throughout the system for persona lookup and recommendation mapping.
"""

PERSONA_METADATA = {
    1: {
        "name": "High Utilization",
        "priority": "CRITICAL",
        "focus": "Reduce utilization and interest; payment planning and autopay education",
        "risk": "Debt spiral, credit damage, high interest charges",
        "criteria_summary": "Utilization ≥50% OR interest charges OR minimum payment only OR overdue"
    },
    2: {
        "name": "Variable Income Budgeter",
        "priority": "HIGH",
        "focus": "Percent-based budgets, emergency fund basics, smoothing strategies",
        "risk": "Income uncertainty plus low buffer leads to payment timing issues",
        "criteria_summary": "Median pay gap >45 days AND cash-flow buffer <1 month"
    },
    3: {
        "name": "Subscription-Heavy",
        "priority": "MEDIUM",
        "focus": "Subscription audit, cancellation/negotiation tips, bill alerts",
        "risk": "Money leak, optimization opportunity",
        "criteria_summary": "≥3 recurring merchants AND (monthly spend ≥$50 OR subscription share ≥10%)"
    },
    4: {
        "name": "Savings Builder",
        "priority": "LOW",
        "focus": "Goal setting, automation, APY optimization (HYSA/CD basics)",
        "risk": "None - positive trajectory, enrichment only",
        "criteria_summary": "(Growth rate ≥2% OR net inflow ≥$200/month) AND all cards <30% utilization"
    },
    5: {
        "name": "Cash Flow Stressed",
        "priority": "HIGH",
        "focus": "Paycheck-to-paycheck budgeting, buffer building, expense smoothing, timing strategies",
        "risk": "Overdraft risk, immediate liquidity crisis",
        "criteria_summary": "≥30% days with balance <$100 AND balance volatility >1.0"
    }
}

# Priority order for sorting (lower number = higher priority)
PRIORITY_ORDER = {
    'CRITICAL': 0,
    'HIGH': 1,
    'MEDIUM': 2,
    'LOW': 3
}


def get_persona_info(persona_id):
    """
    Get metadata for a specific persona.
    
    Args:
        persona_id: Integer from 1-5
        
    Returns:
        Dict with persona metadata, or None if invalid ID
    """
    return PERSONA_METADATA.get(persona_id)


def get_all_persona_ids():
    """Get list of all valid persona IDs"""
    return list(PERSONA_METADATA.keys())


def get_persona_name(persona_id):
    """Get persona name by ID"""
    info = get_persona_info(persona_id)
    return info['name'] if info else None


def get_persona_priority(persona_id):
    """Get persona priority level by ID"""
    info = get_persona_info(persona_id)
    return info['priority'] if info else None

