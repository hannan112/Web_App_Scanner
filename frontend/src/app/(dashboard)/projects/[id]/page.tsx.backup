/* eslint-disable @typescript-eslint/no-explicit-any */
// src/app/(dashboard)/projects/[id]/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { getProjectStats } from "@/lib/api/projects";
import { ProjectStats } from "@/types/project";

interface ProjectDetailPageProps {
  params: {
    id: string;
  };
}


export default function ProjectDetailPage({ params }: ProjectDetailPageProps) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [projectStats, setProjectStats] = useState<ProjectStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "loading") return;
    
    if (!session) {
      router.push("/login");
      return;
    }

    const fetchProjectStats = async () => {
      try {
        const data = await getProjectStats(params.id);
        setProjectStats(data);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchProjectStats();
  }, [session, status, router, params.id]);

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
              href={`/projects/${project.id}/scan/new`}
              className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              New Scan
            </Link>
          </div>
        </div>
      </div>

      {/* Scan Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-white text-gray-800 p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-2">Total Scans</h2>
          <p className="text-3xl font-bold text-blue-600">{scan_stats.total_scans}</p>
        </div>
        
        <div className="bg-white  text-gray-800 p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-2">Scan Types</h2>
          {Object.keys(scan_stats.scan_counts_by_type).length > 0 ? (
            <div className="space-y-1">
              {Object.entries(scan_stats.scan_counts_by_type).map(([type, count]) => (
                <div key={type} className="flex justify-between">
                  <span className="capitalize">{type}</span>
                  <span className="font-semibold">{String(count)}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 italic">No scans yet</p>
          )}
        </div>
        
        <div className="bg-white  text-gray-800 p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-2">Vulnerabilities</h2>
          {Object.keys(scan_stats.vulnerability_counts).length > 0 ? (
            <div className="space-y-1">
              {Object.entries(scan_stats.vulnerability_counts).map(([severity, count]) => (
                <div key={severity} className="flex justify-between">
                  <span className={`capitalize ${
                    severity === 'critical' ? 'text-red-600' :
                    severity === 'high' ? 'text-orange-600' :
                    severity === 'medium' ? 'text-yellow-600' :
                    severity === 'low' ? 'text-blue-600' :
                    'text-gray-600'
                  }`}>
                    {severity}
                  </span>
                  <span className="font-semibold">{String(count)}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 italic">No vulnerabilities detected</p>
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
                    <td className="py-2 px-4 capitalize">{scan.scan_type}</td>
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
              href={`/projects/${project.id}/scan/new`}
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
            href={`/projects/${project.id}/scan/new`}
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

// Helper function to format duration in milliseconds to human-readable format
function formatDuration(ms: number): string {
  if (ms < 0) return '-';
  
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}