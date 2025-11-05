/**
 * UserDetailView Page
 * 
 * Detailed user view: metrics + recommendations + traces
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import UserMetrics from '../components/UserMetrics';
import RecommendationCard from '../components/RecommendationCard';
import DecisionTrace from '../components/DecisionTrace';
import { fetchUserDetail, fetchUserRecommendations, fetchTraces } from '../api/operator';

const UserDetailView = () => {
  const { userId } = useParams();
  const navigate = useNavigate();

  const [userMetrics, setUserMetrics] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [traces, setTraces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadUserData();
  }, [userId]);

  const loadUserData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load all data in parallel
      const [metricsData, recsData, tracesData] = await Promise.all([
        fetchUserDetail(userId),
        fetchUserRecommendations(userId),
        fetchTraces(userId)
      ]);

      setUserMetrics(metricsData);
      setRecommendations(recsData.recommendations || []);
      setTraces(tracesData.traces || []);
    } catch (err) {
      console.error('Failed to load user data:', err);
      setError(err.message || 'Failed to load user data');
    } finally {
      setLoading(false);
    }
  };

  const handleRecommendationUpdate = () => {
    // Reload data after approval/flag action
    loadUserData();
  };

  if (loading) {
    return <div className="loading-page">Loading user data...</div>;
  }

  if (error) {
    return (
      <div className="error-page">
        <h2>Error</h2>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={() => navigate('/operator')}>
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="user-detail-view">
      {/* Breadcrumb Navigation */}
      <nav className="breadcrumb">
        <button className="breadcrumb-link" onClick={() => navigate('/operator')}>
          Operator
        </button>
        <span className="breadcrumb-separator">/</span>
        <span className="breadcrumb-current">User {userId.slice(-4)}</span>
      </nav>

      {/* User Header */}
      <header className="user-header">
        <h1>
          {userMetrics?.full_name || 'User'} (***{userId.slice(-5)})
        </h1>
        <button className="btn btn-secondary" onClick={loadUserData}>
          Refresh
        </button>
      </header>

      {/* 3-Column Layout */}
      <div className="detail-layout">
        {/* Left Column: User Metrics */}
        <aside className="left-column">
          <UserMetrics metrics={userMetrics} />
        </aside>

        {/* Center Column: Recommendations */}
        <main className="center-column">
          <h2>Recommendations ({recommendations.length})</h2>
          {recommendations.length === 0 ? (
            <div className="no-recommendations">
              <p>No recommendations generated for this user yet.</p>
            </div>
          ) : (
            <div className="recommendations-list">
              {recommendations.map((rec) => (
                <RecommendationCard 
                  key={rec.recommendation_id} 
                  recommendation={rec}
                  onUpdate={handleRecommendationUpdate}
                />
              ))}
            </div>
          )}
        </main>

        {/* Right Column: Decision Traces */}
        <aside className="right-column">
          <DecisionTrace traces={traces} />
        </aside>
      </div>
    </div>
  );
};

export default UserDetailView;

