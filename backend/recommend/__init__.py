"""
Recommendation Engine

Generates personalized recommendation packages with:
- Educational content from pre-built catalog
- LLM-generated rationales and actionable items
- Rules-based partner offer eligibility checking
"""

from .generator import generate_recommendation, generate_batch_recommendations
from .storage import (
    create_recommendation_tables,
    insert_recommendation,
    load_recommendation
)

__all__ = [
    'generate_recommendation',
    'generate_batch_recommendations',
    'create_recommendation_tables',
    'insert_recommendation',
    'load_recommendation'
]

