"use client";

import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Scan, Project } from '@/types/project';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface ScanBarChartProps {
  scans: Scan[];
  projects: { [key: string]: string };
  projectsData: Project[];
}

export default function ScanBarChart({ scans, projects, projectsData }: ScanBarChartProps) {
  // Group scans by project and sort by project name for consistent alignment
  const projectScanData = projectsData
    .map(project => {
      const projectScans = scans.filter(scan => 
        scan.project_id?.toString() === project.id.toString()
      );
      
      return {
        projectName: project.name,
        projectId: project.id,
        totalScans: projectScans.length,
        completedScans: projectScans.filter(scan => scan.status === 'completed').length,
        inProgressScans: projectScans.filter(scan => 
          scan.status === 'in_progress' || scan.status === 'running'
        ).length,
        failedScans: projectScans.filter(scan => scan.status === 'failed').length,
      };
    })
    .filter(project => project.totalScans > 0) // Only show projects with scans
    .sort((a, b) => a.projectName.localeCompare(b.projectName)); // Sort alphabetically for consistent alignment

  // Prepare chart data with smooth styling
  const chartData = {
    labels: projectScanData.map(project => project.projectName),
    datasets: [
      {
        label: 'Completed',
        data: projectScanData.map(project => project.completedScans),
        backgroundColor: 'rgba(34, 197, 94, 0.7)',
        borderColor: 'rgba(34, 197, 94, 1)',
        borderWidth: 2,
        borderRadius: 6,
        borderSkipped: false,
        tension: 0.1,
      },
      {
        label: 'In Progress',
        data: projectScanData.map(project => project.inProgressScans),
        backgroundColor: 'rgba(59, 130, 246, 0.7)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2,
        borderRadius: 6,
        borderSkipped: false,
        tension: 0.1,
      },
      {
        label: 'Failed',
        data: projectScanData.map(project => project.failedScans),
        backgroundColor: 'rgba(239, 68, 68, 0.7)',
        borderColor: 'rgba(239, 68, 68, 1)',
        borderWidth: 2,
        borderRadius: 6,
        borderSkipped: false,
        tension: 0.1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12,
            weight: '500' as const,
          },
        },
      },
      title: {
        display: true,
        text: 'Scans by Project and Status',
        font: {
          size: 18,
          weight: 'bold' as const,
        },
        padding: {
          bottom: 20,
        },
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        padding: 12,
        titleFont: {
          size: 13,
          weight: 'bold' as const,
        },
        bodyFont: {
          size: 12,
        },
      },
    },
    scales: {
      x: {
        stacked: false,
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 11,
            weight: '500' as const,
          },
          color: '#6B7280',
          maxRotation: 45,
          minRotation: 0,
        },
        title: {
          display: true,
          text: 'Projects',
          font: {
            size: 13,
            weight: '600' as const,
          },
          color: '#374151',
          padding: {
            top: 10,
          },
        },
      },
      y: {
        stacked: false,
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
          drawBorder: false,
        },
        ticks: {
          stepSize: 1,
          font: {
            size: 11,
            weight: '500' as const,
          },
          color: '#6B7280',
          padding: 8,
        },
        title: {
          display: true,
          text: 'Number of Scans',
          font: {
            size: 13,
            weight: '600' as const,
          },
          color: '#374151',
          padding: {
            bottom: 10,
          },
        },
      },
    },
    animation: {
      duration: 1000,
      easing: 'easeInOutQuart' as const,
    },
  };

  if (projectScanData.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Scan Statistics by Project</h3>
        <div className="text-center text-gray-500 py-8">
          No scan data available to display
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg border border-gray-100">
      <h3 className="text-lg font-semibold text-gray-800 mb-6">Scan Statistics by Project</h3>
      <div className="h-96 relative">
        <Bar data={chartData} options={options} />
      </div>
      
      {/* Summary statistics */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-green-600">
            {projectScanData.reduce((sum, project) => sum + project.completedScans, 0)}
          </div>
          <div className="text-sm text-green-700">Total Completed</div>
        </div>
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">
            {projectScanData.reduce((sum, project) => sum + project.inProgressScans, 0)}
          </div>
          <div className="text-sm text-blue-700">In Progress</div>
        </div>
        <div className="bg-red-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-red-600">
            {projectScanData.reduce((sum, project) => sum + project.failedScans, 0)}
          </div>
          <div className="text-sm text-red-700">Failed</div>
        </div>
      </div>
    </div>
  );
}
