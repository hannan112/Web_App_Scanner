// src/lib/hooks/useProjectData.ts
import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { getProjectById } from '@/lib/api/projects';

interface UseProjectDataProps {
  projectId: string;
}

export function useProjectData({ projectId }: UseProjectDataProps) {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  
  const [project, setProject] = useState<{ name: string; id: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    
    const fetchProject = async () => {
      if (!projectId || !isAuthenticated) return;
      
      try {
        const projectData = await getProjectById(projectId);
        setProject(projectData);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };
    
    fetchProject();
  }, [projectId, isAuthenticated, authLoading, router]);

  return { project, loading, error };
} 