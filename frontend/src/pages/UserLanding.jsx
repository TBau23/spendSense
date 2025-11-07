/**
 * User Landing Page
 * 
 * Simple landing page for end users to select their profile
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Wallet, User, Info } from 'lucide-react';
import { fetchAllUsers } from '../api/user';

const UserLanding = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedUserId, setSelectedUserId] = useState('');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await fetchAllUsers();
      setUsers(data);
      setError(null);
    } catch (err) {
      setError('Failed to load users. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUserSelect = (e) => {
    const userId = e.target.value;
    setSelectedUserId(userId);
    if (userId) {
      navigate(`/user/${userId}`);
    }
  };

  const maskUserId = (userId) => {
    if (!userId || userId.length < 4) return userId;
    return `***${userId.slice(-4)}`;
  };

  return (
    <div className="user-landing-page">
      <div className="landing-content-wrapper">
        <div className="landing-card">
          {/* Header with Logo/Icon */}
          <div className="landing-header">
            <div className="logo-container">
              <div className="logo-icon">
                <Wallet size={48} strokeWidth={2} />
              </div>
              <h1 className="logo-text">SpendSense</h1>
            </div>
            <p className="tagline">Your personalized financial education platform</p>
          </div>

          {/* User Selection */}
          <div className="selection-section">
            <label className="selection-label">
              <span className="label-icon">
                <User size={20} strokeWidth={2} />
              </span>
              Select Your Account
            </label>
            
            {loading ? (
              <div className="loading-state">
                <div className="spinner-modern">
                  <div className="spinner-ring"></div>
                  <div className="spinner-ring"></div>
                  <div className="spinner-ring"></div>
                </div>
                <p className="loading-text">Loading accounts...</p>
              </div>
            ) : error ? (
              <div className="error-state">
                <div className="error-icon">
                  <Info size={48} strokeWidth={2} />
                </div>
                <p className="error-text">{error}</p>
                <button
                  onClick={loadUsers}
                  className="retry-button"
                >
                  Try Again
                </button>
              </div>
            ) : (
              <div className="select-wrapper">
                <select
                  value={selectedUserId}
                  onChange={handleUserSelect}
                  className="account-select"
                >
                  <option value="">Choose your account...</option>
                  {users.map((user) => (
                    <option key={user.user_id} value={user.user_id}>
                      {user.name} ({maskUserId(user.user_id)})
                    </option>
                  ))}
                </select>
                <div className="select-arrow">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M4.427 6.427l3.396 3.396a.25.25 0 00.354 0l3.396-3.396A.25.25 0 0011.396 6H4.604a.25.25 0 00-.177.427z"/>
                  </svg>
                </div>
              </div>
            )}
          </div>

          {/* Footer Disclaimer */}
          <div className="landing-footer">
            <div className="disclaimer-badge">
              <span className="disclaimer-icon">ℹ️</span>
              <div className="disclaimer-content">
                <p className="disclaimer-title">Educational Content Only</p>
                <p className="disclaimer-text">
                  This is educational content, not financial advice. Consult a licensed advisor for personalized guidance.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserLanding;

