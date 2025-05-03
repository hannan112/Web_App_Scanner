/* eslint-disable @typescript-eslint/no-unused-vars */
// src/lib/api/projects.ts
import apiClient from './client';
import { Project, ProjectStats, DashboardData } from "@/types/project";
import { PROJECT_ENDPOINTS } from './constants';

/**
 * Handles API error consistently
 */
const handleApiError = (error: unknown) => {
  console.error('API Error:', error);

  if (typeof error === 'object' && error !== null && 'response' in error &&
      typeof error.response === 'object' && error.response !== null &&
      'data' in error.response && typeof error.response.data === 'object' &&
      error.response.data !== null && 'detail' in error.response.data) {
    return new Error(error.response.data.detail as string);
  }

  if (typeof error === 'object' && error !== null && 'message' in error && typeof error.message === 'string') {
    return new Error(error.message);
  }

  return new Error('An unknown error occurred');
};

/**
 * Get project dashboard data
 */
export const getProjectDashboard = async (): Promise<DashboardData> => {
  try {
    // Use a direct string URL here instead of the constants object
    const response = await apiClient.get('/api/projects/dashboard/');
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

// Similarly update other functions
export const getProjects = async (): Promise<Project[]> => {
  try {
    const response = await apiClient.get('/api/projects/');
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

export const getProjectById = async (id: number | string): Promise<Project> => {
  try {
    const response = await apiClient.get(`/api/projects/${id}/`);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

export const getProjectStats = async (id: number | string): Promise<ProjectStats> => {
  try {
    const response = await apiClient.get(`/api/projects/${id}/stats/`);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

export const createProject = async (projectData: Partial<Project>): Promise<Project> => {
  try {
    const response = await apiClient.post('/api/projects/', projectData);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

export const updateProject = async (id: number | string, projectData: Partial<Project>): Promise<Project> => {
  try {
    const response = await apiClient.patch(`/api/projects/${id}/`, projectData);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

export const deleteProject = async (id: number | string): Promise<void> => {
  try {
    await apiClient.delete(`/api/projects/${id}/`);
  } catch (error) {
    throw handleApiError(error);
  }
};