// src/components/scanning/ScanTable.tsx
import Link from "next/link";
import { Scan } from "@/types/project";
import { formatDate, formatDuration, getStatusBadgeClass, getScanActionLink, capitalizeFirst } from "@/lib/utils";

interface ScanTableProps {
  scans: Scan[];
  projectId?: string;
}

export default function ScanTable({ scans, projectId }: ScanTableProps) {
  if (scans.length === 0) {
    return (
      <div className="bg-white p-8 rounded-lg shadow text-center">
        <h2 className="text-xl font-semibold mb-4">No Scans Found</h2>
        <p className="text-gray-600 mb-6">No security scans have been performed for this project yet.</p>
        {projectId && (
          <Link 
            href={`/projects/${projectId}/scans/new`}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Start Your First Scan
          </Link>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Type
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Started
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Completed
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Duration
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {scans.map((scan) => (
            <tr key={scan.id}>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeClass(scan.status)}`}>
                  {capitalizeFirst(scan.status)}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800 capitalize">
                {scan.configuration_name || "Standard"}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                {scan.started_at ? formatDate(scan.started_at) : formatDate(scan.created_at)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                {scan.completed_at ? formatDate(scan.completed_at) : "-"}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                {scan.completed_at && scan.started_at ? (
                  formatDuration(
                    new Date(scan.completed_at).getTime() - new Date(scan.started_at).getTime()
                  )
                ) : (
                  scan.status === "in_progress" ? "Running..." : "-"
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                {(() => {
                  const action = getScanActionLink(scan);
                  return action.href !== '#' ? (
                    <Link href={action.href} className="text-blue-600 hover:underline">
                      {action.text}
                    </Link>
                  ) : (
                    <span className="text-gray-400">{action.text}</span>
                  );
                })()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
} 