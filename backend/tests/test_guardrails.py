"""
Tests for Epic 5: Guardrails & Operator View

Tests consent enforcement, metrics computation, approval workflow, and traces
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path

from backend.storage.database import get_db_connection, initialize_database
from backend.storage.schemas import create_tables
from backend.guardrails.consent import (
    check_consent, get_consented_users, get_consent_status, 
    update_consent, ConsentError
)
from backend.guardrails.metrics import (
    compute_operator_metrics, get_user_metrics, get_user_list_with_status
)
from backend.recommend.approval import (
    approve_recommendation, flag_recommendation,
    get_recommendations_by_status, get_user_recommendations
)
from backend.recommend.traces import (
    generate_persona_trace, generate_content_selection_trace,
    store_trace, get_traces
)
from backend.recommend.storage import create_recommendation_tables
from backend.personas.storage import create_persona_assignments_table


@pytest.fixture
def test_db():
    """Create a temporary test database"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Initialize database with all tables
    conn = sqlite3.connect(db_path)
    create_tables(conn)
    create_recommendation_tables(db_path)
    create_persona_assignments_table(db_path)
    
    # Apply Epic 5 migrations (add status fields)
    from backend.storage.migrations import migrate_add_recommendation_status, create_decision_traces_table
    migrate_add_recommendation_status(conn)
    create_decision_traces_table(conn)
    
    conn.close()
    
    # Add test data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Insert test users (2 consented, 1 not consented)
    cursor.execute("""
        INSERT INTO users (user_id, name, consent_status)
        VALUES 
            ('user_001', 'Alice Test', 1),
            ('user_002', 'Bob Test', 1),
            ('user_003', 'Charlie Test', 0)
    """)
    
    # Insert test persona assignments
    cursor.execute("""
        INSERT INTO persona_assignments (
            assignment_id, user_id, window_days, as_of_date,
            primary_persona_id, primary_persona_name, status
        ) VALUES 
            ('pa_001', 'user_001', 30, '2025-01-01', 1, 'High Utilization', 'ASSIGNED'),
            ('pa_002', 'user_001', 180, '2025-01-01', 1, 'High Utilization', 'ASSIGNED'),
            ('pa_003', 'user_002', 30, '2025-01-01', 4, 'Savings Builder', 'ASSIGNED')
    """)
    
    # Insert test recommendations with status field
    cursor.execute("""
        INSERT INTO recommendations (
            recommendation_id, user_id, window_30d_persona_id, 
            status, generated_at
        ) VALUES 
            ('rec_001', 'user_001', 1, 'PENDING_REVIEW', '2025-01-01'),
            ('rec_002', 'user_001', 1, 'APPROVED', '2025-01-02'),
            ('rec_003', 'user_002', 4, 'PENDING_REVIEW', '2025-01-03')
    """)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.unlink(db_path)


# ==================== Consent Tests ====================

def test_check_consent_success(test_db):
    """Test that consent check passes for consented user"""
    result = check_consent('user_001', test_db)
    assert result is True


def test_check_consent_failure(test_db):
    """Test that consent check fails for non-consented user"""
    with pytest.raises(ConsentError) as exc_info:
        check_consent('user_003', test_db)
    assert 'has not consented' in str(exc_info.value)


def test_get_consented_users(test_db):
    """Test that only consented users are returned"""
    users = get_consented_users(test_db)
    assert len(users) == 2
    user_ids = [u['user_id'] for u in users]
    assert 'user_001' in user_ids
    assert 'user_002' in user_ids
    assert 'user_003' not in user_ids


def test_get_consent_status(test_db):
    """Test getting consent status for users"""
    assert get_consent_status('user_001', test_db) is True
    assert get_consent_status('user_003', test_db) is False
    assert get_consent_status('nonexistent', test_db) is None


def test_update_consent(test_db):
    """Test updating consent status"""
    # Revoke consent
    update_consent('user_001', False, test_db)
    assert get_consent_status('user_001', test_db) is False
    
    # Grant consent
    update_consent('user_001', True, test_db)
    assert get_consent_status('user_001', test_db) is True


# ==================== Metrics Tests ====================

def test_compute_operator_metrics(test_db):
    """Test aggregate metrics computation"""
    metrics = compute_operator_metrics(test_db)
    
    assert metrics['total_consented_users'] == 2
    assert metrics['total_recommendations_generated'] == 3
    assert metrics['pending_count'] == 2
    assert metrics['approved_count'] == 1
    assert metrics['flagged_count'] == 0
    assert 'approval_rate' in metrics
    assert 'coverage_pct' in metrics


def test_get_user_metrics(test_db):
    """Test per-user metrics computation"""
    metrics = get_user_metrics('user_001', test_db)
    
    assert metrics['user_id'] == 'user_001'
    assert 'personas' in metrics
    assert 'accounts' in metrics
    assert 'recommendations' in metrics
    
    # Check persona data
    assert metrics['personas']['window_30d'] is not None
    assert metrics['personas']['window_30d']['primary_persona_id'] == 1
    
    # Check recommendation counts
    assert metrics['recommendations']['total_generated'] == 2
    assert metrics['recommendations']['pending'] == 1
    assert metrics['recommendations']['approved'] == 1


