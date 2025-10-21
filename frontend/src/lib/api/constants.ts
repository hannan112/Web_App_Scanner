// src/lib/api/constants.ts
// Base API URL - you can override this with an environment variable
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Auth endpoints
export const AUTH_ENDPOINTS = {
  LOGIN: `${API_URL}/api/auth/login/`,
  REGISTER: `${API_URL}/api/auth/register/`,
  VERIFY_EMAIL: (token: string) => `${API_URL}/api/auth/verify-email/${token}/`,
  PASSWORD_RESET_REQUEST: `${API_URL}/api/auth/request-password-reset/`,
  PASSWORD_RESET_CONFIRM: `${API_URL}/api/auth/password-reset/confirm/`,
  GOOGLE_AUTH: `${API_URL}/api/auth/google/`,
  TOKEN_REFRESH: `${API_URL}/api/auth/token/refresh/`,
  // Add a root path for easier imports
  ROOT: `${API_URL}/api/auth`
};

// Project endpoints
export const PROJECT_ENDPOINTS = {
  LIST: `${API_URL}/api/projects/`,
  DETAIL: (id: string | number) => `${API_URL}/api/projects/${id}/`,
  STATS: (id: string | number) => `${API_URL}/api/projects/${id}/stats/`,
  DASHBOARD: `${API_URL}/api/projects/dashboard/`,
  // Add a root path for easier imports
  ROOT: `${API_URL}/api/projects`
};

export const SCAN_ENDPOINTS = {
  LIST: `${API_URL}/api/scanning/scans/`,
  DETAIL: (id: string | number) => `${API_URL}/api/scanning/scans/${id}/`,
  STATUS: (id: string | number) => `${API_URL}/api/scanning/scans/${id}/status/`,
  PROGRESS: (id: string | number) => `${API_URL}/api/scanning/scans/${id}/progress/`,
  RESULTS: (id: string | number) => `${API_URL}/api/scanning/scans/${id}/results/`,
  STOP: (id: string | number) => `${API_URL}/api/scanning/scans/${id}/stop/`,
  REPORT: (id: string | number) => `${API_URL}/api/scanning/scans/${id}/report/`,
  STATISTICS: (id: string | number) => `${API_URL}/api/scanning/scans/${id}/statistics/`,
  CONFIGURATIONS: `${API_URL}/api/scanning/configurations/`,
  ZAP_STATUS: `${API_URL}/api/scanning/zap/status/`,
  ROOT: `${API_URL}/api/scanning`
};
