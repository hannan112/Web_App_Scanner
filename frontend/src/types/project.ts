/* eslint-disable @typescript-eslint/no-explicit-any */
// src/types/project.ts

// Basic project information
export interface Project {
    id: number;
    name: string;
    target_url: string;
    description: string;
    created_at: string;
    updated_at: string;
    last_scan_date: any;
    scan_count: number;
  }
  
  // Project statistics interface
  export interface ProjectStats {
    project: {
      id: string;
      name: string;
      target_url: string;
      description?: string;
      created_at: string;
    };
    scan_stats: {
      total_scans: number;
      scan_counts_by_type: Record<string, number>;
      vulnerability_counts: Record<string, number>;
      recent_scans: Array<{
        id: string;
        scan_type: string;
        status: string;
        start_time: string;
        end_time?: string;
      }>;
    };
    total_scans: number;
    vulnerabilities: {
      critical: number;
      high: number;
      medium: number;
      low: number;
      info: number;
    };
    last_scan_date: string | null;
    scan_status: string | null;
  }
  
  // Dashboard data for project overview
  export interface DashboardData {
    total_projects: number;
    new_projects_last_month: number;
    projects_count: number;
    recent_projects: Project[];
    vulnerabilities_summary: {
      critical: number;
      high: number;
      medium: number;
      low: number;
      info: number;
    };
    scan_stats: {
      total: number;
      completed: number;
      in_progress: number;
      failed: number;
    };
  }
  
  // Scan configuration interface
  export interface ScanConfig {
    scan_depth: number;
    respect_robots_txt: boolean;
    scan_intensity: number;
    user_agent?: string;
    request_delay: number;
    custom_headers?: Record<string, string>;
  }
  
  // Scan result interface
  export interface ScanResult {
    id: number;
    vulnerability_type: string;
    severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
    confidence: number;
    description: string;
    affected_url: string;
    remediation: string;
    created_at: string;
  }
  
  // Scan interface
  export interface Scan {
    id: number;
    project_id: number;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    started_at: string | null;
    completed_at: string | null;
    created_at: string;
    config: ScanConfig;
    results?: ScanResult[];
  }