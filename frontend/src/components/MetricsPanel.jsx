/**
 * MetricsPanel Component
 * 
 * Displays aggregate metrics for operator dashboard
 */

import React from 'react';

const MetricsPanel = ({ metrics }) => {
  if (!metrics) {
    return <div className="metrics-panel loading">Loading metrics...</div>;
  }

  const metricCards = [
    {
      label: 'Total Consented Users',
      value: metrics.total_consented_users,
      color: 'blue'
    },
    {
      label: 'Pending Recommendations',
      value: metrics.pending_count,
      color: 'yellow'
    },
    {
      label: 'Approval Rate',
      value: `${(metrics.approval_rate * 100).toFixed(1)}%`,
      color: 'green'
    },
    {
      label: 'Coverage',
      value: `${(metrics.coverage_pct * 100).toFixed(1)}%`,
      color: 'purple'
    }
  ];

  return (
    <div className="metrics-panel">
      <div className="metrics-grid">
        {metricCards.map((metric, index) => (
          <div key={index} className={`metric-card ${metric.color}`}>
            <div className="metric-label">{metric.label}</div>
            <div className="metric-value">{metric.value}</div>
          </div>
        ))}
      </div>
      <div className="metrics-detail">
        <p>Approved: {metrics.approved_count} | Flagged: {metrics.flagged_count}</p>
      </div>
    </div>
  );
};

export default MetricsPanel;

