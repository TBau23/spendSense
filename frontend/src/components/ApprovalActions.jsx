/**
 * ApprovalActions Component
 * 
 * Approve/Flag buttons with confirmation modal for flagging
 */

import React, { useState } from 'react';
import { approveRecommendation, flagRecommendation } from '../api/operator';

const ApprovalActions = ({ recommendationId, onUpdate }) => {
  const [showFlagModal, setShowFlagModal] = useState(false);
  const [flagNotes, setFlagNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleApprove = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await approveRecommendation(recommendationId);
      setSuccess('Recommendation approved successfully!');
      setTimeout(() => {
        if (onUpdate) onUpdate();
      }, 1000);
    } catch (err) {
      setError(err.message || 'Failed to approve recommendation');
    } finally {
      setLoading(false);
    }
  };

  const handleFlagSubmit = async () => {
    if (!flagNotes.trim()) {
      setError('Please provide notes explaining why you are flagging this recommendation');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await flagRecommendation(recommendationId, flagNotes);
      setSuccess('Recommendation flagged successfully!');
      setShowFlagModal(false);
      setFlagNotes('');
      setTimeout(() => {
        if (onUpdate) onUpdate();
      }, 1000);
    } catch (err) {
      setError(err.message || 'Failed to flag recommendation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="approval-actions">
      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="action-buttons">
        <button 
          className="btn btn-success"
          onClick={handleApprove}
          disabled={loading}
        >
          {loading ? 'Processing...' : 'Approve'}
        </button>

        <button 
          className="btn btn-danger"
          onClick={() => setShowFlagModal(true)}
          disabled={loading}
        >
          Flag
        </button>
      </div>

      {/* Flag Modal */}
      {showFlagModal && (
        <div className="modal-overlay" onClick={() => setShowFlagModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Flag Recommendation</h3>
            <p>Please provide notes explaining why you are flagging this recommendation:</p>
            
            <textarea
              className="flag-notes-input"
              value={flagNotes}
              onChange={(e) => setFlagNotes(e.target.value)}
              placeholder="Enter your notes here..."
              rows="5"
            />

            <div className="modal-actions">
              <button 
                className="btn btn-danger"
                onClick={handleFlagSubmit}
                disabled={loading}
              >
                {loading ? 'Flagging...' : 'Submit Flag'}
              </button>
              <button 
                className="btn btn-secondary"
                onClick={() => setShowFlagModal(false)}
                disabled={loading}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApprovalActions;

