import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getUsers } from '../api/services';
import './Dashboard.css';

function Dashboard() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getUsers();
      setUsers(data);
    } catch (err) {
      setError('Failed to load users. Make sure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter((user) => {
    if (filter === 'all') return true;
    if (filter === 'consented') return user.consent_status === true;
    if (filter === 'no-consent') return user.consent_status === false;
    return user.persona === filter;
  });

  if (loading) {
    return (
      <div className="dashboard">
        <div className="loading">Loading users...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="error">
          <p>{error}</p>
          <button onClick={loadUsers}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Operator Dashboard</h1>
        <p>Monitor and review user profiles and recommendations</p>
      </div>

      <div className="filters">
        <label>Filter by:</label>
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">All Users</option>
          <option value="consented">Consented</option>
          <option value="no-consent">No Consent</option>
          <option value="high_utilization">High Utilization</option>
          <option value="variable_income">Variable Income</option>
          <option value="subscription_heavy">Subscription Heavy</option>
          <option value="savings_builder">Savings Builder</option>
        </select>
      </div>

      <div className="user-list">
        {filteredUsers.length === 0 ? (
          <div className="empty-state">
            <p>No users found. Generate synthetic data to get started.</p>
          </div>
        ) : (
          filteredUsers.map((user) => (
            <div key={user.user_id} className="user-card">
              <div className="user-info">
                <h3>{user.name || `User ${user.user_id}`}</h3>
                <div className="user-meta">
                  <span className={`persona-badge ${user.persona || 'unassigned'}`}>
                    {user.persona || 'Unassigned'}
                  </span>
                  <span className={`consent-badge ${user.consent_status ? 'active' : 'inactive'}`}>
                    {user.consent_status ? '✓ Consent' : '✗ No Consent'}
                  </span>
                </div>
              </div>
              <div className="user-actions">
                <Link to={`/user/${user.user_id}`} className="btn-view">
                  View Details
                </Link>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default Dashboard;

