
// src/lib/api/client.ts
import axios from 'axios';

// Base API URL normalized to include exactly one /api
const RAW_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const TRIMMED_API_URL = RAW_API_URL.replace(/\/$/, '');
export const API_URL = /\/api$/.test(TRIMMED_API_URL)
  ? TRIMMED_API_URL
  : `${TRIMMED_API_URL}/api`;

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Do not send cookies; use JWT Authorization header to avoid CSRF
  withCredentials: false,
});

// Add request interceptor with Django JWT token retrieval
apiClient.interceptors.request.use(
  async (config) => {
    // Use only Django JWT tokens from localStorage
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('accessToken');
      
      if (token) {
        console.log('🔐 Using Django JWT token:', token.substring(0, 20) + '...');
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
      
      console.log('🔄 Got 401, attempting token refresh...');
      
      try {
        // Get refresh token
        const refreshToken = localStorage.getItem('refreshToken');
        
        console.log('🔄 Refresh token exists:', !!refreshToken);
        
        if (refreshToken) {
          // Try to refresh the token
          console.log('🔄 Attempting refresh with endpoint:', `${API_URL}/auth/token/refresh/`);
          
          const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
            refresh: refreshToken
          });
          
          console.log('🔄 Refresh response:', response.status, response.data);
          
          if (response.data.access) {
            console.log('✅ Token refresh successful, updating tokens...');
            // Update tokens in localStorage
            localStorage.setItem('accessToken', response.data.access);
            
            // Update the authorization header
            originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
            
            // Retry the original request
            console.log('🔄 Retrying original request...');
            return axios(originalRequest);
          } else {
            console.log('❌ No access token in refresh response');
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