/**
 * UserList Component
 * 
 * Displays filterable table of users with recommendation status
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const UserList = ({ users, onFilterChange }) => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({
    persona: '',
    status: '',
    sort: 'name'
  });

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const getStatusBadge = (user) => {
    // Epic 6: Check consent first
    if (!user.consent_status) {
      return <span className="badge badge-no-consent">Consent Required</span>;
    }
    
    // Priority order: Pending > Flagged > Approved > No Recs
    if (user.pending_count > 0) {
      return <span className="badge badge-pending">Pending ({user.pending_count})</span>;
    } else if (user.flagged_count > 0) {
      return <span className="badge badge-flagged">Flagged ({user.flagged_count})</span>;
    } else if (user.approved_count > 0) {
      return <span className="badge badge-approved">Approved ({user.approved_count})</span>;
    } else {
      return <span className="badge badge-none">No Recs</span>;
    }
  };

  const getPersonaName = (persona_id) => {
    const personas = {
      1: 'High Utilization',
      2: 'Variable Income',
      3: 'Subscription Heavy',
      4: 'Savings Builder',
      5: 'Cash Flow Stressed',
      null: 'Stable'
    };
    return personas[persona_id] || 'Unknown';
  };

  const maskUserId = (userId) => {
    if (!userId || userId.length < 4) return userId;
    return `***${userId.slice(-4)}`;
  };

  return (
    <div className="user-list">
      {/* Filter Bar */}
      <div className="filter-bar">
        <div className="filter-group">
          <label>Persona:</label>
          <select 
            value={filters.persona} 
            onChange={(e) => handleFilterChange('persona', e.target.value)}
          >
            <option value="">All</option>
            <option value="1">High Utilization</option>
            <option value="2">Variable Income</option>
            <option value="3">Subscription Heavy</option>
            <option value="4">Savings Builder</option>
            <option value="5">Cash Flow Stressed</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Status:</label>
          <select 
            value={filters.status} 
            onChange={(e) => handleFilterChange('status', e.target.value)}
          >
            <option value="">All</option>
            <option value="PENDING_REVIEW">Pending Review</option>
            <option value="APPROVED">Approved</option>
            <option value="FLAGGED">Flagged</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Sort:</label>
          <select 
            value={filters.sort} 
            onChange={(e) => handleFilterChange('sort', e.target.value)}
          >
            <option value="name">Name (A-Z)</option>
            <option value="date">Recent Activity</option>
            <option value="persona">Persona</option>
          </select>
        </div>
      </div>

      {/* User Table */}
      <table className="user-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>User ID</th>
            <th>Primary Persona</th>
            <th>Status</th>
            <th>Recommendations</th>
            <th>Last Activity</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {users.length === 0 ? (
            <tr>
              <td colSpan="7" className="no-results">No users found</td>
            </tr>
          ) : (
            users.map((user) => {
              const isConsented = user.consent_status;
              const rowClass = !isConsented ? 'user-no-consent' : (user.has_pending_recs ? 'has-pending' : '');
              
              return (
                <tr key={user.user_id} className={rowClass}>
                  <td>{user.name}</td>
                  <td className="user-id">{maskUserId(user.user_id)}</td>
                  <td>{isConsented ? getPersonaName(user.primary_persona_id) : '—'}</td>
                  <td>{getStatusBadge(user)}</td>
                  <td>{isConsented ? user.rec_count : '—'}</td>
                  <td>{isConsented && user.last_rec_date ? new Date(user.last_rec_date).toLocaleDateString() : '—'}</td>
                  <td>
                    <button 
                      className="btn btn-primary btn-sm"
                      onClick={() => isConsented && navigate(`/operator/users/${user.user_id}`)}
                      disabled={!isConsented}
                      title={!isConsented ? 'User has not granted consent' : 'View user details'}
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
};

export default UserList;

