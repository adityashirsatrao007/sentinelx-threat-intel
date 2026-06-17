import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://sentinelx-api-2nzs.onrender.com/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatically add JWT token to every request if it exists
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('sentinelx_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Automatically redirect to login if 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('sentinelx_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
