// src/types/api.ts - Standardized API types
export interface ApiResponse<T> {
    data: T;
    message?: string;
    status: string;
  }
  
  export interface PaginatedResponse<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
  }
  
  // Authentication types
  export interface UserCredentials {
    email: string;
    password: string;
  }
  
  export interface AuthUser {
    id: string | number;
    email: string;
    username?: string;
  }
  
  export interface AuthResponse {
    access: string;
    refresh: string;
    user: AuthUser;
  }