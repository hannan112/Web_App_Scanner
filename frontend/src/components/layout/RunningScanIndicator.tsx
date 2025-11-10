'use client';

import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import apiClient from '@/lib/api/client';

interface RunningScanData {
  has_running_scan: boolean;
  scan: {
    id: number;
    status: string;
    progress: number;
    target_url: string;
    start_time: string;
    project_id: number;
    project_name: string;
    scan_type: string;
  } | null;
}

export default function RunningScanIndicator() {
  const [runningScan, setRunningScan] = useState<RunningScanData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const pathname = usePathname();

  useEffect(() => {
    // Check for running scan on mount
    checkRunningScan();

    // Poll every 3 seconds to check for running scans (more frequent for faster updates)
    // This ensures the indicator disappears quickly when scan stops
    const interval = setInterval(checkRunningScan, 3000);

    return () => clearInterval(interval);
  }, []);

  const checkRunningScan = async () => {
    try {
      const response = await apiClient.get('/scanning/scans/running_scan/');
      setRunningScan(response.data);
      setIsLoading(false);
    } catch (error) {
      console.error('Error checking running scan:', error);
      setIsLoading(false);
    }
  };

  // Don't show anything if no running scan or still loading
  if (isLoading || !runningScan?.has_running_scan || !runningScan.scan) {
    return null;
  }

  const { scan } = runningScan;

  // Don't show indicator on scan status/detail pages (e.g., /scans/302/status or /projects/1/scans/302)
  // This prevents showing the indicator when user is already viewing the running scan
  const isScanStatusPage = pathname?.includes('/scans/') && (
    pathname?.includes('/status') || 
    pathname?.endsWith(`/${scan.id}`) ||
    pathname?.includes(`/scans/${scan.id}/`)
  );

  if (isScanStatusPage) {
    return null;
  }

  return (
    <Link
      href={`/projects/${scan.project_id}/scans/${scan.id}`}
      className="flex items-center space-x-2 bg-blue-50 hover:bg-blue-100 text-blue-700 px-3 py-2 rounded-md transition-colors border border-blue-200"
    >
      {/* Animated scanning icon */}
      <div className="relative">
        <svg
          className="animate-spin h-4 w-4 text-blue-600"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          ></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
      </div>

      {/* Scan info */}
      <div className="flex items-center space-x-2 text-sm">
        <span className="font-medium">Scan Running</span>
        <span className="text-blue-600">•</span>
        <span className="hidden sm:inline">{scan.project_name}</span>
        <span className="text-blue-600">•</span>
        <span className="font-semibold">{Math.round(scan.progress)}%</span>
      </div>

      {/* Progress bar (mobile hidden) */}
      <div className="hidden md:block w-24 bg-blue-200 rounded-full h-2">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${scan.progress}%` }}
        ></div>
      </div>
    </Link>
  );
}