def test_get_user_list_with_status(test_db):
    """Test user list with filtering"""
    # All users
    users = get_user_list_with_status(test_db)
    assert len(users) == 2
    
    # Filter by persona
    users = get_user_list_with_status(test_db, persona_filter=1)
    assert len(users) == 1
    assert users[0]['user_id'] == 'user_001'
    
    # Filter by status
    users = get_user_list_with_status(test_db, status_filter='APPROVED')
    assert len(users) == 1


# ==================== Approval Tests ====================

def test_approve_recommendation(test_db):
    """Test approving a recommendation"""
    result = approve_recommendation('rec_001', test_db, reviewer_notes='Looks good')
    
    assert result['recommendation_id'] == 'rec_001'
    assert result['status'] == 'APPROVED'
    assert result['reviewer_notes'] == 'Looks good'
    assert result['reviewed_at'] is not None


def test_flag_recommendation(test_db):
    """Test flagging a recommendation"""
    result = flag_recommendation('rec_003', test_db, reviewer_notes='Problematic content')
    
    assert result['recommendation_id'] == 'rec_003'
    assert result['status'] == 'FLAGGED'
    assert result['reviewer_notes'] == 'Problematic content'


def test_flag_without_notes_fails(test_db):
    """Test that flagging without notes raises error"""
    with pytest.raises(ValueError) as exc_info:
        flag_recommendation('rec_001', test_db, reviewer_notes='')
    assert 'required' in str(exc_info.value).lower()


def test_get_recommendations_by_status(test_db):
    """Test filtering recommendations by status"""
    pending = get_recommendations_by_status('PENDING_REVIEW', test_db)
    assert len(pending) == 2
    
    approved = get_recommendations_by_status('APPROVED', test_db)
    assert len(approved) == 1


def test_get_user_recommendations(test_db):
    """Test getting all recommendations for a user"""
    recs = get_user_recommendations('user_001', test_db)
    assert len(recs) == 2
    
    # Filter by status
    pending = get_user_recommendations('user_001', test_db, status='PENDING_REVIEW')
    assert len(pending) == 1


# ==================== Trace Tests ====================

def test_generate_persona_trace(test_db):
    """Test generating persona assignment trace"""
    assignment = {
        'primary_persona_id': 1,
        'primary_persona_name': 'High Utilization',
        'status': 'ASSIGNED',
        'assignment_trace': '{"criteria_met": {"utilization": 0.68}}'
    }
    
    trace = generate_persona_trace('user_001', 30, assignment, test_db)
    
    assert trace['trace_type'] == 'persona_assignment'
    assert trace['user_id'] == 'user_001'
    assert trace['window_days'] == 30
    assert trace['primary_persona_id'] == 1
    assert 'rationale' in trace


def test_generate_content_selection_trace(test_db):
    """Test generating content selection trace"""
    recommendation = {
        'recommendation_id': 'rec_test',
        'target_personas': '[1]'
    }
    
    educational_items = [
        {'content_id': 'edu_001', 'title': 'Test Content', 'persona_tags': [1]}
    ]
    
    partner_offers = [
        {
            'offer_id': 'offer_001',
            'offer_title': 'Test Offer',
            'eligibility_passed': True,
            'eligibility_details': '{}'
        }
    ]
    
    trace = generate_content_selection_trace(recommendation, educational_items, partner_offers)
    
    assert trace['trace_type'] == 'content_selection'
    assert trace['recommendation_id'] == 'rec_test'
    assert len(trace['educational_items']) == 1
    assert len(trace['partner_offers']) == 1


def test_store_and_retrieve_traces(test_db):
    """Test storing and retrieving traces"""
    trace = {
        'user_id': 'user_001',
        'recommendation_id': 'rec_001',
        'trace_type': 'persona_assignment',
        'window_days': 30,
        'rationale': 'Test trace'
    }
    
    trace_id = store_trace(trace, test_db)
    assert trace_id is not None
    assert trace_id.startswith('trace_')
    
    # Retrieve traces
    traces = get_traces('user_001', test_db)
    assert len(traces) >= 1
    
    # Filter by recommendation
    traces = get_traces('user_001', test_db, recommendation_id='rec_001')
    assert len(traces) >= 1


# ==================== Integration Tests ====================

def test_end_to_end_approval_workflow(test_db):
    """Test complete approval workflow"""
    rec_id = 'rec_001'
    
    # Initial status
    recs = get_recommendations_by_status('PENDING_REVIEW', test_db)
    initial_pending = len(recs)
    
    # Approve recommendation
    approve_recommendation(rec_id, test_db, reviewer_notes='Approved in test')
    
    # Verify status changed
    recs = get_recommendations_by_status('PENDING_REVIEW', test_db)
    assert len(recs) == initial_pending - 1
    
    recs = get_recommendations_by_status('APPROVED', test_db)
    assert any(r['recommendation_id'] == rec_id for r in recs)


def test_metrics_cache(test_db):
    """Test that metrics caching works"""
    # First call
    metrics1 = compute_operator_metrics(test_db)
    
    # Second call (should use cache)
    metrics2 = compute_operator_metrics(test_db)
    
    # Should be identical
    assert metrics1['total_consented_users'] == metrics2['total_consented_users']
    
    # Force refresh
    metrics3 = compute_operator_metrics(test_db, force_refresh=True)
    assert metrics3 is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

