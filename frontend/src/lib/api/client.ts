// src/lib/api/client.ts
import axios from 'axios';
import { getSession } from 'next-auth/react';

// Base API URL
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor with async token retrieval
apiClient.interceptors.request.use(
  async (config) => {
    // Try to get token from nextauth session first (more reliable)
    try {
      const session = await getSession();
      const token = session?.accessToken;
      
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        return config;
      }
    } catch (e) {
      console.error("Error getting session:", e);
    }
    
    // Fallback to localStorage
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

// Improve the response interceptor for 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Handle 401 errors (unauthorized)
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Get refresh token
        const refreshToken = localStorage.getItem('refreshToken');
        
        if (refreshToken) {
          // Try to refresh the token
          const response = await axios.post(`${API_URL}/api/auth/token/refresh/`, {
            refresh: refreshToken
          });
          
          if (response.data.access) {
            // Update tokens in localStorage
            localStorage.setItem('accessToken', response.data.access);
            
            // Update the authorization header
            originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
            
            // Retry the original request
            return axios(originalRequest);
          }
        }
      } catch (refreshError) {
        console.error("Token refresh failed:", refreshError);
        
        // Clear tokens and redirect to login
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        
        // Only redirect if in browser
        if (typeof window !== 'undefined') {
          window.location.href = '/login?error=session_expired';
        }
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;