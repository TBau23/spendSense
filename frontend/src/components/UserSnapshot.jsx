import React from 'react';
import './UserSnapshot.css';

/**
 * UserSnapshot Component
 * 
 * Displays 3-5 key financial metrics for a user based on their persona.
 * Replaces redundant "Why" sections with consolidated metrics summary.
 */
const UserSnapshot = ({ snapshot }) => {
  if (!snapshot || !snapshot.metrics || snapshot.metrics.length === 0) {
    return null;
  }

  return (
    <div className="user-snapshot-card">
      <h4>Your Financial Snapshot</h4>
      <div className="snapshot-metrics">
        {snapshot.metrics.map((metric, idx) => (
          <div key={idx} className="snapshot-metric">
            <span className="metric-label">{metric.label}:</span>
            <span className="metric-value">{metric.value}</span>
            {metric.detail && (
              <span className="metric-detail">{metric.detail}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default UserSnapshot;

