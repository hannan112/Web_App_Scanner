// src/lib/api/constants.ts
// Base API URL - normalize to include exactly one /api
const RAW_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const TRIMMED_API_URL = RAW_API_URL.replace(/\/$/, '');
export const API_URL = /\/api$/.test(TRIMMED_API_URL)
  ? TRIMMED_API_URL
  : `${TRIMMED_API_URL}/api`;

// Auth endpoints
export const AUTH_ENDPOINTS = {
  LOGIN: `${API_URL}/auth/login/`,
  REGISTER: `${API_URL}/auth/register/`,
  VERIFY_EMAIL: (token: string) => `${API_URL}/auth/verify-email/${token}/`,
  PASSWORD_RESET_REQUEST: `${API_URL}/auth/request-password-reset/`,
  PASSWORD_RESET_CONFIRM: `${API_URL}/auth/password-reset/confirm/`,
  GOOGLE_AUTH: `${API_URL}/auth/google/`,
  TOKEN_REFRESH: `${API_URL}/auth/token/refresh/`,
  // Add a root path for easier imports
  ROOT: `${API_URL}/auth`
};

// Project endpoints
export const PROJECT_ENDPOINTS = {
  LIST: `${API_URL}/projects/`,
  DETAIL: (id: string | number) => `${API_URL}/projects/${id}/`,
  STATS: (id: string | number) => `${API_URL}/projects/${id}/stats/`,
  DASHBOARD: `${API_URL}/projects/dashboard/`,
  // Add a root path for easier imports
  ROOT: `${API_URL}/projects`
};

export const SCAN_ENDPOINTS = {
  LIST: `${API_URL}/scanning/scans/`,
  DETAIL: (id: string | number) => `${API_URL}/scanning/scans/${id}/`,
  STATUS: (id: string | number) => `${API_URL}/scanning/scans/${id}/status/`,
  PROGRESS: (id: string | number) => `${API_URL}/scanning/scans/${id}/progress/`,
  RESULTS: (id: string | number) => `${API_URL}/scanning/scans/${id}/results/`,
  STOP: (id: string | number) => `${API_URL}/scanning/scans/${id}/stop/`,
  REPORT: (id: string | number) => `${API_URL}/scanning/scans/${id}/report/`,
  STATISTICS: (id: string | number) => `${API_URL}/scanning/scans/${id}/statistics/`,
  CONFIGURATIONS: `${API_URL}/scanning/configurations/`,
  ZAP_STATUS: `${API_URL}/scanning/zap/status/`,
  ROOT: `${API_URL}/scanning`
};
