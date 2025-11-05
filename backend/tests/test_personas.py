"""
Tests for Persona Assignment System

Tests persona evaluation logic, prioritization, and assignment workflow.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from personas.evaluators import (
    evaluate_persona_1,
    evaluate_persona_2,
    evaluate_persona_3,
    evaluate_persona_4,
    evaluate_persona_5,
    evaluate_all_personas
)
from personas.prioritize import sort_matched_personas, select_primary_and_secondary
from personas.assign import assign_personas_for_user
from personas.metadata import PERSONA_METADATA


class TestPersona1Evaluator:
    """Test Persona 1: High Utilization"""
    
    def test_high_utilization_matches(self):
        """User with 68% utilization should match Persona 1"""
        features = {
            'credit': {
                'max_utilization': 0.68,
                'interest_charges_present': False,
                'minimum_payment_only': False,
                'is_overdue': False
            }
        }
        
        matched, severity, details = evaluate_persona_1(features)
        
        assert matched is True
        assert severity == 0.68
        assert 'max_utilization' in details['triggered_by']
    
    def test_interest_charges_matches(self):
        """User with interest charges should match Persona 1"""
        features = {
            'credit': {
                'max_utilization': 0.35,
                'interest_charges_present': True,
                'minimum_payment_only': False,
                'is_overdue': False
            }
        }
        
        matched, severity, details = evaluate_persona_1(features)
        
        assert matched is True
        assert 'interest_charges' in details['triggered_by']
    
    def test_minimum_payment_only_matches(self):
        """User making only minimum payments should match Persona 1"""
        features = {
            'credit': {
                'max_utilization': 0.35,
                'interest_charges_present': False,
                'minimum_payment_only': True,
                'is_overdue': False
            }
        }
        
        matched, severity, details = evaluate_persona_1(features)
        
        assert matched is True
        assert 'minimum_payment_only' in details['triggered_by']
    
    def test_overdue_matches(self):
        """User with overdue payments should match Persona 1"""
        features = {
            'credit': {
                'max_utilization': 0.20,
                'interest_charges_present': False,
                'minimum_payment_only': False,
                'is_overdue': True
            }
        }
        
        matched, severity, details = evaluate_persona_1(features)
        
        assert matched is True
        assert 'is_overdue' in details['triggered_by']
    
    def test_low_utilization_no_issues_does_not_match(self):
        """User with low utilization and no issues should not match"""
        features = {
            'credit': {
                'max_utilization': 0.25,
                'interest_charges_present': False,
                'minimum_payment_only': False,
                'is_overdue': False
            }
        }
        
        matched, severity, details = evaluate_persona_1(features)
        
        assert matched is False


class TestPersona2Evaluator:
    """Test Persona 2: Variable Income Budgeter"""
    
    def test_variable_income_matches(self):
        """User with 60-day pay gap and 0.5 month buffer should match"""
        features = {
            'income': {
                'median_pay_gap_days': 60,
                'cash_flow_buffer_months': 0.5
            }
        }
        
        matched, severity, details = evaluate_persona_2(features)
        
        assert matched is True
        assert severity == pytest.approx(60 / 45.0, rel=0.01)
        assert len(details['triggered_by']) == 2
    
    def test_long_gap_but_good_buffer_does_not_match(self):
        """User with long pay gap but good buffer should not match"""
        features = {
            'income': {
                'median_pay_gap_days': 60,
                'cash_flow_buffer_months': 2.0
            }
        }
        
        matched, severity, details = evaluate_persona_2(features)
        
        assert matched is False
    
    def test_short_gap_does_not_match(self):
        """User with regular pay gaps should not match"""
        features = {
            'income': {
                'median_pay_gap_days': 30,
                'cash_flow_buffer_months': 0.5
            }
        }
        
        matched, severity, details = evaluate_persona_2(features)
        
        assert matched is False


class TestPersona3Evaluator:
    """Test Persona 3: Subscription-Heavy"""
    
    def test_high_spend_matches(self):
        """User with 5 merchants and $75/month should match"""
        features = {
            'subscriptions': {
                'recurring_merchant_count': 5,
                'monthly_recurring_spend': 75.0,
                'subscription_share': 0.12
            }
        }
        
        matched, severity, details = evaluate_persona_3(features)
        
        assert matched is True
        assert severity == 0.12
        assert 'recurring_merchant_count' in details['triggered_by']
        assert 'monthly_recurring_spend' in details['triggered_by']
    
    def test_high_share_matches(self):
        """User with ≥10% subscription share should match"""
        features = {
            'subscriptions': {
                'recurring_merchant_count': 4,
                'monthly_recurring_spend': 40.0,
                'subscription_share': 0.15
            }
        }
        
        matched, severity, details = evaluate_persona_3(features)
        
        assert matched is True
        assert 'subscription_share' in details['triggered_by']
    
    def test_few_merchants_does_not_match(self):
        """User with only 2 merchants should not match"""
        features = {
            'subscriptions': {
                'recurring_merchant_count': 2,
                'monthly_recurring_spend': 60.0,
                'subscription_share': 0.12
            }
        }
        
        matched, severity, details = evaluate_persona_3(features)
        
        assert matched is False
    
    def test_low_spend_and_share_does_not_match(self):
        """User with merchants but low spend/share should not match"""
        features = {
            'subscriptions': {
                'recurring_merchant_count': 4,
                'monthly_recurring_spend': 30.0,
                'subscription_share': 0.05
            }
        }
        
        matched, severity, details = evaluate_persona_3(features)
        
        assert matched is False


class TestPersona4Evaluator:
    """Test Persona 4: Savings Builder"""
    
    def test_good_growth_low_utilization_matches(self):
        """User with 3% growth and 15% utilization should match"""
        features = {
            'savings': {
                'growth_rate': 0.03,
                'net_inflow': 100.0,
                'window_days': 30
            },
            'credit': {
                'max_utilization': 0.15
            }
        }
        
        matched, severity, details = evaluate_persona_4(features)
        
        assert matched is True
        assert severity == 0.03
        assert 'growth_rate' in details['triggered_by']
    
    def test_high_inflow_no_credit_cards_matches(self):
        """User with $250/month inflow and no credit cards should match"""
        features = {
            'savings': {
                'growth_rate': 0.01,
                'net_inflow': 250.0,
                'window_days': 30
            },
            'credit': {
                'max_utilization': None  # No credit cards
            }
        }
        
        matched, severity, details = evaluate_persona_4(features)
        
        assert matched is True
        assert details['criteria']['no_credit_cards'] is True
    
    def test_high_utilization_does_not_match(self):
        """User with good savings but high utilization should not match"""
        features = {
            'savings': {
                'growth_rate': 0.05,
                'net_inflow': 300.0,
                'window_days': 30
            },
            'credit': {
                'max_utilization': 0.45
            }
        }
        
        matched, severity, details = evaluate_persona_4(features)
        
        assert matched is False
    
    def test_low_savings_does_not_match(self):
        """User with low savings and good credit should not match"""
        features = {
            'savings': {
                'growth_rate': 0.01,
                'net_inflow': 50.0,
                'window_days': 30
            },
            'credit': {
                'max_utilization': 0.15
            }
        }
        
        matched, severity, details = evaluate_persona_4(features)
        
        assert matched is False


class TestPersona5Evaluator:
    """Test Persona 5: Cash Flow Stressed"""
    
    def test_cash_flow_stressed_matches(self):
        """User with 45% low balance days and 1.2 volatility should match"""
        features = {
            'cash_flow': {
                'pct_days_below_100': 0.45,
                'balance_volatility': 1.2
            }
        }
        
        matched, severity, details = evaluate_persona_5(features)
        
        assert matched is True
        assert severity == 0.45
        assert len(details['triggered_by']) == 2
    
    def test_low_volatility_does_not_match(self):
        """User with frequent low balance but low volatility should not match"""
        features = {
            'cash_flow': {
                'pct_days_below_100': 0.40,
                'balance_volatility': 0.8
            }
        }
        
        matched, severity, details = evaluate_persona_5(features)
        
        assert matched is False
    
    def test_infrequent_low_balance_does_not_match(self):
        """User with high volatility but infrequent low balance should not match"""
        features = {
            'cash_flow': {
                'pct_days_below_100': 0.15,
                'balance_volatility': 1.5
            }
        }
        
        matched, severity, details = evaluate_persona_5(features)
        
        assert matched is False


class TestPrioritization:
    """Test prioritization and tie-breaking logic"""
    
    def test_critical_beats_high(self):
        """CRITICAL priority should beat HIGH priority"""
        personas = [
            {'persona_id': 5, 'priority': 'HIGH', 'severity': 0.50},
            {'persona_id': 1, 'priority': 'CRITICAL', 'severity': 0.60}
        ]
        
        sorted_personas = sort_matched_personas(personas)
        
        assert sorted_personas[0]['persona_id'] == 1
        assert sorted_personas[1]['persona_id'] == 5
    
    def test_severity_tie_breaking_within_same_priority(self):
        """Within same priority, higher severity should win"""
        personas = [
            {'persona_id': 2, 'priority': 'HIGH', 'severity': 1.2},
            {'persona_id': 5, 'priority': 'HIGH', 'severity': 0.45}
        ]
        
        sorted_personas = sort_matched_personas(personas)
        
        assert sorted_personas[0]['persona_id'] == 2
        assert sorted_personas[0]['severity'] > sorted_personas[1]['severity']
    
    def test_persona_id_tie_breaking_equal_severity(self):
        """With equal priority and severity, lower persona_id should win"""
        personas = [
            {'persona_id': 5, 'priority': 'HIGH', 'severity': 0.50},
            {'persona_id': 2, 'priority': 'HIGH', 'severity': 0.50}
        ]
        
        sorted_personas = sort_matched_personas(personas)
        
        assert sorted_personas[0]['persona_id'] == 2
    
    def test_select_primary_and_secondary(self):
        """Should correctly select primary and secondary personas"""
        personas = [
            {'persona_id': 1, 'priority': 'CRITICAL', 'severity': 0.68},
            {'persona_id': 3, 'priority': 'MEDIUM', 'severity': 0.12},
            {'persona_id': 5, 'priority': 'HIGH', 'severity': 0.35}
        ]
        
        sorted_personas = sort_matched_personas(personas)
        primary, secondary = select_primary_and_secondary(sorted_personas)
        
        assert primary['persona_id'] == 1
        assert secondary['persona_id'] == 5
    
    def test_select_only_primary_when_one_match(self):
        """Should return None for secondary when only one match"""
        personas = [
            {'persona_id': 4, 'priority': 'LOW', 'severity': 0.05}
        ]
        
        primary, secondary = select_primary_and_secondary(personas)
        
        assert primary['persona_id'] == 4
        assert secondary is None


class TestAssignmentWorkflow:
    """Test complete assignment workflow"""
    
    def test_stable_user_assignment(self):
        """User matching no personas should get STABLE status"""
        features = {
            'credit': {
                'max_utilization': 0.25,
                'interest_charges_present': False,
                'minimum_payment_only': False,
                'is_overdue': False
            },
            'income': {
                'median_pay_gap_days': 30,
                'cash_flow_buffer_months': 2.0
            },
            'subscriptions': {
                'recurring_merchant_count': 2,
                'monthly_recurring_spend': 30.0,
                'subscription_share': 0.05
            },
            'savings': {
                'growth_rate': 0.01,
                'net_inflow': 100.0,
                'window_days': 30
            },
            'cash_flow': {
                'pct_days_below_100': 0.10,
                'balance_volatility': 0.5
            }
        }
        
        assignment = assign_personas_for_user(
            user_id='test_user',
            window_days=30,
            as_of_date='2025-11-04',
            features=features
        )
        
        assert assignment['status'] == 'STABLE'
        assert assignment['primary'] is None
        assert assignment['secondary'] is None
    
    def test_multi_persona_assignment(self):
        """User matching multiple personas should get primary + secondary"""
        features = {
            'credit': {
                'max_utilization': 0.68,
                'interest_charges_present': True,
                'minimum_payment_only': False,
                'is_overdue': False
            },
            'income': {
                'median_pay_gap_days': 30,
                'cash_flow_buffer_months': 2.0
            },
            'subscriptions': {
                'recurring_merchant_count': 5,
                'monthly_recurring_spend': 75.0,
                'subscription_share': 0.12
            },
            'savings': {
                'growth_rate': 0.01,
                'net_inflow': 100.0,
                'window_days': 30
            },
            'cash_flow': {
                'pct_days_below_100': 0.10,
                'balance_volatility': 0.5
            }
        }
        
        assignment = assign_personas_for_user(
            user_id='test_user',
            window_days=30,
            as_of_date='2025-11-04',
            features=features
        )
        
        assert assignment['status'] == 'ASSIGNED'
        assert assignment['primary']['persona_id'] == 1  # CRITICAL priority
        assert assignment['secondary']['persona_id'] == 3  # MEDIUM priority
    
    def test_assignment_includes_trace(self):
        """Assignment should include audit trace JSON"""
        features = {
            'credit': {
                'max_utilization': 0.68,
                'interest_charges_present': False,
                'minimum_payment_only': False,
                'is_overdue': False
            },
            'income': {'median_pay_gap_days': 30, 'cash_flow_buffer_months': 2.0},
            'subscriptions': {'recurring_merchant_count': 2, 'monthly_recurring_spend': 30.0, 'subscription_share': 0.05},
            'savings': {'growth_rate': 0.01, 'net_inflow': 100.0, 'window_days': 30},
            'cash_flow': {'pct_days_below_100': 0.10, 'balance_volatility': 0.5}
        }
        
        assignment = assign_personas_for_user(
            user_id='test_user',
            window_days=30,
            as_of_date='2025-11-04',
            features=features
        )
        
        assert 'assignment_trace' in assignment
        assert assignment['assignment_trace'] is not None
        
        # Verify trace is valid JSON
        import json
        trace = json.loads(assignment['assignment_trace'])
        assert 'user_id' in trace
        assert 'evaluations' in trace
        assert 'result' in trace


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

