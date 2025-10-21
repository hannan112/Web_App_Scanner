/* eslint-disable @typescript-eslint/no-unused-vars */
// src/app/(dashboard)/projects/new/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/contexts/AuthContext";
import Link from "next/link";
import { createProject } from "@/lib/api/projects";

export default function CreateProjectPage() {
  const { user, loading: authLoading, isAuthenticated } = useAuth();
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: "",
    target_url: "",
    description: ""
  });
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check authentication
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-6 h-6 border-4 border-t-blue-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    router.push("/login");
    return null;
  }

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
      const project = await createProject(formData);
      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-semibold text-gray-800 mb-6">Create New Project</h1>
      <div className="mb-6">
        <p className="text-gray-800 mt-1">
          Set up a new security scanning project by providing the basic information below.
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
            <label htmlFor="name" className="block text-sm font-medium text-gray-800 mb-1">
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
              placeholder="My Security Project"
            />
            {validationErrors.name && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.name}</p>
            )}
          </div>

          <div className="mb-4">
            <label htmlFor="target_url" className="block text-sm font-medium text-gray-800 mb-1">
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
              placeholder="https://example.com"
            />
            {validationErrors.target_url && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.target_url}</p>
            )}
            <p className="mt-1 text-sm text-gray-800">
              The URL of the website you want to scan. This must be a reachable website.
            </p>
          </div>

          <div className="mb-6">
            <label htmlFor="description" className="block text-sm font-medium text-gray-800 mb-1">
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
            <Link href="/projects" className="px-4 py-2 text-gray-600 bg-gray-200 rounded hover:bg-gray-300">
              Cancel
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-400"
            >
              {submitting ? "Creating..." : "Create Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}