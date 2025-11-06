/**
 * User Landing Page
 * 
 * Simple landing page for end users to select their profile
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchAllUsers } from '../api/user';

const UserLanding = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedUserId, setSelectedUserId] = useState('');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await fetchAllUsers();
      setUsers(data);
      setError(null);
    } catch (err) {
      setError('Failed to load users. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUserSelect = (e) => {
    const userId = e.target.value;
    setSelectedUserId(userId);
    if (userId) {
      navigate(`/user/${userId}`);
    }
  };

  const maskUserId = (userId) => {
    if (!userId || userId.length < 4) return userId;
    return `***${userId.slice(-4)}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-lg shadow-xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-indigo-600 mb-2">SpendSense</h1>
            <p className="text-gray-600">Your personalized financial education platform</p>
          </div>

          {/* User Selection */}
          <div className="space-y-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Your Account
            </label>
            
            {loading ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                <p className="text-gray-500 mt-2">Loading users...</p>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800 text-sm">{error}</p>
                <button
                  onClick={loadUsers}
                  className="mt-2 text-red-600 hover:text-red-800 font-medium text-sm"
                >
                  Try Again
                </button>
              </div>
            ) : (
              <select
                value={selectedUserId}
                onChange={handleUserSelect}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-gray-900"
              >
                <option value="">Choose your account...</option>
                {users.map((user) => (
                  <option key={user.user_id} value={user.user_id}>
                    {user.name} ({maskUserId(user.user_id)})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Footer */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              This is educational content, not financial advice.
              <br />
              Consult a licensed advisor for personalized guidance.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserLanding;

