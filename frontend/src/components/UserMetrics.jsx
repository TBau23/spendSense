/**
 * UserMetrics Component
 * 
 * Displays user-specific metrics with 30d vs 180d comparison
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

  const getPersonaPriority = (persona_id) => {
    const priorities = {
      1: 'CRITICAL',
      2: 'HIGH',
      3: 'MEDIUM',
      4: 'LOW',
      5: 'HIGH'
    };
    return priorities[persona_id] || 'LOW';
  };

  const getPriorityClass = (priority) => {
    return {
      'CRITICAL': 'priority-critical',
      'HIGH': 'priority-high',
      'MEDIUM': 'priority-medium',
      'LOW': 'priority-low'
    }[priority] || 'priority-low';
  };

  const persona30d = metrics.personas?.window_30d;
  const persona180d = metrics.personas?.window_180d;
  
  // Determine if persona changed
  const personaChanged = persona30d?.primary_persona_id !== persona180d?.primary_persona_id;
  
  // Progress bar component
  const ProgressBar = ({ value, label, thresholds, reverse = false }) => {
    const percentage = Math.min(Math.max(value * 100, 0), 100);
    let colorClass = 'progress-good';
    
    if (thresholds) {
      if (reverse) {
        // For metrics where lower is better (utilization, days below $100)
        if (percentage >= thresholds.critical) colorClass = 'progress-critical';
        else if (percentage >= thresholds.warning) colorClass = 'progress-warning';
      } else {
        // For metrics where higher is better (savings growth)
        if (percentage >= thresholds.good) colorClass = 'progress-good';
        else if (percentage >= thresholds.warning) colorClass = 'progress-warning';
        else colorClass = 'progress-critical';
      }
    }
    
    return (
      <div className="progress-container">
        <div className="progress-label">
          <span>{label}</span>
          <span className="progress-value">{percentage.toFixed(1)}%</span>
        </div>
        <div className="progress-bar">
          <div className={`progress-fill ${colorClass}`} style={{ width: `${percentage}%` }} />
        </div>
      </div>
    );
  };

  return (
    <div className="user-metrics">
      {/* Layout: Grid for full width display */}
      <div className="metrics-grid-layout">
        {/* Persona Comparison */}
        <div className="metric-section persona-comparison">
          <h4>Persona Timeline</h4>
          
          <div className="timeline-comparison">
            {/* 30d Window */}
            <div className="timeline-item current">
              <div className="timeline-label">30 Days</div>
              {persona30d ? (
                <div className={`persona-badge ${getPriorityClass(getPersonaPriority(persona30d.primary_persona_id))}`}>
                  <div className="persona-name">{getPersonaName(persona30d.primary_persona_id)}</div>
                  <div className="persona-priority">{getPersonaPriority(persona30d.primary_persona_id)}</div>
                </div>
              ) : (
                <div className="persona-badge priority-low">
                  <div className="persona-name">Not Assigned</div>
                </div>
              )}
            </div>

            {/* Change Indicator */}
            <div className="timeline-arrow">
              {personaChanged ? '→' : '='}
            </div>

            {/* 180d Window */}
            <div className="timeline-item historical">
              <div className="timeline-label">180 Days</div>
              {persona180d ? (
                <div className={`persona-badge ${getPriorityClass(getPersonaPriority(persona180d.primary_persona_id))}`}>
                  <div className="persona-name">{getPersonaName(persona180d.primary_persona_id)}</div>
                  <div className="persona-priority">{getPersonaPriority(persona180d.primary_persona_id)}</div>
                </div>
              ) : (
                <div className="persona-badge priority-low">
                  <div className="persona-name">Not Assigned</div>
                </div>
              )}
            </div>
          </div>

          {personaChanged && (
            <div className="persona-change-notice">
              Persona changed from 180d to 30d window
            </div>
          )}
        </div>

        {/* Key Features with Progress Bars */}
        <div className="metric-section">
          <h4>Key Indicators</h4>
          {metrics.features && Object.keys(metrics.features).length > 0 ? (
            <div className="features-visual">
              {metrics.features.credit_utilization !== undefined && (
                <ProgressBar 
                  value={metrics.features.credit_utilization} 
                  label="Credit Utilization"
                  thresholds={{ critical: 50, warning: 30 }}
                  reverse={true}
                />
              )}
              {metrics.features.savings_growth_rate !== undefined && (
                <ProgressBar 
                  value={Math.abs(metrics.features.savings_growth_rate)} 
                  label="Savings Growth"
                  thresholds={{ good: 2, warning: 0.5 }}
                  reverse={false}
                />
              )}
              {metrics.features.pct_days_below_100 !== undefined && (
                <ProgressBar 
                  value={metrics.features.pct_days_below_100} 
                  label="Days Below $100"
                  thresholds={{ critical: 30, warning: 10 }}
                  reverse={true}
                />
              )}
            </div>
          ) : (
            <p className="no-data">Features not available</p>
          )}
        </div>

        {/* Accounts Summary */}
        <div className="metric-section">
          <h4>Accounts</h4>
          <div className="accounts-grid">
            <div className="account-item">
              <div className="account-label">Checking</div>
              <div className="account-count">{metrics.accounts?.checking_count || 0}</div>
            </div>
            <div className="account-item">
              <div className="account-label">Savings</div>
              <div className="account-count">{metrics.accounts?.savings_count || 0}</div>
            </div>
            <div className="account-item">
              <div className="account-label">Credit Cards</div>
              <div className="account-count">{metrics.accounts?.credit_card_count || 0}</div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default UserMetrics;

