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

const handleApiError = (error: unknown) => {
  console.error('API Error:', error);

  const err = error as any;

  // Handle axios error response
  if (err.response?.data) {
    const data = err.response.data;

    // Check for field-specific validation errors (Django serializer format)
    if (typeof data === 'object' && !data.detail && !data.message) {
      // Extract first error from validation errors object
      const errorKeys = Object.keys(data);
      if (errorKeys.length > 0) {
        const firstKey = errorKeys[0];
        const firstError = data[firstKey];
        if (Array.isArray(firstError) && firstError.length > 0) {
          return new Error(`${firstKey}: ${firstError[0]}`);
        } else if (typeof firstError === 'string') {
          return new Error(`${firstKey}: ${firstError}`);
        }
      }
    }

    // Check for detail or message fields
    if (data.detail) {
      return new Error(data.detail);
    }

    if (data.message) {
      return new Error(data.message);
    }

    // If it's a string, use it directly
    if (typeof data === 'string') {
      return new Error(data);
    }
  }

  // Handle network errors
  if (err.message && typeof err.message === 'string') {
    if (err.message.includes('Network Error') || err.message.includes('timeout')) {
      return new Error('Network error. Please check your connection and try again.');
    }
    return new Error(err.message);
  }

  return new Error('An unknown error occurred. Please try again.');
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
    // Convert field name for backend compatibility
    const backendData = {
      ...userData,
      password_confirm: userData.confirmPassword,
    };
    delete backendData.confirmPassword;

    const response = await apiClient.post(AUTH_ENDPOINTS.REGISTER, backendData);
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