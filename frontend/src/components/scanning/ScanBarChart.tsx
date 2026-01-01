"use client";

import { Scan, Project } from '@/types/project';
import Link from 'next/link';

interface ScanBarChartProps {
  scans: Scan[];
  projectsData: Project[];
}

export default function ScanBarChart({ scans, projectsData }: ScanBarChartProps) {
  // Group scans by project and sort by project name
  console.log("DEBUG: ScanBarChart projectsData sample:", projectsData[0]);
  const projectScanData = projectsData
    .map(project => {
      const projectScans = scans.filter(scan =>
        scan.project_id?.toString() === project.id.toString()
      );

      const total = projectScans.length;
      const completed = projectScans.filter(scan => scan.status === 'completed').length;
      const inProgress = projectScans.filter(scan => scan.status === 'in_progress' || scan.status === 'pending').length;
      const failed = projectScans.filter(scan => scan.status === 'failed').length;
      const stopped = projectScans.filter(scan => scan.status === 'stopped').length;

      return {
        projectName: project.name,
        projectId: project.id,
        projectUuid: project.uuid,
        total,
        completed,
        inProgress,
        failed,
        stopped,
        // Calculate percentages for the health bar
        completedPct: total > 0 ? (completed / total) * 100 : 0,
        inProgressPct: total > 0 ? (inProgress / total) * 100 : 0,
        failedPct: total > 0 ? (failed / total) * 100 : 0,
        stoppedPct: total > 0 ? (stopped / total) * 100 : 0,
      };
    })
    .filter(project => project.total > 0) // Only show projects with scans
    .sort((a, b) => a.projectName.localeCompare(b.projectName));

  if (projectScanData.length === 0) {
    return (
      <div className="bg-white/5 backdrop-blur-md border border-white/20 p-6 rounded-lg shadow-lg">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Project Health Overview</h3>
        <div className="text-center text-slate-500 py-8">
          No scan data available to display
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/20 rounded-lg shadow-lg overflow-hidden">
      <div className="p-6 border-b border-white/10">
        <h3 className="text-lg font-semibold text-slate-900">Project Health Overview</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full bg-transparent">
          <thead>
            <tr className="bg-white/5 border-b border-white/10">
              <th className="py-3 px-6 text-left text-xs font-medium text-slate-900 uppercase tracking-wider">Project</th>
              <th className="py-3 px-6 text-left text-xs font-medium text-slate-900 uppercase tracking-wider w-1/3">Scan Distribution</th>
              <th className="py-3 px-6 text-center text-xs font-medium text-slate-900 uppercase tracking-wider">Active</th>
              <th className="py-3 px-6 text-center text-xs font-medium text-slate-900 uppercase tracking-wider">Completed</th>
              <th className="py-3 px-6 text-center text-xs font-medium text-slate-900 uppercase tracking-wider">Total</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {projectScanData.map((project) => (
              <tr key={project.projectId} className="hover:bg-white/10 transition-colors">
                <td className="py-4 px-6 whitespace-nowrap">
                  <Link href={`/projects/${project.projectUuid || project.projectId}`} className="text-sm font-medium text-blue-600 hover:underline">
                    {project.projectName}
                  </Link>
                </td>
                <td className="py-4 px-6 align-middle">
                  <div className="w-full h-2.5 bg-slate-200 rounded-full overflow-hidden flex">
                    {project.completedPct > 0 && (
                      <div
                        className="h-full bg-green-500"
                        style={{ width: `${project.completedPct}%` }}
                        title={`${project.completed} Completed`}
                      />
                    )}
                    {project.inProgressPct > 0 && (
                      <div
                        className="h-full bg-blue-500"
                        style={{ width: `${project.inProgressPct}%` }}
                        title={`${project.inProgress} In Progress`}
                      />
                    )}
                    {project.failedPct > 0 && (
                      <div
                        className="h-full bg-red-500"
                        style={{ width: `${project.failedPct}%` }}
                        title={`${project.failed} Failed`}
                      />
                    )}
                    {project.stoppedPct > 0 && (
                      <div
                        className="h-full bg-orange-400"
                        style={{ width: `${project.stoppedPct}%` }}
                        title={`${project.stopped} Stopped`}
                      />
                    )}
                  </div>
                </td>
                <td className="py-4 px-6 text-center whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${project.inProgress > 0 ? 'bg-blue-100 text-blue-800' : 'text-slate-500'}`}>
                    {project.inProgress}
                  </span>
                </td>
                <td className="py-4 px-6 text-center whitespace-nowrap text-sm text-slate-700">
                  {project.completed}
                </td>
                <td className="py-4 px-6 text-center whitespace-nowrap text-sm font-medium text-slate-900">
                  {project.total}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="bg-white/5 p-4 border-t border-white/10 flex justify-center space-x-6 text-xs text-slate-600">
        <div className="flex items-center">
          <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
          Completed
        </div>
        <div className="flex items-center">
          <span className="w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
          In Progress
        </div>
        <div className="flex items-center">
          <span className="w-3 h-3 bg-red-500 rounded-full mr-2"></span>
          Failed
        </div>
        <div className="flex items-center">
          <span className="w-3 h-3 bg-orange-400 rounded-full mr-2"></span>
          Stopped
        </div>
      </div>
    </div>
  );
}
