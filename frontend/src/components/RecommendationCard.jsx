/**
 * RecommendationCard Component
 * 
 * Displays single recommendation with educational items, actionable items, and partner offers
 * in a modern grid layout with carousels
 */

import React, { useState } from 'react';
import ApprovalActions from './ApprovalActions';
import UserSnapshot from './UserSnapshot';

// Carousel component for cycling through items
const ItemCarousel = ({ items, renderItem }) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  if (!items || items.length === 0) return null;

  const goToNext = () => {
    setCurrentIndex((prev) => (prev + 1) % items.length);
  };

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev - 1 + items.length) % items.length);
  };

  return (
    <div className="carousel-container">
      <div className="carousel-content">
        {renderItem(items[currentIndex], currentIndex)}
      </div>
      
      {items.length > 1 && (
        <div className="carousel-controls">
          <button onClick={goToPrevious} className="carousel-btn" aria-label="Previous">
            ‹
          </button>
          <div className="carousel-indicators">
            {items.map((_, idx) => (
              <button
                key={idx}
                className={`indicator ${idx === currentIndex ? 'active' : ''}`}
                onClick={() => setCurrentIndex(idx)}
                aria-label={`Go to item ${idx + 1}`}
              />
            ))}
          </div>
          <button onClick={goToNext} className="carousel-btn" aria-label="Next">
            ›
          </button>
        </div>
      )}
    </div>
  );
};

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

  // Count available sections
  const hasEducational = recommendation.educational_items?.length > 0;
  const hasActionable = recommendation.actionable_items?.length > 0;
  const hasPartnerOffers = recommendation.partner_offers?.length > 0;
  const sectionCount = [hasEducational, hasActionable, hasPartnerOffers].filter(Boolean).length;

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

          {/* Grid Layout for Recommendation Sections */}
          <div className={`recommendation-grid sections-${sectionCount}`}>
            
            {/* Educational Content Section */}
            {hasEducational && (
              <div className="rec-section educational-section">
                <div className="section-header">
                  <h4>Educational Content</h4>
                  <span className="section-count">{recommendation.educational_items.length}</span>
                </div>
                <ItemCarousel
                  items={recommendation.educational_items}
                  renderItem={(item) => (
                    <div className="carousel-item">
                      <h5 className="item-title">{item.content_title}</h5>
                      {item.content_snippet && (
                        <p className="item-description">{item.content_snippet}</p>
                      )}
                    </div>
                  )}
                />
              </div>
            )}

            {/* Actionable Items Section */}
            {hasActionable && (
              <div className="rec-section actionable-section">
                <div className="section-header">
                  <h4>Actionable Items</h4>
                  <span className="section-count">{recommendation.actionable_items.length}</span>
                </div>
                <ItemCarousel
                  items={recommendation.actionable_items}
                  renderItem={(item) => (
                    <div className="carousel-item">
                      <p className="action-text">{item.action_text}</p>
                      {item.action_rationale && (
                        <div className="rationale-box">
                          <strong>Because:</strong>
                          <p>{item.action_rationale}</p>
                        </div>
                      )}
                      {item.data_cited && (
                        <details className="data-cited">
                          <summary>Data Cited</summary>
                          <pre>{JSON.stringify(JSON.parse(item.data_cited), null, 2)}</pre>
                        </details>
                      )}
                    </div>
                  )}
                />
              </div>
            )}

            {/* Partner Offers Section */}
            {hasPartnerOffers && (
              <div className="rec-section partner-section">
                <div className="section-header">
                  <h4>Partner Offers</h4>
                  <span className="section-count">{recommendation.partner_offers.length}</span>
                </div>
                <ItemCarousel
                  items={recommendation.partner_offers}
                  renderItem={(item) => (
                    <div className="carousel-item">
                      <h5 className="item-title">{item.offer_title}</h5>
                      <p className="item-description">{item.offer_description}</p>
                      {item.why_relevant && (
                        <div className="rationale-box">
                          <strong>Why relevant:</strong>
                          <p>{item.why_relevant}</p>
                        </div>
                      )}
                      <div className={`eligibility-badge ${item.eligibility_passed ? 'passed' : 'failed'}`}>
                        {item.eligibility_passed ? '✓ Eligible' : '✗ Not Eligible'}
                      </div>
                    </div>
                  )}
                />
              </div>
            )}
          </div>

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

