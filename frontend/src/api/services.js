import apiClient from './client';

/**
 * API service functions for SpendSense backend
 */

// Health check
export const healthCheck = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

// User services
export const getUsers = async () => {
  const response = await apiClient.get('/users');
  return response.data;
};

export const getUserProfile = async (userId) => {
  const response = await apiClient.get(`/profile/${userId}`);
  return response.data;
};

export const getUserSignals = async (userId) => {
  const response = await apiClient.get(`/signals/${userId}`);
  return response.data;
};

export const getUserRecommendations = async (userId) => {
  const response = await apiClient.get(`/recommendations/${userId}`);
  return response.data;
};

// Consent services
export const getConsentStatus = async (userId) => {
  const response = await apiClient.get(`/consent/${userId}`);
  return response.data;
};

export const recordConsent = async (userId, consentData) => {
  const response = await apiClient.post('/consent', {
    user_id: userId,
    ...consentData,
  });
  return response.data;
};

export const revokeConsent = async (userId) => {
  const response = await apiClient.delete(`/consent/${userId}`);
  return response.data;
};

// Operator services
export const getReviewQueue = async () => {
  const response = await apiClient.get('/operator/review');
  return response.data;
};

export const submitFeedback = async (feedbackData) => {
  const response = await apiClient.post('/feedback', feedbackData);
  return response.data;
};

