/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable react/no-unescaped-entities */
"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/contexts/AuthContext";
import Link from "next/link";
import { getScanById, checkScanStatus, getScanProgress, stopScan, getZAPStatus, getActiveScanStatistics } from "@/lib/api/scans";
import { getProjectById } from "@/lib/api/projects";
import PageTitle from "@/components/PageTitle";

export default function ScanStatusPage({ params }: { params: Promise<{ id: string }> }) {
  const { user, loading: authLoading, isAuthenticated } = useAuth();
  const router = useRouter();
  
  const [scanId, setScanId] = useState<string>("");
  const [scanData, setScanData] = useState<any>(null);
  const [projectName, setProjectName] = useState<string>("");
  const [progress, setProgress] = useState<number>(0);
  const [scanStatus, setScanStatus] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isStopping, setIsStopping] = useState<boolean>(false);
  const [pollCount, setPollCount] = useState<number>(0);
  const [redirectCountdown, setRedirectCountdown] = useState<number | null>(null);
  const [zapStatus, setZapStatus] = useState<any>(null);
  const [activeScanStats, setActiveScanStats] = useState<any>(null);
  const [currentPhase, setCurrentPhase] = useState<string>("");
  const [pollingError, setPollingError] = useState<string | null>(null);
  const [consecutiveFailures, setConsecutiveFailures] = useState<number>(0);
  
  // Keep a ref to the polling interval to properly clean it up
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Resolve params first
  useEffect(() => {
    params.then(resolvedParams => {
      setScanId(resolvedParams.id);
    });
  }, [params]);

  // Helper function to get more detailed progress stage information based on scan type
  const getProgressStage = (progress: number, scanType?: string): string => {
    const isActive = scanType === 'active' || scanType === 'comprehensive';
    const isComprehensive = scanType === 'comprehensive';
    
    if (isComprehensive) {
      // Comprehensive scan phases
      if (progress < 5) return "Initializing comprehensive scan...";
      if (progress < 15) return "Phase 1: Passive reconnaissance...";
      if (progress < 25) return "Analyzing DNS and SSL/TLS...";
      if (progress < 35) return "Detecting technologies and server info...";
      if (progress < 45) return "Phase 2: Active discovery starting...";
      if (progress < 55) return "Running ZAP spider...";
      if (progress < 65) return "Running AJAX spider...";
      if (progress < 75) return "Phase 3: Active vulnerability testing...";
      if (progress < 85) return "Testing for security vulnerabilities...";
      if (progress < 95) return "Finalizing comprehensive scan...";
      return "Processing final results...";
    } else if (isActive) {
      // Active scan phases
      if (progress < 10) return "Initializing active scan...";
      if (progress < 20) return "Starting ZAP proxy...";
      if (progress < 30) return "Running spider discovery...";
      if (progress < 40) return "Running AJAX spider...";
      if (progress < 50) return "Analyzing discovered URLs...";
      if (progress < 60) return "Testing for SQL injection...";
      if (progress < 70) return "Testing for XSS vulnerabilities...";
      if (progress < 80) return "Testing authentication flaws...";
      if (progress < 90) return "Running additional security tests...";
      return "Finalizing active scan...";
    } else {
      // Passive scan phases (original)
      if (progress < 10) return "Initializing...";
      if (progress < 20) return "Analyzing DNS...";
      if (progress < 30) return "Checking SSL/TLS...";
      if (progress < 40) return "Analyzing server information...";
      if (progress < 50) return "Checking content security...";
      if (progress < 60) return "Analyzing CORS policies...";
      if (progress < 70) return "Detecting technologies...";
      if (progress < 80) return "Analyzing cookies...";
      if (progress < 90) return "Finalizing passive scan...";
      return "Completing scan...";
    }
  };

  // Helper function to get description based on scan type
  const getScanTypeDescription = (scanType?: string): string => {
    switch (scanType) {
      case 'passive':
        return "Passive scanning collects information without sending potentially harmful requests.";
      case 'active':
        return "Active scanning tests for vulnerabilities by sending specialized requests to the target.";
      case 'comprehensive':
        return "Comprehensive scanning combines passive reconnaissance with active vulnerability testing for complete coverage.";
      default:
        return "Scan in progress...";
    }
  };
  
  // Fetch ZAP status for active scans
  const fetchZAPStatus = useCallback(async () => {
    if (scanData?.configuration?.scan_type === 'active' || scanData?.configuration?.scan_type === 'comprehensive') {
      try {
        const status = await getZAPStatus();
        setZapStatus(status);
      } catch (err) {
        console.warn('Failed to fetch ZAP status:', err);
      }
    }
  }, [scanData]);
  
  // Fetch active scan statistics
  const fetchActiveScanStats = useCallback(async () => {
    if (scanId && (scanData?.configuration?.scan_type === 'active' || scanData?.configuration?.scan_type === 'comprehensive')) {
      try {
        const stats = await getActiveScanStatistics(scanId);
        setActiveScanStats(stats);
      } catch (err) {
        console.warn('Failed to fetch active scan statistics:', err);
      }
    }
  }, [scanId, scanData]);
  
  // Fetch initial scan data with retry logic
  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    
    const fetchScanData = async (retryCount = 0) => {
      if (!scanId) return;
      try {
        // Use checkScanStatus to get scan data with project_info
        const scan = await checkScanStatus(scanId);
        setScanData(scan);
        setScanStatus(scan.status);
        setProgress(scan.progress || 0);
        setError(null); // Clear any previous errors
        
        // Set project name from project_info if available
        if (scan.project_info?.name) {
          setProjectName(scan.project_info.name);
        } else if (scan.project_id) {
          // Fallback: fetch project information separately if project_info not available
          try {
            const project = await getProjectById(scan.project_id.toString());
            setProjectName(project.name);
          } catch (projectError) {
            console.error("Error fetching project details:", projectError);
            setProjectName("Unknown Project");
          }
        }
      } catch (err: any) {
        console.error("Error fetching scan data:", err);
        
        // Retry up to 3 times for network errors
        const isNetworkError = !err.response || err.code === 'ECONNABORTED' || err.message?.includes('timeout');
        if (isNetworkError && retryCount < 3) {
          console.log(`Retrying fetch scan data (attempt ${retryCount + 1}/3)...`);
          setTimeout(() => fetchScanData(retryCount + 1), 2000 * (retryCount + 1)); // Exponential backoff
          return;
        }
        
        setError(err.message || "Failed to load scan details. The scan may still be running on the server.");
      } finally {
        if (retryCount === 0) {
          setLoading(false);
        }
      }
    };
    
    if (isAuthenticated) {
      fetchScanData();
    }
  }, [scanId, isAuthenticated, router]);
  
  // Fetch ZAP status and active scan stats when scan data is loaded
  useEffect(() => {
    if (scanData) {
      fetchZAPStatus();
      fetchActiveScanStats();
    }
  }, [scanData, fetchZAPStatus, fetchActiveScanStats]);
  
  // Poll for status updates
  const pollStatus = useCallback(async () => {
    if (!scanId) return;
    
    try {
      setPollCount(prev => prev + 1);
      const progressData = await getScanProgress(scanId);
      
      // Reset consecutive failures on successful poll
      setConsecutiveFailures(0);
      setPollingError(null);
      
      // Debug logging
      console.log('Poll progress update:', {
        scanId,
        status: progressData.status,
        progress: progressData.progress,
        timestamp: new Date().toISOString()
      });
      
      // Update UI with new status and progress
      setScanStatus(progressData.status);
      setProgress(progressData.progress || 0);
      
      // Update current phase if available
      if (progressData.current_phase) {
        setCurrentPhase(progressData.current_phase);
      }
      
      // Update project name if available in progress response
      if (progressData.project_info?.name && !projectName) {
        setProjectName(progressData.project_info.name);
      }
      
      // Fetch additional data for active scans
      if (progressData.status === 'running' || progressData.status === 'in_progress') {
        fetchZAPStatus();
        fetchActiveScanStats();
      }
      
      // If scan is completed, prepare for redirect
      if (progressData.status === 'completed') {
        console.log('Scan completed, preparing for redirect');
        // Clear the polling interval
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        
        // Start countdown for redirection
        setRedirectCountdown(3);
      }
      
      // Only show "failed" status if the backend actually reports it as failed
      // Don't set error state here - let the UI handle it based on scanStatus
      if (progressData.status === 'failed') {
        console.log('Scan marked as failed by backend');
        // Clear the polling interval
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }
    } catch (err: any) {
      const failures = consecutiveFailures + 1;
      setConsecutiveFailures(failures);
      
      console.warn("Error polling scan progress:", err);
      
      // Check if it's a network/timeout error vs actual scan failure
      const isNetworkError = !err.response || err.code === 'ECONNABORTED' || err.message?.includes('timeout');
      
      if (isNetworkError) {
        // For network errors, show a warning but keep polling
        setPollingError(`Connection issue (${failures} failed attempts). Scan may still be running on the server.`);
        
        // Only stop polling after 20 consecutive failures (20 seconds with 1s interval)
        // This allows for temporary network issues
        if (failures >= 20) {
          setError("Unable to connect to the server. The scan may still be running. Please refresh the page to check the latest status.");
          // Clear the polling interval
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        }
      } else {
        // For other errors (like 404, 500), show error but don't assume scan failed
        setPollingError(`Error fetching scan status (${failures} failed attempts).`);
        
        // Stop polling after 10 consecutive non-network errors
        if (failures >= 10) {
          setError("Unable to fetch scan status. Please refresh the page.");
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        }
      }
    }
  }, [scanId, consecutiveFailures, projectName, fetchZAPStatus, fetchActiveScanStats]);
  
  // Set up polling interval
  useEffect(() => {
    // Continue polling if scan is running, in progress, pending, OR if we have polling errors
    // (to recover from temporary network issues)
    if (scanStatus === 'running' || scanStatus === 'in_progress' || scanStatus === 'pending' || 
        (pollingError && consecutiveFailures < 20)) {
      // Clear any existing interval
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
      
      // Use exponential backoff for retries after failures
      // Base interval: 1 second, but increase to 3 seconds after 5 failures, 5 seconds after 10 failures
      const pollInterval = consecutiveFailures < 5 ? 1000 : 
                          consecutiveFailures < 10 ? 3000 : 5000;
      
      // Set new interval - poll more frequently for better real-time updates
      pollingIntervalRef.current = setInterval(pollStatus, pollInterval);
      
      // Clean up on unmount
      return () => {
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      };
    } else {
      // Stop polling if scan is completed, failed, or stopped
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }
  }, [scanStatus, pollStatus, pollingError, consecutiveFailures]);
  
  // Handle redirection countdown
  useEffect(() => {
    if (redirectCountdown !== null && redirectCountdown > 0) {
      const timer = setTimeout(() => {
        setRedirectCountdown(redirectCountdown - 1);
      }, 1000);
      
      return () => clearTimeout(timer);
    } else if (redirectCountdown === 0) {
      router.push(`/scans/${scanId}/results`);
    }
  }, [redirectCountdown, router, scanId]);
  
  // Handle stop scan
  const handleStopScan = async () => {
    setIsStopping(true);
    
    try {
      await stopScan(scanId);
      setScanStatus('stopped');
      
      // Clear polling interval
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    } catch (err: any) {
      setError(err.message || "Failed to stop scan");
    } finally {
      setIsStopping(false);
    }
  };
  
  // Get status display text and color
  const getStatusDisplay = () => {
    switch (scanStatus) {
      case 'pending':
        return { text: 'Pending', className: 'bg-yellow-100 text-yellow-800' };
      case 'running':
        return { text: 'In Progress', className: 'bg-blue-100 text-blue-800' };
      case 'completed':
        return { text: 'Completed', className: 'bg-green-100 text-green-800' };
      case 'failed':
        return { text: 'Failed', className: 'bg-red-100 text-red-800' };
      case 'stopped':
        return { text: 'Stopped', className: 'bg-orange-100 text-orange-800' };
      default:
        return { text: 'Unknown', className: 'bg-gray-100 text-gray-800' };
    }
  };
  
  // Determine project name for display
  const displayProjectName = scanData?.project_info?.name || projectName || "Unknown Project";
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-6 h-6 border-4 border-t-blue-600 rounded-full animate-spin"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="p-3 mb-4 text-sm text-red-600 bg-red-100 rounded">
          {error}
        </div>
        <div className="flex space-x-4">
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Retry
          </button>
          <Link href="/scans" className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300">
            Back to Scans
          </Link>
        </div>
      </div>
    );
  }
  
  const statusInfo = getStatusDisplay();
  
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <PageTitle 
        title="Scan Status" 
        subtitle={`Project: ${displayProjectName}`} 
      />
      
      <div className="bg-white rounded-lg shadow overflow-hidden mb-6">
        {/* Scan Information Header */}
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center">
            <div>
              <h2 className="text-lg font-medium text-gray-900">
                Scan for {displayProjectName}
              </h2>
            </div>
            <div className="mt-2 sm:mt-0">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusInfo.className}`}>
                {statusInfo.text}
              </span>
              {redirectCountdown !== null && (
                <span className="ml-2 text-sm text-gray-600">
                  Redirecting in {redirectCountdown}s...
                </span>
              )}
            </div>
          </div>
        </div>
        
        {/* Scan Status Content */}
        <div className="px-6 py-5">
          <div className="mb-6">
            <h3 className="text-base font-medium text-gray-900 mb-2">Progress</h3>
            <div className="relative pt-1">
              <div className="flex mb-2 items-center justify-between">
                <div>
                  <span className="text-xs font-semibold inline-block text-blue-600">
                    {Math.round(progress)}% Complete
                  </span>
                </div>
                {scanStatus === 'running' && (
                  <div className="text-right">
                    <span className="text-xs font-semibold inline-block text-blue-600">
                      {currentPhase || getProgressStage(progress, scanData?.configuration?.scan_type)}
                    </span>
                  </div>
                )}
              </div>
              <div className="overflow-hidden h-4 mb-4 text-xs flex rounded bg-blue-100 border-2 border-blue-200 shadow-inner">
                <div 
                  style={{ width: `${progress}%` }}
                  className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-300 ease-out"
                ></div>
              </div>
              {scanStatus === 'running' && (
                <div className="text-center">
                  <div className="inline-flex items-center text-xs text-blue-600 bg-blue-50 px-3 py-1 rounded-full">
                    <div className="w-2 h-2 bg-blue-600 rounded-full mr-2 animate-pulse"></div>
                    Live updates every second
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {(scanStatus === 'running' || scanStatus === 'in_progress') && (
            <div className="text-center mb-6">
              <div className="flex items-center justify-center mb-4">
                <div className="w-6 h-6 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mr-3"></div>
                <span className="text-lg font-medium text-blue-600">Scan in Progress</span>
              </div>
              {pollingError && (
                <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                  <p className="text-yellow-800 text-sm">{pollingError}</p>
                  <p className="text-yellow-700 text-xs mt-1">The scan continues on the server. Status updates will resume when connection is restored.</p>
                </div>
              )}
              <p className="text-gray-600">
                Your scan is running. This page will automatically update as the scan progresses.
              </p>
              <p className="text-gray-500 text-sm mt-2">
                {getScanTypeDescription(scanData?.configuration?.scan_type)}
              </p>
              {currentPhase && (
                <p className="text-blue-600 text-sm mt-2 font-medium">
                  Current Phase: {currentPhase}
                </p>
              )}
              <p className="text-gray-500 text-sm mt-2">
                You'll be redirected to the results page when the scan completes.
              </p>
              
              {/* ZAP Status for Active Scans */}
              {(scanData?.configuration?.scan_type === 'active' || scanData?.configuration?.scan_type === 'comprehensive') && zapStatus && (
                <div className="mt-4 p-3 bg-blue-50 rounded-md">
                  <div className="flex items-center justify-center mb-2">
                    <div className={`w-2 h-2 rounded-full mr-2 ${
                      zapStatus.status === 'connected' ? 'bg-green-500' : 'bg-red-500'
                    }`}></div>
                    <span className="text-sm font-medium text-blue-700">
                      ZAP Status: {zapStatus.status === 'connected' ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                  {zapStatus.version && (
                    <p className="text-xs text-blue-600">Version: {zapStatus.version}</p>
                  )}
                </div>
              )}
              
              {/* Active Scan Statistics */}
              {activeScanStats && (
                <div className="mt-4 p-3 bg-green-50 rounded-md">
                  <h4 className="text-sm font-medium text-green-700 mb-2">Live Statistics</h4>
                  <div className="grid grid-cols-2 gap-2 text-xs text-green-600">
                    {activeScanStats.spider_urls_found !== undefined && (
                      <div>URLs Found: {activeScanStats.spider_urls_found}</div>
                    )}
                    {activeScanStats.total_vulnerabilities !== undefined && (
                      <div>Vulnerabilities: {activeScanStats.total_vulnerabilities}</div>
                    )}
                    {activeScanStats.ajax_spider_urls_found !== undefined && (
                      <div>AJAX URLs: {activeScanStats.ajax_spider_urls_found}</div>
                    )}
                    {activeScanStats.scan_duration && (
                      <div>Duration: {activeScanStats.scan_duration}</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
          
          {scanStatus === 'pending' && (
            <div className="text-center mb-6">
              <p className="text-gray-600">
                Your scan is queued and will begin shortly.
              </p>
            </div>
          )}
          
          {scanStatus === 'failed' && (
            <div className="text-center mb-6 p-4 bg-red-50 rounded-md">
              <p className="text-red-600">
                The scan failed to complete. This could be due to connectivity issues or problems with the target site.
              </p>
              <p className="text-red-500 text-sm mt-2">
                You can try running the scan again or contact support if the issue persists.
              </p>
              {scanData?.error_message && (
                <div className="mt-3 text-left p-3 bg-red-100 rounded-md overflow-auto max-h-32">
                  <p className="text-sm font-medium text-red-700">Error details:</p>
                  <p className="text-xs text-red-600 mt-1 whitespace-pre-wrap">{scanData.error_message}</p>
                </div>
              )}
              <button
                onClick={async () => {
                  try {
                    const latestStatus = await checkScanStatus(scanId);
                    setScanData(latestStatus);
                    setScanStatus(latestStatus.status);
                    setProgress(latestStatus.progress || 0);
                    setError(null);
                    // If scan is actually still running, restart polling
                    if (latestStatus.status === 'running' || latestStatus.status === 'in_progress') {
                      setConsecutiveFailures(0);
                      setPollingError(null);
                    }
                  } catch (err: any) {
                    setError(err.message || "Failed to refresh scan status");
                  }
                }}
                className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
              >
                Refresh Status
              </button>
            </div>
          )}
          
          {scanStatus === 'stopped' && (
            <div className="text-center mb-6 p-4 bg-orange-50 rounded-md">
              <p className="text-orange-600">
                The scan was manually stopped before completion.
              </p>
            </div>
          )}
          
          {scanStatus === 'completed' && (
            <div className="text-center mb-6 p-4 bg-green-50 rounded-md">
              <p className="text-green-600">
                The scan has completed successfully! You'll be redirected to the results page shortly.
              </p>
            </div>
          )}
          
          <div className="flex justify-center space-x-4">
            {(scanStatus === 'running' || scanStatus === 'in_progress') && (
              <button
                onClick={handleStopScan}
                disabled={isStopping}
                className="px-4 py-2 border border-red-300 text-red-700 bg-white rounded hover:bg-red-50 disabled:opacity-50 flex items-center"
              >
                {isStopping ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Stopping...
                  </>
                ) : (
                  'Stop Scan'
                )}
              </button>
            )}
            
            {scanStatus === 'completed' && (
              <Link
                href={`/scans/${scanId}/results`}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                View Results
              </Link>
            )}
            
            {(scanStatus === 'failed' || scanStatus === 'stopped') && scanData?.project_id && (
              <Link
                href={`/projects/${scanData.project_id}/scans/new`}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Start New Scan
              </Link>
            )}
            
            <Link
              href="/scans"
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              Back to Scans
            </Link>
            {(pollingError || error) && (
              <button
                onClick={async () => {
                  try {
                    setError(null);
                    setPollingError(null);
                    setConsecutiveFailures(0);
                    const latestStatus = await checkScanStatus(scanId);
                    setScanData(latestStatus);
                    setScanStatus(latestStatus.status);
                    setProgress(latestStatus.progress || 0);
                    // If scan is still running, restart polling
                    if (latestStatus.status === 'running' || latestStatus.status === 'in_progress' || latestStatus.status === 'pending') {
                      // Polling will restart automatically via the useEffect
                    }
                  } catch (err: any) {
                    setError(err.message || "Failed to refresh scan status");
                  }
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Refresh Status
              </button>
            )}
          </div>
        </div>
      </div>
      
      {scanData && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Scan Details</h3>
          </div>
          <div className="px-6 py-4">
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-4">
              <div className="col-span-1">
                <dt className="text-sm font-medium text-gray-500">Project</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {scanData.project_id ? (
                    <Link href={`/projects/${scanData.project_id}`} className="text-blue-600 hover:underline">
                      {displayProjectName}
                    </Link>
                  ) : (
                    "Unknown Project"
                  )}
                </dd>
              </div>
              
              <div className="col-span-1">
                <dt className="text-sm font-medium text-gray-500">Started</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {scanData.started_at 
                    ? new Date(scanData.started_at).toLocaleString() 
                    : scanData.created_at 
                      ? new Date(scanData.created_at).toLocaleString()
                      : "Not started yet"}
                </dd>
              </div>
              
              <div className="col-span-1">
                <dt className="text-sm font-medium text-gray-500">Configuration</dt>
                <dd className="mt-1 text-sm text-gray-900 capitalize">
                  {scanData.configuration_name 
                    ? `${scanData.configuration_name} Scan` 
                    : "Standard Scan"}
                </dd>
              </div>
              
              <div className="col-span-1">
                <dt className="text-sm font-medium text-gray-500">Status</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.className}`}>
                    {statusInfo.text}
                  </span>
                </dd>
              </div>
              
              {scanData.completed_at && (
                <div className="col-span-1">
                  <dt className="text-sm font-medium text-gray-500">Completed</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {new Date(scanData.completed_at).toLocaleString()}
                  </dd>
                </div>
              )}
            </dl>
          </div>
        </div>
      )}
    </div>
  );
}