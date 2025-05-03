/* eslint-disable @typescript-eslint/no-explicit-any */
// src/lib/api/auth.ts
import apiClient from './client';
import { AUTH_ENDPOINTS } from './constants';

interface UserCredentials {
  email: string;
  password: string;
}

interface RegistrationData {
  email: string;
  username: string;
  password: string;
  confirmPassword?: string;
}

interface ApiError {
  response?: {
    data?: {
      detail?: string;
      message?: string;
    };
  };
  message?: unknown;
}

const handleApiError = (error: unknown) => {
  console.error('API Error:', error);
  
  const err = error as ApiError;
  if (err.response?.data?.detail) {
    return new Error(err.response.data.detail);
  }
  
  if (err.response?.data?.message) {
    return new Error(err.response.data.message);
  }
  
  if ((error as any).message && typeof (error as any).message === 'string') {
    return new Error((error as any).message);
  }
  
  return new Error('An unknown error occurred');
};

export const login = async (credentials: UserCredentials) => {
  try {
    const response = await apiClient.post(`${AUTH_ENDPOINTS}/login/`, credentials);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

export const register = async (userData: RegistrationData) => {
  try {
    const response = await apiClient.post(`${AUTH_ENDPOINTS}/register/`, userData);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

export const verifyEmail = async (token: string) => {
  try {
    const response = await apiClient.get(`${AUTH_ENDPOINTS}/verify-email/${token}/`);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

export const requestPasswordReset = async (email: string) => {
  try {
    const response = await apiClient.post(`${AUTH_ENDPOINTS}/request-password-reset/`, { email });
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

export const confirmPasswordReset = async (uid: string, token: string, newPassword: string) => {
  try {
    await apiClient.post(`${AUTH_ENDPOINTS}/password-reset/confirm/`, {
      uid,
      token,
      new_password: newPassword,
    });
  } catch (error) {
    throw handleApiError(error);
  }
};

export const changePassword = async (oldPassword: string, newPassword: string) => {
  try {
    const response = await apiClient.post(`${AUTH_ENDPOINTS}/password/change/`, {
      old_password: oldPassword,
      new_password: newPassword
    });
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};