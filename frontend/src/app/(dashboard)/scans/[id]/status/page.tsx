/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable react/no-unescaped-entities */
"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { getScanById, checkScanStatus, stopScan } from "@/lib/api/scans";
import { getProjectById } from "@/lib/api/projects";
import PageTitle from "@/components/PageTitle";

export default function ScanStatusPage({ params }: { params: Promise<{ id: string }> }) {
  const { data: session, status } = useSession();
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
  
  // Keep a ref to the polling interval to properly clean it up
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Resolve params first
  useEffect(() => {
    params.then(resolvedParams => {
      setScanId(resolvedParams.id);
    });
  }, [params]);

  // Helper function to get more detailed progress stage information
  const getProgressStage = (progress: number): string => {
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
  };

  // Helper function to get description based on scan type
  const getScanTypeDescription = (scanType?: string): string => {
    switch (scanType) {
      case 'passive':
        return "Passive scanning collects information without sending potentially harmful requests.";
      case 'active':
        return "Active scanning tests for vulnerabilities by sending specialized requests to the target.";
      case 'full':
        return "Full scanning combines passive reconnaissance with comprehensive vulnerability testing.";
      default:
        return "Scan in progress...";
    }
  };
  
  // Fetch initial scan data
  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
      return;
    }
    
    const fetchScanData = async () => {
      if (!scanId) return;
      try {
        const scan = await getScanById(scanId);
        setScanData(scan);
        setScanStatus(scan.status);
        setProgress(scan.progress || 0);
        
        // Fetch project information
        if (scan.project_id) {
          try {
            const project = await getProjectById(scan.project_id.toString());
            setProjectName(project.name);
          } catch (projectError) {
            console.error("Error fetching project details:", projectError);
            setProjectName("Unknown Project");
          }
        }
      } catch (err: any) {
        setError(err.message || "Failed to load scan details");
      } finally {
        setLoading(false);
      }
    };
    
    if (status === "authenticated") {
      fetchScanData();
    }
  }, [scanId, status, router]);
  
  // Poll for status updates
  const pollStatus = useCallback(async () => {
    if (!scanId) return;
    
    try {
      setPollCount(prev => prev + 1);
      const statusData = await checkScanStatus(scanId);
      
      // Update UI with new status
      setScanStatus(statusData.status);
      setProgress(statusData.progress || 0);
      
      // If scan is completed or failed, prepare for redirect
      if (statusData.status === 'completed') {
        // Clear the polling interval
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        
        // Start countdown for redirection
        setRedirectCountdown(3);
      }
    } catch (err) {
      console.warn("Error polling scan status:", err);
      
      // If we've failed to poll multiple times, show an error
      if (pollCount > 5) {
        setError("Unable to update scan status. Please refresh the page.");
        // Clear the polling interval
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }
    }
  }, [scanId, pollCount]);
  
  // Set up polling interval
  useEffect(() => {
    if (scanStatus === 'in_progress' || scanStatus === 'pending') {
      // Clear any existing interval
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
      
      // Set new interval
      pollingIntervalRef.current = setInterval(pollStatus, 3000);
      
      // Clean up on unmount
      return () => {
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      };
    }
  }, [scanStatus, pollStatus]);
  
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
      case 'in_progress':
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
        subtitle={`Monitoring scan progress for ${projectName}`} 
      />
      
      <div className="bg-white rounded-lg shadow overflow-hidden mb-6">
        {/* Scan Information Header */}
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center">
            <div>
              <h2 className="text-lg font-medium text-gray-900">
                Scan for {projectName}
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                Scan ID: {scanId}
              </p>
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
                {scanStatus === 'in_progress' && (
                  <div className="text-right">
                    <span className="text-xs font-semibold inline-block text-blue-600">
                      {getProgressStage(progress)}
                    </span>
                  </div>
                )}
              </div>
              <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-blue-100">
                <div 
                  style={{ width: `${progress}%` }}
                  className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-600 transition-all duration-500"
                ></div>
              </div>
            </div>
          </div>
          
          {scanStatus === 'in_progress' && (
            <div className="text-center mb-6">
              <p className="text-gray-600">
                Your scan is running. This page will automatically update as the scan progresses.
              </p>
              <p className="text-gray-500 text-sm mt-2">
                {getScanTypeDescription(scanData?.configuration?.scan_type)}
              </p>
              <p className="text-gray-500 text-sm mt-2">
                You'll be redirected to the results page when the scan completes.
              </p>
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
            {scanStatus === 'in_progress' && (
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
                href={`/projects/${scanData.project_id}/scan/new`}
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
                      {projectName}
                    </Link>
                  ) : (
                    "Unknown Project"
                  )}
                </dd>
              </div>
              
              <div className="col-span-1">
                <dt className="text-sm font-medium text-gray-500">Configuration</dt>
                <dd className="mt-1 text-sm text-gray-900 capitalize">
                  {scanData.configuration_name || (scanData.configuration?.scan_type ? `${scanData.configuration.scan_type} Scan` : 'Standard')}
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
              
              {scanData.configuration && (
                <div className="col-span-2 mt-2">
                  <dt className="text-sm font-medium text-gray-500">Scan Configuration</dt>
                  <dd className="mt-1 bg-gray-50 rounded-md p-3">
                    <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2 text-sm">
                      <div className="col-span-1">
                        <dt className="text-xs text-gray-500">Type</dt>
                        <dd className="font-medium text-gray-900 capitalize">{scanData.configuration.scan_type || "Standard"}</dd>
                      </div>
                      <div className="col-span-1">
                        <dt className="text-xs text-gray-500">Crawl Depth</dt>
                        <dd className="font-medium text-gray-900">{scanData.configuration.crawl_depth || 2}</dd>
                      </div>
                      <div className="col-span-1">
                        <dt className="text-xs text-gray-500">Max Pages</dt>
                        <dd className="font-medium text-gray-900">{scanData.configuration.crawl_max_pages || 100}</dd>
                      </div>
                      <div className="col-span-1">
                        <dt className="text-xs text-gray-500">Respect robots.txt</dt>
                        <dd className="font-medium text-gray-900">
                          {scanData.configuration.respect_robots_txt === false ? 'No' : 'Yes'}
                        </dd>
                      </div>
                    </dl>
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