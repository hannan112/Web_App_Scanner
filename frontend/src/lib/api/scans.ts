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
    const response = await apiClient.get(SCAN_ENDPOINTS.RESULTS(id), {
      params: {
        // Ensure backend does not truncate/limit vulnerabilities
        limit_vulnerabilities: false,
      },
    });
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
 * Get scan progress (real-time updates)
 */
export const getScanProgress = async (id: string) => {
  try {
    const response = await apiClient.get(SCAN_ENDPOINTS.PROGRESS(id));
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
  scan_type: 'passive' | 'active' | 'comprehensive';
  min_confidence: number;
  user_agent?: string;
  request_timeout: number;
  
  // Passive scan tools
  use_sslyze: boolean;
  use_nuclei: boolean;
  use_wappalyzer: boolean;
  use_zap_passive: boolean;
  
  // Active scan settings
  use_zap_active?: boolean;
  enable_spider?: boolean;
  enable_ajax_spider?: boolean;
  max_spider_depth?: number;
  max_spider_duration?: number;
  
  // ZAP Active Scan Configuration
  zap_attack_strength?: 'LOW' | 'MEDIUM' | 'HIGH' | 'INSANE';
  zap_active_scan_policy?: string;
  
  // Vulnerability testing categories
  test_sql_injection?: boolean;
  test_xss?: boolean;
  test_csrf?: boolean;
  test_authentication?: boolean;
  test_authorization?: boolean;
  test_session_management?: boolean;
  test_file_inclusion?: boolean;
  test_path_traversal?: boolean;
  test_command_injection?: boolean;
  test_xxe?: boolean;
  
  // Rate limiting and safety
  max_concurrent_requests?: number;
  request_delay_ms?: number;
  scan_timeout_minutes?: number;
  
  // Enhanced discovery settings
  use_enhanced_discovery?: boolean;
  discovery_timeout?: number;
  max_subdomains?: number;
  max_wayback_urls?: number;
  max_directories?: number;
}) => {
  try {
    // Convert minutes to seconds for backend compatibility
    const processedConfigData = {
      ...configData,
      // Convert spider duration from minutes to seconds (backend expects seconds)
      max_spider_duration: configData.max_spider_duration ? configData.max_spider_duration * 60 : undefined,
      // Convert discovery timeout from seconds to seconds (no conversion needed)
      discovery_timeout: configData.discovery_timeout,
      // Keep scan_timeout_minutes in minutes (backend expects minutes)
      scan_timeout_minutes: configData.scan_timeout_minutes,
    };
    
    console.log('Creating scan configuration with converted values:', {
      original_spider_duration: configData.max_spider_duration,
      converted_spider_duration: processedConfigData.max_spider_duration,
      original_discovery_timeout: configData.discovery_timeout,
      converted_discovery_timeout: processedConfigData.discovery_timeout,
      original_scan_timeout: configData.scan_timeout_minutes,
      converted_scan_timeout: processedConfigData.scan_timeout_minutes,
    });
    
    const response = await apiClient.post(SCAN_ENDPOINTS.CONFIGURATIONS, processedConfigData);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Get ZAP connection status
 */
export const getZAPStatus = async () => {
  try {
    const response = await apiClient.get(SCAN_ENDPOINTS.ZAP_STATUS);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};


/**
 * Get active scan statistics
 */
export const getActiveScanStatistics = async (id: string) => {
  try {
    const response = await apiClient.get(SCAN_ENDPOINTS.STATISTICS(id));
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};
