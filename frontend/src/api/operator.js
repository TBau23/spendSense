/**
 * Operator API Client
 * 
 * Client functions for operator dashboard API calls
 */

import axios from 'axios';

// Get base URL from environment variable or default to localhost
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Error handler
const handleError = (error) => {
  if (error.response) {
    // Server responded with error status
    console.error('API Error:', error.response.data);
    throw new Error(error.response.data.detail || error.response.data.error || 'API request failed');
  } else if (error.request) {
    // Request made but no response
    console.error('Network Error:', error.request);
    throw new Error('Network error - could not reach server');
  } else {
    // Something else happened
    console.error('Error:', error.message);
    throw error;
  }
};

/**
 * Fetch list of users with optional filters
 * 
 * @param {Object} filters - Filter options
 * @param {number} filters.persona - Filter by persona ID
 * @param {string} filters.status - Filter by recommendation status
 * @param {string} filters.sort - Sort by (name, date, persona)
 * @returns {Promise<Object>} - Users list response
 */
export const fetchUsers = async (filters = {}) => {
  try {
    const params = new URLSearchParams();
    if (filters.persona) params.append('persona', filters.persona);
    if (filters.status) params.append('status', filters.status);
    if (filters.sort) params.append('sort', filters.sort);
    
    const response = await apiClient.get(`/api/operator/users?${params.toString()}`);
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

/**
 * Fetch detailed information for a specific user
 * 
 * @param {string} userId - User identifier
 * @returns {Promise<Object>} - User detail response
 */
export const fetchUserDetail = async (userId) => {
  try {
    const response = await apiClient.get(`/api/operator/users/${userId}`);
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

/**
 * Fetch all recommendations for a user
 * 
 * @param {string} userId - User identifier
 * @returns {Promise<Object>} - User recommendations response
 */
export const fetchUserRecommendations = async (userId) => {
  try {
    const response = await apiClient.get(`/api/operator/users/${userId}/recommendations`);
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

/**
 * Fetch full recommendation with all items
 * 
 * @param {string} recId - Recommendation identifier
 * @returns {Promise<Object>} - Recommendation object
 */
export const fetchRecommendation = async (recId) => {
  try {
    const response = await apiClient.get(`/api/operator/recommendations/${recId}`);
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

/**
 * Approve a recommendation
 * 
 * @param {string} recId - Recommendation identifier
 * @param {string} notes - Optional reviewer notes
 * @returns {Promise<Object>} - Updated recommendation
 */
export const approveRecommendation = async (recId, notes = null) => {
  try {
    const response = await apiClient.post(`/api/operator/recommendations/${recId}/approve`, {
      reviewer_notes: notes
    });
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

/**
 * Flag a recommendation as problematic
 * 
 * @param {string} recId - Recommendation identifier
 * @param {string} notes - Required reviewer notes explaining why flagged
 * @returns {Promise<Object>} - Updated recommendation
 */
export const flagRecommendation = async (recId, notes) => {
  if (!notes || notes.trim() === '') {
    throw new Error('Reviewer notes are required when flagging a recommendation');
  }
  
  try {
    const response = await apiClient.post(`/api/operator/recommendations/${recId}/flag`, {
      reviewer_notes: notes
    });
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

/**
 * Fetch decision traces for a user
 * 
 * @param {string} userId - User identifier
 * @param {string} recId - Optional recommendation ID filter
 * @returns {Promise<Object>} - Traces response
 */
export const fetchTraces = async (userId, recId = null) => {
  try {
    const params = recId ? `?recommendation_id=${recId}` : '';
    const response = await apiClient.get(`/api/operator/traces/${userId}${params}`);
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

/**
 * Fetch aggregate operator metrics
 * 
 * @param {boolean} forceRefresh - Bypass cache and recompute
 * @returns {Promise<Object>} - Metrics object
 */
export const fetchMetrics = async (forceRefresh = false) => {
  try {
    const params = forceRefresh ? '?force_refresh=true' : '';
    const response = await apiClient.get(`/api/operator/metrics${params}`);
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

/**
 * Health check
 * 
 * @returns {Promise<Object>} - Health status
 */
export const healthCheck = async () => {
  try {
    const response = await apiClient.get('/api/health');
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

// ========== Epic 6: Consent & Recommendation Management ==========

/**
 * Generate a new recommendation for a user
 * 
 * @param {string} userId - User identifier
 * @returns {Promise<Object>} - Generated recommendation
 */
export const generateRecommendation = async (userId) => {
  try {
    const response = await apiClient.post(`/api/operator/users/${userId}/generate`);
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

/**
 * Delete a recommendation (soft delete)
 * 
 * @param {string} recId - Recommendation identifier
 * @returns {Promise<Object>} - Delete confirmation
 */
export const deleteRecommendation = async (recId) => {
  try {
    const response = await apiClient.delete(`/api/operator/recommendations/${recId}`);
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

/**
 * Grant consent for a user
 * 
 * @param {string} userId - User identifier
 * @returns {Promise<Object>} - Consent grant confirmation
 */
export const grantConsent = async (userId) => {
  try {
    const response = await apiClient.post('/api/operator/consent/grant', {
      user_id: userId
    });
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

/**
 * Revoke consent for a user
 * 
 * @param {string} userId - User identifier
 * @returns {Promise<Object>} - Consent revoke confirmation
 */
export const revokeConsent = async (userId) => {
  try {
    const response = await apiClient.post('/api/operator/consent/revoke', {
      user_id: userId
    });
    return response.data;
  } catch (error) {
    handleError(error);
  }
};

