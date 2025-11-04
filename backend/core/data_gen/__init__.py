"""
Data generation module for SpendSense
Synthetic Plaid-style transaction data generation
"""

from .archetypes import ARCHETYPES, get_archetype_distribution
from .generator import generate_synthetic_data

__all__ = [
    'ARCHETYPES',
    'get_archetype_distribution',
    'generate_synthetic_data'
]

