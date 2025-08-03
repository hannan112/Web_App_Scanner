// src/app/(dashboard)/projects/[id]/scans/[scanId]/page.tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ProjectScanDetailPage({ 
  params 
}: { 
  params: Promise<{ id: string; scanId: string }> 
}) {
  const router = useRouter();

  useEffect(() => {
    // Resolve params in useEffect
    params.then(resolvedParams => {
      router.push(`/scans/${resolvedParams.scanId}/results`);
    });
  }, [params, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="w-6 h-6 border-4 border-t-blue-600 rounded-full animate-spin"></div>
      <span className="ml-3 text-gray-700">Redirecting to scan results...</span>
    </div>
  );
}