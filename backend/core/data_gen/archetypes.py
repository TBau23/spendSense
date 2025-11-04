"""
User archetype definitions for SpendSense
Defines financial behavior patterns that trigger each of the 5 personas
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class Archetype:
    """Defines a user archetype with expected financial behaviors"""
    name: str
    persona_target: str  # Which persona should this trigger
    income_range: tuple  # (min, max) monthly income
    credit_card_count: int
    credit_utilization_target: float  # 0.0 to 1.0
    has_savings_account: bool
    savings_behavior: str  # "none", "minimal", "consistent", "aggressive"
    subscription_count: int
    payment_behavior: str  # "full", "minimum", "mixed"
    payroll_frequency: str  # "biweekly", "monthly", "irregular"
    payroll_variability: float  # 0.0 to 1.0 (higher = more variable)
    starting_checking_balance: float
    checking_balance_volatility: str  # "low", "medium", "high"
    target_low_balance_days_pct: float  # For Cash Flow Stressed
    description: str
    
    
# Core archetypes matching the 5 personas
ARCHETYPES: Dict[str, Archetype] = {
    "high_utilizer": Archetype(
        name="High Utilizer",
        persona_target="Persona 1: High Utilization",
        income_range=(3000, 5000),
        credit_card_count=2,
        credit_utilization_target=0.65,  # 65% utilization
        has_savings_account=False,
        savings_behavior="none",
        subscription_count=4,
        payment_behavior="minimum",  # Often makes minimum payments
        payroll_frequency="biweekly",
        payroll_variability=0.1,
        starting_checking_balance=500,
        checking_balance_volatility="medium",
        target_low_balance_days_pct=0.15,
        description="High credit utilization, minimum payments, struggling with debt"
    ),
    
    "variable_income": Archetype(
        name="Variable Income Budgeter",
        persona_target="Persona 2: Variable Income",
        income_range=(2500, 6000),  # Wide range
        credit_card_count=1,
        credit_utilization_target=0.25,  # Low utilization
        has_savings_account=True,
        savings_behavior="minimal",
        subscription_count=3,
        payment_behavior="full",
        payroll_frequency="irregular",  # Key characteristic
        payroll_variability=0.8,  # High variability, gaps >45 days
        starting_checking_balance=800,
        checking_balance_volatility="high",
        target_low_balance_days_pct=0.20,
        description="Irregular income, gaps >45 days, low cash buffer"
    ),
    
    "subscription_heavy": Archetype(
        name="Subscription Heavy",
        persona_target="Persona 3: Subscription Heavy",
        income_range=(4000, 7000),
        credit_card_count=1,
        credit_utilization_target=0.20,
        has_savings_account=True,
        savings_behavior="consistent",
        subscription_count=8,  # Many subscriptions
        payment_behavior="full",
        payroll_frequency="biweekly",
        payroll_variability=0.1,
        starting_checking_balance=2000,
        checking_balance_volatility="low",
        target_low_balance_days_pct=0.05,
        description="Many recurring subscriptions, otherwise stable finances"
    ),
    
    "savings_builder": Archetype(
        name="Savings Builder",
        persona_target="Persona 4: Savings Builder",
        income_range=(5000, 8000),
        credit_card_count=1,
        credit_utilization_target=0.15,  # Low utilization
        has_savings_account=True,
        savings_behavior="aggressive",  # Consistent transfers
        subscription_count=4,
        payment_behavior="full",
        payroll_frequency="biweekly",
        payroll_variability=0.05,
        starting_checking_balance=3000,
        checking_balance_volatility="low",
        target_low_balance_days_pct=0.02,
        description="Consistent savings growth, low utilization, positive trajectory"
    ),
    
    "cash_flow_stressed": Archetype(
        name="Cash Flow Stressed",
        persona_target="Persona 5: Cash Flow Stressed",
        income_range=(2800, 4000),
        credit_card_count=0,  # May not have credit
        credit_utilization_target=0.0,
        has_savings_account=False,
        savings_behavior="none",
        subscription_count=2,
        payment_behavior="full",  # Not about credit, about cash flow
        payroll_frequency="biweekly",
        payroll_variability=0.1,
        starting_checking_balance=150,  # Low starting balance
        checking_balance_volatility="high",  # Key characteristic
        target_low_balance_days_pct=0.35,  # >30% of days <$100
        description="Living paycheck to paycheck, balance frequently <$100, high volatility"
    ),
    
    # Multi-persona combinations
    "high_util_cash_stressed": Archetype(
        name="High Utilization + Cash Flow Stressed",
        persona_target="Multiple",
        income_range=(3000, 4000),
        credit_card_count=2,
        credit_utilization_target=0.75,
        has_savings_account=False,
        savings_behavior="none",
        subscription_count=3,
        payment_behavior="minimum",
        payroll_frequency="biweekly",
        payroll_variability=0.2,
        starting_checking_balance=80,
        checking_balance_volatility="high",
        target_low_balance_days_pct=0.40,
        description="High credit utilization AND cash flow stress - compound issues"
    ),
    
    "variable_income_subscriptions": Archetype(
        name="Variable Income + Subscription Heavy",
        persona_target="Multiple",
        income_range=(3500, 6000),
        credit_card_count=1,
        credit_utilization_target=0.30,
        has_savings_account=True,
        savings_behavior="minimal",
        subscription_count=7,
        payment_behavior="full",
        payroll_frequency="irregular",
        payroll_variability=0.7,
        starting_checking_balance=1200,
        checking_balance_volatility="medium",
        target_low_balance_days_pct=0.18,
        description="Variable income with many subscriptions - timing issues"
    ),
    
    # Stable/control group
    "stable_finances": Archetype(
        name="Stable Finances",
        persona_target="None",
        income_range=(5000, 7000),
        credit_card_count=1,
        credit_utilization_target=0.10,
        has_savings_account=True,
        savings_behavior="consistent",
        subscription_count=4,
        payment_behavior="full",
        payroll_frequency="biweekly",
        payroll_variability=0.05,
        starting_checking_balance=3500,
        checking_balance_volatility="low",
        target_low_balance_days_pct=0.01,
        description="Stable finances, no immediate issues - control group"
    ),
    
    # Edge cases
    "edge_high_util_threshold": Archetype(
        name="Edge: Exactly 50% Utilization",
        persona_target="Persona 1 (threshold)",
        income_range=(4000, 5000),
        credit_card_count=1,
        credit_utilization_target=0.50,  # Exactly at threshold
        has_savings_account=True,
        savings_behavior="minimal",
        subscription_count=3,
        payment_behavior="mixed",
        payroll_frequency="biweekly",
        payroll_variability=0.1,
        starting_checking_balance=1500,
        checking_balance_volatility="low",
        target_low_balance_days_pct=0.08,
        description="Edge case: exactly at 50% utilization threshold"
    ),
    
    "edge_subscription_threshold": Archetype(
        name="Edge: Exactly 3 Subscriptions",
        persona_target="Persona 3 (threshold)",
        income_range=(4500, 6000),
        credit_card_count=1,
        credit_utilization_target=0.15,
        has_savings_account=True,
        savings_behavior="consistent",
        subscription_count=3,  # Exactly at threshold
        payment_behavior="full",
        payroll_frequency="biweekly",
        payroll_variability=0.1,
        starting_checking_balance=2500,
        checking_balance_volatility="low",
        target_low_balance_days_pct=0.03,
        description="Edge case: exactly 3 recurring merchants"
    ),
    
    "edge_cash_flow_threshold": Archetype(
        name="Edge: Exactly 30% Low Balance Days",
        persona_target="Persona 5 (threshold)",
        income_range=(3500, 4500),
        credit_card_count=1,
        credit_utilization_target=0.20,
        has_savings_account=True,
        savings_behavior="minimal",
        subscription_count=3,
        payment_behavior="full",
        payroll_frequency="biweekly",
        payroll_variability=0.15,
        starting_checking_balance=200,
        checking_balance_volatility="medium",
        target_low_balance_days_pct=0.30,  # Exactly at threshold
        description="Edge case: exactly 30% of days with balance <$100"
    ),
    
    "edge_no_transactions": Archetype(
        name="Edge: Minimal Activity",
        persona_target="None",
        income_range=(3000, 4000),
        credit_card_count=0,
        credit_utilization_target=0.0,
        has_savings_account=False,
        savings_behavior="none",
        subscription_count=0,
        payment_behavior="full",
        payroll_frequency="monthly",
        payroll_variability=0.05,
        starting_checking_balance=1000,
        checking_balance_volatility="low",
        target_low_balance_days_pct=0.05,
        description="Edge case: minimal transaction activity"
    ),
    
    "edge_no_credit": Archetype(
        name="Edge: Cash-Only User",
        persona_target="None",
        income_range=(4000, 5000),
        credit_card_count=0,
        credit_utilization_target=0.0,
        has_savings_account=True,
        savings_behavior="consistent",
        subscription_count=3,
        payment_behavior="full",
        payroll_frequency="biweekly",
        payroll_variability=0.1,
        starting_checking_balance=2000,
        checking_balance_volatility="low",
        target_low_balance_days_pct=0.04,
        description="Edge case: no credit cards, cash-only transactions"
    ),
}


def get_archetype_distribution(total_users: int) -> Dict[str, int]:
    """
    Calculate archetype distribution for a given number of users
    
    Args:
        total_users: Total number of users to generate
        
    Returns:
        Dictionary mapping archetype name to count
    """
    # Target proportions from technical design
    proportions = {
        "high_utilizer": 0.24,              # 18/75
        "variable_income": 0.16,             # 12/75
        "subscription_heavy": 0.16,          # 12/75
        "savings_builder": 0.16,             # 12/75
        "cash_flow_stressed": 0.13,          # 10/75
        "high_util_cash_stressed": 0.05,     # 4/75 (part of multi-persona)
        "variable_income_subscriptions": 0.05,  # 4/75 (part of multi-persona)
        "stable_finances": 0.08,             # 6/75
        "edge_high_util_threshold": 0.02,    # 2/75
        "edge_subscription_threshold": 0.02, # 2/75
        "edge_cash_flow_threshold": 0.02,    # 2/75
        "edge_no_transactions": 0.01,        # 1/75
        "edge_no_credit": 0.01,              # 1/75
    }
    
    distribution = {}
    allocated = 0
    
    for archetype, proportion in proportions.items():
        count = max(1, int(total_users * proportion))  # Ensure at least 1
        distribution[archetype] = count
        allocated += count
    
    # Adjust the largest category if needed to match total
    if allocated != total_users:
        diff = total_users - allocated
        largest = max(distribution, key=distribution.get)
        distribution[largest] += diff
    
    return distribution


def get_archetype_by_name(name: str) -> Archetype:
    """
    Get an archetype by name
    
    Args:
        name: Archetype name
        
    Returns:
        Archetype object
        
    Raises:
        KeyError: If archetype name not found
    """
    return ARCHETYPES[name]

