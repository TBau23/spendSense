"""
Persona Assignment Module

This module handles persona assignment logic based on behavioral signals
from the feature engineering pipeline.
"""

from .metadata import PERSONA_METADATA, get_persona_info
from .evaluators import (
    evaluate_persona_1,
    evaluate_persona_2,
    evaluate_persona_3,
    evaluate_persona_4,
    evaluate_persona_5,
    evaluate_all_personas
)
from .prioritize import sort_matched_personas
from .assign import assign_personas_for_user, assign_all_personas
from .trace import generate_assignment_trace

__all__ = [
    'PERSONA_METADATA',
    'get_persona_info',
    'evaluate_persona_1',
    'evaluate_persona_2',
    'evaluate_persona_3',
    'evaluate_persona_4',
    'evaluate_persona_5',
    'evaluate_all_personas',
    'sort_matched_personas',
    'assign_personas_for_user',
    'assign_all_personas',
    'generate_assignment_trace',
]

