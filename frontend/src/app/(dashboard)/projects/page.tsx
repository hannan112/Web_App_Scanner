/* eslint-disable react/no-unescaped-entities */
// src/app/(dashboard)/projects/page.tsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { getProjects, deleteProject } from "@/lib/api/projects";
import { Project } from "@/types/project";

export default function ProjectsPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);

  useEffect(() => {
    if (status === "loading") return;
    
    if (!session) {
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
  }, [session, status, router]);

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
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full bg-white">
            <thead>
              <tr>
                <th className="py-2 px-4 border-b text-left text-gray-800 font-semibold">Name</th>
                <th className="py-2 px-4 border-b text-left text-gray-800 font-semibold">Target URL</th>
                <th className="py-2 px-4 border-b text-left text-gray-800 font-semibold">Created</th>
                <th className="py-2 px-4 border-b text-left text-gray-800 font-semibold">Scans</th>
                <th className="py-2 px-4 border-b text-left text-gray-800 font-semibold">Last Scan</th>
                <th className="py-2 px-4 border-b text-left text-gray-800 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr key={project.id}>
                  <td className="py-2 px-4 border-b text-gray-800">
                    <Link href={`/projects/${project.id}`} className="text-blue-600 hover:underline font-medium">
                      {project.name}
                    </Link>
                  </td>
                  <td className="py-2 px-4 border-b">
                    <a href={project.target_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                      {project.target_url}
                    </a>
                  </td>
                  <td className="py-2 px-4 border-b text-gray-800">
                    {new Date(project.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-2 px-4 border-b text-gray-800">
                    {project.scan_count || 0}
                  </td>
                  <td className="py-2 px-4 border-b text-gray-800">
                    {project.last_scan_date 
                      ? new Date(project.last_scan_date).toLocaleDateString() 
                      : 'Never'}
                  </td>
                  <td className="py-2 px-4 border-b">
                    <div className="flex space-x-2">
                      <Link href={`/projects/${project.id}`} className="text-blue-600 hover:underline">
                        View
                      </Link>
                      <Link href={`/projects/${project.id}/edit`} className="text-green-600 hover:underline">
                        Edit
                      </Link>
                      {deleteConfirm === project.id ? (
                        <div className="flex space-x-2">
                          <button 
                            onClick={() => handleDelete(project.id)}
                            className="text-red-600 hover:underline font-bold"
                          >
                            Confirm
                          </button>
                          <button 
                            onClick={() => setDeleteConfirm(null)}
                            className="text-gray-600 hover:underline"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <button 
                          onClick={() => setDeleteConfirm(project.id)}
                          className="text-red-600 hover:underline"
                        >
                          Delete
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
          <h2 className="text-xl font-semibold mb-4">No Projects Found</h2>
          <p className="text-gray-600 mb-6">You haven't created any projects yet. Create your first project to get started.</p>
          <Link href="/projects/new" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            Create New Project
          </Link>
        </div>
      )}
    </div>
  );
}