import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getUserProfile, getUserSignals, getUserRecommendations } from '../api/services';
import './UserDetail.css';

function UserDetail() {
  const { userId } = useParams();
  const [profile, setProfile] = useState(null);
  const [signals, setSignals] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('profile');

  useEffect(() => {
    loadUserData();
  }, [userId]);

  const loadUserData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [profileData, signalsData, recsData] = await Promise.all([
        getUserProfile(userId),
        getUserSignals(userId),
        getUserRecommendations(userId),
      ]);
      
      setProfile(profileData);
      setSignals(signalsData);
      setRecommendations(recsData);
    } catch (err) {
      setError('Failed to load user data. Make sure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="user-detail">
        <div className="loading">Loading user data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="user-detail">
        <div className="error">
          <p>{error}</p>
          <Link to="/dashboard">Back to Dashboard</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="user-detail">
      <div className="detail-header">
        <Link to="/dashboard" className="back-link">← Back to Dashboard</Link>
        <h1>User {userId}</h1>
        {profile && (
          <div className="profile-summary">
            <span className={`persona-badge ${profile.persona}`}>
              {profile.persona}
            </span>
            <span className={`consent-badge ${profile.consent_status ? 'active' : 'inactive'}`}>
              {profile.consent_status ? '✓ Consent' : '✗ No Consent'}
            </span>
          </div>
        )}
      </div>

      <div className="tabs">
        <button
          className={activeTab === 'profile' ? 'active' : ''}
          onClick={() => setActiveTab('profile')}
        >
          Profile
        </button>
        <button
          className={activeTab === 'signals' ? 'active' : ''}
          onClick={() => setActiveTab('signals')}
        >
          Behavioral Signals
        </button>
        <button
          className={activeTab === 'recommendations' ? 'active' : ''}
          onClick={() => setActiveTab('recommendations')}
        >
          Recommendations
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'profile' && (
          <div className="profile-tab">
            <h2>User Profile</h2>
            <p>Profile data will be displayed here once backend is implemented.</p>
            <pre>{JSON.stringify(profile, null, 2)}</pre>
          </div>
        )}

        {activeTab === 'signals' && (
          <div className="signals-tab">
            <h2>Behavioral Signals</h2>
            <div className="signal-windows">
              <div className="signal-window">
                <h3>30-Day Window</h3>
                <p>Recent behavioral patterns</p>
              </div>
              <div className="signal-window">
                <h3>180-Day Window</h3>
                <p>Long-term behavioral trends</p>
              </div>
            </div>
            <pre>{JSON.stringify(signals, null, 2)}</pre>
          </div>
        )}

        {activeTab === 'recommendations' && (
          <div className="recommendations-tab">
            <h2>Generated Recommendations</h2>
            <p>Personalized recommendations will appear here once backend is implemented.</p>
            <pre>{JSON.stringify(recommendations, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default UserDetail;

