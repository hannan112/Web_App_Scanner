/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
// src/app/(dashboard)/projects/[id]/scans/page.tsx

"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { getProjectById } from "@/lib/api/projects";
import { getAllScans } from "@/lib/api/scans";
import { Scan } from "@/types/project";
import PageTitle from "@/components/PageTitle";

export default function ProjectScansPage({ params }: { params: { id: string } }) {
  const { data: session, status } = useSession();
  const router = useRouter();
  
  const [project, setProject] = useState<any>(null);
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
      return;
    }
    
    const fetchData = async () => {
      try {
        // Fetch project details
        const projectData = await getProjectById(params.id);
        setProject(projectData);
        
        // Fetch all scans
        const allScans = await getAllScans();
        
        // Filter scans for this project
        const projectScans = allScans.filter(
          (          scan: { project_id: { toString: () => string; }; }) => scan.project_id?.toString() === params.id
        );
        
        setScans(projectScans);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [params.id, status, router]);

  // Function to format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  // Function to get status badge class
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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-6 h-6 border-4 border-t-blue-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="p-4 mb-4 text-sm text-red-600 bg-red-100 rounded">
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
        <PageTitle 
          title={`Scans for ${project?.name}`}
          subtitle={`View all security scans for ${project?.name}`} 
        />
        
        <div className="flex space-x-2">
          <Link 
            href={`/projects/${params.id}/scan/new`}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Start New Scan
          </Link>
          <Link 
            href={`/projects/${params.id}`}
            className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
          >
            Back to Project
          </Link>
        </div>
      </div>

      {scans.length > 0 ? (
        <div className="bg-white rounded-lg shadow">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Started
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Completed
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {scans.map((scan) => (
                <tr key={scan.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeClass(scan.status)}`}>
                      {scan.status.charAt(0).toUpperCase() + scan.status.slice(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800 capitalize">
                    {scan.configuration_name || "Standard"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {scan.start_time ? formatDate(scan.start_time) : formatDate(scan.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {scan.end_time ? formatDate(scan.end_time) : "-"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {scan.end_time && scan.start_time ? (
                      formatDuration(
                        new Date(scan.end_time).getTime() - new Date(scan.start_time).getTime()
                      )
                    ) : (
                      scan.status === "in_progress" ? "Running..." : "-"
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {scan.status === "completed" ? (
                      <Link href={`/scans/${scan.id}/results`} className="text-blue-600 hover:underline">
                        View Results
                      </Link>
                    ) : scan.status === "in_progress" ? (
                      <Link href={`/scans/${scan.id}/status`} className="text-blue-600 hover:underline">
                        View Progress
                      </Link>
                    ) : scan.status === "failed" || scan.status === "stopped" ? (
                      <Link href={`/scans/${scan.id}/status`} className="text-blue-600 hover:underline">
                        View Details
                      </Link>
                    ) : (
                      <span className="text-gray-400">Pending</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <h2 className="text-xl font-semibold mb-4">No Scans Found</h2>
          <p className="text-gray-600 mb-6">No security scans have been performed for this project yet.</p>
          <Link 
            href={`/projects/${params.id}/scan/new`}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Start Your First Scan
          </Link>
        </div>
      )}
    </div>
  );
}

// Helper function to format duration in milliseconds
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