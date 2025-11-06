/**
 * User Insights Component
 * 
 * Displays transaction insights for end users
 */

import React from 'react';

const UserInsights = ({ insights }) => {
  if (!insights) {
    return null;
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(Math.abs(amount));
  };

  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`;
  };

  return (
    <div className="user-insights-container mb-8">
      {/* Summary Cards */}
      <div className="grid md:grid-cols-2 gap-4 mb-6">
        {/* Total Spend */}
        <div className="insight-card">
          <div className="insight-card-header">Total Spending</div>
          <div className="insight-card-value">{formatCurrency(insights.total_spend || 0)}</div>
          <div className="insight-card-subtitle">Last 30 days</div>
        </div>

        {/* Transaction Count */}
        <div className="insight-card">
          <div className="insight-card-header">Transactions</div>
          <div className="insight-card-value">{insights.transaction_count || 0}</div>
          <div className="insight-card-subtitle">Last 30 days</div>
        </div>
      </div>

      {/* Top Merchants */}
      {insights.top_merchants && insights.top_merchants.length > 0 && (
        <div className="insights-section">
          <h3 className="insights-section-title">🏪 Top Merchants</h3>
          <div className="merchant-grid">
            {insights.top_merchants.slice(0, 5).map((merchant, index) => {
              const percentage = insights.total_spend > 0
                ? (merchant.total_spend / insights.total_spend) * 100
                : 0;
              
              return (
                <div key={index} className="merchant-card">
                  <div className="merchant-rank-badge">#{index + 1}</div>
                  <div className="merchant-info">
                    <div className="merchant-name">{merchant.merchant_name || 'Unknown'}</div>
                    <div className="merchant-amount">{formatCurrency(merchant.total_spend)}</div>
                    <div className="merchant-percentage">{formatPercentage(percentage)} of total</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Top Categories */}
      {insights.top_categories && insights.top_categories.length > 0 && (
        <div className="insights-section">
          <h3 className="insights-section-title">Spending by Category</h3>
          <div className="insights-list">
            {insights.top_categories.slice(0, 5).map((category, index) => {
              const percentage = insights.total_spend > 0
                ? (category.total_spend / insights.total_spend) * 100
                : 0;

              return (
                <div key={index} className="insights-category-item">
                  <div className="insights-category-header">
                    <span className="insights-list-item-label">{category.category || 'Uncategorized'}</span>
                    <span className="insights-list-item-value">
                      {formatCurrency(category.total_spend)} <span className="insights-percentage">({formatPercentage(percentage)})</span>
                    </span>
                  </div>
                  <div className="insights-progress-bar">
                    <div
                      className="insights-progress-fill"
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default UserInsights;

