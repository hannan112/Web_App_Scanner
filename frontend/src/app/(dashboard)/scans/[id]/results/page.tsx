/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState, useEffect, SetStateAction } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/contexts/AuthContext";
import Link from "next/link";
import { getScanById, getScanResults, generateScanReport } from "@/lib/api/scans";
import { getProjectById } from "@/lib/api/projects";
import ScanResults from "@/components/scanning/ScanResults";
import PageTitle from "@/components/PageTitle";
import ErrorBoundary from "@/components/ErrorBoundary";

export default function ScanResultsPage({ params }: { params: Promise<{ id: string }> }) {
  const { user, loading: authLoading, isAuthenticated } = useAuth();
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
    if (!isAuthenticated) {
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

    if (isAuthenticated) {
      fetchData();
    }
  }, [scanId, isAuthenticated, router]);

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

  // Handle raw data download
  const handleDownload = async (type: string) => {
    try {
      const rawBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const trimmedBase = rawBase.replace(/\/$/, '');
      const apiBase = /\/api$/.test(trimmedBase) ? trimmedBase : `${trimmedBase}/api`;
      const response = await fetch(`${apiBase}/scanning/scans/${scanId}/download_raw_data/?type=${type}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to download data');
      }

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      const filename = contentDisposition
        ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
        : `scan_${scanId}_${type}.json`;

      // Create download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

    } catch (error) {
      console.error('Error downloading data:', error);
      setError(`Failed to download ${type} data`);
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
        <div className="p-3 mb-4 text-sm text-red-600 bg-red-100/80 backdrop-blur-sm rounded border border-red-200">
          Error: {error}
        </div>
        <div className="flex space-x-4">
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-md"
          >
            Retry
          </button>
          <Link href="/scans" className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 shadow-md">
            Back to Scans
          </Link>
        </div>
      </div>
    );
  }

  // Determine project name for display
  const projectName = projectData?.name || scanData?.project_info?.name || scanData?.project?.name || "Unknown Project";

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header with summary and action buttons */}
      <PageTitle
        title="Scan Results"
        subtitle={`Project: ${projectName}`}
      />


      {/* Data Export Section */}

      <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-lg shadow-lg p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 mb-2">Export Scan Summary</h2>
            <p className="text-sm text-slate-700">
              Download optimized scan results and key security findings.
              Raw data storage has been optimized to save disk space.
            </p>
          </div>
          <svg className="w-8 h-8 text-blue-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => handleDownload('vulnerabilities')}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 shadow-md"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            Vulnerabilities ({resultData?.summary?.total_vulnerabilities || 0})
          </button>

          <button
            onClick={() => handleDownload('attack_surface')}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 shadow-md"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0-9v9m0 9c-5 0-9-4-9-9s4-9 9-9" />
            </svg>
            Attack Surface (&lt;1MB)
          </button>

          <button
            onClick={() => handleDownload('raw_findings')}
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 shadow-md"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Raw Findings
          </button>
        </div>
      </div>

      <div className="flex justify-end space-x-3 mb-6">
        <button
          onClick={handleGenerateReport}
          disabled={isGeneratingReport}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center shadow-md"
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
            href={`/projects/${projectData.id}/scans/new`}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center shadow-md"
          >
            <svg className="w-4 h-4 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            New Scan
          </Link>
        )}

        <Link href="/scans" className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 shadow-md">
          Back to Scans
        </Link>
      </div>

      {/* Scan Results Component */}
      <ErrorBoundary>
        <ScanResults
          scanId={scanId}
          projectId={scanData?.project_id}
          vulnerabilities={Array.isArray(resultData?.vulnerabilities) ? resultData.vulnerabilities : []}
          passiveReconData={resultData?.passive_reconnaissance || resultData?.passive_data}
          activeReconData={resultData?.active_data}
          crawlData={resultData?.crawl_data ? {
            pages_crawled: resultData.crawl_data.pages_crawled || 0,
            urls_count: resultData.crawl_data.urls_count || 0,
            forms_count: resultData.crawl_data.forms_count || 0
          } : undefined}
          scanType={scanData?.configuration?.scan_type}
          targetUrl={scanData?.target_url || scanData?.url || scanData?.scan_url || resultData?.target_url || resultData?.url || resultData?.project_info?.target_url}
          vulnerabilitySummary={resultData?.vulnerability_summary}
          onError={(errMsg: SetStateAction<string | null>) => setError(errMsg)}
        />
      </ErrorBoundary>

      {/* Disclaimer & Legal Notice */}
      <footer className="mt-12 pt-8 border-t border-slate-200">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Disclaimer & Legal Notice</h3>

        <div className="bg-slate-50 border border-slate-200 rounded-lg p-6 space-y-4">
          <div>
            <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wide mb-1">Accuracy of Results</h4>
            <p className="text-sm text-slate-600 leading-relaxed">
              Please note that this security scanning tool is in an initial stage of development. While every effort has been made to ensure accuracy, the results provided in this report may contain errors, false positives, or false negatives. This report should be used as a preliminary assessment and does not guarantee the complete security of the target application. We recommend manual verification of all critical findings.
            </p>
          </div>

          <div>
            <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wide mb-1">Legal Disclaimer</h4>
            <p className="text-sm text-slate-600 leading-relaxed">
              The authors and maintainers of this tool are not responsible for any damage caused by the use or misuse of this software. This tool is intended for educational and authorized security testing purposes only. The user assumes all legal and regulatory responsibility for the use of this tool against any target systems. By using this report, you acknowledge that you have proper authorization to scan the target URL.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}