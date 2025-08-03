// src/app/(dashboard)/projects/[id]/scan/page.tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function OldScanPageRedirect({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();

  useEffect(() => {
    params.then(resolvedParams => {
      router.replace(`/projects/${resolvedParams.id}/scans/new`);
    });
  }, [params, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="w-6 h-6 border-4 border-t-blue-600 rounded-full animate-spin"></div>
      <span className="ml-3 text-gray-700">Redirecting to new scan page...</span>
    </div>
  );
}