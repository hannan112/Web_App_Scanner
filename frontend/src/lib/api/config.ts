/* eslint-disable @typescript-eslint/no-explicit-any */
// src/lib/api/config.ts
import axios from 'axios';

// Normalize API base URL to ensure exactly one /api prefix
const RAW_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const TRIMMED_API_URL = RAW_API_URL.replace(/\/$/, '');
export const API_URL = /\/api$/.test(TRIMMED_API_URL)
  ? TRIMMED_API_URL
  : `${TRIMMED_API_URL}/api`;

// Create axios instance with the correct base URL
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('accessToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Export helper functions
export const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('accessToken');
  }
  return null;
};

// Add this for token refresh handling
export const setupInterceptors = (refreshTokenFn: () => Promise<any>) => {
  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      if (
        error.response?.status === 401 &&
        !originalRequest._retry &&
        typeof window !== 'undefined' &&
        localStorage.getItem('refreshToken')
      ) {
        originalRequest._retry = true;
        try {
          await refreshTokenFn();

          // Retry the original request with new token
          const token = localStorage.getItem('accessToken');
          if (token) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    }
  );
};

api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('accessToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    console.error("API Request error:", error);
    return Promise.reject(error);
  }
);

// Add response interceptor for better error logging
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response) {
      console.error(`API Error (${error.response.status}):`, error.response.data);

      // If unauthorized, log token state
      if (error.response.status === 401) {
        console.warn("401 Unauthorized: Token state check:", {
          access: localStorage.getItem('accessToken') ? "Present" : "Missing",
          refresh: localStorage.getItem('refreshToken') ? "Present" : "Missing"
        });
      }
    }
    return Promise.reject(error);
  }
);

export { api };