"use client";

import { useState, useEffect } from 'react';
import { getZAPStatus } from '@/lib/api/scans';
import { ZAPStatus as ZAPStatusType } from '@/types/project';

interface ZAPStatusProps {
  className?: string;
  showDetails?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export default function ZAPStatus({ 
  className = "", 
  showDetails = false, 
  autoRefresh = false,
  refreshInterval = 30000 
}: ZAPStatusProps) {
  const [status, setStatus] = useState<ZAPStatusType | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const zapStatus = await getZAPStatus();
      setStatus(zapStatus);
      setLastChecked(new Date());
    } catch (error) {
      console.error('Failed to fetch ZAP status:', error);
      setStatus({
        status: 'error',
        error: 'Failed to connect to ZAP service'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      const interval = setInterval(fetchStatus, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const getStatusColor = () => {
    if (loading) return 'bg-gray-100 text-gray-600';
    
    switch (status?.status) {
      case 'connected':
        return 'bg-green-100 text-green-800';
      case 'disconnected':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  const getStatusIcon = () => {
    if (loading) {
      return (
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
      );
    }

    switch (status?.status) {
      case 'connected':
        return <div className="w-2 h-2 bg-green-500 rounded-full"></div>;
      case 'disconnected':
        return <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>;
      case 'error':
        return <div className="w-2 h-2 bg-red-500 rounded-full"></div>;
      default:
        return <div className="w-2 h-2 bg-gray-400 rounded-full"></div>;
    }
  };

  const getStatusText = () => {
    if (loading) return 'Checking...';
    
    switch (status?.status) {
      case 'connected':
        return 'ZAP Connected';
      case 'disconnected':
        return 'ZAP Disconnected';
      case 'error':
        return 'ZAP Error';
      default:
        return 'ZAP Unknown';
    }
  };

  return (
    <div className={`${className}`}>
      <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor()}`}>
        {getStatusIcon()}
        <span className="ml-2">{getStatusText()}</span>
        {autoRefresh && (
          <button
            onClick={fetchStatus}
            className="ml-2 opacity-60 hover:opacity-100 transition-opacity"
            title="Refresh status"
          >
            <svg 
              className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth="2" 
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" 
              />
            </svg>
          </button>
        )}
      </div>

      {showDetails && status && !loading && (
        <div className="mt-2 p-3 bg-gray-50 rounded-md">
          <div className="text-xs text-gray-600 space-y-1">
            {status.version && (
              <div>
                <span className="font-medium">Version:</span> {status.version}
              </div>
            )}
            {status.url && (
              <div>
                <span className="font-medium">URL:</span> {status.url}
              </div>
            )}
            {status.error && (
              <div className="text-red-600">
                <span className="font-medium">Error:</span> {status.error}
              </div>
            )}
            {lastChecked && (
              <div>
                <span className="font-medium">Last checked:</span> {lastChecked.toLocaleTimeString()}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}