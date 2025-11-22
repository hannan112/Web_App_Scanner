/* eslint-disable react/no-unescaped-entities */
// src/app/(dashboard)/projects/page.tsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/contexts/AuthContext";
import { useRouter } from "next/navigation";
import { getProjects, deleteProject } from "@/lib/api/projects";
import { Project } from "@/types/project";

export default function ProjectsPage() {
  const { loading: authLoading, isAuthenticated } = useAuth();
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);

  useEffect(() => {
    if (authLoading) return;

    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    const fetchProjects = async () => {
      try {
        const data = await getProjects();
        setProjects(data);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, [authLoading, isAuthenticated, router]);

  const handleDelete = async (id: number) => {
    try {
      await deleteProject(id);
      setProjects(projects.filter(project => project.id !== id));
      setDeleteConfirm(null);
    } catch (err) {
      setError((err as Error).message);
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
      <h1 className="text-2xl font-semibold text-gray-800 mb-6">My Projects</h1>
      <div className="flex justify-between items-center mb-6">
        <Link href="/projects/new" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          Create Project
        </Link>
      </div>

      {projects.length > 0 ? (
        <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-lg shadow-lg overflow-visible p-6">
          <table className="min-w-full bg-transparent" style={{ borderCollapse: 'collapse' }}>
            <thead>
              <tr className="border-b border-slate-200">
                <th className="py-2 px-4 text-left text-slate-900 font-semibold">Name</th>
                <th className="py-2 px-4 text-left text-slate-900 font-semibold">Target URL</th>
                <th className="py-2 px-4 text-left text-slate-900 font-semibold">Created</th>
                <th className="py-2 px-4 text-left text-slate-900 font-semibold">Scans</th>
                <th className="py-2 px-4 text-left text-slate-900 font-semibold">Last Scan</th>
                <th className="py-2 px-4 text-left text-slate-900 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr key={project.id} className="border-b border-slate-200 hover:bg-white/20 transition-colors">
                  <td className="py-2 px-4 text-slate-800">
                    <Link href={`/projects/${project.id}`} className="text-blue-600 hover:underline font-medium">
                      {project.name}
                    </Link>
                  </td>
                  <td className="py-2 px-4">
                    <a href={project.target_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                      {project.target_url}
                    </a>
                  </td>
                  <td className="py-2 px-4 text-slate-800">
                    {new Date(project.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-2 px-4 text-slate-800">
                    {project.scan_count || 0}
                  </td>
                  <td className="py-2 px-4 text-slate-800">
                    {project.last_scan_date
                      ? new Date(project.last_scan_date).toLocaleDateString()
                      : 'Never'}
                  </td>
                  <td className="py-2 px-4">
                    <div className="relative inline-block text-left">
                      <button
                        type="button"
                        className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        id={`menu-button-${project.id}`}
                        aria-expanded="true"
                        aria-haspopup="true"
                        onClick={() => setDeleteConfirm(deleteConfirm === project.id ? null : project.id)}
                      >
                        <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <circle cx="12" cy="6" r="1.5" />
                          <circle cx="12" cy="12" r="1.5" />
                          <circle cx="12" cy="18" r="1.5" />
                        </svg>
                      </button>
                      {deleteConfirm === project.id && (
                        <div className="origin-top-right absolute right-0 mt-2 w-36 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-20">
                          <div className="py-1" role="menu" aria-orientation="vertical" aria-labelledby={`menu-button-${project.id}`}>
                            <Link href={`/projects/${project.id}`} className="block px-4 py-2 text-sm text-blue-700 hover:bg-gray-100" role="menuitem">View</Link>
                            <Link href={`/projects/${project.id}/edit`} className="block px-4 py-2 text-sm text-green-700 hover:bg-gray-100" role="menuitem">Edit</Link>
                            <button onClick={() => handleDelete(project.id)} className="block w-full text-left px-4 py-2 text-sm text-red-700 hover:bg-gray-100" role="menuitem">Delete</button>
                          </div>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-white/10 backdrop-blur-md border border-white/20 p-8 rounded-lg shadow-lg text-center">
          <h2 className="text-xl font-semibold mb-4 text-slate-900">No Projects Found</h2>
          <p className="text-slate-700 mb-6">You haven't created any projects yet. Create your first project to get started.</p>
          <Link href="/projects/new" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 shadow-md">
            Create New Project
          </Link>
        </div>
      )}
    </div>
  );
}