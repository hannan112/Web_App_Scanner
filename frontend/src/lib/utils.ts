// src/lib/utils.ts
// Centralized utility functions to reduce code duplication

/**
 * Format duration in milliseconds to human-readable format
 */
export function formatDuration(ms: number): string {
  if (ms < 0) return '-';
  
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}

/**
 * Format date string to localized format
 */
export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString();
}

/**
 * Get CSS classes for status badges
 */
export function getStatusBadgeClass(status: string): string {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'in_progress':
      return 'bg-blue-100 text-blue-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    case 'stopped':
      return 'bg-orange-100 text-orange-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

/**
 * Get action link for scan based on status
 */
export function getScanActionLink(scan: { id: number; status: string }): { href: string; text: string } {
  const scanId = scan.id.toString();
  
  switch (scan.status) {
    case 'completed':
      return {
        href: `/scans/${scanId}/results`,
        text: 'View Results'
      };
    case 'in_progress':
      return {
        href: `/scans/${scanId}/status`,
        text: 'View Progress'
      };
    case 'failed':
    case 'stopped':
      return {
        href: `/scans/${scanId}/status`,
        text: 'View Details'
      };
    default:
      return {
        href: '#',
        text: 'Pending'
      };
  }
}

/**
 * Capitalize first letter of string
 */
export function capitalizeFirst(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
} 