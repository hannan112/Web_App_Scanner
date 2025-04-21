// auth.ts - Authentication service for Next.js frontend

// Single declaration of API_URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Interface definitions
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

interface AuthResponse {
  access: string;
  refresh: string;
  user?: {
    id: number;
    email: string;
    username: string;
  };
}

// Login function
export const login = async (credentials: UserCredentials): Promise<AuthResponse> => {
  try {
    const response = await fetch(`${API_URL}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Login failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

// Register function
export const register = async (userData: RegistrationData): Promise<{ message: string }> => {
  try {
    const response = await fetch(`${API_URL}/auth/register/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Registration failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
};

// Verify email function
export const verifyEmail = async (token: string): Promise<{ message: string }> => {
  try {
    const response = await fetch(`${API_URL}/auth/verify-email/${token}/`, {
      method: 'GET',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Email verification failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Email verification error:', error);
    throw error;
  }
};

// Request password reset function
export const requestPasswordReset = async (email: string): Promise<{ message: string }> => {
  try {
    const response = await fetch(`${API_URL}/auth/request-password-reset/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Password reset request failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Password reset request error:', error);
    throw error;
  }
};

// Reset password function
export const resetPassword = async (token: string, password: string): Promise<{ message: string }> => {
  try {
    const response = await fetch(`${API_URL}/auth/reset-password/${token}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Password reset failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Password reset error:', error);
    throw error;
  }
};

// Confirm password reset function (DRF style with uid and token)
export const confirmPasswordReset = async (
  uid: string,
  token: string,
  newPassword: string
): Promise<void> => {
  try {
    const response = await fetch(`${API_URL}/auth/password/reset/confirm/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        uid,
        token,
        new_password: newPassword,
      }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to reset password');
    }
  } catch (error) {
    console.error('Confirm password reset error:', error);
    throw error;
  }
};

// Google OAuth login function
export const googleLogin = async (token: string): Promise<AuthResponse> => {
  try {
    const response = await fetch(`${API_URL}/auth/google/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Google login failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Google login error:', error);
    throw error;
  }
};

// Token refresh function
export const refreshToken = async (refresh: string): Promise<{ access: string }> => {
  try {
    const response = await fetch(`${API_URL}/auth/token/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Token refresh failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Token refresh error:', error);
    throw error;
  }
};

// No redundant re-exports at the bottom of the file
// All functions are exported directly using the export keyword