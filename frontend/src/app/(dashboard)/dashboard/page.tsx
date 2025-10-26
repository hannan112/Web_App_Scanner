// src/app/(dashboard)/dashboard/page.tsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/contexts/AuthContext";
import { useRouter } from "next/navigation";
import { getProjectDashboard } from "@/lib/api/projects";
import { DashboardData } from "@/types/project";


export default function DashboardPage() {
  const { loading: authLoading, isAuthenticated } = useAuth();
  const router = useRouter();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    const fetchDashboardData = async () => {
      try {
        const data = await getProjectDashboard();
        setDashboardData(data);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [authLoading, isAuthenticated, router]);

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
      {/* Debug component - remove after fixing the issue */}
      
      <h1 className="text-2xl font-bold mb-6 text-gray-800">Dashboard</h1>

      {/* Stats Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-2 text-gray-800">Total Projects</h2>
          <p className="text-3xl font-bold text-blue-600">
            {dashboardData?.total_projects || 0}
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-2 text-gray-800">New Projects (30 days)</h2>
          <p className="text-3xl font-bold text-green-600">
            {dashboardData?.new_projects_last_month || 0}
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-2 text-gray-800">Actions</h2>
          <Link href="/projects/new" className="block w-full text-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            Create New Project
          </Link>
        </div>
      </div>

      {/* Recent Projects */}
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">Recent Projects</h2>
        
        {dashboardData?.recent_projects && dashboardData.recent_projects.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white" style={{ borderCollapse: 'collapse' }}>
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="py-2 px-4 text-left text-gray-800 font-semibold">Name</th>
                  <th className="py-2 px-4 text-left text-gray-800 font-semibold">Target URL</th>
                  <th className="py-2 px-4 text-left text-gray-800 font-semibold">Created</th>
                  <th className="py-2 px-4 text-left text-gray-800 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {dashboardData.recent_projects.map((project) => (
                  <tr key={project.id} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="py-2 px-4 text-gray-800">{project.name}</td>
                    <td className="py-2 px-4">
                      <a href={project.target_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                        {project.target_url}
                      </a>
                    </td>
                    <td className="py-2 px-4 text-gray-800">
                      {new Date(project.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-2 px-4">
                      <Link href={`/projects/${project.id}`} className="text-blue-600 hover:underline mr-4">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="bg-gray-50 p-6 text-center rounded">
            <p className="text-gray-800 font-semibold text-xl mb-4">No Projects Found</p>
            <p className="text-gray-600 mb-4">Create your first project to get started.</p>
            <Link href="/projects/new" className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              Create New Project
            </Link>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <Link href="/projects" className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300">
          View All Projects
        </Link>
      </div>
    </div>
  );
}