/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react/no-unescaped-entities */
// src/app/(dashboard)/scans/page.tsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { getAllScans } from "@/lib/api/scans";
import { Project, Scan } from "@/types/project";
import { getProjects } from "@/lib/api/projects";

export default function ScansPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [scans, setScans] = useState<Scan[]>([]);
  const [projects, setProjects] = useState<{[key: string]: string}>({});
  const [projectsData, setProjectsData] = useState<Project[]>([]); // Initialize as empty array
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "loading") return;
    
    if (!session) {
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
        
        // Create a map of project IDs to names
        const projectMap = projectsArray.reduce((acc, project) => {
          acc[project.id] = project.name;
          return acc;
        }, {} as {[key: string]: string});
        setProjects(projectMap);
        
        // Fetch all scans
        const scansData = await getAllScans();
        setScans(scansData);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [session, status, router]);

  // Get scan status badge class
  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
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

      {scans.length > 0 ? (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full bg-white">
            <thead>
              <tr>
                <th className="py-2 px-4 border-b text-left text-gray-800 font-semibold">Status</th>
                <th className="py-2 px-4 border-b text-left text-gray-800 font-semibold">Project</th>
                <th className="py-2 px-4 border-b text-left text-gray-800 font-semibold">Type</th>
                <th className="py-2 px-4 border-b text-left text-gray-800 font-semibold">Started</th>
                <th className="py-2 px-4 border-b text-left text-gray-800 font-semibold">Completed</th>
                <th className="py-2 px-4 border-b text-left text-gray-800 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {scans.map((scan) => (
                <tr key={scan.id}>
                  <td className="py-2 px-4 border-b">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(scan.status)}`}>
                      {scan.status.charAt(0).toUpperCase() + scan.status.slice(1)}
                    </span>
                  </td>
                  <td className="py-2 px-4 border-b text-gray-800">
                    <Link href={`/projects/${scan.project_id}`} className="text-blue-600 hover:underline">
                      {projects[scan.project_id] || scan.project_id}
                    </Link>
                  </td>
                  <td className="py-2 px-4 border-b text-gray-800 capitalize">
                    {scan.configuration_name || 'Standard'}
                  </td>
                  <td className="py-2 px-4 border-b text-gray-800">
                    {scan.started_at ? formatDate(scan.started_at) : formatDate(scan.created_at)}
                  </td>
                  <td className="py-2 px-4 border-b text-gray-800">
                    {scan.completed_at ? formatDate(scan.completed_at) : '-'}
                  </td>
                  <td className="py-2 px-4 border-b">
                    <div className="flex space-x-2">
                      {scan.status === 'completed' && (
                        <Link href={`/scans/${scan.id}/results`} className="text-blue-600 hover:underline">
                          View Results
                        </Link>
                      )}
                      {scan.status === 'in_progress' && (
                        <Link href={`/scans/${scan.id}/status`} className="text-blue-600 hover:underline">
                          View Progress
                        </Link>
                      )}
                      {scan.status === 'in_progress' && (
                        <button className="text-red-600 hover:underline">
                          Stop
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