// src/app/(dashboard)/projects/[id]/scans/[scanId]/status/page.tsx

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

// This component redirects to the main scan status page
export default function ProjectScanStatusPage({ 
  params 
}: { 
  params: { id: string; scanId: string } 
}) {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the main scan status page
    router.push(`/scans/${params.scanId}/status`);
  }, [params.scanId, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="w-6 h-6 border-4 border-t-blue-600 rounded-full animate-spin"></div>
      <span className="ml-3 text-gray-700">Redirecting to scan status...</span>
    </div>
  );
}