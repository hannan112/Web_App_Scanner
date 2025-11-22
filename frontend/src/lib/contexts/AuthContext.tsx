// src/lib/contexts/AuthContext.tsx
"use client";

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  email: string;
  username: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  loginWithGoogle: (accessToken: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  checkAuthStatus: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('accessToken');

      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }

      // Verify token with backend
      const rawBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const trimmedBase = rawBase.replace(/\/$/, '');
      const apiBase = /\/api$/.test(trimmedBase) ? trimmedBase : `${trimmedBase}/api`;
      const response = await fetch(`${apiBase}/auth/user/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        // Token is invalid, clear it
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        setUser(null);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const rawBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const trimmedBase = rawBase.replace(/\/$/, '');
      const apiBase = /\/api$/.test(trimmedBase) ? trimmedBase : `${trimmedBase}/api`;
      const response = await fetch(`${apiBase}/auth/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('accessToken', data.access);
        localStorage.setItem('refreshToken', data.refresh);

        await checkAuthStatus();
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || 'Login failed' };
      }
    } catch {
      return { success: false, error: 'Network error' };
    }
  };

  const loginWithGoogle = async (accessToken: string) => {
    try {
      const rawBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const trimmedBase = rawBase.replace(/\/$/, '');
      const apiBase = /\/api$/.test(trimmedBase) ? trimmedBase : `${trimmedBase}/api`;
      const response = await fetch(`${apiBase}/auth/google/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ access_token: accessToken }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('accessToken', data.access);
        localStorage.setItem('refreshToken', data.refresh);

        await checkAuthStatus();
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.error || 'Google login failed' };
      }
    } catch {
      return { success: false, error: 'Network error' };
    }
  };

  const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    setUser(null);
    router.push('/login');
  };

  useEffect(() => {
    checkAuthStatus();
  }, []);

  // Handle redirects based on authentication status
  useEffect(() => {
    if (!loading) {
      const currentPath = window.location.pathname;
      const isAuthPage = ['/login', '/register', '/password-reset'].some(route =>
        currentPath.startsWith(route)
      );
      // Only these are protected, not root/home/blog/contact
      const isProtectedRoute = ['/dashboard', '/projects', '/scans'].some(route =>
        currentPath.startsWith(route)
      );
      // Remove isRootPath logic; root/home should be public
      if (!user && isProtectedRoute) {
        // User not authenticated and trying to access protected route
        const returnUrl = encodeURIComponent(currentPath);
        router.push(`/login?returnUrl=${returnUrl}`);
      } else if (user && isAuthPage) {
        // User authenticated but on auth page (not home)
        router.push('/dashboard');
      }
    }
  }, [user, loading, router]);

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    loginWithGoogle,
    logout,
    checkAuthStatus,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
