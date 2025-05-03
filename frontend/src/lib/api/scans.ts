// src/lib/api/scans.ts
import apiClient from './client';
import { SCAN_ENDPOINTS } from './constants';

const handleApiError = (error: unknown) => {
  console.error('API Error:', error);
  if (error && typeof error === 'object' && 'response' in error) {
    const apiError = error as { response?: { data?: { detail?: string } }; message?: string };
    return new Error(apiError.response?.data?.detail || apiError.message || 'An unknown error occurred');
  }
  return new Error('An unknown error occurred');
};

/**
 * Get a scan by ID
 */
export const getScanById = async (id: string) => {
  try {
    const response = await apiClient.get(SCAN_ENDPOINTS.DETAIL(id));
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Get scan results
 */
export const getScanResults = async (id: string) => {
  try {
    const response = await apiClient.get(SCAN_ENDPOINTS.RESULTS(id));
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Get scan status
 */
export const checkScanStatus = async (id: string) => {
  try {
    const response = await apiClient.get(SCAN_ENDPOINTS.STATUS(id));
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Stop a scan
 */
export const stopScan = async (id: string) => {
  try {
    const response = await apiClient.post(SCAN_ENDPOINTS.STOP(id), {});
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Generate a PDF report for a scan
 */
export const generateScanReport = async (id: string) => {
  try {
    const response = await apiClient.post(
      SCAN_ENDPOINTS.REPORT(id),
      {},
      { responseType: 'blob' }
    );
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Get all scans
 */
export const getAllScans = async () => {
  try {
    const response = await apiClient.get(SCAN_ENDPOINTS.LIST);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Create a new scan
 */
export const createScan = async (projectId: string, configId: string) => {
  try {
    const response = await apiClient.post(SCAN_ENDPOINTS.LIST, {
      project: projectId,
      configuration: configId,
    });
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Get scan configurations for a project
 */
export const getScanConfigurations = async (projectId: string) => {
  try {
    const response = await apiClient.get(SCAN_ENDPOINTS.CONFIGURATIONS, {
      params: { project: projectId },
    });
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Create a scan configuration
 */
export const createScanConfiguration = async (configData: {
  project: string;
  scan_type: string;
  crawl_depth: number;
  respect_robots_txt: boolean;
  crawl_max_pages: number;
}) => {
  try {
    const response = await apiClient.post(SCAN_ENDPOINTS.CONFIGURATIONS, configData);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};
