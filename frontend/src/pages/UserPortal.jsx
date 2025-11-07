/**
 * User Portal Page
 * 
 * Main end user view with three states:
 * - State A: Non-consented (show grant consent)
 * - State B: Consented, no approved recs (show "check back soon")
 * - State C: Consented, has approved recs (show full portal)
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Lock, Clock, Sparkles, ShieldCheck, RefreshCw, Lightbulb, Info } from 'lucide-react';
import { fetchUser, fetchUserRecommendations, fetchUserInsights } from '../api/user';
import UserInsights from '../components/UserInsights';
import RecommendationCard from '../components/RecommendationCard';
import ConsentToggle from '../components/ConsentToggle';

const UserPortal = () => {
  const { userId } = useParams();
  const navigate = useNavigate();
  
  const [user, setUser] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadUserData();
  }, [userId]);

  const loadUserData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch user info
      const userData = await fetchUser(userId);
      setUser(userData);

      // If consented, fetch recommendations and insights
      if (userData.consent) {
        const [recsData, insightsData] = await Promise.all([
          fetchUserRecommendations(userId),
          fetchUserInsights(userId)
        ]);
        setRecommendations(recsData);
        setInsights(insightsData);
      } else {
        setRecommendations([]);
        setInsights(null);
      }
    } catch (err) {
      console.error('Error loading user data:', err);
      setError('Failed to load your data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleConsentChange = (newConsentStatus) => {
    // Reload data after consent change
    loadUserData();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
          <p className="text-gray-600">Loading your portal...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
          <div className="text-red-600 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Oops!</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => navigate('/user')}
            className="btn btn-primary"
          >
            Back to User Selection
          </button>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">User Not Found</h2>
          <button
            onClick={() => navigate('/user')}
            className="btn btn-primary mt-4"
          >
            Back to User Selection
          </button>
        </div>
      </div>
    );
  }

  // Determine which state to show
  const isConsented = user.consent;
  const hasRecommendations = recommendations.length > 0;

  // State A: Non-consented
  if (!isConsented) {
    return (
      <div className="consent-page">
        <div className="consent-content-wrapper">
          <div className="consent-card">
            {/* Navigation */}
            <button
              onClick={() => navigate('/user')}
              className="back-btn-consent"
            >
              ← Back to User Selection
            </button>

            {/* Content */}
            <div className="consent-content">
              <h1 className="consent-welcome-title">
                Welcome, {user.name}!
              </h1>
              
              {/* Lock Icon with Animation */}
              <div className="consent-icon-container">
                <div className="consent-glow"></div>
                <div className="consent-lock-icon">
                  <Lock size={60} strokeWidth={2.5} />
                </div>
              </div>
              
              <h2 className="consent-heading">
                Get Personalized Financial Education
              </h2>
              <p className="consent-description">
                Grant consent to unlock personalized insights and recommendations based on your spending patterns. 
                We'll analyze your financial behavior and provide educational content tailored just for you.
              </p>
              
              {/* Benefits Box */}
              <div className="benefits-box">
                <h3 className="benefits-title">What you'll get:</h3>
                <ul className="benefits-list">
                  <li className="benefit-item">
                    <span className="benefit-check">✓</span>
                    <span>Personalized spending insights and analysis</span>
                  </li>
                  <li className="benefit-item">
                    <span className="benefit-check">✓</span>
                    <span>Educational content matched to your financial situation</span>
                  </li>
                  <li className="benefit-item">
                    <span className="benefit-check">✓</span>
                    <span>Actionable recommendations reviewed by our team</span>
                  </li>
                  <li className="benefit-item">
                    <span className="benefit-check">✓</span>
                    <span>Relevant product suggestions (no sales pressure)</span>
                  </li>
                </ul>
              </div>

              {/* Consent Button */}
              <div className="consent-button-wrapper">
                <ConsentToggle
                  userId={userId}
                  currentConsent={false}
                  onConsentChange={handleConsentChange}
                />
              </div>

              {/* Privacy Notice */}
              <p className="privacy-notice">
                <span className="privacy-icon">
                  <ShieldCheck size={20} strokeWidth={2} />
                </span>
                You can revoke consent at any time. We respect your privacy and data rights.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // State B: Consented, no approved recommendations
  if (!hasRecommendations) {
    return (
      <div className="waiting-page">
        <div className="waiting-content-wrapper">
          <div className="waiting-card">
            {/* Navigation */}
            <button
              onClick={() => navigate('/user')}
              className="back-btn-waiting"
            >
              ← Back to User Selection
            </button>

            {/* Content */}
            <div className="waiting-content">
              <h1 className="welcome-title">
                Welcome, {user.name}!
              </h1>
              
              {/* Animated Icon */}
              <div className="waiting-animation">
                <div className="waiting-circle pulse-1"></div>
                <div className="waiting-circle pulse-2"></div>
                <div className="waiting-circle pulse-3"></div>
                <div className="waiting-icon">
                  <Clock size={56} strokeWidth={2.5} />
                </div>
              </div>
              
              <h2 className="waiting-heading">
                Your Recommendations Are In Review
              </h2>
              <p className="waiting-description">
                Thank you for granting consent! Our team is carefully reviewing your personalized recommendations to ensure 
                they're accurate and helpful. We'll notify you when they're ready.
              </p>
              
              {/* Info Box */}
              <div className="info-box-waiting">
                <div className="info-box-icon">
                  <Sparkles size={32} strokeWidth={2} />
                </div>
                <div className="info-box-content">
                  <p className="info-box-title">What's happening now?</p>
                  <ul className="info-box-list">
                    <li>✓ Your spending patterns have been analyzed</li>
                    <li>✓ Personalized insights have been identified</li>
                    <li>✓ Educational content has been curated</li>
                    <li>⏳ Our team is reviewing your recommendations</li>
                  </ul>
                </div>
              </div>

              <p className="check-back-message">
                Check back soon to see your personalized financial education content!
              </p>

              {/* Consent Management */}
              <div className="consent-section-waiting">
                <ConsentToggle
                  userId={userId}
                  currentConsent={true}
                  onConsentChange={handleConsentChange}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // State C: Consented with approved recommendations - Full portal
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="user-portal-header">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <button
            onClick={() => navigate('/user')}
            className="back-to-selection-btn"
          >
            ← Back to User Selection
          </button>
          <h1 className="user-portal-title">Welcome back, {user.name}!</h1>
          <p className="user-portal-subtitle">
            Your personalized financial education portal
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Insights */}
        {insights && <UserInsights insights={insights} />}

        {/* Recommendations */}
        <div className="recommendations-section">
          <div className="recommendations-header">
            <h2 className="recommendations-section-title">
              <span className="recommendations-icon">
                <Lightbulb size={32} strokeWidth={2.5} />
              </span>
              Your Recommendations
            </h2>
            <div className="recommendations-disclaimer">
              <span className="disclaimer-icon">
                <Info size={20} strokeWidth={2} />
              </span>
              This is educational content, not financial advice. Consult a licensed advisor for personalized guidance.
            </div>
          </div>
          {recommendations.map((rec) => (
            <RecommendationCard 
              key={rec.recommendation_id} 
              recommendation={rec}
              onUpdate={loadUserData}
              hideOperatorActions={true}
            />
          ))}
        </div>

        {/* Consent Management */}
        <div className="consent-management-card">
          <h3 className="consent-card-title">Manage Your Consent</h3>
          <p className="consent-card-text">
            You can revoke consent at any time to stop receiving personalized recommendations.
          </p>
          <ConsentToggle
            userId={userId}
            currentConsent={true}
            onConsentChange={handleConsentChange}
          />
        </div>

      </div>
    </div>
  );
};

export default UserPortal;

