// src/lib/hooks/useScansData.ts
import { useState, useEffect } from 'react';
import { getAllScans } from '@/lib/api/scans';
import { Scan } from '@/types/project';

interface UseScansDataProps {
  projectId: string;
  enabled?: boolean;
}

export function useScansData({ projectId, enabled = true }: UseScansDataProps) {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchScans = async () => {
      if (!projectId || !enabled) return;
      
      try {
        const allScans = await getAllScans();
        
        // Filter scans for this project
        const projectScans = allScans.filter(
          (scan: { project_id: { toString: () => string; }; }) => 
            scan.project_id?.toString() === projectId
        );
        
        setScans(projectScans);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };
    
    fetchScans();
  }, [projectId, enabled]);

  return { scans, loading, error };
} 