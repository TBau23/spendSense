/**
 * Consent Toggle Component
 * 
 * Allows users to grant or revoke consent for data processing
 */

import React, { useState } from 'react';
import { grantConsent, revokeConsent } from '../api/user';

const ConsentToggle = ({ userId, currentConsent, onConsentChange }) => {
  const [loading, setLoading] = useState(false);
  const [showRevokeConfirm, setShowRevokeConfirm] = useState(false);

  const handleGrant = async () => {
    setLoading(true);
    try {
      await grantConsent(userId);
      if (onConsentChange) {
        onConsentChange(true);
      }
    } catch (err) {
      console.error('Failed to grant consent:', err);
      alert('Failed to grant consent. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async () => {
    setShowRevokeConfirm(false);
    setLoading(true);
    try {
      await revokeConsent(userId);
      if (onConsentChange) {
        onConsentChange(false);
      }
    } catch (err) {
      console.error('Failed to revoke consent:', err);
      alert('Failed to revoke consent. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (currentConsent) {
    // Show revoke option
    return (
      <>
        <button
          onClick={() => setShowRevokeConfirm(true)}
          disabled={loading}
          className="btn-revoke-consent"
        >
          {loading ? (
            <>
              <span className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
              Processing...
            </>
          ) : (
            'Revoke Consent'
          )}
        </button>

        {/* Revoke Confirmation Modal */}
        {showRevokeConfirm && (
          <div className="modal-overlay" onClick={() => setShowRevokeConfirm(false)}>
            <div className="revoke-modal" onClick={(e) => e.stopPropagation()}>
              {/* Warning Icon */}
              <div className="revoke-modal-icon">
                <div className="revoke-icon-circle">⚠️</div>
              </div>
              
              {/* Modal Header */}
              <div className="revoke-modal-header">
                <h3 className="revoke-modal-title">Revoke Consent</h3>
                <p className="revoke-modal-subtitle">
                  Are you sure you want to revoke consent?
                </p>
              </div>
              
              {/* Modal Body */}
              <div className="revoke-modal-body">
                <p className="revoke-modal-description">This will:</p>
                <div className="revoke-consequences">
                  <div className="revoke-consequence-item">
                    <span className="revoke-consequence-icon">🗑️</span>
                    <span className="revoke-consequence-text">Remove all your personalized recommendations</span>
                  </div>
                  <div className="revoke-consequence-item">
                    <span className="revoke-consequence-icon">⏸️</span>
                    <span className="revoke-consequence-text">Stop processing your financial data</span>
                  </div>
                  <div className="revoke-consequence-item">
                    <span className="revoke-consequence-icon">🔒</span>
                    <span className="revoke-consequence-text">Hide your insights and analysis</span>
                  </div>
                </div>
                
                {/* Info Notice */}
                <div className="revoke-modal-notice">
                  <span className="revoke-notice-icon">ℹ️</span>
                  <span className="revoke-notice-text">
                    You can grant consent again at any time to resume receiving personalized content.
                  </span>
                </div>
              </div>
              
              {/* Modal Footer */}
              <div className="revoke-modal-footer">
                <button
                  onClick={() => setShowRevokeConfirm(false)}
                  className="btn-modal-cancel"
                >
                  Cancel
                </button>
                <button
                  onClick={handleRevoke}
                  className="btn-modal-revoke"
                >
                  Revoke Consent
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    );
  } else {
    // Show grant option
    return (
      <button
        onClick={handleGrant}
        disabled={loading}
        className="btn-grant-consent"
      >
        {loading ? (
          <>
            <span className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
            Processing...
          </>
        ) : (
          'Grant Consent'
        )}
      </button>
    );
  }
};

export default ConsentToggle;

