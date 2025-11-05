/**
 * UserMetrics Component
 * 
 * Displays user-specific metrics (personas, features, accounts)
 */

import React from 'react';

const UserMetrics = ({ metrics }) => {
  if (!metrics) {
    return <div className="user-metrics loading">Loading...</div>;
  }

  const getPersonaName = (persona_id) => {
    const personas = {
      1: 'High Utilization',
      2: 'Variable Income',
      3: 'Subscription Heavy',
      4: 'Savings Builder',
      5: 'Cash Flow Stressed'
    };
    return personas[persona_id] || 'Stable';
  };

  return (
    <div className="user-metrics">
      <h3>User Metrics</h3>

      {/* Persona Assignments */}
      <div className="metric-section">
        <h4>Persona Assignments</h4>
        <div className="persona-info">
          <div className="persona-window">
            <strong>30d Window:</strong>
            <p>{metrics.personas?.window_30d ? 
              getPersonaName(metrics.personas.window_30d.primary_persona_id) : 
              'Not assigned'
            }</p>
          </div>
          <div className="persona-window">
            <strong>180d Window:</strong>
            <p>{metrics.personas?.window_180d ? 
              getPersonaName(metrics.personas.window_180d.primary_persona_id) : 
              'Not assigned'
            }</p>
          </div>
        </div>
      </div>

      {/* Key Features */}
      <div className="metric-section">
        <h4>Key Features</h4>
        {metrics.features && Object.keys(metrics.features).length > 0 ? (
          <dl className="feature-list">
            {metrics.features.credit_utilization !== undefined && (
              <>
                <dt>Credit Utilization:</dt>
                <dd>{(metrics.features.credit_utilization * 100).toFixed(1)}%</dd>
              </>
            )}
            {metrics.features.savings_growth_rate !== undefined && (
              <>
                <dt>Savings Growth:</dt>
                <dd>{(metrics.features.savings_growth_rate * 100).toFixed(1)}%</dd>
              </>
            )}
            {metrics.features.pct_days_below_100 !== undefined && (
              <>
                <dt>Days Below $100:</dt>
                <dd>{(metrics.features.pct_days_below_100 * 100).toFixed(1)}%</dd>
              </>
            )}
          </dl>
        ) : (
          <p className="no-data">Features not available</p>
        )}
      </div>

      {/* Accounts */}
      <div className="metric-section">
        <h4>Accounts</h4>
        <dl className="account-list">
          <dt>Checking:</dt>
          <dd>{metrics.accounts?.checking_count || 0}</dd>
          <dt>Savings:</dt>
          <dd>{metrics.accounts?.savings_count || 0}</dd>
          <dt>Credit Cards:</dt>
          <dd>{metrics.accounts?.credit_card_count || 0}</dd>
        </dl>
      </div>

      {/* Recommendation Stats */}
      <div className="metric-section">
        <h4>Recommendations</h4>
        <dl className="rec-stats">
          <dt>Total:</dt>
          <dd>{metrics.recommendations?.total_generated || 0}</dd>
          <dt>Pending:</dt>
          <dd className="pending">{metrics.recommendations?.pending || 0}</dd>
          <dt>Approved:</dt>
          <dd className="approved">{metrics.recommendations?.approved || 0}</dd>
          <dt>Flagged:</dt>
          <dd className="flagged">{metrics.recommendations?.flagged || 0}</dd>
        </dl>
      </div>
    </div>
  );
};

export default UserMetrics;

