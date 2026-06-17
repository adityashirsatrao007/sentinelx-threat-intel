import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

// Production backend on Render — works from any network, forever
const API_URL = 'https://sentinelx-api-2nzs.onrender.com/api/v1';
console.log('[API] Base URL:', API_URL);

const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    // Bypass ngrok's browser warning interstitial for API calls
    'ngrok-skip-browser-warning': 'true',
    'Content-Type': 'application/json',
  },
});

// Inject Bearer token on every request
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await SecureStore.getItemAsync('userToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (e) {
      // SecureStore may fail in certain environments
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth endpoints
export const authAPI = {
  register: (name, email, password) =>
    api.post('/auth/register', { name, email, password, role: 'user' }),
  login: (email, password) =>
    api.post('/auth/login', { email, password }),
  me: () => api.get('/auth/me'),
};

// Dashboard endpoints
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getThreats: (skip = 0, limit = 20) =>
    api.get(`/dashboard/threats?skip=${skip}&limit=${limit}`),
  getTrends: (days = 7) =>
    api.get(`/dashboard/trends?days=${days}`),
};

// Alerts endpoints
export const alertsAPI = {
  list: (unacknowledgedOnly = false) =>
    api.get(`/alerts?unacknowledged_only=${unacknowledgedOnly}`),
  acknowledge: (alertId) =>
    api.post(`/alerts/${alertId}/acknowledge`),
  acknowledgeAll: () =>
    api.post('/alerts/acknowledge-all'),
};

export default api;
