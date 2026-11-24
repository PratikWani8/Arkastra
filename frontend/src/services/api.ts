import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.warn('[API Client Warning]:', error.response?.data?.message || error.message);
    return Promise.reject(error);
  }
);

// System
export const fetchHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

// Dashboard
export const fetchOverview = async () => {
  const response = await apiClient.get('/dashboard/overview');
  return response.data;
};

export const fetchCurrentFlux = async () => {
  const response = await apiClient.get('/dashboard/current-flux');
  return response.data;
};

export const fetchLatestForecast = async () => {
  const response = await apiClient.get('/dashboard/forecast');
  return response.data;
};

export const fetchRecentEvents = async (limit = 10) => {
  const response = await apiClient.get(`/dashboard/recent-events?limit=${limit}`);
  return response.data;
};

// Solar Data
export const fetchSolarFlux = async (limit = 100) => {
  const response = await apiClient.get(`/solar/flux?limit=${limit}`);
  return response.data;
};

export const fetchSolarEvents = async (limit = 50, flareClass = '') => {
  const query = flareClass ? `&flareClass=${flareClass}` : '';
  const response = await apiClient.get(`/solar/events?limit=${limit}${query}`);
  return response.data;
};

export const fetchSolarObservations = async (page = 1, limit = 50) => {
  const response = await apiClient.get(`/solar/observations?page=${page}&limit=${limit}`);
  return response.data;
};

// Forecast
export const triggerForecastPrediction = async (params = {}) => {
  const response = await apiClient.post('/forecast/predict', params);
  return response.data;
};

export const fetchForecastHistory = async (page = 1, limit = 20, riskLevel = '', verificationStatus = '') => {
  let query = `?page=${page}&limit=${limit}`;
  if (riskLevel) query += `&riskLevel=${riskLevel}`;
  if (verificationStatus) query += `&verificationStatus=${verificationStatus}`;
  const response = await apiClient.get(`/forecast/history${query}`);
  return response.data;
};

export const fetchForecastById = async (id: string) => {
  const response = await apiClient.get(`/forecast/${id}`);
  return response.data;
};

// Model Scientific Metrics
export const fetchModelMetrics = async () => {
  const response = await apiClient.get('/model/metrics');
  return response.data;
};

export const fetchModelBaselineComparison = async () => {
  const response = await apiClient.get('/model/baseline-comparison');
  return response.data;
};

export const fetchModelMetadata = async () => {
  const response = await apiClient.get('/model/metadata');
  return response.data;
};

export const fetchFeatureImportance = async () => {
  const response = await apiClient.get('/model/feature-importance');
  return response.data;
};
