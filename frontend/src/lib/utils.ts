import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { Scan } from "@/types/project"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDuration(milliseconds: number): string {
  if (!Number.isFinite(milliseconds) || milliseconds < 0) return '-'
  const totalSeconds = Math.floor(milliseconds / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60

  const parts: string[] = []
  if (hours > 0) parts.push(`${hours}h`)
  if (minutes > 0 || hours > 0) parts.push(`${minutes}m`)
  parts.push(`${seconds}s`)
  return parts.join(' ')
}

export function formatDate(dateString: string): string {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleString();
}

export function capitalizeFirst(str: string): string {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function getStatusBadgeClass(status: string): string {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    case 'in_progress':
      return 'bg-blue-100 text-blue-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export function getScanActionLink(scan: Scan): { href: string; text: string } {
  if (scan.status === 'completed') {
    return { href: `/projects/${scan.project_id}/scans/${scan.uuid}`, text: 'View Results' };
  }
  if (scan.status === 'failed') {
    return { href: '#', text: 'Failed' };
  }
  if (scan.status === 'in_progress') {
    return { href: '#', text: 'Scanning...' };
  }
  return { href: '#', text: 'Details' };
}
