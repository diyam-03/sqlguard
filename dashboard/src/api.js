import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE,
});

// Attach token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const login = (username, password) =>
  api.post('/auth/login', { username, password });

export const register = (username, password, role) =>
  api.post('/auth/register', { username, password, role });

// Detection
export const detectQuery = (sql_query, user_id = 1) =>
  api.post('/detect', { sql_query, user_id, session_id: 'dashboard' });

// Stats
export const getStats = () => api.get('/stats');
export const getTrends = () => api.get('/stats/trends');
export const getDistribution = () => api.get('/stats/distribution');

// Queries
export const getQueries = (limit = 50) =>
  api.get(`/queries?limit=${limit}`);

// Alerts
export const getAlerts = (limit = 20) =>
  api.get(`/alerts?limit=${limit}`);

export default api;