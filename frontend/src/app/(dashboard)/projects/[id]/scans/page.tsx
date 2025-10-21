// src/app/(dashboard)/projects/[id]/scans/page.tsx

"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useProjectData } from "@/lib/hooks/useProjectData";
import { useScansData } from "@/lib/hooks/useScansData";
import PageTitle from "@/components/PageTitle";
import ScanTable from "@/components/scanning/ScanTable";

export default function ProjectScansPage({ params }: { params: Promise<{ id: string }> }) {
  const [projectId, setProjectId] = useState<string>("");
  
  // Resolve params first
  useEffect(() => {
    params.then(resolvedParams => {
      setProjectId(resolvedParams.id);
    });
  }, [params]);

  // Use custom hooks for data fetching
  const { project, loading: projectLoading, error: projectError } = useProjectData({ projectId });
  const { scans, loading: scansLoading, error: scansError } = useScansData({ projectId, enabled: !!projectId });

  const loading = projectLoading || scansLoading;
  const error = projectError || scansError;

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
            href={`/projects/${projectId}/scans/new`}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Start New Scan
          </Link>
          <Link 
            href={`/projects/${projectId}`}
            className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
          >
            Back to Project
          </Link>
        </div>
      </div>

      <ScanTable scans={scans} projectId={projectId} />
    </div>
  );
}

