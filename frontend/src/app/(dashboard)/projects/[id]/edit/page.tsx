/* eslint-disable @typescript-eslint/no-unused-vars */
// src/app/(dashboard)/projects/[id]/edit/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { getProjectById, updateProject } from "@/lib/api/projects";
import { Project } from "@/types/project";

interface EditProjectPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default function EditProjectPage({ params }: EditProjectPageProps) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [projectId, setProjectId] = useState<string>("");
  const [formData, setFormData] = useState({
    name: "",
    target_url: "",
    description: ""
  });
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Resolve params first
  useEffect(() => {
    params.then(resolvedParams => {
      setProjectId(resolvedParams.id);
    });
  }, [params]);

  useEffect(() => {
    if (status === "loading" || !projectId) return;
    
    if (!session) {
      router.push("/login");
      return;
    }

    const fetchProject = async () => {
      try {
        const data = await getProjectById(projectId);
        setProject(data);
        setFormData({
          name: data.name,
          target_url: data.target_url,
          description: data.description || ""
        });
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchProject();
  }, [session, status, router, projectId]);

  const validateForm = () => {
    const errors: {[key: string]: string} = {};
    
    if (!formData.name.trim()) {
      errors.name = "Project name is required";
    }
    
    if (!formData.target_url.trim()) {
      errors.target_url = "Target URL is required";
    } else {
      try {
        new URL(formData.target_url);
      } catch (e) {
        errors.target_url = "Please enter a valid URL";
      }
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear validation error for this field if it exists
    if (validationErrors[name]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setSubmitting(true);
    setError(null);
    
    try {
      await updateProject(projectId, formData);
      router.push(`/projects/${projectId}`);
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-6 h-6 border-4 border-t-blue-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!project) {
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

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Edit Project</h1>
        <p className="text-gray-600 mt-1">
          Update the information for your project.
        </p>
      </div>

      {error && (
        <div className="p-3 mb-4 text-sm text-red-600 bg-red-100 rounded">
          {error}
        </div>
      )}

      <div className="bg-white p-6 rounded-lg shadow">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Project Name*
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md ${
                validationErrors.name ? "border-red-500" : "border-gray-300"
              }`}
            />
            {validationErrors.name && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.name}</p>
            )}
          </div>

          <div className="mb-4">
            <label htmlFor="target_url" className="block text-sm font-medium text-gray-700 mb-1">
              Target URL*
            </label>
            <input
              type="text"
              id="target_url"
              name="target_url"
              value={formData.target_url}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md ${
                validationErrors.target_url ? "border-red-500" : "border-gray-300"
              }`}
            />
            {validationErrors.target_url && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.target_url}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              The URL of the website you want to scan. This must be a reachable website.
            </p>
          </div>

          <div className="mb-6">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="Project description (optional)"
            ></textarea>
          </div>

          <div className="flex items-center justify-between">
            <Link 
              href={`/projects/${projectId}`} 
              className="px-4 py-2 text-gray-600 bg-gray-200 rounded hover:bg-gray-300"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-400"
            >
              {submitting ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}