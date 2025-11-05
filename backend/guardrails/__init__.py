"""
Guardrails Module

Epic 5: Consent enforcement, metrics computation, and operator controls
"""

from .consent import check_consent, get_consented_users, ConsentError
from .metrics import compute_operator_metrics, get_user_metrics

__all__ = [
    'check_consent',
    'get_consented_users',
    'ConsentError',
    'compute_operator_metrics',
    'get_user_metrics'
]

