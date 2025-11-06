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
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3 className="text-xl font-bold text-gray-900">Revoke Consent</h3>
              </div>
              <div className="modal-body">
                <p className="text-gray-700 mb-4">
                  Are you sure you want to revoke consent? This will:
                </p>
                <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                  <li>Remove all your personalized recommendations</li>
                  <li>Stop processing your financial data</li>
                  <li>Hide your insights and analysis</li>
                </ul>
                <p className="text-sm text-gray-600">
                  You can grant consent again at any time to resume receiving personalized content.
                </p>
              </div>
              <div className="modal-footer">
                <button
                  onClick={() => setShowRevokeConfirm(false)}
                  className="btn btn-secondary mr-3"
                >
                  Cancel
                </button>
                <button
                  onClick={handleRevoke}
                  className="btn btn-danger"
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

