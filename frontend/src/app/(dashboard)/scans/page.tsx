/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react/no-unescaped-entities */
// src/app/(dashboard)/scans/page.tsx
"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/contexts/AuthContext";
import { useRouter } from "next/navigation";
import { getAllScans, stopScan } from "@/lib/api/scans";
import { Project, Scan } from "@/types/project";
import { getProjects } from "@/lib/api/projects";
import ScanBarChart from "@/components/scanning/ScanBarChart";

export default function ScansPage() {
  const { user, loading: authLoading, isAuthenticated } = useAuth();
  const router = useRouter();
  const [scans, setScans] = useState<Scan[]>([]);
  const [projects, setProjects] = useState<{[key: string]: string}>({});
  const [projectsData, setProjectsData] = useState<Project[]>([]); // Initialize as empty array
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stoppingId, setStoppingId] = useState<number | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const [shouldPoll, setShouldPoll] = useState(true);
  const scansRef = useRef<Scan[]>([]);
  const refreshScansRef = useRef<() => Promise<void>>();

  // Global cleanup on component unmount
  useEffect(() => {
    return () => {
      console.log('Scans page component unmounting - forcing cleanup');
      setShouldPoll(false);
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  // Re-enable polling when component mounts
  useEffect(() => {
    setShouldPoll(true);
    return () => {
      setShouldPoll(false);
    };
  }, []);

  const refreshScans = useCallback(async () => {
    try {
      const scansData = await getAllScans();
      // Keep all scans including stopped ones for display purposes
      setScans(scansData);
      // Update the ref for polling logic
      scansRef.current = scansData;
    } catch (err) {
      setError((err as Error).message);
    }
  }, []);

  // Update the ref whenever refreshScans changes
  useEffect(() => {
    refreshScansRef.current = refreshScans;
  }, [refreshScans]);

  useEffect(() => {
    if (authLoading) return;
    
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    const fetchData = async () => {
      try {
        // Fetch projects first
        const projectsResult = await getProjects();
        // Ensure projectsData is an array
        const projectsArray = Array.isArray(projectsResult) ? projectsResult : [];
        setProjectsData(projectsArray);
        
        // Create a map of project IDs to names (handle both string and number IDs)
        const projectMap = projectsArray.reduce((acc, project) => {
          acc[project.id] = project.name;
          acc[String(project.id)] = project.name; // Also map string version
          return acc;
        }, {} as {[key: string]: string});
        setProjects(projectMap);
        
        // Initial scans load
        await refreshScans();
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Cleanup function to stop polling when component unmounts
    return () => {
      console.log('Scans page unmounting - stopping all polling');
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [isAuthenticated, authLoading, router, refreshScans]);

  // Simple polling effect - only runs once on mount
  useEffect(() => {
    if (!isAuthenticated || !shouldPoll) {
      return;
    }

    // Check if there are running scans and start polling
    const hasRunningScans = scansRef.current.some(scan => 
      scan.status === 'running' || 
      scan.status === 'in_progress' || 
      scan.status === 'pending'
    );

    if (hasRunningScans && !pollingRef.current) {
      const runningScans = scansRef.current.filter(s => 
        s.status === 'running' || s.status === 'in_progress' || s.status === 'pending'
      );
      console.log('Starting polling - found running scans:', runningScans.map(s => ({ id: s.id, status: s.status })));
      
      pollingRef.current = setInterval(async () => {
        if (!shouldPoll) {
          console.log('Polling stopped - shouldPoll is false');
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          return;
        }
        
        try {
          if (refreshScansRef.current) {
            await refreshScansRef.current();
          }
          
          // Check if we should stop polling after refresh
          const stillHasRunningScans = scansRef.current.some(scan => 
            scan.status === 'running' || 
            scan.status === 'in_progress' || 
            scan.status === 'pending'
          );
          
          if (!stillHasRunningScans && pollingRef.current) {
            console.log('Stopping polling - no more running scans');
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
        } catch (err) {
          console.warn('Error during polling:', err);
          // Stop polling if we get repeated errors
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
        }
      }, 2000);
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [isAuthenticated, shouldPoll]);

  const handleStop = async (id: number) => {
    try {
      setStoppingId(id);
      await stopScan(String(id));
      
      // Immediately update the scan status to stopped
      setScans(prev => {
        const updatedScans = prev.map(s => s.id === id ? { ...s, status: 'stopped' } as Scan : s);
        
        // Update the ref as well
        scansRef.current = updatedScans;
        
        // Check if there are any remaining running scans
        const hasRemainingRunningScans = updatedScans.some(scan => 
          scan.status === 'running' || 
          scan.status === 'in_progress' || 
          scan.status === 'pending'
        );
        
        // If no running scans remain, disable polling
        if (!hasRemainingRunningScans) {
          console.log('All scans stopped - disabling polling');
          setShouldPoll(false);
          // Also stop polling immediately
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
        }
        
        return updatedScans;
      });
      
      // Wait a moment for the backend to process the stop request
      setTimeout(async () => {
        try {
          await refreshScans();
        } catch (err) {
          console.warn('Error refreshing scans after stop:', err);
        }
      }, 1000);
      
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setStoppingId(null);
    }
  };

  // Get scan status badge class
  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'stopped':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Format date 
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
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
      <div className="p-4">
        <div className="p-3 mb-4 text-sm text-red-600 bg-red-100 rounded">
          Error: {error}
        </div>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-800">Security Scans</h1>
        <Link 
          href="/scans/new" 
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          New Scan
        </Link>
      </div>

      {/* Bar Chart Visualization */}
      {scans.length > 0 && (
        <div className="mb-8">
          <ScanBarChart 
            scans={scans} 
            projects={projects} 
            projectsData={projectsData} 
          />
        </div>
      )}

      {scans.length > 0 ? (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full bg-white" style={{ borderCollapse: 'collapse' }}>
            <thead>
              <tr className="border-b border-gray-200">
                <th className="py-2 px-4 text-left text-gray-800 font-semibold">Status</th>
                <th className="py-2 px-4 text-left text-gray-800 font-semibold">Project</th>
                <th className="py-2 px-4 text-left text-gray-800 font-semibold">Type</th>
                <th className="py-2 px-4 text-left text-gray-800 font-semibold">Started</th>
                <th className="py-2 px-4 text-left text-gray-800 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {scans.map((scan) => (
                <tr key={scan.id} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="py-2 px-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(scan.status)}`}>
                      {scan.status.charAt(0).toUpperCase() + scan.status.slice(1)}
                    </span>
                  </td>
                  <td className="py-2 px-4 text-gray-800">
                    <Link href={`/projects/${scan.project_id}`} className="text-blue-600 hover:underline">
                      {projects[scan.project_id] || projects[String(scan.project_id)] || `Project ${scan.project_id}`}
                    </Link>
                  </td>
                  <td className="py-2 px-4 text-gray-800 capitalize">
                    {scan.config?.scan_type ? 
                      (scan.config.scan_type === 'active' ? 'Active' :
                       scan.config.scan_type === 'passive' ? 'Passive' :
                       scan.config.scan_type === 'comprehensive' ? 'Comprehensive' :
                       scan.config.scan_type) :
                      (scan.configuration_name || 'Standard')
                    }
                  </td>
                  <td className="py-2 px-4 text-gray-800">
                    {scan.started_at ? formatDate(scan.started_at) : formatDate(scan.created_at)}
                  </td>
                  <td className="py-2 px-4">
                    <div className="flex space-x-2">
                      {scan.status === 'completed' && (
                        <Link href={`/scans/${scan.id}/results`} className="text-blue-600 hover:underline">
                          View Results
                        </Link>
                      )}
                      {(scan.status === 'in_progress' || scan.status === 'running') && (
                        <Link href={`/scans/${scan.id}/status`} className="text-blue-600 hover:underline">
                          View Progress
                        </Link>
                      )}
                      {(scan.status === 'in_progress' || scan.status === 'running') && (
                        <button
                          onClick={() => handleStop(scan.id)}
                          disabled={stoppingId === scan.id}
                          className={`text-red-600 hover:underline disabled:opacity-50`}
                        >
                          {stoppingId === scan.id ? 'Stopping…' : 'Stop'}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <h2 className="text-xl font-semibold mb-4">No Scans Found</h2>
          <p className="text-gray-600 mb-6">You haven't run any security scans yet.</p>
          <Link href="/scans/new" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            Start Your First Scan
          </Link>
        </div>
      )}
    </div>
  );
}