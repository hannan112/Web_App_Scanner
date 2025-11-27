/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
// src/app/(dashboard)/projects/[id]/scans/new/page.tsx

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/contexts/AuthContext";
import Link from "next/link";
import { getProjectById } from "@/lib/api/projects";
import { createScan, createScanConfiguration } from "@/lib/api/scans";
import PageTitle from "@/components/PageTitle";


export default function NewProjectScanPage({ params }: { params: Promise<{ id: string }> }) {
  const { user, loading: authLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  const [projectId, setProjectId] = useState<string>("");
  const [projectName, setProjectName] = useState<string>("");
  const [customConfigs, setCustomConfigs] = useState({
    scan_type: "passive" as 'passive' | 'active' | 'comprehensive',
    min_confidence: 0.7,
    user_agent: "",
    request_timeout: 30,

    // Passive scan tools
    use_sslyze: true,
    use_nuclei: true,
    use_wappalyzer: true,
    use_zap_passive: true,

    // Active scan settings
    use_zap_active: true,
    enable_spider: true,
    enable_ajax_spider: true,
    max_spider_depth: 3,
    max_spider_duration: 10, // 10 minutes

    // ZAP Active Scan Configuration
    zap_attack_strength: "MEDIUM" as 'LOW' | 'MEDIUM' | 'HIGH' | 'INSANE',
    zap_active_scan_policy: "Default Policy",

    // Vulnerability testing categories
    test_sql_injection: true,
    test_xss: true,
    test_csrf: true,
    test_authentication: true,
    test_authorization: true,
    test_session_management: true,
    test_file_inclusion: false,
    test_path_traversal: false,
    test_command_injection: true,
    test_xxe: true,

    // SQL Injection testing tools
    use_sqlmap: true,
    use_nosqlmap: false,
    sqlmap_risk_level: 2,
    sqlmap_level: 2,
    sqlmap_timeout: 300,

    // Rate limiting and safety
    max_concurrent_requests: 5,
    request_delay_ms: 100,
    scan_timeout_minutes: 60,

    // Enhanced discovery settings
    use_enhanced_discovery: true,
    discovery_timeout: 30,
    max_subdomains: 100,
    max_wayback_urls: 200,
    max_directories: 50,
  });

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Resolve params first
  useEffect(() => {
    params.then(resolvedParams => {
      setProjectId(resolvedParams.id);
    });
  }, [params]);

  // Check if user is authenticated
  useEffect(() => {
    if (authLoading) return;

    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  // Fetch project and scan configurations
  useEffect(() => {
    const fetchData = async () => {
      if (authLoading || !isAuthenticated || !projectId) return;

      try {
        // Get project details
        const project = await getProjectById(projectId);
        setProjectName(project.name);

        // Always use default configuration for new scans
      } catch (err: any) {
        console.error("Error fetching project data:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [projectId, isAuthenticated, authLoading]);

  // Handle custom config changes
  const handleCustomConfigChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;

    setCustomConfigs(prev => ({
      ...prev,
      [name]: type === 'checkbox'
        ? (e.target as HTMLInputElement).checked
        : type === 'number'
          ? parseFloat(value)
          : value
    }));
  };

  // Get scan type description
  const getScanTypeDescription = (scanType: string) => {
    switch (scanType) {
      case 'passive':
        return 'Safe information gathering without active testing. Analyzes DNS, SSL, headers, and technologies.';
      case 'active':
        return 'Comprehensive vulnerability testing with active probing. May send test payloads to the target.';
      case 'comprehensive':
        return 'Combines passive reconnaissance with active vulnerability testing for complete coverage.';
      default:
        return '';
    }
  };

  // Check if active scanning features are selected
  const isActiveScanning = customConfigs.scan_type === 'active' || customConfigs.scan_type === 'comprehensive';

  // Start scan handler
  const handleStartScan = async () => {
    setSubmitting(true);
    setError(null);

    try {
      // Create a scan configuration
      try {
        const configData = {
          project: projectId,
          ...customConfigs
        };

        console.log("Final config data being sent:", configData);
        console.log("Active scanning fields:", {
          use_zap_active: configData.use_zap_active,
          enable_spider: configData.enable_spider,
          enable_ajax_spider: configData.enable_ajax_spider,
          max_spider_depth: configData.max_spider_depth,
          test_sql_injection: configData.test_sql_injection
        });

        // Call an API function to create configuration
        const createdConfig = await createScanConfiguration(configData);
        const configId = createdConfig.id;
        console.log("Created configuration:", createdConfig);

        // Now create the scan with the project ID and config ID
        console.log(`Creating scan for project ${projectId} with config ${configId}`);
        const scan = await createScan(projectId, configId);
        console.log("Created scan:", scan);

        // Redirect to scan status page
        router.push(`/scans/${scan.id}/status`);
      } catch (configErr: unknown) {
        console.error("Configuration creation error:", configErr);
        const errorMessage = configErr instanceof Error ? configErr.message : 'Unknown error occurred';
        throw new Error("Failed to create scan configuration: " + errorMessage);
      }
    } catch (err: any) {
      console.error("Scan creation error:", err);
      setError(err.message || "Failed to start scan");
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-6 h-6 border-4 border-t-blue-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <PageTitle
        title="Start New Security Scan"
        subtitle={`Configure and run a security scan for ${projectName}`}
      />

      <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-lg p-6 rounded-lg mb-6">
        {error && (
          <div className="p-3 mb-4 text-sm text-red-600 bg-red-100/80 backdrop-blur-sm rounded border border-red-200">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {/* Scan Type Selection */}
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-medium text-slate-900">Security Scan Configuration</h2>
              <p className="text-sm text-slate-600">
                Configure your security scan settings. Choose from passive, active, or comprehensive scanning modes.
              </p>
            </div>



            <div className="space-y-4">
              <div>
                <label htmlFor="scan_type" className="block text-sm font-medium text-slate-700 mb-2">
                  Scan Type
                </label>
                <select
                  id="scan_type"
                  name="scan_type"
                  value={customConfigs.scan_type}
                  onChange={handleCustomConfigChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="passive">Passive - Information Gathering</option>
                  <option value="active">Active - Vulnerability Testing</option>
                  <option value="comprehensive">Comprehensive - Complete Assessment</option>
                </select>
                <p className="mt-2 text-sm text-slate-600">
                  {getScanTypeDescription(customConfigs.scan_type)}
                </p>

                {/* Scan type specific warnings */}
                {customConfigs.scan_type === 'passive' && (
                  <div className="mt-3 p-3 bg-blue-50/80 backdrop-blur-sm border border-blue-200 rounded-md">
                    <p className="text-sm text-blue-800">
                      <strong>Safe Mode:</strong> Passive scanning only gathers information without active testing.
                      It&apos;s safe to run on any website and won&apos;t impact performance.
                    </p>
                  </div>
                )}

                {customConfigs.scan_type === 'active' && (
                  <div className="mt-3 p-3 bg-yellow-50/80 backdrop-blur-sm border border-yellow-200 rounded-md">
                    <p className="text-sm text-yellow-800">
                      <strong>Active Testing:</strong> This scan actively tests for vulnerabilities by sending specialized requests.
                      Only scan websites you have permission to test.
                    </p>
                  </div>
                )}

                {customConfigs.scan_type === 'comprehensive' && (
                  <div className="mt-3 p-3 bg-orange-50/80 backdrop-blur-sm border border-orange-200 rounded-md">
                    <p className="text-sm text-orange-800">
                      <strong>Complete Assessment:</strong> Combines passive reconnaissance with active vulnerability testing.
                      Ensure you have explicit permission before running this scan type.
                    </p>
                  </div>
                )}
              </div>

              {/* General Configuration */}
              <div className="space-y-4">
                <h3 className="text-md font-medium text-slate-900">General Configuration</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="min_confidence" className="block text-sm font-medium text-slate-700 mb-1">
                      Minimum Confidence
                    </label>
                    <input
                      type="number"
                      id="min_confidence"
                      name="min_confidence"
                      min="0.1"
                      max="1.0"
                      step="0.1"
                      value={customConfigs.min_confidence}
                      onChange={handleCustomConfigChange}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                    <p className="mt-1 text-xs text-slate-500">
                      Minimum confidence level for findings (0.1-1.0)
                    </p>
                  </div>

                  <div>
                    <label htmlFor="request_timeout" className="block text-sm font-medium text-slate-700 mb-1">
                      Request Timeout (seconds)
                    </label>
                    <input
                      type="number"
                      id="request_timeout"
                      name="request_timeout"
                      min="5"
                      max="120"
                      value={customConfigs.request_timeout}
                      onChange={handleCustomConfigChange}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                    <p className="mt-1 text-xs text-slate-500">
                      Timeout for HTTP requests (5-120 seconds)
                    </p>
                  </div>
                </div>

                <div>
                  <label htmlFor="user_agent" className="block text-sm font-medium text-slate-700 mb-1">
                    Custom User Agent (Optional)
                  </label>
                  <input
                    type="text"
                    id="user_agent"
                    name="user_agent"
                    value={customConfigs.user_agent}
                    onChange={handleCustomConfigChange}
                    placeholder="SecurityScannerBot/1.0"
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    Custom user agent string for HTTP requests
                  </p>
                </div>
              </div>

              {/* Passive Scan Tools */}
              <div className="space-y-4">
                <h3 className="text-md font-medium text-slate-900">Passive Analysis Tools</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="use_sslyze"
                      name="use_sslyze"
                      checked={customConfigs.use_sslyze}
                      onChange={handleCustomConfigChange}
                      className="h-4 w-4 text-blue-600 rounded border-gray-300"
                    />
                    <label htmlFor="use_sslyze" className="ml-2 block text-sm text-slate-700">
                      SSLyze - SSL/TLS analysis
                    </label>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="use_nuclei"
                      name="use_nuclei"
                      checked={customConfigs.use_nuclei}
                      onChange={handleCustomConfigChange}
                      className="h-4 w-4 text-blue-600 rounded border-gray-300"
                    />
                    <label htmlFor="use_nuclei" className="ml-2 block text-sm text-slate-700">
                      Nuclei - Template-based scanning
                    </label>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="use_wappalyzer"
                      name="use_wappalyzer"
                      checked={customConfigs.use_wappalyzer}
                      onChange={handleCustomConfigChange}
                      className="h-4 w-4 text-blue-600 rounded border-gray-300"
                    />
                    <label htmlFor="use_wappalyzer" className="ml-2 block text-sm text-slate-700">
                      Wappalyzer - Technology detection
                    </label>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="use_zap_passive"
                      name="use_zap_passive"
                      checked={customConfigs.use_zap_passive}
                      onChange={handleCustomConfigChange}
                      className="h-4 w-4 text-blue-600 rounded border-gray-300"
                    />
                    <label htmlFor="use_zap_passive" className="ml-2 block text-sm text-slate-700">
                      ZAP - Passive security analysis
                    </label>
                  </div>
                </div>
              </div>

              {/* Active Scan Configuration */}
              {isActiveScanning && (
                <>
                  <div className="space-y-4">
                    <h3 className="text-md font-medium text-slate-900">Active Scanning Configuration</h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label htmlFor="zap_attack_strength" className="block text-sm font-medium text-slate-700 mb-1">
                          Attack Strength
                        </label>
                        <select
                          id="zap_attack_strength"
                          name="zap_attack_strength"
                          value={customConfigs.zap_attack_strength}
                          onChange={handleCustomConfigChange}
                          className="w-full p-2 border border-gray-300 rounded-md"
                        >
                          <option value="LOW">Low</option>
                          <option value="MEDIUM">Medium</option>
                          <option value="HIGH">High</option>
                          <option value="INSANE">Insane</option>
                        </select>
                        <p className="mt-1 text-xs text-slate-500">
                          Higher strength = more thorough but slower
                        </p>
                      </div>

                      <div>
                        <label htmlFor="max_spider_depth" className="block text-sm font-medium text-slate-700 mb-1">
                          Spider Depth
                        </label>
                        <input
                          type="number"
                          id="max_spider_depth"
                          name="max_spider_depth"
                          min="1"
                          max="10"
                          value={customConfigs.max_spider_depth}
                          onChange={handleCustomConfigChange}
                          className="w-full p-2 border border-gray-300 rounded-md"
                        />
                        <p className="mt-1 text-xs text-slate-500">
                          Maximum crawling depth (1-10)
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label htmlFor="max_spider_duration" className="block text-sm font-medium text-slate-700 mb-1">
                          Spider Duration (minutes)
                        </label>
                        <input
                          type="number"
                          id="max_spider_duration"
                          name="max_spider_duration"
                          min="1"
                          max="60"
                          value={customConfigs.max_spider_duration}
                          onChange={handleCustomConfigChange}
                          className="w-full p-2 border border-gray-300 rounded-md"
                        />
                        <p className="mt-1 text-xs text-slate-500">
                          Maximum time for spidering
                        </p>
                      </div>

                      <div>
                        <label htmlFor="scan_timeout_minutes" className="block text-sm font-medium text-slate-700 mb-1">
                          Scan Timeout (minutes)
                        </label>
                        <input
                          type="number"
                          id="scan_timeout_minutes"
                          name="scan_timeout_minutes"
                          min="10"
                          max="300"
                          value={customConfigs.scan_timeout_minutes}
                          onChange={handleCustomConfigChange}
                          className="w-full p-2 border border-gray-300 rounded-md"
                        />
                        <p className="mt-1 text-xs text-slate-500">
                          Total scan timeout (10-300 minutes)
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="enable_spider"
                          name="enable_spider"
                          checked={customConfigs.enable_spider}
                          onChange={handleCustomConfigChange}
                          className="h-4 w-4 text-blue-600 rounded border-gray-300"
                        />
                        <label htmlFor="enable_spider" className="ml-2 block text-sm text-slate-700">
                          Enable Traditional Spider
                        </label>
                      </div>

                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="enable_ajax_spider"
                          name="enable_ajax_spider"
                          checked={customConfigs.enable_ajax_spider}
                          onChange={handleCustomConfigChange}
                          className="h-4 w-4 text-blue-600 rounded border-gray-300"
                        />
                        <label htmlFor="enable_ajax_spider" className="ml-2 block text-sm text-slate-700">
                          Enable AJAX Spider
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-md font-medium text-slate-900">Vulnerability Testing Categories</h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="test_sql_injection"
                          name="test_sql_injection"
                          checked={customConfigs.test_sql_injection}
                          onChange={handleCustomConfigChange}
                          className="h-4 w-4 text-blue-600 rounded border-gray-300"
                        />
                        <label htmlFor="test_sql_injection" className="ml-2 block text-sm text-slate-700">
                          SQL Injection
                        </label>
                      </div>

                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="test_xss"
                          name="test_xss"
                          checked={customConfigs.test_xss}
                          onChange={handleCustomConfigChange}
                          className="h-4 w-4 text-blue-600 rounded border-gray-300"
                        />
                        <label htmlFor="test_xss" className="ml-2 block text-sm text-slate-700">
                          Cross-Site Scripting
                        </label>
                      </div>

                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="test_csrf"
                          name="test_csrf"
                          checked={customConfigs.test_csrf}
                          onChange={handleCustomConfigChange}
                          className="h-4 w-4 text-blue-600 rounded border-gray-300"
                        />
                        <label htmlFor="test_csrf" className="ml-2 block text-sm text-slate-700">
                          CSRF
                        </label>
                      </div>

                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="test_authentication"
                          name="test_authentication"
                          checked={customConfigs.test_authentication}
                          onChange={handleCustomConfigChange}
                          className="h-4 w-4 text-blue-600 rounded border-gray-300"
                        />
                        <label htmlFor="test_authentication" className="ml-2 block text-sm text-slate-700">
                          Authentication
                        </label>
                      </div>

                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="test_authorization"
                          name="test_authorization"
                          checked={customConfigs.test_authorization}
                          onChange={handleCustomConfigChange}
                          className="h-4 w-4 text-blue-600 rounded border-gray-300"
                        />
                        <label htmlFor="test_authorization" className="ml-2 block text-sm text-slate-700">
                          Authorization
                        </label>
                      </div>

                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="test_session_management"
                          name="test_session_management"
                          checked={customConfigs.test_session_management}
                          onChange={handleCustomConfigChange}
                          className="h-4 w-4 text-blue-600 rounded border-gray-300"
                        />
                        <label htmlFor="test_session_management" className="ml-2 block text-sm text-slate-700">
                          Session Management
                        </label>
                      </div>

                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="test_command_injection"
                          name="test_command_injection"
                          checked={customConfigs.test_command_injection}
                          onChange={handleCustomConfigChange}
                          className="h-4 w-4 text-blue-600 rounded border-gray-300"
                        />
                        <label htmlFor="test_command_injection" className="ml-2 block text-sm text-slate-700">
                          Command Injection
                        </label>
                      </div>

                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="test_xxe"
                          name="test_xxe"
                          checked={customConfigs.test_xxe}
                          onChange={handleCustomConfigChange}
                          className="h-4 w-4 text-blue-600 rounded border-gray-300"
                        />
                        <label htmlFor="test_xxe" className="ml-2 block text-sm text-slate-700">
                          XXE Injection
                        </label>
                      </div>
                    </div>
                  </div>

                  {/* SQL Injection Testing Tools Configuration */}
                  {customConfigs.test_sql_injection && (
                    <div className="space-y-4">
                      <h3 className="text-md font-medium text-slate-900">SQL Injection Testing Tools</h3>
                      <p className="text-sm text-slate-600">
                        Configure specialized tools for SQL injection testing. These tools are automatically enabled for active scans.
                      </p>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            id="use_sqlmap"
                            name="use_sqlmap"
                            checked={customConfigs.use_sqlmap}
                            onChange={handleCustomConfigChange}
                            className="h-4 w-4 text-blue-600 rounded border-gray-300"
                            disabled={true} // Always enabled for SQL injection testing
                          />
                          <label htmlFor="use_sqlmap" className="ml-2 block text-sm text-slate-700">
                            SQLMap (Traditional SQL) <span className="text-green-600 font-medium">✓ Required</span>
                          </label>
                        </div>

                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <label htmlFor="sqlmap_risk_level" className="block text-sm font-medium text-slate-700 mb-1">
                            SQLMap Risk Level
                          </label>
                          <select
                            id="sqlmap_risk_level"
                            name="sqlmap_risk_level"
                            value={customConfigs.sqlmap_risk_level}
                            onChange={handleCustomConfigChange}
                            className="w-full p-2 border border-gray-300 rounded-md"
                          >
                            <option value={1}>1 - Low Risk</option>
                            <option value={2}>2 - Medium Risk</option>
                            <option value={3}>3 - High Risk</option>
                          </select>
                          <p className="mt-1 text-xs text-slate-500">
                            Higher risk = more thorough testing
                          </p>
                        </div>

                        <div>
                          <label htmlFor="sqlmap_level" className="block text-sm font-medium text-slate-700 mb-1">
                            SQLMap Level
                          </label>
                          <select
                            id="sqlmap_level"
                            name="sqlmap_level"
                            value={customConfigs.sqlmap_level}
                            onChange={handleCustomConfigChange}
                            className="w-full p-2 border border-gray-300 rounded-md"
                          >
                            <option value={1}>1 - Basic</option>
                            <option value={2}>2 - Standard</option>
                            <option value={3}>3 - Thorough</option>
                            <option value={4}>4 - Comprehensive</option>
                            <option value={5}>5 - Maximum</option>
                          </select>
                          <p className="mt-1 text-xs text-slate-500">
                            Higher level = more payloads tested
                          </p>
                        </div>

                        <div>
                          <label htmlFor="sqlmap_timeout" className="block text-sm font-medium text-slate-700 mb-1">
                            SQLMap Timeout (seconds)
                          </label>
                          <input
                            type="number"
                            id="sqlmap_timeout"
                            name="sqlmap_timeout"
                            min="60"
                            max="1800"
                            value={customConfigs.sqlmap_timeout}
                            onChange={handleCustomConfigChange}
                            className="w-full p-2 border border-gray-300 rounded-md"
                          />
                          <p className="mt-1 text-xs text-slate-500">
                            Timeout per URL (60-1800 seconds)
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="space-y-4">
                    <h3 className="text-md font-medium text-slate-900">Rate Limiting & Safety</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label htmlFor="max_concurrent_requests" className="block text-sm font-medium text-slate-700 mb-1">
                          Max Concurrent Requests
                        </label>
                        <input
                          type="number"
                          id="max_concurrent_requests"
                          name="max_concurrent_requests"
                          min="1"
                          max="20"
                          value={customConfigs.max_concurrent_requests}
                          onChange={handleCustomConfigChange}
                          className="w-full p-2 border border-gray-300 rounded-md"
                        />
                        <p className="mt-1 text-xs text-slate-500">
                          Number of concurrent requests (1-20)
                        </p>
                      </div>

                      <div>
                        <label htmlFor="request_delay_ms" className="block text-sm font-medium text-slate-700 mb-1">
                          Request Delay (ms)
                        </label>
                        <input
                          type="number"
                          id="request_delay_ms"
                          name="request_delay_ms"
                          min="0"
                          max="5000"
                          value={customConfigs.request_delay_ms}
                          onChange={handleCustomConfigChange}
                          className="w-full p-2 border border-gray-300 rounded-md"
                        />
                        <p className="mt-1 text-xs text-slate-500">
                          Delay between requests in milliseconds
                        </p>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4">
            <Link
              href={`/projects/${projectId}`}
              className="px-4 py-2 text-slate-700 bg-gray-200 rounded-md hover:bg-gray-300"
            >
              Cancel
            </Link>

            <button
              onClick={handleStartScan}
              disabled={submitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-blue-300"
            >
              {submitting ? (
                <>
                  <span className="inline-block animate-spin mr-2">⟳</span>
                  Starting Scan...
                </>
              ) : (
                "Start Scan"
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}