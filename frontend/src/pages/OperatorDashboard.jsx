/**
 * OperatorDashboard Page
 * 
 * Main operator view: metrics + user list with filtering
 */

import React, { useState, useEffect } from 'react';
import MetricsPanel from '../components/MetricsPanel';
import UserList from '../components/UserList';
import { fetchMetrics, fetchUsers } from '../api/operator';

const OperatorDashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    persona: '',
    status: '',
    sort: 'name'
  });

  // Load metrics
  useEffect(() => {
    loadMetrics();
  }, []);

  // Load users when filters change
  useEffect(() => {
    loadUsers();
  }, [filters]);

  const loadMetrics = async () => {
    try {
      const data = await fetchMetrics();
      setMetrics(data);
    } catch (err) {
      console.error('Failed to load metrics:', err);
      setError('Failed to load metrics');
    }
  };

  const loadUsers = async () => {
    setLoading(true);
    try {
      const cleanFilters = {};
      if (filters.persona) cleanFilters.persona = parseInt(filters.persona);
      if (filters.status) cleanFilters.status = filters.status;
      if (filters.sort) cleanFilters.sort = filters.sort;

      const data = await fetchUsers(cleanFilters);
      setUsers(data.users || []);
      setError(null);
    } catch (err) {
      console.error('Failed to load users:', err);
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  const handleRefresh = () => {
    loadMetrics();
    loadUsers();
  };

  return (
    <div className="operator-dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <h1>SpendSense Operator View</h1>
        <button className="btn btn-secondary" onClick={handleRefresh}>
          Refresh
        </button>
      </header>

      {/* Error Display */}
      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {/* Metrics Panel */}
      <MetricsPanel metrics={metrics} />

      {/* User List */}
      <div className="user-list-section">
        <h2>Users</h2>
        {loading ? (
          <div className="loading">Loading users...</div>
        ) : (
          <UserList users={users} onFilterChange={handleFilterChange} />
        )}
      </div>
    </div>
  );
};

export default OperatorDashboard;

