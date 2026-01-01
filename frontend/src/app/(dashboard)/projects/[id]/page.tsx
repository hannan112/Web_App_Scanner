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
        const data = await getScanResults(last.uuid);
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
        <div className="p-3 mb-4 text-sm text-red-600 bg-red-100/80 backdrop-blur-sm rounded border border-red-200">
          Error: {error}
        </div>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-md"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!projectStats) {
    return (
      <div className="p-4">
        <div className="p-3 mb-4 text-sm text-orange-600 bg-orange-100/80 backdrop-blur-sm rounded border border-orange-200">
          Project not found
        </div>
        <Link href="/projects" className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-md">
          Back to Projects
        </Link>
      </div>
    );
  }

  const { project, scan_stats } = projectStats;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Project Header */}
      <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-lg rounded-lg overflow-hidden mb-8">
        <div className="px-6 py-4 border-b border-white/10 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-slate-900">Project Details</h2>
          <div className="space-x-2">
            <Link
              href={`/projects/${project.uuid}/edit`}
              className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm shadow-md"
            >
              Edit
            </Link>
          </div>
        </div>
        <div className="p-6">
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-6">
            <div>
              <dt className="text-sm font-medium text-slate-700">Project Name</dt>
              <dd className="mt-1 text-lg text-slate-900">{project.name}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-slate-700">Target URL</dt>
              <dd className="mt-1 text-lg text-blue-600">
                <a href={project.target_url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                  {project.target_url}
                </a>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-slate-700">Description</dt>
              <dd className="mt-1 text-base text-slate-800">{project.description || "No description provided"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-slate-700">Created At</dt>
              <dd className="mt-1 text-base text-slate-800">{new Date(project.created_at).toLocaleString()}</dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Scan Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Consolidated Scan Information */}
        <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-lg p-6 rounded-lg">
          <h2 className="text-lg font-semibold mb-4 text-slate-900">Scan Overview</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-600">{scan_stats.total_scans}</p>
              <p className="text-sm text-slate-700">Total Scans</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-green-600">{Object.keys(scan_stats.scan_counts_by_type).length}</p>
              <p className="text-sm text-slate-700">Scan Types</p>
            </div>
          </div>
          {Object.keys(scan_stats.scan_counts_by_type).length > 0 && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <h3 className="text-sm font-semibold text-slate-800 mb-2">Scan Types Breakdown</h3>
              <div className="space-y-2">
                {Object.entries(scan_stats.scan_counts_by_type).map(([type, count]) => (
                  <div key={type} className="flex justify-between items-center">
                    <span className="capitalize text-sm text-slate-700">{type}</span>
                    <div className="flex items-center">
                      <div className="w-16 bg-white/20 rounded-full h-2 mr-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${(Number(count) / scan_stats.total_scans) * 100}%` }}
                        ></div>
                      </div>
                      <span className="font-semibold text-sm text-slate-900">{String(count)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Enhanced Last Scan with Analytics */}
        <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-lg p-6 rounded-lg">
          <h2 className="text-lg font-semibold mb-4 text-slate-900">Last Scan Analytics</h2>
          {lastScanMeta ? (
            <div className="space-y-4">
              {/* Scan Details */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-700">Type</span>
                  <span className="font-semibold capitalize text-slate-900">{lastScanMeta.scan_type || lastScanMeta.configuration?.scan_type || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-700">Status</span>
                  <span className="font-semibold capitalize text-slate-900">{lastScanMeta.status || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-700">Started</span>
                  <span className="font-semibold text-slate-800">{lastScanMeta.start_time ? new Date(lastScanMeta.start_time).toLocaleString() : '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-700">Duration</span>
                  <span className="font-semibold text-slate-800">{
                    lastScanMeta.end_time && lastScanMeta.start_time
                      ? formatDuration(new Date(lastScanMeta.end_time).getTime() - new Date(lastScanMeta.start_time).getTime())
                      : (lastScanMeta.status === 'running' ? 'In progress' : '-')
                  }</span>
                </div>
              </div>

              {/* Vulnerability Analytics */}
              {lastScanSummary ? (
                <div className="pt-4 border-t border-white/10">
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-slate-700">Total Vulnerabilities</span>
                    <span className="font-semibold text-lg text-slate-900">{lastScanSummary.total_vulnerabilities}</span>
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
                          borderColor: '#1e293b' // Darker background for borders
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
                              },
                              color: '#475569' // Darker gray for legend text
                            }
                          },
                          tooltip: {
                            callbacks: {
                              label: function (context) {
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
                    <div className="flex justify-between text-red-400">
                      <span>Critical</span>
                      <span className="font-semibold">{lastScanSummary.critical_count}</span>
                    </div>
                    <div className="flex justify-between text-orange-400">
                      <span>High</span>
                      <span className="font-semibold">{lastScanSummary.high_count}</span>
                    </div>
                    <div className="flex justify-between text-yellow-400">
                      <span>Medium</span>
                      <span className="font-semibold">{lastScanSummary.medium_count}</span>
                    </div>
                    <div className="flex justify-between text-blue-400">
                      <span>Low</span>
                      <span className="font-semibold">{lastScanSummary.low_count}</span>
                    </div>
                    <div className="flex justify-between text-slate-400 col-span-2">
                      <span>Info</span>
                      <span className="font-semibold">{lastScanSummary.info_count}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-slate-600 italic mt-2">Summary unavailable</p>
              )}

              <div className="pt-2 border-t border-white/10">
                <Link href={`/projects/${project.uuid}/scans/${lastScanMeta.uuid}`} className="text-blue-600 hover:underline text-sm">View last scan</Link>
              </div>
            </div>
          ) : (
            <p className="text-slate-600 italic">No scans yet</p>
          )}
        </div>
      </div>

      {/* Recent Scans */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-slate-900">Scan History</h2>
          <Link
            href={`/projects/${project.uuid}/scans/new`}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 shadow-md"
          >
            Start New Scan
          </Link>
        </div>

        {scan_stats.recent_scans && scan_stats.recent_scans.length > 0 ? (
          <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-lg rounded-lg overflow-hidden">
            <table className="min-w-full bg-transparent">
              <thead className="bg-white/5">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                    Started
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {scan_stats.recent_scans.map((scan: any) => (
                  <tr key={scan.id} className="hover:bg-white/10 transition-colors">
                    <td className="py-2 px-4">
                      <span className="inline-block px-2 py-1 rounded-full text-xs font-semibold bg-indigo-100/80 backdrop-blur-sm text-indigo-800 capitalize border border-indigo-200/50">
                        {scan.scan_type || scan.configuration?.scan_type || 'Unknown'}
                      </span>
                    </td>
                    <td className="py-2 px-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium border ${scan.status === 'completed' ? 'bg-green-100/80 backdrop-blur-sm text-green-800 border-green-200/50' :
                        scan.status === 'running' ? 'bg-blue-100/80 backdrop-blur-sm text-blue-800 border-blue-200/50' :
                          scan.status === 'failed' ? 'bg-red-100/80 backdrop-blur-sm text-red-800 border-red-200/50' :
                            scan.status === 'stopped' ? 'bg-orange-100/80 backdrop-blur-sm text-orange-800 border-orange-200/50' :
                              'bg-gray-100/80 backdrop-blur-sm text-gray-800 border-gray-200/50'
                        }`}>
                        {scan.status}
                      </span>
                    </td>
                    <td className="py-2 px-4 text-slate-700">
                      {new Date(scan.start_time).toLocaleString()}
                    </td>
                    <td className="py-2 px-4 text-slate-700">
                      {scan.end_time ?
                        formatDuration(new Date(scan.end_time).getTime() - new Date(scan.start_time).getTime()) :
                        scan.status === 'running' ? 'In progress' : '-'}
                    </td>
                    <td className="py-2 px-4">
                      <Link href={`/projects/${project.uuid}/scans/${scan.uuid}`} className="text-blue-600 hover:underline">
                        View Results
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="bg-white/10 backdrop-blur-md border border-white/20 p-6 text-center rounded-lg shadow">
            <p className="text-slate-700 mb-4">No scans have been performed yet.</p>
            <Link
              href={`/projects/${project.uuid}/scans/new`}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Start First Scan
            </Link>
          </div>
        )}
      </div>

      {/* Actions and Navigation */}
      <div className="flex justify-between items-center">
        <Link href="/projects" className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 shadow-md">
          Back to Projects
        </Link>

        <div className="flex space-x-2">
          <Link
            href={`/projects/${project.uuid}/scans/new`}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 shadow-md"
          >
            New Scan
          </Link>
          <Link
            href={`/projects/${project.uuid}/scans`}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 shadow-md"
          >
            View All Scans
          </Link>
        </div>
      </div>
    </div >
  );
}

