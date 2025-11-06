/**
 * User API Client
 * 
 * API functions for end user portal
 */

const API_BASE = 'http://localhost:8000';

/**
 * Fetch all users for dropdown selection
 */
export const fetchAllUsers = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/users`);
    if (!response.ok) {
      throw new Error(`Failed to fetch users: ${response.status}`);
    }
    const data = await response.json();
    return data.users || []; // Backend returns { users: [...] }
  } catch (error) {
    console.error('Error fetching all users:', error);
    throw error;
  }
};

/**
 * Fetch basic user info (name, consent status)
 */
export const fetchUser = async (userId) => {
  try {
    const response = await fetch(`${API_BASE}/api/users/${userId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch user: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching user ${userId}:`, error);
    throw error;
  }
};

/**
 * Fetch approved recommendations for user
 */
export const fetchUserRecommendations = async (userId) => {
  try {
    const response = await fetch(`${API_BASE}/api/users/${userId}/recommendations`);
    if (!response.ok) {
      throw new Error(`Failed to fetch recommendations: ${response.status}`);
    }
    const data = await response.json();
    return data.recommendations || []; // Backend returns { recommendations: [...] }
  } catch (error) {
    console.error(`Error fetching recommendations for user ${userId}:`, error);
    throw error;
  }
};

/**
 * Fetch transaction insights for user
 */
export const fetchUserInsights = async (userId) => {
  try {
    const response = await fetch(`${API_BASE}/api/users/${userId}/insights`);
    if (!response.ok) {
      throw new Error(`Failed to fetch insights: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching insights for user ${userId}:`, error);
    throw error;
  }
};

/**
 * Grant consent for user
 */
export const grantConsent = async (userId) => {
  try {
    const response = await fetch(`${API_BASE}/api/operator/consent/grant`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_id: userId }),
    });
    if (!response.ok) {
      throw new Error(`Failed to grant consent: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error granting consent for user ${userId}:`, error);
    throw error;
  }
};

/**
 * Revoke consent for user
 */
export const revokeConsent = async (userId) => {
  try {
    const response = await fetch(`${API_BASE}/api/operator/consent/revoke`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_id: userId }),
    });
    if (!response.ok) {
      throw new Error(`Failed to revoke consent: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error revoking consent for user ${userId}:`, error);
    throw error;
  }
};

