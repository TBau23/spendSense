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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="max-w-2xl w-full bg-white rounded-lg shadow-xl p-8">
          {/* Navigation */}
          <button
            onClick={() => navigate('/user')}
            className="text-indigo-600 hover:text-indigo-800 mb-6 flex items-center"
          >
            ← Back to User Selection
          </button>

          {/* Content */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Welcome, {user.name}!
            </h1>
            <div className="text-6xl mb-6">🔒</div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Get Personalized Financial Education
            </h2>
            <p className="text-gray-600 mb-6 leading-relaxed">
              Grant consent to unlock personalized insights and recommendations based on your spending patterns. 
              We'll analyze your financial behavior and provide educational content tailored just for you.
            </p>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8 text-left">
              <h3 className="font-semibold text-blue-900 mb-3">What you'll get:</h3>
              <ul className="space-y-2 text-gray-700">
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>Personalized spending insights and analysis</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>Educational content matched to your financial situation</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>Actionable recommendations reviewed by our team</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>Relevant product suggestions (no sales pressure)</span>
                </li>
              </ul>
            </div>

            <ConsentToggle
              userId={userId}
              currentConsent={false}
              onConsentChange={handleConsentChange}
            />

            <p className="text-xs text-gray-500 mt-6">
              You can revoke consent at any time. We respect your privacy and data rights.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // State B: Consented, no approved recommendations
  if (!hasRecommendations) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="max-w-2xl w-full bg-white rounded-lg shadow-xl p-8">
          {/* Navigation */}
          <button
            onClick={() => navigate('/user')}
            className="text-indigo-600 hover:text-indigo-800 mb-6 flex items-center"
          >
            ← Back to User Selection
          </button>

          {/* Content */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Welcome, {user.name}!
            </h1>
            <div className="text-6xl mb-6">⏳</div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Your Recommendations Are Being Prepared
            </h2>
            <p className="text-gray-600 mb-6 leading-relaxed">
              Our team is analyzing your financial data and preparing personalized educational content for you. 
              This usually takes just a few moments.
            </p>
            
            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6 mb-8">
              <p className="text-indigo-900 font-medium">
                Check back soon or refresh this page to see your recommendations!
              </p>
            </div>

            <button
              onClick={loadUserData}
              className="btn btn-primary mb-6"
            >
              Refresh Now
            </button>

            <div className="pt-6 border-t border-gray-200">
              <ConsentToggle
                userId={userId}
                currentConsent={true}
                onConsentChange={handleConsentChange}
              />
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
          <h2 className="recommendations-section-title">
            <span className="recommendations-icon">💡</span>
            Your Recommendations
          </h2>
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

        {/* Disclaimer */}
        <div className="disclaimer-text">
          This is educational content, not financial advice. Consult a licensed advisor for personalized guidance.
        </div>
      </div>
    </div>
  );
};

export default UserPortal;

