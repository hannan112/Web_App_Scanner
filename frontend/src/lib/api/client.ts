/* eslint-disable @typescript-eslint/no-unused-vars */
// src/lib/api/client.ts
import axios from 'axios';

// Base API URL
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL, // Use just the base URL here, not combined with /api
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Get token from localStorage directly each time
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('accessToken');
      
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Get the refresh token
        const refreshToken = localStorage.getItem('refreshToken');
        
        if (refreshToken) {
          // Call your token refresh endpoint
          const response = await axios.post('/api/auth/token/refresh/', { 
            refresh: refreshToken 
          });
          
          const { access } = response.data;
          
          // Update stored token
          localStorage.setItem('accessToken', access);
          
          // Update the authorization header
          originalRequest.headers.Authorization = `Bearer ${access}`;
          
          // Retry the original request
          return axios(originalRequest);
        }
      } catch (refreshError) {
        // If refresh fails, redirect to login
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login?error=session_expired';
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;