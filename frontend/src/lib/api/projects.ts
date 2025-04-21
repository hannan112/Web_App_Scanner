/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
// src/lib/api/projects.ts
import { Project, ProjectStats, DashboardData } from "@/types/project";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface ApiError extends Error {
  response?: {
    data?: {
      detail?: string;
      message?: string;
    };
    status?: number;
  };
}

// Add utility function to safely get access token
const getAccessToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('accessToken');
  }
  return null;
};

// Function to handle API errors
const handleApiError = async (error: ApiError | any): Promise<never> => {
  console.error('API Error:', error);
  
  if (error instanceof Response) {
    try {
      const errorData = await error.json();
      throw new Error(errorData.detail || errorData.message || 'Network response was not ok');
    } catch (e) {
      throw new Error(`HTTP Error: ${error.status} ${error.statusText}`);
    }
  }
  
  if (error.response?.data?.detail) {
    throw new Error(error.response.data.detail);
  }

  if (error.message && typeof error.message === 'string') {
    throw new Error(error.message);
  }
  
  throw new Error('An unknown error occurred');
};

// Get project dashboard data
export const getProjectDashboard = async (): Promise<DashboardData> => {
  try {
    const accessToken = getAccessToken();
    if (!accessToken) {
      throw new Error('No access token found');
    }

    const response = await fetch(`${API_URL}/projects/dashboard/`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw response;
    }

    const data = await response.json();
    if (!data) {
      throw new Error('No data received from server');
    }

    return data;
  } catch (error) {
    throw await handleApiError(error);
  }
};

// Get all projects
export const getProjects = async (): Promise<Project[]> => {
  try {
    const accessToken = getAccessToken();
    if (!accessToken) {
      throw new Error('No access token found');
    }

    const response = await fetch(`${API_URL}/projects/`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw response;
    }

    return await response.json();
  } catch (error) {
    throw await handleApiError(error);
  }
};

// Get project by ID
export const getProjectById = async (id: number | string): Promise<Project> => {
  try {
    const accessToken = getAccessToken();
    if (!accessToken) {
      throw new Error('No access token found');
    }

    const response = await fetch(`${API_URL}/projects/${id}/`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw response;
    }

    return await response.json();
  } catch (error) {
    throw await handleApiError(error);
  }
};

// Get project statistics
export const getProjectStats = async (id: number | string): Promise<ProjectStats> => {
  try {
    const accessToken = getAccessToken();
    if (!accessToken) {
      throw new Error('No access token found');
    }

    const response = await fetch(`${API_URL}/projects/${id}/stats/`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw response;
    }

    return await response.json();
  } catch (error) {
    throw await handleApiError(error);
  }
};

// Create new project
export const createProject = async (projectData: Partial<Project>): Promise<Project> => {
  try {
    const accessToken = getAccessToken();
    if (!accessToken) {
      throw new Error('No access token found');
    }

    const response = await fetch(`${API_URL}/projects/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify(projectData),
    });

    if (!response.ok) {
      throw response;
    }

    return await response.json();
  } catch (error) {
    throw await handleApiError(error);
  }
};

// Update project
export const updateProject = async (id: number | string, projectData: Partial<Project>): Promise<Project> => {
  try {
    const accessToken = getAccessToken();
    if (!accessToken) {
      throw new Error('No access token found');
    }

    const response = await fetch(`${API_URL}/projects/${id}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify(projectData),
    });

    if (!response.ok) {
      throw response;
    }

    return await response.json();
  } catch (error) {
    throw await handleApiError(error);
  }
};

// Delete project
export const deleteProject = async (id: number | string): Promise<void> => {
  try {
    const accessToken = getAccessToken();
    if (!accessToken) {
      throw new Error('No access token found');
    }

    const response = await fetch(`${API_URL}/projects/${id}/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw response;
    }
  } catch (error) {
    throw await handleApiError(error);
  }
};

