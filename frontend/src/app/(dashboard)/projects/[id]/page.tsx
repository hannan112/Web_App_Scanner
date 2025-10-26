/* eslint-disable @typescript-eslint/no-explicit-any */
// src/app/(dashboard)/projects/[id]/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/contexts/AuthContext";
import Link from "next/link";
import { getProjectStats } from "@/lib/api/projects";
import { getScanResults } from "@/lib/api/scans";
import { ProjectStats } from "@/types/project";
import { formatDuration } from "@/lib/utils";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface ProjectDetailPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default function ProjectDetailPage({ params }: ProjectDetailPageProps) {
  const { loading: authLoading, isAuthenticated } = useAuth();
  const router = useRouter();
  const [projectId, setProjectId] = useState<string>("");
  const [projectStats, setProjectStats] = useState<ProjectStats | null>(null);
  const [lastScanSummary, setLastScanSummary] = useState<any | null>(null);
  const [lastScanMeta, setLastScanMeta] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Resolve params first
  useEffect(() => {
    params.then(resolvedParams => {
      setProjectId(resolvedParams.id);
    });
  }, [params]);

  useEffect(() => {
    if (authLoading || !projectId) return;
    
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    const fetchProjectStats = async () => {
      try {
        const data = await getProjectStats(projectId);
        setProjectStats(data);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchProjectStats();
  }, [authLoading, isAuthenticated, router, projectId]);

  // When we have projectStats, fetch last scan summary if available
  useEffect(() => {
    const loadLastScanSummary = async () => {
      if (!projectStats?.scan_stats?.recent_scans || projectStats.scan_stats.recent_scans.length === 0) {
        setLastScanSummary(null);
        setLastScanMeta(null);
        return;
      }

      const last = projectStats.scan_stats.recent_scans[0];
      setLastScanMeta(last);
      try {
        const data = await getScanResults(String(last.id));
        // Prefer server-provided summary if present
        const summary = data?.summary || null;
        setLastScanSummary(summary);
      } catch {
        // If results fetch fails, keep meta only
        setLastScanSummary(null);
      }
    };

    loadLastScanSummary();
  }, [projectStats]);

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

  if (!projectStats) {
    return (
      <div className="p-4">
        <div className="p-3 mb-4 text-sm text-orange-600 bg-orange-100 rounded">
          Project not found
        </div>
        <Link href="/projects" className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700">
          Back to Projects
        </Link>
      </div>
    );
  }

  const { project, scan_stats } = projectStats;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Project Header */}
      <div className="bg-white text-gray-800 p-6 rounded-lg shadow mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold">{project.name}</h1>
            <a 
              href={project.target_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              {project.target_url}
            </a>
            {project.description && (
              <p className="mt-2 text-gray-600">{project.description}</p>
            )}
            <p className="mt-2 text-sm text-gray-500">
              Created: {new Date(project.created_at).toLocaleString()}
            </p>
          </div>
          
          <div className="flex space-x-2">
            <Link 
              href={`/projects/${project.id}/edit`}
              className="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              Edit
            </Link>
            <Link 
              href={`/projects/${project.id}/scans/new`}
              className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              New Scan
            </Link>
          </div>
        </div>
      </div>

      {/* Scan Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Consolidated Scan Information */}
        <div className="bg-white text-gray-800 p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Scan Overview</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-600">{scan_stats.total_scans}</p>
              <p className="text-sm text-gray-600">Total Scans</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-green-600">{Object.keys(scan_stats.scan_counts_by_type).length}</p>
              <p className="text-sm text-gray-600">Scan Types</p>
            </div>
          </div>
          {Object.keys(scan_stats.scan_counts_by_type).length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Scan Types Breakdown</h3>
              <div className="space-y-2">
                {Object.entries(scan_stats.scan_counts_by_type).map(([type, count]) => (
                  <div key={type} className="flex justify-between items-center">
                    <span className="capitalize text-sm">{type}</span>
                    <div className="flex items-center">
                      <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${(Number(count) / scan_stats.total_scans) * 100}%` }}
                        ></div>
                      </div>
                      <span className="font-semibold text-sm">{String(count)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Enhanced Last Scan with Analytics */}
        <div className="bg-white text-gray-800 p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Last Scan Analytics</h2>
          {lastScanMeta ? (
            <div className="space-y-4">
              {/* Scan Details */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Type</span>
                  <span className="font-semibold capitalize">{lastScanMeta.scan_type || lastScanMeta.configuration?.scan_type || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Status</span>
                  <span className="font-semibold capitalize">{lastScanMeta.status || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Started</span>
                  <span className="font-semibold">{lastScanMeta.start_time ? new Date(lastScanMeta.start_time).toLocaleString() : '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Duration</span>
                  <span className="font-semibold">{
                    lastScanMeta.end_time && lastScanMeta.start_time
                      ? formatDuration(new Date(lastScanMeta.end_time).getTime() - new Date(lastScanMeta.start_time).getTime())
                      : (lastScanMeta.status === 'running' ? 'In progress' : '-')
                  }</span>
                </div>
              </div>

              {/* Vulnerability Analytics */}
              {lastScanSummary ? (
                <div className="pt-4 border-t border-gray-100">
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-gray-600">Total Vulnerabilities</span>
                    <span className="font-semibold text-lg">{lastScanSummary.total_vulnerabilities}</span>
                  </div>
                  
                  {/* Vulnerability Severity Chart */}
                  <div className="h-48">
                    <Doughnut
                      data={{
                        labels: ['Critical', 'High', 'Medium', 'Low', 'Info'],
                        datasets: [{
                          data: [
                            lastScanSummary.critical_count || 0,
                            lastScanSummary.high_count || 0,
                            lastScanSummary.medium_count || 0,
                            lastScanSummary.low_count || 0,
                            lastScanSummary.info_count || 0
                          ],
                          backgroundColor: [
                            '#DC2626', // Red for Critical
                            '#EA580C', // Orange for High
                            '#D97706', // Amber for Medium
                            '#2563EB', // Blue for Low
                            '#6B7280'  // Gray for Info
                          ],
                          borderWidth: 2,
                          borderColor: '#ffffff'
                        }]
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: {
                            position: 'bottom',
                            labels: {
                              usePointStyle: true,
                              padding: 20,
                              font: {
                                size: 12
                              }
                            }
                          },
                          tooltip: {
                            callbacks: {
                              label: function(context) {
                                const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
                                const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : '0';
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                              }
                            }
                          }
                        }
                      }}
                    />
                  </div>

                  {/* Vulnerability Counts */}
                  <div className="grid grid-cols-2 gap-2 text-xs mt-3">
                    <div className="flex justify-between text-red-600">
                      <span>Critical</span>
                      <span className="font-semibold">{lastScanSummary.critical_count}</span>
                    </div>
                    <div className="flex justify-between text-orange-600">
                      <span>High</span>
                      <span className="font-semibold">{lastScanSummary.high_count}</span>
                    </div>
                    <div className="flex justify-between text-yellow-600">
                      <span>Medium</span>
                      <span className="font-semibold">{lastScanSummary.medium_count}</span>
                    </div>
                    <div className="flex justify-between text-blue-600">
                      <span>Low</span>
                      <span className="font-semibold">{lastScanSummary.low_count}</span>
                    </div>
                    <div className="flex justify-between text-gray-600 col-span-2">
                      <span>Info</span>
                      <span className="font-semibold">{lastScanSummary.info_count}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-gray-500 italic mt-2">Summary unavailable</p>
              )}
              
              <div className="pt-2 border-t border-gray-100">
                <Link href={`/projects/${project.id}/scans/${lastScanMeta.id}`} className="text-blue-600 hover:underline text-sm">View last scan</Link>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 italic">No scans yet</p>
          )}
        </div>
      </div>

      {/* Recent Scans */}
      <div className="bg-white  text-gray-800 p-6 rounded-lg shadow mb-6">
        <h2 className="text-xl font-semibold mb-4">Recent Scans</h2>
        
        {scan_stats.recent_scans && scan_stats.recent_scans.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="py-2 px-4 text-left">Type</th>
                  <th className="py-2 px-4 text-left">Status</th>
                  <th className="py-2 px-4 text-left">Started</th>
                  <th className="py-2 px-4 text-left">Duration</th>
                  <th className="py-2 px-4 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {scan_stats.recent_scans.map((scan: any) => (
                  <tr key={scan.id} className="border-t">
                    <td className="py-2 px-4">
                      <span className="inline-block px-2 py-1 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 capitalize">
                        {scan.scan_type || scan.configuration?.scan_type || 'Unknown'}
                      </span>
                    </td>
                    <td className="py-2 px-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        scan.status === 'completed' ? 'bg-green-100 text-green-800' :
                        scan.status === 'running' ? 'bg-blue-100 text-blue-800' :
                        scan.status === 'failed' ? 'bg-red-100 text-red-800' :
                        scan.status === 'stopped' ? 'bg-orange-100 text-orange-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {scan.status}
                      </span>
                    </td>
                    <td className="py-2 px-4 text-gray-600">
                      {new Date(scan.start_time).toLocaleString()}
                    </td>
                    <td className="py-2 px-4 text-gray-600">
                      {scan.end_time ? 
                        formatDuration(new Date(scan.end_time).getTime() - new Date(scan.start_time).getTime()) : 
                        scan.status === 'running' ? 'In progress' : '-'}
                    </td>
                    <td className="py-2 px-4">
                      <Link href={`/projects/${project.id}/scans/${scan.id}`} className="text-blue-600 hover:underline">
                        View Results
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="bg-gray-50 p-6 text-center rounded">
            <p className="text-gray-600 mb-4">No scans have been performed yet.</p>
            <Link 
              href={`/projects/${project.id}/scans/new`}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Start First Scan
            </Link>
          </div>
        )}
      </div>

      {/* Actions and Navigation */}
      <div className="flex justify-between items-center">
        <Link href="/projects" className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300">
          Back to Projects
        </Link>
        
        <div className="flex space-x-2">
          <Link 
            href={`/projects/${project.id}/scans/new`}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            New Scan
          </Link>
          <Link 
            href={`/projects/${project.id}/scans`}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
          >
            View All Scans
          </Link>
        </div>
      </div>
    </div>
  );
}

