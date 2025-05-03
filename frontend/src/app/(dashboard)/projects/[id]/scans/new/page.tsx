/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
// src/app/(dashboard)/projects/[id]/scans/new/page.tsx

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { getProjectById } from "@/lib/api/projects";
import { getScanConfigurations, createScan, createScanConfiguration } from "@/lib/api/scans";
import PageTitle from "@/components/PageTitle";

export default function NewProjectScanPage({ params }: { params: { id: string } }) {
  const { data: session, status } = useSession();
  const router = useRouter();
  
  const [projectName, setProjectName] = useState<string>("");
  const [configurations, setConfigurations] = useState<any[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<string>("");
  const [customConfigs, setCustomConfigs] = useState({
    scan_type: "full",
    crawl_depth: 2,
    respect_robots_txt: true,
    crawl_max_pages: 100,
    crawl_timeout: 30,
  });
  
  const [useDefaultConfig, setUseDefaultConfig] = useState(true);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Check if user is authenticated
  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    }
  }, [status, router]);

  // Fetch project and scan configurations
  useEffect(() => {
    const fetchData = async () => {
      if (status !== "authenticated") return;
      
      try {
        // Get project details
        const project = await getProjectById(params.id);
        setProjectName(project.name);
        
        // Get scan configurations
        try {
          console.log(`Fetching configurations for project ${params.id}`);
          const configs = await getScanConfigurations(params.id);
          console.log('Configurations:', configs);
          
          const mappedConfigs = configs.map((config: any) => ({
            ...config,
            crawl_max_pages: config.crawl_max_pages || 100 // Default value if not provided
          }));
          setConfigurations(mappedConfigs);
          
          if (configs.length > 0) {
            setSelectedConfig(configs[0].id);
          } else {
            // If no configs, use default one
            setUseDefaultConfig(true);
          }
        } catch (configErr) {
          // If no configurations exist yet, we'll use custom/default one
          console.log("No existing configurations found, using default");
          setUseDefaultConfig(true);
        }
      } catch (err: any) {
        console.error("Error fetching project data:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [params.id, status, router]);

  // Handle config selection change
  const handleConfigChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedConfig(e.target.value);
  };

  // Handle custom config changes
  const handleCustomConfigChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    setCustomConfigs(prev => ({
      ...prev,
      [name]: type === 'checkbox' 
        ? (e.target as HTMLInputElement).checked 
        : type === 'number' 
          ? parseInt(value) 
          : value
    }));
  };

  // Toggle between existing and custom config
  const toggleConfigMode = () => {
    setUseDefaultConfig(!useDefaultConfig);
  };

  // Start scan handler
  const handleStartScan = async () => {
    setSubmitting(true);
    setError(null);
    
    try {
      let configId = selectedConfig;
      
      // If using default/custom config, create a temporary one first
      if (useDefaultConfig || !configId) {
        // Create a default configuration first
        try {
          console.log("Creating new configuration with:", {
            project: params.id,
            scan_type: customConfigs.scan_type,
            crawl_depth: customConfigs.crawl_depth,
            respect_robots_txt: customConfigs.respect_robots_txt,
            crawl_max_pages: customConfigs.crawl_max_pages
          });
          
          const configData = {
            project: params.id,
            scan_type: customConfigs.scan_type,
            crawl_depth: customConfigs.crawl_depth,
            respect_robots_txt: customConfigs.respect_robots_txt,
            crawl_max_pages: customConfigs.crawl_max_pages
          };
          
          // Call an API function to create configuration
          const createdConfig = await createScanConfiguration(configData);
          configId = createdConfig.id;
          console.log("Created configuration:", createdConfig);
        } catch (configErr: unknown) {
          console.error("Configuration creation error:", configErr);
          const errorMessage = configErr instanceof Error ? configErr.message : 'Unknown error occurred';
          throw new Error("Failed to create scan configuration: " + errorMessage);
        }
      }
      
      // Now create the scan with the project ID and config ID
      console.log(`Creating scan for project ${params.id} with config ${configId}`);
      const scan = await createScan(params.id, configId);
      console.log("Created scan:", scan);
      
      // Redirect to scan status page
      router.push(`/scans/${scan.id}/status`);
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

      <div className="bg-white p-6 rounded-lg shadow mb-6">
        {error && (
          <div className="p-3 mb-4 text-sm text-red-600 bg-red-100 rounded">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {/* Scan Configuration Selection */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-lg font-medium text-gray-900">Scan Configuration</h2>
              
              <div className="flex items-center">
                <span className="text-sm text-gray-600 mr-2">
                  {useDefaultConfig ? "Using Default Configuration" : "Using Saved Configuration"}
                </span>
                <button 
                  onClick={toggleConfigMode}
                  type="button"
                  className="text-sm text-blue-600 hover:underline"
                >
                  {useDefaultConfig ? "Use Saved Configuration" : "Use Default Configuration"}
                </button>
              </div>
            </div>
            
            {!useDefaultConfig && configurations.length > 0 ? (
              <div>
                <label htmlFor="configSelect" className="block text-sm font-medium text-gray-700 mb-1">
                  Select Configuration
                </label>
                <select
                  id="configSelect"
                  value={selectedConfig}
                  onChange={handleConfigChange}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  {configurations.map(config => (
                    <option key={config.id} value={config.id}>
                      {config.name || `${config.scan_type} (Depth: ${config.crawl_depth}, Max Pages: ${config.crawl_max_pages})`}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label htmlFor="scan_type" className="block text-sm font-medium text-gray-700 mb-1">
                    Scan Type
                  </label>
                  <select
                    id="scan_type"
                    name="scan_type"
                    value={customConfigs.scan_type}
                    onChange={handleCustomConfigChange}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    <option value="passive">Passive (Information Gathering Only)</option>
                    <option value="active">Active (Basic Vulnerability Scanning)</option>
                    <option value="full">Full (Comprehensive Security Analysis)</option>
                  </select>
                  <p className="mt-1 text-xs text-gray-500">
                    Passive: No active testing, only information gathering.<br />
                    Active: Limited testing with minimal impact.<br />
                    Full: Complete testing, may impact application performance.
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="crawl_depth" className="block text-sm font-medium text-gray-700 mb-1">
                      Crawl Depth
                    </label>
                    <input
                      type="number"
                      id="crawl_depth"
                      name="crawl_depth"
                      min="1"
                      max="10"
                      value={customConfigs.crawl_depth}
                      onChange={handleCustomConfigChange}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      How deep the scanner should crawl (1-10). Higher values take longer.
                    </p>
                  </div>
                  
                  <div>
                    <label htmlFor="crawl_max_pages" className="block text-sm font-medium text-gray-700 mb-1">
                      Maximum Pages
                    </label>
                    <input
                      type="number"
                      id="crawl_max_pages"
                      name="crawl_max_pages"
                      min="10"
                      max="1000"
                      value={customConfigs.crawl_max_pages}
                      onChange={handleCustomConfigChange}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Maximum number of pages to scan (10-1000).
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="respect_robots_txt"
                    name="respect_robots_txt"
                    checked={customConfigs.respect_robots_txt}
                    onChange={handleCustomConfigChange}
                    className="h-4 w-4 text-blue-600 rounded border-gray-300"
                  />
                  <label htmlFor="respect_robots_txt" className="ml-2 block text-sm text-gray-700">
                    Respect robots.txt (recommended)
                  </label>
                </div>
              </div>
            )}
          </div>
          
          {/* Selected Configuration Details */}
          {!useDefaultConfig && selectedConfig && configurations.length > 0 && (
            <div className="bg-gray-50 p-4 rounded-md">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Configuration Details</h3>
              
              {(() => {
                const config = configurations.find(c => c.id === selectedConfig);
                if (!config) return null;
                
                return (
                  <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                    <div className="col-span-1">
                      <dt className="text-gray-500">Type</dt>
                      <dd className="font-medium text-gray-900 capitalize">{config.scan_type}</dd>
                    </div>
                    <div className="col-span-1">
                      <dt className="text-gray-500">Crawl Depth</dt>
                      <dd className="font-medium text-gray-900">{config.crawl_depth}</dd>
                    </div>
                    <div className="col-span-1">
                      <dt className="text-gray-500">Max Pages</dt>
                      <dd className="font-medium text-gray-900">{config.crawl_max_pages}</dd>
                    </div>
                    <div className="col-span-1">
                      <dt className="text-gray-500">Respect robots.txt</dt>
                      <dd className="font-medium text-gray-900">
                        {config.respect_robots_txt ? 'Yes' : 'No'}
                      </dd>
                    </div>
                  </dl>
                );
              })()}
            </div>
          )}
          
          {/* Warning message for active scans */}
          {(useDefaultConfig && customConfigs.scan_type !== 'passive') || 
           (!useDefaultConfig && selectedConfig && configurations.find(c => c.id === selectedConfig)?.scan_type !== 'passive') ? (
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-yellow-700">
                    <strong>Active scanning notice:</strong> This scan will actively interact with the target website. 
                    Only scan websites you have permission to test.
                  </p>
                </div>
              </div>
            </div>
          ) : null}
          
          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4">
            <Link 
              href={`/projects/${params.id}`}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
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