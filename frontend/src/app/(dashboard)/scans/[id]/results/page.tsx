/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
// src/app/(dashboard)/scans/[id]/results/page.tsx
"use client";

import { useState, useEffect, SetStateAction } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { getScanById, getScanResults, generateScanReport } from "@/lib/api/scans";
import { getProjectById } from "@/lib/api/projects";
import ScanResults from "@/components/scanning/ScanResults";
import PageTitle from "@/components/PageTitle";

export default function ScanResultsPage({ params }: { params: Promise<{ id: string }> }) {
  const { data: session, status } = useSession();
  const router = useRouter();
  
  const [scanId, setScanId] = useState<string>("");
  const [scanData, setScanData] = useState<any>(null);
  const [projectData, setProjectData] = useState<any>(null);
  const [resultData, setResultData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState<boolean>(false);
  
  // Resolve params first
  useEffect(() => {
    params.then(resolvedParams => {
      setScanId(resolvedParams.id);
    });
  }, [params]);
  
  // Fetch scan and project data
  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
      return;
    }
    
    const fetchData = async () => {
      if (!scanId) return;
      try {
        // Get scan data
        const scan = await getScanById(scanId);
        setScanData(scan);
        
        // Only allow viewing completed scans
        if (scan.status !== 'completed') {
          router.push(`/scans/${scanId}/status`);
          return;
        }
        
        // Get scan results
        const results = await getScanResults(scanId);
        setResultData(results);

        // Get project data if project_id exists and is defined
        if (scan.project_id && scan.project_id !== 'undefined') {
          try {
            const project = await getProjectById(String(scan.project_id));
            setProjectData(project);
          } catch (projectErr) {
            console.warn("Could not fetch project details, continuing without project data:", projectErr);
            // Don't set error, just continue without project data
          }
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    if (status === "authenticated") {
      fetchData();
    }
  }, [scanId, status, router]);
  
  // Handle report generation
  const handleGenerateReport = async () => {
    setIsGeneratingReport(true);
    
    try {
      const reportBlob = await generateScanReport(scanId);
      
      if (!reportBlob) {
        throw new Error('Failed to generate report');
      }
      
      // Create download link
      const url = window.URL.createObjectURL(reportBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `security-scan-report-${scanId}.pdf`;
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsGeneratingReport(false);
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
          Error: {error}
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
  
  const projectName = projectData ? projectData.name : "Unknown Project";
  const projectLink = projectData ? (
    <Link href={`/projects/${projectData.id}`} className="hover:underline">
      {projectName}
    </Link>
  ) : (
    <span>{projectName}</span>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header with summary and action buttons */}
      <PageTitle 
        title="Scan Results" 
        subtitle={<span>Project: {projectLink}</span>}
      />
      
      <div className="flex justify-end space-x-3 mb-6">
        <button
          onClick={handleGenerateReport}
          disabled={isGeneratingReport}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center"
        >
          {isGeneratingReport ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Generating...
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-2" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V8z" clipRule="evenodd" />
              </svg>
              Generate PDF Report
            </>
          )}
        </button>
        
        {projectData && (
          <Link 
            href={`/projects/${projectData.id}/scan/new`} 
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 flex items-center"
          >
            <svg className="w-4 h-4 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            New Scan
          </Link>
        )}
        
        <Link href="/scans" className="px-4 py-2 text-gray-700 bg-gray-200 rounded hover:bg-gray-300">
          Back to Scans
        </Link>
      </div>
      
      {/* Scan Results Component */}
      <ScanResults 
        scanId={scanId} 
        projectId={scanData?.project_id} 
        vulnerabilities={resultData?.vulnerabilities || []}
        passiveReconData={resultData?.passive_data}
        crawlData={resultData?.crawl_data ? {
          pages_crawled: resultData.crawl_data.pages_crawled || 0,
          urls_count: resultData.crawl_data.urls_count || 0,
          forms_count: resultData.crawl_data.forms_count || 0
        } : undefined}
        onError={(errMsg: SetStateAction<string | null>) => setError(errMsg)} 
      />
      </div>
  );
}