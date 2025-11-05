/**
 * RecommendationCard Component
 * 
 * Displays single recommendation with educational items, actionable items, and partner offers
 */

import React, { useState } from 'react';
import ApprovalActions from './ApprovalActions';
import UserSnapshot from './UserSnapshot';

const RecommendationCard = ({ recommendation, onUpdate }) => {
  const [expanded, setExpanded] = useState(false);

  const getStatusColor = (status) => {
    const colors = {
      'PENDING_REVIEW': 'yellow',
      'APPROVED': 'green',
      'FLAGGED': 'red'
    };
    return colors[status] || 'gray';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className={`recommendation-card status-${getStatusColor(recommendation.status)}`}>
      {/* Card Header */}
      <div className="card-header" onClick={() => setExpanded(!expanded)}>
        <div className="card-title">
          <span className={`status-badge ${getStatusColor(recommendation.status)}`}>
            {recommendation.status.replace('_', ' ')}
          </span>
          <span className="card-date">Generated: {formatDate(recommendation.generated_at)}</span>
        </div>
        <button className="expand-btn">{expanded ? '▼' : '▶'}</button>
      </div>

      {/* Card Content */}
      {expanded && (
        <div className="card-content">
          {/* User Snapshot */}
          {recommendation.user_snapshot && (
            <UserSnapshot snapshot={recommendation.user_snapshot} />
          )}

          {/* Educational Items */}
          {recommendation.educational_items && recommendation.educational_items.length > 0 && (
            <div className="content-section">
              <h4>Educational Content ({recommendation.educational_items.length})</h4>
              {recommendation.educational_items.map((item, idx) => (
                <div key={idx} className="content-item educational">
                  <h5>{item.content_title}</h5>
                  {item.content_snippet && <p className="snippet">{item.content_snippet}</p>}
                </div>
              ))}
            </div>
          )}

          {/* Actionable Items */}
          {recommendation.actionable_items && recommendation.actionable_items.length > 0 && (
            <div className="content-section">
              <h4>Actionable Items ({recommendation.actionable_items.length})</h4>
              {recommendation.actionable_items.map((item, idx) => (
                <div key={idx} className="content-item actionable">
                  <p className="action-text">✓ {item.action_text}</p>
                  {item.action_rationale && (
                    <p className="rationale"><strong>Because:</strong> {item.action_rationale}</p>
                  )}
                  {item.data_cited && (
                    <details className="data-cited">
                      <summary>Data Cited</summary>
                      <pre>{JSON.stringify(JSON.parse(item.data_cited), null, 2)}</pre>
                    </details>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Partner Offers */}
          {recommendation.partner_offers && recommendation.partner_offers.length > 0 && (
            <div className="content-section">
              <h4>Partner Offers ({recommendation.partner_offers.length})</h4>
              {recommendation.partner_offers.map((item, idx) => (
                <div key={idx} className="content-item partner-offer">
                  <h5>{item.offer_title}</h5>
                  <p>{item.offer_description}</p>
                  {item.why_relevant && (
                    <p className="rationale"><strong>Why relevant:</strong> {item.why_relevant}</p>
                  )}
                  <p className={`eligibility ${item.eligibility_passed ? 'passed' : 'failed'}`}>
                    Eligibility: {item.eligibility_passed ? '✓ Passed' : '✗ Failed'}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Reviewer Notes */}
          {recommendation.reviewer_notes && (
            <div className="reviewer-notes">
              <h4>Reviewer Notes</h4>
              <p>{recommendation.reviewer_notes}</p>
            </div>
          )}

          {/* Approval Actions (only for pending) */}
          {recommendation.status === 'PENDING_REVIEW' && (
            <ApprovalActions 
              recommendationId={recommendation.recommendation_id} 
              onUpdate={onUpdate}
            />
          )}
        </div>
      )}
    </div>
  );
};

export default RecommendationCard;

