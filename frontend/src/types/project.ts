/* eslint-disable @typescript-eslint/no-explicit-any */
// src/types/project.ts
import { Key, ReactNode } from "react";

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
    id: Key | null | undefined;
    name: ReactNode;
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
    use_zap_active: boolean;
    enable_spider: boolean;
    enable_ajax_spider: boolean;
    max_spider_depth: number;
    max_spider_duration: number;
    
    // ZAP Active Scan Configuration
    zap_attack_strength: 'LOW' | 'MEDIUM' | 'HIGH' | 'INSANE';
    zap_active_scan_policy: string;
    
    // Vulnerability testing categories
    test_sql_injection: boolean;
    test_xss: boolean;
    test_csrf: boolean;
    test_authentication: boolean;
    test_authorization: boolean;
    test_session_management: boolean;
    test_file_inclusion: boolean;
    test_path_traversal: boolean;
    test_command_injection: boolean;
    test_xxe: boolean;
    
    // SQL Injection testing tools
    use_sqlmap: boolean;
    use_nosqlmap: boolean;
    sqlmap_risk_level: number;
    sqlmap_level: number;
    sqlmap_timeout: number;
    
    // Rate limiting and safety
    max_concurrent_requests: number;
    request_delay_ms: number;
    scan_timeout_minutes: number;
    
    // Enhanced discovery settings
    use_enhanced_discovery: boolean;
    discovery_timeout: number;
    max_subdomains: number;
    max_wayback_urls: number;
    max_directories: number;
}

// Scan result interface
export interface ScanResult {
    id: number;
    name: string;
    vulnerability_type: string;
    severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
    confidence: number;
    description: string;
    url?: string;
    parameter?: string;
    evidence?: string;
    affected_url?: string;
    remediation: string;
    created_at: string;
}

// Scan interface
export interface Scan {
    configuration_name: string;
    id: number;
    project_id: number;
    status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'stopped';
    started_at: string | null;
    completed_at: string | null;
    created_at: string;
    config: ScanConfig;
    results?: ScanResult[];
}

// AJAX Spider related interfaces
export interface AjaxSpiderUrlData {
    url: string;
    source: string;
    text: string;
    parent: string;
}

export interface AjaxSpiderFormData {
    url: string;
    action: string;
    method: string;
    inputs: Array<{
        name: string;
        type: string;
        value: string;
        required: boolean;
    }>;
}

export interface AjaxSpiderRequestData {
    url: string;
    method: string;
    resourceType: string;
    timestamp: string;
    isAjax: boolean;
}

export interface AjaxSpiderResult {
    id: number;
    scan: number;
    urls_discovered: AjaxSpiderUrlData[];
    forms_discovered: AjaxSpiderFormData[];
    ajax_requests: AjaxSpiderRequestData[];
    javascript_objects: Record<string, any>;
    start_time: string;
    end_time: string;
    duration: number;
    pages_crawled: number;
    created_at: string;
}

// New Passive Recon Result interface
export interface PassiveReconResult {
    id: number;
    scan: number;
    dns_records?: Record<string, any>;
    server_info?: Record<string, any>;
    robots_txt?: string;
    sitemap_xml?: string | any[];
    technologies?: Record<string, any>;
    response_headers?: Record<string, any>;
    enhanced_discovery?: Record<string, any>;
    urls_discovered?: string[];
    forms_discovered?: Record<string, any>[];
    cookies?: Record<string, string>;
    created_at: string;
}

// Active Scan Result interface
export interface ActiveScanResult {
    id: number;
    scan: number;
    spider_results?: Record<string, any>;
    ajax_spider_results?: Record<string, any>;
    urls_discovered?: string[];
    forms_discovered?: Record<string, any>[];
    attack_surface?: Record<string, any>;
    raw_findings?: Record<string, any>;
    authentication_tests?: Record<string, any>;
    session_analysis?: Record<string, any>;
    zap_scan_id?: string;
    zap_spider_id?: string;
    zap_ajax_spider_id?: string;
    zap_active_scan_id?: string;
    total_requests_made: number;
    total_responses_received: number;
    scan_duration_seconds: number;
    created_at: string;
    
    // Enhanced discovery fields
    api_endpoints?: string[];
    js_endpoints?: string[];
    discovery_tools_used?: string[];
    discovery_stats?: Record<string, any>;
    total_urls?: number;
    total_forms?: number;
}

// Crawl data interface
export interface CrawlData {
    pages_crawled: number;
    urls_count: number;
    forms_count: number;
}

// ScanResultData interface (what's returned from the API)
export interface ScanResultData {
    id: number;
    uuid: string;
    status: string;
    progress: number;
    start_time: string;
    end_time: string;
    error_message: string | null;
    created_at: string;
    updated_at: string;
    configuration: ScanConfig;
    vulnerabilities: ScanResult[];
    passive_data?: PassiveReconResult;
    active_data?: ActiveScanResult;
    crawl_data?: CrawlData;
    ajax_spider_data?: AjaxSpiderResult;
    project_info?: {
        id: number;
        name: string;
        target_url: string;
    };
}

// ZAP Connection Status interface
export interface ZAPStatus {
    status: 'connected' | 'disconnected' | 'error';
    version?: string;
    url?: string;
    error?: string;
}

// Scan Statistics interface
export interface ScanStatistics {
    spider_urls_found: number;
    ajax_spider_urls_found: number;
    total_vulnerabilities: number;
    vulnerability_severity_breakdown: {
        critical: number;
        high: number;
        medium: number;
        low: number;
        info: number;
    };
    scan_duration: string;
    zap_version: string;
}