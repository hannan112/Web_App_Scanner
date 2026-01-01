/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
// src/components/scanning/ScanResults.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { PassiveReconResult, ScanResult, AjaxSpiderResult, CrawlData, ActiveScanResult, ScanStatistics } from '@/types/project';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
} from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
import VulnerabilityModal from './VulnerabilityModal';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

interface ScanResultsProps {
  scanId: string;
  projectId?: number | string;
  vulnerabilities: ScanResult[];
  passiveReconData?: PassiveReconResult;
  activeReconData?: ActiveScanResult;
  crawlData?: CrawlData;
  ajaxSpiderData?: AjaxSpiderResult;
  scanStatistics?: ScanStatistics;
  scanType?: string;
  targetUrl?: string;
  vulnerabilitySummary?: {
    total_count: number;
    showing_count: number;
    truncated: boolean;
  };
  onError?: (message: string) => void;
}

const ScanResults: React.FC<ScanResultsProps> = ({
  scanId,
  projectId,
  vulnerabilities = [],
  passiveReconData,
  activeReconData,
  crawlData,
  ajaxSpiderData,
  scanStatistics,
  scanType,
  targetUrl,
  vulnerabilitySummary,
  onError
}) => {
  // Immediate data sanitization to prevent any object rendering issues
  const sanitizedVulnerabilities = Array.isArray(vulnerabilities) ? vulnerabilities : [];
  const sanitizedPassiveReconData = passiveReconData && typeof passiveReconData === 'object' ? passiveReconData : null;
  const sanitizedActiveReconData = activeReconData && typeof activeReconData === 'object' ? activeReconData : null;

  // Deep sanitization function to ensure no objects are rendered
  const deepSanitize = (obj: any, path: string = ''): any => {
    if (obj === null || obj === undefined) return obj;

    if (typeof obj === 'object') {
      if (Array.isArray(obj)) {
        return obj.map((item, index) => {
          if (typeof item === 'object' && item !== null) {
            console.warn(`⚠️ Object in array at ${path}[${index}]:`, item);
            return JSON.stringify(item);
          }
          return deepSanitize(item, `${path}[${index}]`);
        });
      } else {
        console.warn(`⚠️ Object detected at ${path}:`, obj);
        return JSON.stringify(obj);
      }
    }

    return obj;
  };
  // State for filtering and search
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [confidenceFilter, setConfidenceFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showUrlsModal, setShowUrlsModal] = useState<boolean>(false);
  const [showFormsModal, setShowFormsModal] = useState<boolean>(false);
  const [modalSearchTerm, setModalSearchTerm] = useState<string>('');

  // Discovery modal states
  const [showSubdomainsModal, setShowSubdomainsModal] = useState<boolean>(false);
  const [showApiEndpointsModal, setShowApiEndpointsModal] = useState<boolean>(false);
  const [showHistoricalUrlsModal, setShowHistoricalUrlsModal] = useState<boolean>(false);
  const [showDirectoriesModal, setShowDirectoriesModal] = useState<boolean>(false);
  const [showAssetsModal, setShowAssetsModal] = useState<boolean>(false);

  const [selectedVulnerabilityId, setSelectedVulnerabilityId] = useState<number | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  // Grouping state
  const [viewMode, setViewMode] = useState<'list' | 'grouped' | 'tree'>('grouped');
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());



  // Determine scan type
  const effectiveScanType = scanType || 'security';
  const isPassiveScan = effectiveScanType === 'passive';
  const isActiveScan = effectiveScanType === 'active' || effectiveScanType === 'comprehensive';

  // For passive scans, we only show passive recon data
  // For active/comprehensive scans, we show combined data from all sources

  // Debug logging and Initialize with empty arrays/objects if data is missing
  // Helper to clean malformed URLs (fix concatenated domains)
  const cleanUrl = (url: string): string => {
    if (!url || typeof url !== 'string') return url;

    // Handle concatenated URLs like "http://domain1.comhttps://domain2.com/path"
    const httpIndex = url.indexOf('http', 1); // Find second occurrence of 'http'
    if (httpIndex > 0) {
      // Extract the second URL which is usually the correct one
      return url.substring(httpIndex);
    }

    return url;
  };

  // Get all discovered URLs from various sources
  const getAllDiscoveredUrls = useCallback(() => {
    const urls = new Set<string>();

    // From passive recon - safely add URLs
    if (sanitizedPassiveReconData?.urls_discovered && Array.isArray(sanitizedPassiveReconData.urls_discovered)) {
      sanitizedPassiveReconData.urls_discovered.forEach(url => {
        if (url && typeof url === 'string' && url.trim()) {
          const cleanedUrl = cleanUrl(url.trim());
          urls.add(cleanedUrl);
        }
      });
    }

    // From active recon - safely add URLs
    if (sanitizedActiveReconData?.urls_discovered && Array.isArray(sanitizedActiveReconData.urls_discovered)) {
      sanitizedActiveReconData.urls_discovered.forEach(url => {
        if (url && typeof url === 'string' && url.trim()) {
          const cleanedUrl = cleanUrl(url.trim());
          urls.add(cleanedUrl);
        }
      });
    }

    return Array.from(urls);
  }, [sanitizedPassiveReconData, sanitizedActiveReconData]);

  useEffect(() => {
    console.log('🔍 ScanResults Debug - activeReconData:', sanitizedActiveReconData);
    console.log('🔍 ScanResults Debug - passiveReconData:', sanitizedPassiveReconData);
    console.log('🔍 ScanResults Debug - scanType:', scanType);
    console.log('🔧 Effective scanType after workaround:', effectiveScanType);

    // Comprehensive data validation and sanitization
    try {
      if (sanitizedActiveReconData) {
        console.log('📊 Active URLs discovered:', sanitizedActiveReconData.urls_discovered?.length || 0);
        console.log('📊 API endpoints:', sanitizedActiveReconData.api_endpoints?.length || 0);
        console.log('📊 JS endpoints:', sanitizedActiveReconData.js_endpoints?.length || 0);
        console.log('📊 Forms discovered:', sanitizedActiveReconData.forms_discovered?.length || 0);
        console.log('📊 Discovery tools:', sanitizedActiveReconData.discovery_tools_used?.length || 0);
      } else {
        console.log('❌ NO activeReconData received');
      }

      if (sanitizedPassiveReconData) {
        console.log('📊 Passive URLs discovered:', sanitizedPassiveReconData.urls_discovered?.length || 0);
        console.log('📊 Technologies:', sanitizedPassiveReconData.technologies ? Object.keys(sanitizedPassiveReconData.technologies).length : 0);
        console.log('📊 DNS records:', !!sanitizedPassiveReconData.dns_records);
        console.log('📊 Robots.txt:', !!sanitizedPassiveReconData.robots_txt);
      } else {
        console.log('❌ NO passiveReconData received');
      }

      // Test URL combination
      const testUrls = getAllDiscoveredUrls();
      console.log('🔧 Combined URLs count:', testUrls.length);
      console.log('🔧 Sample URLs:', testUrls.slice(0, 3));
    } catch (error) {
      console.error('Error during data validation:', error);
      if (onError) {
        onError('Error validating scan data');
      }
    }
  }, [sanitizedPassiveReconData, sanitizedActiveReconData, onError, effectiveScanType, scanType, getAllDiscoveredUrls]);

  // Get filtered vulnerabilities based on severity
  const safeVulnerabilities = sanitizedVulnerabilities.map(vuln => {
    // Ensure all vulnerability properties are safe to render
    return {
      ...vuln,
      severity: typeof vuln.severity === 'string' ? vuln.severity : 'unknown',
      confidence: typeof vuln.confidence === 'number' ? vuln.confidence : 0,
      name: typeof vuln.name === 'string' ? vuln.name : 'Unknown Vulnerability',
      description: typeof vuln.description === 'string' ? vuln.description : 'No description available',
      url: typeof vuln.url === 'string' ? vuln.url : null,
      parameter: typeof vuln.parameter === 'string' ? vuln.parameter : null,
      evidence: typeof vuln.evidence === 'string' ? vuln.evidence : JSON.stringify(vuln.evidence),
      remediation: typeof vuln.remediation === 'string' ? vuln.remediation : null,
      is_fp: !!vuln.is_fp,
      fp_confidence: typeof vuln.fp_confidence === 'number' ? vuln.fp_confidence : 0
    };
  });

  // Separate vulnerabilities from info-level findings
  const actualVulnerabilities = safeVulnerabilities.filter(v => v && v.severity !== 'info');

  const infoFindings = safeVulnerabilities.filter(v => v && v.severity === 'info');

  // Get vulnerability stats (excluding info)
  const vulnStats = {
    critical: actualVulnerabilities.filter(v => v && v.severity === 'critical').length,
    high: actualVulnerabilities.filter(v => v && v.severity === 'high').length,
    medium: actualVulnerabilities.filter(v => v && v.severity === 'medium').length,
    low: actualVulnerabilities.filter(v => v && v.severity === 'low').length,
    fp: actualVulnerabilities.filter(v => v && v.is_fp).length,
    total: actualVulnerabilities.length
  };

  // Filter vulnerabilities based on both severity and confidence
  const filteredVulnerabilities = actualVulnerabilities.filter(v => {
    if (!v) return false;

    // Apply severity filter
    let severityMatch = true;
    if (severityFilter === 'fp') {
      severityMatch = !!v.is_fp;
    } else {
      severityMatch = severityFilter === 'all' || v.severity === severityFilter;
    }

    // Apply confidence filter
    let confidenceMatch = true;
    if (confidenceFilter !== 'all') {
      const confidenceThreshold = parseFloat(confidenceFilter) / 100; // Convert percentage to decimal
      confidenceMatch = (v.confidence || 0) >= confidenceThreshold;
    }

    return severityMatch && confidenceMatch;
  }).sort((a, b) => {
    const severityWeight: Record<string, number> = {
      'critical': 5,
      'high': 4,
      'medium': 3,
      'low': 2,
      'info': 1,
      'unknown': 0
    };

    const weightA = severityWeight[(a.severity || 'unknown').toLowerCase()] || 0;
    const weightB = severityWeight[(b.severity || 'unknown').toLowerCase()] || 0;

    return weightB - weightA; // Descending order
  });

  // Group vulnerabilities by name and severity
  const groupedVulnerabilities = React.useMemo(() => {
    const groups = new Map<string, {
      name: string;
      severity: string;
      count: number;
      vulnerabilities: any[];
    }>();

    filteredVulnerabilities.forEach(vuln => {
      const key = `${vuln.name}-${vuln.severity}`;
      if (!groups.has(key)) {
        groups.set(key, {
          name: vuln.name,
          severity: vuln.severity,
          count: 0,
          vulnerabilities: []
        });
      }
      const group = groups.get(key)!;
      group.count++;
      group.vulnerabilities.push(vuln);
    });

    return Array.from(groups.entries()).map(([key, value]) => ({
      key,
      ...value
    }));
  }, [filteredVulnerabilities]);

  const toggleGroup = (groupKey: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupKey)) {
      newExpanded.delete(groupKey);
    } else {
      newExpanded.add(groupKey);
    }
    setExpandedGroups(newExpanded);
  };

  // Tree View Helper Functions
  interface FileTreeNode {
    name: string;
    path: string;
    type: 'file' | 'directory';
    children: Map<string, FileTreeNode>;
    vulnerabilities: any[];
    totalVulnCount: number;
    maxSeverity: string;
  }

  const buildFileTree = useCallback((urls: string[], vulns: any[]) => {
    const root = new Map<string, FileTreeNode>();

    // Helper to get severity weight
    const getSeverityWeight = (severity: string) => {
      const map: Record<string, number> = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'info': 0, 'unknown': -1 };
      return map[severity?.toLowerCase()] || -1;
    };

    // Helper to get max severity
    const getMaxSeverity = (s1: string, s2: string) => {
      return getSeverityWeight(s1) > getSeverityWeight(s2) ? s1 : s2;
    };

    // 1. Build the structure from URLs
    urls.forEach(url => {
      try {
        const urlObj = new URL(url);
        const domain = urlObj.hostname;
        const pathParts = urlObj.pathname.split('/').filter(p => p);

        // Ensure domain node exists
        if (!root.has(domain)) {
          root.set(domain, {
            name: domain,
            path: domain,
            type: 'directory',
            children: new Map(),
            vulnerabilities: [],
            totalVulnCount: 0,
            maxSeverity: 'none'
          });
        }

        let currentNode = root.get(domain)!;
        let currentPath = domain;

        pathParts.forEach((part, index) => {
          currentPath += `/${part}`;
          if (!currentNode.children.has(part)) {
            // Determine type: it's a file if it has an extension OR if it's the last part and looks like a file
            // But we might change this later if it gets children
            const hasExtension = part.includes('.');
            const isLast = index === pathParts.length - 1;

            currentNode.children.set(part, {
              name: part,
              path: currentPath,
              type: (isLast && hasExtension) ? 'file' : 'directory',
              children: new Map(),
              vulnerabilities: [],
              totalVulnCount: 0,
              maxSeverity: 'none'
            });
          }
          currentNode = currentNode.children.get(part)!;

          // If a node we thought was a file actually has children (from another URL), it must be a directory
          if (index < pathParts.length - 1 && currentNode.type === 'file') {
            currentNode.type = 'directory';
          }
        });
      } catch (e) {
        // Ignore invalid URLs
      }
    });

    // 2. Attach vulnerabilities to the correct nodes
    vulns.forEach(vuln => {
      if (vuln.url) {
        try {
          const urlObj = new URL(vuln.url);
          const domain = urlObj.hostname;
          const pathParts = urlObj.pathname.split('/').filter(p => p);

          if (root.has(domain)) {
            let currentNode = root.get(domain)!;

            // If path is empty (just domain), add here
            if (pathParts.length === 0) {
              currentNode.vulnerabilities.push(vuln);
            } else {
              // Navigate to the specific node
              // Navigate to the specific node
              for (const part of pathParts) {
                if (currentNode.children.has(part)) {
                  currentNode = currentNode.children.get(part)!;
                } else {
                  // If the specific path node doesn't exist (maybe wasn't in discovered URLs), 
                  // add it now as a file node since it has a vuln
                  const newPath = `${currentNode.path}/${part}`;
                  const newNode: FileTreeNode = {
                    name: part,
                    path: newPath,
                    type: 'file',
                    children: new Map(),
                    vulnerabilities: [],
                    totalVulnCount: 0,
                    maxSeverity: 'none'
                  };
                  currentNode.children.set(part, newNode);
                  currentNode = newNode;
                }
              }
              currentNode.vulnerabilities.push(vuln);
            }
          }
        } catch (e) {
          // Ignore
        }
      }
    });

    // 3. Recursive aggregation of counts and severity
    const aggregateNode = (node: FileTreeNode) => {
      let localCount = node.vulnerabilities.length;
      let localMaxSev = node.vulnerabilities.reduce((max, v) => getMaxSeverity(max, v.severity || 'none'), 'none');

      // Process children
      for (const child of node.children.values()) {
        aggregateNode(child);
        localCount += child.totalVulnCount;
        localMaxSev = getMaxSeverity(localMaxSev, child.maxSeverity);
      }

      node.totalVulnCount = localCount;
      node.maxSeverity = localMaxSev;
    };

    // Run aggregation on all root nodes
    for (const rootNode of root.values()) {
      aggregateNode(rootNode);
    }

    return root;
  }, []);

  const FileTreeItem: React.FC<{ node: FileTreeNode; level: number }> = ({ node, level }) => {
    const [isOpen, setIsOpen] = useState(level < 1); // Only expand root by default
    const hasChildren = node.children.size > 0;
    const directVulnCount = node.vulnerabilities.length;
    const totalVulnCount = node.totalVulnCount;

    return (
      <div className="select-none">
        <div
          className={`flex items-center py-1.5 px-2 hover:bg-gray-100 rounded cursor-pointer transition-colors ${level === 0 ? 'bg-gray-50 mb-1' : ''}`}
          style={{ paddingLeft: `${level * 1.5 + 0.5}rem` }}
          onClick={() => setIsOpen(!isOpen)}
        >
          <span className="mr-2 text-gray-500 w-4 flex justify-center flex-shrink-0">
            {hasChildren ? (
              isOpen ? (
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
              ) : (
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
              )
            ) : (
              node.type === 'file' ? (
                <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
              ) : (
                <svg className="w-3.5 h-3.5 text-blue-300" fill="currentColor" viewBox="0 0 24 24"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" /></svg>
              )
            )}
          </span>

          <span className={`truncate mr-2 text-sm ${node.type === 'directory' ? 'font-medium text-gray-700' : 'text-gray-600'}`}>
            {node.name}
          </span>

          {totalVulnCount > 0 && (
            <div className="ml-auto flex items-center space-x-2">
              {directVulnCount > 0 && (
                <span className="text-xs text-gray-400" title={`${directVulnCount} vulnerabilities directly on this item`}>
                  ({directVulnCount})
                </span>
              )}
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${node.maxSeverity === 'critical' ? 'bg-red-100 text-red-800' :
                node.maxSeverity === 'high' ? 'bg-orange-100 text-orange-800' :
                  node.maxSeverity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    node.maxSeverity === 'low' ? 'bg-green-100 text-green-800' :
                      'bg-blue-100 text-blue-800'
                }`}>
                {totalVulnCount}
              </span>
            </div>
          )}
        </div>

        {isOpen && (
          <div>
            {/* Show direct vulnerabilities for this node */}
            {node.vulnerabilities.length > 0 && (
              <div className="pl-4 border-l-2 border-gray-100 ml-4 mb-1">
                {node.vulnerabilities.map((vuln, idx) => (
                  <div key={idx} className="py-1 pl-4 pr-2 text-xs flex items-center justify-between hover:bg-red-50 rounded cursor-pointer group"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedVulnerabilityId(vuln.id);
                      setIsModalOpen(true);
                    }}
                  >
                    <div className="flex items-center gap-2 truncate mr-2">
                      <span className="truncate text-gray-600 group-hover:text-gray-900">{vuln.name}</span>
                      {vuln.is_fp && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] uppercase bg-gray-100 text-gray-500 border border-gray-200" title={`ML Confidence: ${(vuln.fp_confidence * 100).toFixed(1)}%`}>
                          Possible FP
                        </span>
                      )}
                    </div>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] uppercase ${getSeverityBadgeClass(vuln.severity)}`}>
                      {vuln.severity}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Show children nodes */}
            {hasChildren && (
              <div className="border-l border-gray-100 ml-2.5">
                {Array.from(node.children.values())
                  .sort((a, b) => {
                    // Directories first, then files
                    if (a.type !== b.type) return a.type === 'directory' ? -1 : 1;
                    return a.name.localeCompare(b.name);
                  })
                  .map((child, idx) => (
                    <FileTreeItem key={`${child.path}-${idx}`} node={child} level={level + 1} />
                  ))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };




  // Helper to safely render any value as string
  const safeRender = (value: any, fallback: string = 'N/A'): string => {
    if (value === null || value === undefined) return fallback;
    if (typeof value === 'string') return value;
    if (typeof value === 'number' || typeof value === 'boolean') return String(value);
    if (typeof value === 'object') {
      try {
        return JSON.stringify(value);
      } catch {
        return fallback;
      }
    }
    return String(value);
  };


  // Helper to get CSS classes for severity badges
  const getSeverityBadgeClass = (severity: string): string => {
    const baseClasses = 'px-2 py-1 rounded-full text-xs font-medium';
    const safeSeverity = (severity || 'unknown').toLowerCase();
    switch (safeSeverity) {
      case 'critical':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'high':
        return `${baseClasses} bg-orange-100 text-orange-800`;
      case 'medium':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'low':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'info':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  // Safe access to nested properties
  const safeGetNestedValue = (obj: any, path: string, defaultValue: any = null) => {
    if (!obj) return defaultValue;
    try {
      return path.split('.').reduce((prev, curr) => {
        return prev ? prev[curr] : null;
      }, obj) || defaultValue;
    } catch (e) {
      return defaultValue;
    }
  };

  // Get filtered forms with JSON parsing support
  const getAllDiscoveredForms = () => {
    const forms = [];

    // Helper function to safely parse form data (handles both objects and JSON strings)
    const parseFormData = (formData: any) => {
      try {
        // If it's a string, try to parse as JSON
        if (typeof formData === 'string') {
          const parsed = JSON.parse(formData);
          return parsed;
        }
        // If it's already an object, return as-is
        if (typeof formData === 'object' && formData !== null) {
          return formData;
        }
        return null;
      } catch (error) {
        console.warn('Failed to parse form data:', formData, error);
        return null;
      }
    };

    // Safely add forms from passive recon data
    if (sanitizedPassiveReconData?.forms_discovered && Array.isArray(sanitizedPassiveReconData.forms_discovered)) {
      const validForms = sanitizedPassiveReconData.forms_discovered
        .map(parseFormData)
        .filter(form =>
          form && typeof form === 'object' && (form.action || form.method || form.url)
        )
        .map(form => ({
          ...form,
          action: typeof form.action === 'string' ? form.action : null,
          method: typeof form.method === 'string' ? form.method : 'GET',
          url: typeof form.url === 'string' ? form.url : null,
          inputs: Array.isArray(form.inputs) ? form.inputs : [],
          fields: Array.isArray(form.fields) ? form.fields : []
        }));
      forms.push(...validForms);
    }

    // Safely add forms from active recon data
    if (sanitizedActiveReconData?.forms_discovered && Array.isArray(sanitizedActiveReconData.forms_discovered)) {
      const validForms = sanitizedActiveReconData.forms_discovered
        .map(parseFormData)
        .filter(form =>
          form && typeof form === 'object' && (form.action || form.method || form.url)
        )
        .map(form => ({
          ...form,
          action: typeof form.action === 'string' ? form.action : null,
          method: typeof form.method === 'string' ? form.method : 'GET',
          url: typeof form.url === 'string' ? form.url : null,
          inputs: Array.isArray(form.inputs) ? form.inputs : [],
          fields: Array.isArray(form.fields) ? form.fields : []
        }));
      forms.push(...validForms);
    }

    return forms;

  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-4 border-t-blue-600 rounded-full animate-spin"></div>
        <p className="ml-3 text-gray-600">Loading scan results...</p>
      </div>
    );
  }

  // Safe component rendering with comprehensive error handling
  try {
    const allUrls = getAllDiscoveredUrls();
    const allForms = getAllDiscoveredForms();

    // Additional debugging to catch any remaining object rendering issues
    console.log('🔍 Render Debug - vulnStats:', vulnStats);
    console.log('🔍 Render Debug - allUrls length:', allUrls.length);
    console.log('🔍 Render Debug - allForms length:', allForms.length);
    console.log('🔍 Render Debug - allForms sample:', allForms.slice(0, 2));

    // Validate all data before rendering
    if (allForms.some(form => typeof form !== 'object' || form === null)) {
      console.error('❌ Invalid form objects detected:', allForms.filter(form => typeof form !== 'object' || form === null));
    }

    if (allUrls.some(url => typeof url !== 'string')) {
      console.error('❌ Invalid URL objects detected:', allUrls.filter(url => typeof url !== 'string'));
    }

    return (
      <div className="space-y-8">
        {/* Scan Type Banner */}
        <div className={`rounded-lg p-4 border shadow-lg backdrop-blur-md ${isPassiveScan ? 'bg-blue-50/80 border-blue-200/50' :
          isActiveScan ? 'bg-green-50/80 border-green-200/50' :
            'bg-white/10 border-white/20'
          }`}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className={`text-lg font-semibold ${isPassiveScan ? 'text-blue-900' : isActiveScan ? 'text-green-900' : 'text-slate-900'}`}>
                {isPassiveScan ? 'Passive Reconnaissance Results' : isActiveScan ? 'Comprehensive Security Scan Results' : 'Scan Results'}
              </h2>
              <p className={`text-sm mt-1 ${isPassiveScan ? 'text-blue-700' : isActiveScan ? 'text-green-700' : 'text-slate-700'}`}>
                {isPassiveScan
                  ? 'Showing passive reconnaissance data - information gathered without direct interaction'
                  : isActiveScan
                    ? 'Showing comprehensive results from passive reconnaissance, active discovery, and vulnerability testing'
                    : 'Displaying available scan data'
                }
              </p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${isPassiveScan ? 'bg-blue-100/80 backdrop-blur-sm text-blue-800 border-blue-200/50' :
              isActiveScan ? 'bg-green-100/80 backdrop-blur-sm text-green-800 border-green-200/50' :
                'bg-gray-100/80 backdrop-blur-sm text-gray-800 border-gray-200/50'
              }`}>
              {effectiveScanType === 'active' ? 'ACTIVE SCAN' :
                effectiveScanType === 'passive' ? 'PASSIVE SCAN' :
                  effectiveScanType === 'ajax' ? 'AJAX SCAN' :
                    effectiveScanType === 'comprehensive' ? 'COMPREHENSIVE SCAN' :
                      'SECURITY SCAN'}
            </span>
          </div>
        </div>

        {/* Warning for missing passive data in active scans */}
        {isActiveScan && !sanitizedPassiveReconData && (
          <div className="bg-yellow-50/80 backdrop-blur-md border border-yellow-200/50 rounded-lg p-4 mb-6 shadow-lg">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div>
                <h3 className="text-sm font-medium text-yellow-800 mb-1">Partial Active Scan Results</h3>
                <p className="text-sm text-yellow-700">
                  This active scan is missing passive reconnaissance data. Active scanning discovered {allUrls.length} URLs and {allForms.length} forms,
                  but passive discovery (subdomains, enhanced discovery, etc.) may not have completed successfully.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Attack Surface Summary - Different layout for passive vs active */}
        {isActiveScan ? (
          // Active/Comprehensive Scan Layout - Combined view with all discoveries
          <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold text-slate-900 mb-6">Complete Attack Surface Analysis</h2>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 bg-green-50/80 backdrop-blur-sm rounded-lg hover:bg-green-100/80 cursor-pointer transition-colors border border-green-200/50" onClick={() => setShowUrlsModal(true)}>
                <div className="text-2xl font-bold text-green-600">{allUrls.length}</div>
                <div className="text-sm text-slate-700">Total URLs</div>
                <div className="text-xs text-slate-600 mt-1">From all sources</div>
              </div>

              <div className="text-center p-4 bg-blue-50/80 backdrop-blur-sm rounded-lg hover:bg-blue-100/80 cursor-pointer transition-colors border border-blue-200/50" onClick={() => setShowFormsModal(true)}>
                <div className="text-2xl font-bold text-blue-600">{allForms.length}</div>
                <div className="text-sm text-slate-700">Forms Found</div>
                <div className="text-xs text-slate-600 mt-1">Entry points</div>
              </div>

              <div className="text-center p-4 bg-purple-50/80 backdrop-blur-sm rounded-lg border border-purple-200/50">
                <div className="text-2xl font-bold text-purple-600">
                  {(safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.api_endpoints.count', 0) +
                    (sanitizedActiveReconData?.api_endpoints?.length || 0))}
                </div>
                <div className="text-sm text-slate-700">API Endpoints</div>
                <div className="text-xs text-slate-600 mt-1">Combined discovery</div>
              </div>

              <div className="text-center p-4 bg-yellow-50/80 backdrop-blur-sm rounded-lg border border-yellow-200/50">
                <div className="text-2xl font-bold text-yellow-600">
                  {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.summary.total_discoveries', 0)}
                </div>
                <div className="text-sm text-slate-700">Total Assets</div>
                <div className="text-xs text-slate-600 mt-1">All discoveries</div>
              </div>
            </div>

            {/* Unified Discovery Results for Active Scans */}
            <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-medium text-slate-800">Unified Discovery Results</h3>
                <span className="text-sm text-slate-600">
                  Combined from passive reconnaissance, active crawling, and enhanced discovery
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="bg-white/50 backdrop-blur-sm p-3 rounded border border-white/20">
                  <div className="text-sm font-medium text-slate-700 mb-2">All URLs ({allUrls.length})</div>
                  <div className="text-xs text-slate-600 space-y-1 max-h-20 overflow-y-auto">
                    {allUrls.slice(0, 3).map((url, idx) => (
                      <div key={idx} className="truncate">{url}</div>
                    ))}
                    {allUrls.length > 3 && <div className="text-blue-600">+{allUrls.length - 3} more...</div>}
                  </div>
                  <div className="text-xs text-slate-600 mt-1">Passive + Active + Enhanced</div>
                </div>

                <div className="bg-white/50 backdrop-blur-sm p-3 rounded border border-white/20">
                  <div className="text-sm font-medium text-slate-700 mb-2">Forms & Entry Points ({allForms.length})</div>
                  <div className="text-xs text-slate-600 space-y-1 max-h-20 overflow-y-auto">
                    {allForms.slice(0, 3).map((form: any, idx: number) => (
                      <div key={idx} className="truncate">{form.action || form.url || 'Form'}</div>
                    ))}
                    {allForms.length > 3 && <div className="text-blue-600">+{allForms.length - 3} more...</div>}
                  </div>
                  <div className="text-xs text-slate-600 mt-1">Discovered during crawling</div>
                </div>

                <div className="bg-white/50 backdrop-blur-sm p-3 rounded border border-white/20">
                  <div className="text-sm font-medium text-slate-700 mb-2">Technologies & Assets</div>
                  <div className="text-xs text-slate-600 space-y-1 max-h-20 overflow-y-auto">
                    {(Array.isArray(safeGetNestedValue(sanitizedPassiveReconData, 'technologies.files', [])) ? safeGetNestedValue(sanitizedPassiveReconData, 'technologies.files', []) : []).slice(0, 3).map((asset: string, idx: number) => (
                      <div key={idx} className="truncate">{asset}</div>
                    ))}
                    {(Array.isArray(safeGetNestedValue(sanitizedPassiveReconData, 'technologies.files', [])) ? safeGetNestedValue(sanitizedPassiveReconData, 'technologies.files', []).length : 0) > 3 &&
                      <div className="text-blue-600">+{(safeGetNestedValue(sanitizedPassiveReconData, 'technologies.files', []) || []).length - 3} more...</div>
                    }
                  </div>
                  <div className="text-xs text-slate-600 mt-1">CSS, JS, and other assets</div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          // Passive Scan Layout - New structure as requested
          <div className="space-y-6">
            {/* Analytics and Statistics Section */}
            <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold text-slate-900 mb-6">Scan Analytics & Statistics</h2>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Vulnerability Distribution Chart */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-800">Vulnerability Distribution</h3>
                  <div className="h-64">
                    <Doughnut
                      data={{
                        labels: ['Critical', 'High', 'Medium', 'Low', 'Info'],
                        datasets: [{
                          data: [
                            vulnStats.critical,
                            vulnStats.high,
                            vulnStats.medium,
                            vulnStats.low,
                            infoFindings.length
                          ],
                          backgroundColor: [
                            '#DC2626', // Red for Critical
                            '#EA580C', // Orange for High
                            '#D97706', // Amber for Medium
                            '#2563EB', // Blue for Low
                            '#6B7280'  // Gray for Info
                          ],
                          borderWidth: 2,
                          borderColor: '#ffffff'
                        }]
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: {
                            position: 'bottom',
                            labels: {
                              usePointStyle: true,
                              padding: 20,
                              font: {
                                size: 12
                              }
                            }
                          },
                          tooltip: {
                            callbacks: {
                              label: function (context) {
                                const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
                                const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : '0';
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                              }
                            }
                          }
                        }
                      }}
                    />
                  </div>

                  {/* Vulnerability Counts */}
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="flex items-center justify-between p-2 bg-red-50 rounded-lg">
                      <div className="flex items-center">
                        <div className="w-3 h-3 bg-red-600 rounded-full mr-2"></div>
                        <span className="text-gray-700">Critical</span>
                      </div>
                      <span className="font-semibold text-red-600">{vulnStats.critical}</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-orange-50 rounded-lg">
                      <div className="flex items-center">
                        <div className="w-3 h-3 bg-orange-600 rounded-full mr-2"></div>
                        <span className="text-gray-700">High</span>
                      </div>
                      <span className="font-semibold text-orange-600">{vulnStats.high}</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-yellow-50 rounded-lg">
                      <div className="flex items-center">
                        <div className="w-3 h-3 bg-yellow-600 rounded-full mr-2"></div>
                        <span className="text-gray-700">Medium</span>
                      </div>
                      <span className="font-semibold text-yellow-600">{vulnStats.medium}</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-blue-50 rounded-lg">
                      <div className="flex items-center">
                        <div className="w-3 h-3 bg-blue-600 rounded-full mr-2"></div>
                        <span className="text-gray-700">Low</span>
                      </div>
                      <span className="font-semibold text-blue-600">{vulnStats.low}</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-gray-50 rounded-lg col-span-2">
                      <div className="flex items-center">
                        <div className="w-3 h-3 bg-gray-600 rounded-full mr-2"></div>
                        <span className="text-gray-700">Info</span>
                      </div>
                      <span className="font-semibold text-gray-600">{infoFindings.length}</span>
                    </div>
                  </div>
                </div>

                {/* Scan Statistics */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-800">Scan Statistics</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">{vulnStats.total}</div>
                      <div className="text-sm text-blue-700">Total Vulnerabilities</div>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">{infoFindings.length}</div>
                      <div className="text-sm text-green-700">Info Findings</div>
                    </div>
                    <div className="bg-orange-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">{vulnStats.critical + vulnStats.high}</div>
                      <div className="text-sm text-orange-700">High Priority</div>
                    </div>
                    <div className="bg-yellow-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-yellow-600">{vulnStats.medium + vulnStats.low}</div>
                      <div className="text-sm text-yellow-700">Medium/Low Priority</div>
                    </div>
                    {vulnStats.fp > 0 && (
                      <div className="bg-gray-100 p-4 rounded-lg col-span-2 sm:col-span-1">
                        <div className="text-2xl font-bold text-gray-700">{vulnStats.fp}</div>
                        <div className="text-sm text-gray-600">ML False Positives</div>
                      </div>
                    )}
                  </div>

                  {/* Confidence Distribution */}
                  <div className="mt-6">
                    <h4 className="text-md font-semibold text-gray-700 mb-3">Confidence Distribution</h4>
                    <div className="h-48">
                      <Line
                        data={{
                          labels: ['≥50%', '≥60%', '≥70%', '≥80%', '≥90%', '100%'],
                          datasets: [{
                            label: 'Vulnerabilities',
                            data: [100, 90, 80, 70, 60, 50].map(threshold =>
                              actualVulnerabilities.filter(v => (v.confidence || 0) >= threshold / 100).length
                            ),
                            borderColor: '#2563EB',
                            backgroundColor: 'rgba(37, 99, 235, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4, // Smooth curves
                            pointBackgroundColor: '#2563EB',
                            pointBorderColor: '#ffffff',
                            pointBorderWidth: 2,
                            pointRadius: 6,
                            pointHoverRadius: 8,
                          }]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              display: false
                            },
                            tooltip: {
                              callbacks: {
                                label: function (context) {
                                  return `${context.parsed.y} vulnerabilities with ≥${100 - (context.dataIndex * 10)}% confidence`;
                                }
                              }
                            }
                          },
                          scales: {
                            x: {
                              title: {
                                display: true,
                                text: 'Confidence Level',
                                font: {
                                  size: 12,
                                  weight: 'bold'
                                }
                              },
                              grid: {
                                display: true,
                                color: 'rgba(0, 0, 0, 0.1)'
                              }
                            },
                            y: {
                              title: {
                                display: true,
                                text: 'Number of Vulnerabilities',
                                font: {
                                  size: 12,
                                  weight: 'bold'
                                }
                              },
                              beginAtZero: true,
                              grid: {
                                display: true,
                                color: 'rgba(0, 0, 0, 0.1)'
                              },
                              ticks: {
                                stepSize: 1
                              }
                            }
                          },
                          elements: {
                            line: {
                              tension: 0.4 // Smooth line
                            }
                          }
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Additional Analytics */}
              <div className="mt-8 pt-6 border-t border-gray-200">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Detailed Analysis</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Vulnerability Types */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-gray-700 mb-3">Top Vulnerability Types</h4>
                    <div className="space-y-2">
                      {Object.entries(
                        actualVulnerabilities.reduce((acc: any, vuln) => {
                          const type = vuln.name || vuln.vulnerability_type || 'Unknown Vulnerability';
                          acc[type] = (acc[type] || 0) + 1;
                          return acc;
                        }, {})
                      )
                        .sort(([, a], [, b]) => (b as number) - (a as number))
                        .slice(0, 5)
                        .map(([type, count]) => (
                          <div key={type} className="flex justify-between text-sm">
                            <span className="text-gray-600 truncate" title={type}>{type}</span>
                            <span className="font-semibold text-gray-800">{count as number}</span>
                          </div>
                        ))}
                    </div>
                  </div>

                  {/* Discovered URLs */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-gray-700 mb-3">Discovered URLs</h4>
                    <div className="text-center mb-3">
                      <div className="text-2xl font-bold text-purple-600">
                        {allUrls.length}
                      </div>
                      <div className="text-sm text-gray-600">Total URLs</div>
                    </div>
                    <div className="text-center">
                      <button
                        onClick={() => setShowUrlsModal(true)}
                        className="text-blue-600 hover:text-blue-800 hover:underline text-sm font-medium"
                      >
                        Click to view
                      </button>
                    </div>
                  </div>

                  {/* Scan Coverage */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-gray-700 mb-3">Scan Coverage</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Scan Type</span>
                        <span className="font-semibold text-gray-800 capitalize">
                          {scanType === 'active' ? 'Active Scan' :
                            scanType === 'passive' ? 'Passive Scan' :
                              scanType === 'ajax' ? 'AJAX Spider Scan' :
                                scanType || 'Security Scan'}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Target</span>
                        <span className="font-semibold text-gray-800 truncate max-w-32" title={targetUrl}>
                          {targetUrl ? new URL(targetUrl).hostname : 'Unknown'}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Status</span>
                        <span className="font-semibold text-gray-800 capitalize">
                          Completed
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* First Display: Target Analysis - Complete Information */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Target Analysis</h2>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Target Information */}
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-blue-900 mb-4">Target Information</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between py-2 border-b border-blue-100">
                        <span className="font-medium text-blue-700">Target URL</span>
                        <a href={targetUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline break-all">
                          {targetUrl || 'Unknown'}
                        </a>
                      </div>
                      <div className="flex justify-between py-2 border-b border-blue-100">
                        <span className="font-medium text-blue-700">IP Address</span>
                        <span className="text-blue-900">
                          {safeGetNestedValue(sanitizedPassiveReconData, 'server_info.ip_address') ||
                            safeGetNestedValue(sanitizedPassiveReconData, 'dns_records.a_records.0') || 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between py-2 border-b border-blue-100">
                        <span className="font-medium text-blue-700">Protocol</span>
                        <span className="text-blue-900">
                          {safeGetNestedValue(sanitizedPassiveReconData, 'server_info.protocol', 'Unknown')}
                        </span>
                      </div>
                      <div className="flex justify-between py-2 border-b border-blue-100">
                        <span className="font-medium text-blue-700">Port</span>
                        <span className="text-blue-900">{safeGetNestedValue(sanitizedPassiveReconData, 'server_info.port', 'Unknown')}</span>
                      </div>
                      <div className="flex justify-between py-2">
                        <span className="font-medium text-blue-700">HTTPS</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${safeGetNestedValue(sanitizedPassiveReconData, 'server_info.is_https', false)
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                          }`}>
                          {safeGetNestedValue(sanitizedPassiveReconData, 'server_info.is_https', false) ? 'Enabled' : 'Disabled'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Technology Stack */}
                <div className="space-y-4">
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-purple-900 mb-4">Technology Stack</h3>
                    <div className="space-y-3">
                      {safeGetNestedValue(sanitizedPassiveReconData, 'technologies.servers') &&
                        Array.isArray(safeGetNestedValue(sanitizedPassiveReconData, 'technologies.servers')) &&
                        safeGetNestedValue(sanitizedPassiveReconData, 'technologies.servers').length > 0 && (
                          <div>
                            <span className="text-sm font-medium text-purple-700">Web Servers:</span>
                            <div className="mt-1 flex flex-wrap gap-1">
                              {safeGetNestedValue(sanitizedPassiveReconData, 'technologies.servers', []).map((server: string, idx: number) => (
                                <span key={idx} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                  {server}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                      {safeGetNestedValue(sanitizedPassiveReconData, 'technologies.frameworks') &&
                        Array.isArray(safeGetNestedValue(sanitizedPassiveReconData, 'technologies.frameworks')) &&
                        safeGetNestedValue(sanitizedPassiveReconData, 'technologies.frameworks').length > 0 && (
                          <div>
                            <span className="text-sm font-medium text-purple-700">Frameworks:</span>
                            <div className="mt-1 flex flex-wrap gap-1">
                              {safeGetNestedValue(sanitizedPassiveReconData, 'technologies.frameworks', []).map((framework: string, idx: number) => (
                                <span key={idx} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
                                  {framework}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                      {safeGetNestedValue(sanitizedPassiveReconData, 'technologies.languages') &&
                        Array.isArray(safeGetNestedValue(sanitizedPassiveReconData, 'technologies.languages')) &&
                        safeGetNestedValue(sanitizedPassiveReconData, 'technologies.languages').length > 0 && (
                          <div>
                            <span className="text-sm font-medium text-purple-700">Languages:</span>
                            <div className="mt-1 flex flex-wrap gap-1">
                              {safeGetNestedValue(sanitizedPassiveReconData, 'technologies.languages', []).map((language: string, idx: number) => (
                                <span key={idx} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                                  {language}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                      {!safeGetNestedValue(sanitizedPassiveReconData, 'technologies.servers') &&
                        !safeGetNestedValue(sanitizedPassiveReconData, 'technologies.frameworks') &&
                        !safeGetNestedValue(sanitizedPassiveReconData, 'technologies.languages') && (
                          <div className="text-sm text-purple-600">No technology information detected</div>
                        )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Second Display: Passive Reconnaissance Summary with Clickable Cards */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Passive Reconnaissance Summary</h2>
              <p className="text-sm text-gray-600 mb-6">Information gathered without direct interaction</p>

              <div className="flex flex-wrap justify-center gap-4">
                {/* Subdomains Card */}
                {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.subdomains.subdomains') &&
                  Array.isArray(safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.subdomains.subdomains')) &&
                  safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.subdomains.subdomains').length > 0 && (
                    <div
                      className="w-48 text-center p-4 bg-blue-50 rounded-lg border border-blue-200 cursor-pointer hover:bg-blue-100 transition-colors"
                      onClick={() => setShowSubdomainsModal(true)}
                    >
                      <div className="text-2xl font-bold text-blue-600">
                        {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.summary.subdomains_found', 0)}
                      </div>
                      <div className="text-sm text-gray-600">Subdomains</div>
                      <div className="text-xs text-gray-500 mt-1">Click to view</div>
                    </div>
                  )}

                {/* API Endpoints Card */}
                {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.api_endpoints.api_endpoints') &&
                  Array.isArray(safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.api_endpoints.api_endpoints')) &&
                  safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.api_endpoints.api_endpoints').length > 0 && (
                    <div
                      className="w-48 text-center p-4 bg-purple-50 rounded-lg border border-purple-200 cursor-pointer hover:bg-purple-100 transition-colors"
                      onClick={() => setShowApiEndpointsModal(true)}
                    >
                      <div className="text-2xl font-bold text-purple-600">
                        {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.summary.api_endpoints_found', 0)}
                      </div>
                      <div className="text-sm text-gray-600">API Endpoints</div>
                      <div className="text-xs text-gray-500 mt-1">Click to view</div>
                    </div>
                  )}

                {/* Historical URLs Card */}
                {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.wayback_urls.urls') &&
                  Array.isArray(safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.wayback_urls.urls')) &&
                  safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.wayback_urls.urls').length > 0 && (
                    <div
                      className="w-48 text-center p-4 bg-green-50 rounded-lg border border-green-200 cursor-pointer hover:bg-green-100 transition-colors"
                      onClick={() => setShowHistoricalUrlsModal(true)}
                    >
                      <div className="text-2xl font-bold text-green-600">
                        {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.summary.wayback_urls_found', 0)}
                      </div>
                      <div className="text-sm text-gray-600">Historical URLs</div>
                      <div className="text-xs text-gray-500 mt-1">Click to view</div>
                    </div>
                  )}

                {/* Directories Card */}
                {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.directories.directories') &&
                  Array.isArray(safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.directories.directories')) &&
                  safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.directories.directories').length > 0 && (
                    <div
                      className="w-48 text-center p-4 bg-yellow-50 rounded-lg border border-yellow-200 cursor-pointer hover:bg-yellow-100 transition-colors"
                      onClick={() => setShowDirectoriesModal(true)}
                    >
                      <div className="text-2xl font-bold text-yellow-600">
                        {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.summary.directories_found', 0)}
                      </div>
                      <div className="text-sm text-gray-600">Directories</div>
                      <div className="text-xs text-gray-500 mt-1">Click to view</div>
                    </div>
                  )}

                {/* Assets (JS files) Card */}
                {safeGetNestedValue(sanitizedPassiveReconData, 'technologies.files') &&
                  Array.isArray(safeGetNestedValue(sanitizedPassiveReconData, 'technologies.files')) &&
                  safeGetNestedValue(sanitizedPassiveReconData, 'technologies.files').length > 0 && (
                    <div
                      className="w-48 text-center p-4 bg-indigo-50 rounded-lg border border-indigo-200 cursor-pointer hover:bg-indigo-100 transition-colors"
                      onClick={() => setShowAssetsModal(true)}
                    >
                      <div className="text-2xl font-bold text-indigo-600">
                        {safeGetNestedValue(sanitizedPassiveReconData, 'technologies.files', []).length}
                      </div>
                      <div className="text-sm text-gray-600">Assets (JS files)</div>
                      <div className="text-xs text-gray-500 mt-1">Click to view</div>
                    </div>
                  )}

                {/* Show message if no discoveries found */}
                {(!safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.subdomains.subdomains') ||
                  safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.subdomains.subdomains').length === 0) &&
                  (!safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.api_endpoints.api_endpoints') ||
                    safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.api_endpoints.api_endpoints').length === 0) &&
                  (!safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.wayback_urls.urls') ||
                    safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.wayback_urls.urls').length === 0) &&
                  (!safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.directories.directories') ||
                    safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.directories.directories').length === 0) &&
                  (!safeGetNestedValue(sanitizedPassiveReconData, 'technologies.files') ||
                    safeGetNestedValue(sanitizedPassiveReconData, 'technologies.files').length === 0) && (
                    <div className="text-center py-8">
                      <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
                        <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                      </div>
                      <p className="text-gray-500 text-sm">No enhanced discoveries found in passive reconnaissance</p>
                      <p className="text-gray-400 text-xs mt-1">Basic target analysis data is available in the sections below</p>
                    </div>
                  )}

              </div>
            </div>

            {/* Third Display: Summary of All Discoveries */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Summary of All Discoveries</h2>

              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-medium text-gray-800 mb-4">All Discovered Endpoints</h3>

                <div className="max-h-60 overflow-y-auto space-y-2">
                  {/* API Endpoints */}
                  {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.api_endpoints.api_endpoints') &&
                    Array.isArray(safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.api_endpoints.api_endpoints')) && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-2 border-b pb-1">API Endpoints</h4>
                        <div className="space-y-1 pl-2">
                          {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.api_endpoints.api_endpoints', []).map((endpoint: any, index: number) => (
                            <div key={index} className="flex items-center justify-between text-sm">
                              <span className="text-blue-600 break-all flex-1 mr-3">
                                {typeof endpoint === 'object' ? endpoint.url : endpoint}
                              </span>
                              {typeof endpoint === 'object' && endpoint.status ? (
                                <span className={`px-2 py-0.5 rounded text-xs font-medium w-12 text-center ${endpoint.status === 200 ? 'bg-green-100 text-green-800' :
                                  endpoint.status === 403 ? 'bg-yellow-100 text-yellow-800' :
                                    endpoint.status === 401 ? 'bg-red-100 text-red-800' :
                                      'bg-gray-100 text-gray-800'
                                  }`}>
                                  {endpoint.status}
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded text-xs font-medium w-12 text-center bg-gray-100 text-gray-800">
                                  N/A
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                  {/* Subdomains */}
                  {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.subdomains.subdomains') &&
                    Array.isArray(safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.subdomains.subdomains')) && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-2 border-b pb-1">Discovered Subdomains</h4>
                        <div className="space-y-1 pl-2">
                          {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.subdomains.subdomains', []).map((subdomain: string, index: number) => (
                            <div key={index} className="text-sm text-blue-600 break-all">{subdomain}</div>
                          ))}
                        </div>
                      </div>
                    )}

                  {/* Historical URLs */}
                  {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.wayback_urls.urls') &&
                    Array.isArray(safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.wayback_urls.urls')) && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-2 border-b pb-1">Historical URLs</h4>
                        <div className="space-y-1 pl-2">
                          {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.wayback_urls.urls', []).map((url: string, index: number) => (
                            <div key={index} className="text-sm text-green-600 break-all">{url}</div>
                          ))}
                        </div>
                      </div>
                    )}

                  {/* Directories */}
                  {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.directories.directories') &&
                    Array.isArray(safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.directories.directories')) && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-2 border-b pb-1">Discovered Directories</h4>
                        <div className="space-y-1 pl-2">
                          {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.directories.directories', []).map((dir: any, index: number) => (
                            <div key={index} className="text-sm text-yellow-600 break-all">
                              {typeof dir === 'object' ? dir.url : dir}
                              {typeof dir === 'object' && dir.status && (
                                <span className={`ml-2 px-2 py-0.5 rounded text-xs ${dir.status === 200 ? 'bg-green-100 text-green-800' :
                                  dir.status === 403 ? 'bg-yellow-100 text-yellow-800' :
                                    dir.status === 401 ? 'bg-red-100 text-red-800' :
                                      'bg-gray-100 text-gray-800'
                                  }`}>
                                  {dir.status}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                </div>

                <div className="mt-4 text-sm text-gray-600 text-center">
                  Total Discoveries: {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.summary.total_discoveries', 0)}
                </div>
              </div>
            </div>

            {/* Fourth Display: HTTP Response Headers */}
            {sanitizedPassiveReconData?.response_headers && Object.keys(sanitizedPassiveReconData.response_headers).length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">HTTP Response Headers</h2>

                {/* Headers Grid */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(sanitizedPassiveReconData.response_headers)
                      .filter(([key]) => key !== 'recommendations' && key !== 'missing_security_headers')
                      .map(([header, value]) => (
                        <div key={header} className="bg-white p-3 rounded border">
                          <div className="text-sm font-medium text-gray-700 truncate">{header}</div>
                          <div className="text-xs text-gray-600 mt-1 break-all">
                            {typeof value === 'object' && value !== null ? (
                              <div className="max-h-32 overflow-y-auto">
                                <pre className="whitespace-pre-wrap text-xs">
                                  {JSON.stringify(value, null, 2)}
                                </pre>
                              </div>
                            ) : (
                              String(value)
                            )}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>

                {/* Recommendations Section */}
                {safeGetNestedValue(sanitizedPassiveReconData, 'response_headers.recommendations') &&
                  Array.isArray(safeGetNestedValue(sanitizedPassiveReconData, 'response_headers.recommendations')) &&
                  safeGetNestedValue(sanitizedPassiveReconData, 'response_headers.recommendations').length > 0 && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <h3 className="text-lg font-semibold text-yellow-900 mb-4">Security Recommendations</h3>
                      <div className="max-h-96 overflow-y-auto space-y-2 pr-2 scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-200">
                        {safeGetNestedValue(sanitizedPassiveReconData, 'response_headers.recommendations', []).map((recommendation: string, index: number) => (
                          <div key={index} className="text-sm text-yellow-800 bg-white p-3 rounded border border-yellow-200">
                            <div className="flex items-start gap-2">
                              <span className="text-yellow-600 font-medium">{index + 1}.</span>
                              <span className="flex-1">{recommendation}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
              </div>
            )}
          </div>
        )}

        {/* Security Vulnerabilities - Different messaging for passive vs active */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {isPassiveScan ? 'Security Observations' : 'Security Vulnerabilities'}
              </h2>
              {isPassiveScan && actualVulnerabilities.length === 0 && (
                <p className="text-sm text-gray-600 mt-1">
                  Passive scans have limited vulnerability detection. For comprehensive testing, run an active scan.
                </p>
              )}
              <div className="mt-2 flex space-x-2">
                {vulnStats.critical > 0 && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                    {vulnStats.critical} Critical
                  </span>
                )}
                {vulnStats.high > 0 && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-orange-100 text-orange-800">
                    {vulnStats.high} High
                  </span>
                )}
                {vulnStats.medium > 0 && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                    {vulnStats.medium} Medium
                  </span>
                )}
                {vulnStats.low > 0 && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                    {vulnStats.low} Low
                  </span>
                )}
                {vulnStats.fp > 0 && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-200 text-gray-700 border border-gray-300">
                    {vulnStats.fp} F. Positives
                  </span>
                )}
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                  {vulnStats.total} Total
                </span>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex bg-gray-100 p-1 rounded-lg">
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${viewMode === 'list'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-900'
                    }`}
                >
                  List
                </button>
                <button
                  onClick={() => setViewMode('grouped')}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${viewMode === 'grouped'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-900'
                    }`}
                >
                  Grouped
                </button>
                <button
                  onClick={() => setViewMode('tree')}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${viewMode === 'tree'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-900'
                    }`}
                >
                  Tree
                </button>
              </div>
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="border border-gray-300 rounded-md text-sm px-3 py-2 min-w-[140px]"
              >
                <option value="all">All Severities ({actualVulnerabilities.filter(v => confidenceFilter === 'all' || (v && (v.confidence || 0) >= parseFloat(confidenceFilter) / 100)).length})</option>
                <option value="fp">False Positives ({vulnStats.fp})</option>
                <option value="critical">Critical ({actualVulnerabilities.filter(v => v && v.severity === 'critical' && (confidenceFilter === 'all' || (v.confidence || 0) >= parseFloat(confidenceFilter) / 100)).length})</option>
                <option value="high">High ({actualVulnerabilities.filter(v => v && v.severity === 'high' && (confidenceFilter === 'all' || (v.confidence || 0) >= parseFloat(confidenceFilter) / 100)).length})</option>
                <option value="medium">Medium ({actualVulnerabilities.filter(v => v && v.severity === 'medium' && (confidenceFilter === 'all' || (v.confidence || 0) >= parseFloat(confidenceFilter) / 100)).length})</option>
                <option value="low">Low ({actualVulnerabilities.filter(v => v && v.severity === 'low' && (confidenceFilter === 'all' || (v.confidence || 0) >= parseFloat(confidenceFilter) / 100)).length})</option>
              </select>
              <select
                value={confidenceFilter}
                onChange={(e) => setConfidenceFilter(e.target.value)}
                className="border border-gray-300 rounded-md text-sm px-3 py-2 min-w-[140px]"
              >
                <option value="all">All Confidence ({actualVulnerabilities.filter(v => severityFilter === 'all' || v?.severity === severityFilter).length})</option>
                <option value="50">≥50% ({actualVulnerabilities.filter(v => v && (severityFilter === 'all' || v.severity === severityFilter) && (v.confidence || 0) >= 0.5).length})</option>
                <option value="60">≥60% ({actualVulnerabilities.filter(v => v && (severityFilter === 'all' || v.severity === severityFilter) && (v.confidence || 0) >= 0.6).length})</option>
                <option value="70">≥70% ({actualVulnerabilities.filter(v => v && (severityFilter === 'all' || v.severity === severityFilter) && (v.confidence || 0) >= 0.7).length})</option>
                <option value="80">≥80% ({actualVulnerabilities.filter(v => v && (severityFilter === 'all' || v.severity === severityFilter) && (v.confidence || 0) >= 0.8).length})</option>
                <option value="90">≥90% ({actualVulnerabilities.filter(v => v && (severityFilter === 'all' || v.severity === severityFilter) && (v.confidence || 0) >= 0.9).length})</option>
                <option value="100">100% ({actualVulnerabilities.filter(v => v && (severityFilter === 'all' || v.severity === severityFilter) && (v.confidence || 0) >= 1.0).length})</option>
              </select>
            </div>
          </div>

          {filteredVulnerabilities.length === 0 ? (
            <div className="text-center py-12 border border-gray-200 rounded-lg bg-gray-50">
              <div className="text-gray-400 text-4xl mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.031 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <p className="text-lg text-gray-500 font-medium">
                No vulnerabilities found
                {severityFilter !== 'all' || confidenceFilter !== 'all' ? ' matching the selected filters:' : ''}
              </p>
              {(severityFilter !== 'all' || confidenceFilter !== 'all') && (
                <div className="mt-2 text-sm text-gray-400">
                  {severityFilter !== 'all' && (
                    <span className="inline-block mr-4">• Severity: {severityFilter}</span>
                  )}
                  {confidenceFilter !== 'all' && (
                    <span className="inline-block">• Confidence: ≥{confidenceFilter}%</span>
                  )}
                </div>
              )}
              {actualVulnerabilities.length === 0 && (
                <p className="text-sm text-gray-400 mt-2">
                  {isPassiveScan
                    ? 'No security issues detected in passive reconnaissance. Run an active scan for comprehensive vulnerability testing.'
                    : 'This is a positive security indicator. The target appears to have good security posture.'}
                </p>
              )}
            </div>
          ) : (
            <div>
              {/* Show info about all vulnerabilities being displayed */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-blue-800">
                      {severityFilter !== 'all' || confidenceFilter !== 'all' ? 'Filtered Vulnerability Report' : 'Complete Vulnerability Report'}
                    </h3>
                    <div className="mt-2 text-sm text-blue-700">
                      <p>
                        Displaying {filteredVulnerabilities.length} security vulnerabilities
                        {severityFilter !== 'all' || confidenceFilter !== 'all' ? ' matching the selected filters' : ' found during the scan'}.
                        {infoFindings.length > 0 && (
                          <span className="font-medium"> {infoFindings.length} informational findings are shown separately below.</span>
                        )}
                        {vulnerabilitySummary?.truncated && (
                          <span className="font-medium text-red-600"> Note: Total of {vulnerabilitySummary.total_count} vulnerabilities were detected, but only {vulnerabilitySummary.showing_count} are displayed here.</span>
                        )}
                      </p>
                      {(severityFilter !== 'all' || confidenceFilter !== 'all') && (
                        <div className="mt-2 text-xs text-blue-600">
                          <span className="font-medium">Active filters:</span>
                          {severityFilter !== 'all' && (
                            <span className="ml-2 px-2 py-1 bg-blue-100 rounded">Severity: {severityFilter}</span>
                          )}
                          {confidenceFilter !== 'all' && (
                            <span className="ml-2 px-2 py-1 bg-blue-100 rounded">Confidence: ≥{confidenceFilter}%</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Scrollable container for vulnerabilities */}
              <div className="border border-gray-200 rounded-lg bg-gray-50">
                <div className="px-4 py-3 border-b border-gray-200 bg-white rounded-t-lg">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-gray-700">
                      Vulnerabilities ({filteredVulnerabilities.length})
                    </h3>
                    <div className="text-xs text-gray-500 hidden sm:block">
                      Scroll to view all vulnerabilities
                    </div>
                  </div>
                </div>
                <div
                  className="overflow-y-auto space-y-4 p-4 scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-200"
                  style={{
                    maxHeight: 'calc(100vh - 300px)', // Responsive height based on viewport
                    minHeight: '300px'
                  }}
                >
                  {viewMode === 'list' ? (
                    filteredVulnerabilities.map((vuln) => (
                      <div key={vuln.id} className="border border-gray-200 rounded-lg p-5 hover:shadow-sm transition-shadow">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-3">
                              <h3 className="text-lg font-semibold text-gray-900">
                                {safeRender(vuln.name, 'Unknown Vulnerability')}
                              </h3>
                              {vuln.is_fp && (
                                <span className="px-2 py-0.5 rounded text-xs font-semibold uppercase bg-gray-100 text-gray-600 border border-gray-300" title={`ML Confidence: ${(vuln.fp_confidence * 100).toFixed(1)}%`}>
                                  Likely FP
                                </span>
                              )}
                            </div>
                            <p className="mt-2 text-gray-600">
                              {safeRender(vuln.description, 'No description available')}
                            </p>
                          </div>
                          <div className="flex flex-col items-end space-y-2">
                            <span className={getSeverityBadgeClass(vuln.severity)}>
                              {(vuln.severity || 'unknown').toUpperCase()}
                            </span>
                            <span className="text-xs text-gray-500">
                              {Math.round((vuln.confidence || 0) * 100)}% confidence
                            </span>
                          </div>
                        </div>

                        {(vuln.url || vuln.parameter) && (
                          <div className="border-t border-gray-100 pt-4 mt-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                              {vuln.url && (
                                <div>
                                  <span className="font-medium text-gray-700">Affected URL:</span>
                                  <a href={vuln.url} target="_blank" rel="noopener noreferrer"
                                    className="ml-2 text-blue-600 hover:underline break-all">
                                    {typeof vuln.url === 'string' ? vuln.url : JSON.stringify(vuln.url)}
                                  </a>
                                </div>
                              )}
                              {vuln.parameter && (
                                <div>
                                  <span className="font-medium text-gray-700">Parameter:</span>
                                  <span className="ml-2 text-gray-600 font-mono bg-gray-100 px-2 py-1 rounded">
                                    {typeof vuln.parameter === 'string' ? vuln.parameter : JSON.stringify(vuln.parameter)}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {vuln.evidence && (
                          <details className="mt-4">
                            <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 py-2">
                              View Technical Evidence
                            </summary>
                            <div className="mt-2 bg-gray-50 rounded-lg p-4 border border-gray-200">
                              <pre className="text-xs text-gray-700 whitespace-pre-wrap overflow-x-auto">
                                {typeof vuln.evidence === 'string' ? vuln.evidence : JSON.stringify(vuln.evidence, null, 2)}
                              </pre>
                            </div>
                          </details>
                        )}

                        {vuln.remediation && (
                          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                            <h4 className="text-sm font-semibold text-blue-900 mb-2">Recommended Action</h4>
                            <p className="text-sm text-blue-800">
                              {typeof vuln.remediation === 'string' ? vuln.remediation : JSON.stringify(vuln.remediation)}
                            </p>
                          </div>
                        )}
                      </div>
                    ))
                  ) : viewMode === 'tree' ? (
                    <div className="border border-gray-200 rounded-lg p-4 bg-white">
                      <h4 className="text-sm font-medium text-gray-700 mb-3 border-b pb-2">Site Structure & Vulnerabilities</h4>
                      {(() => {
                        const allUrls = getAllDiscoveredUrls();
                        const treeRoot = buildFileTree(allUrls, filteredVulnerabilities);

                        if (treeRoot.size === 0) {
                          return <div className="text-sm text-gray-500 italic">No URL structure available to display.</div>;
                        }

                        return (
                          <div className="space-y-1">
                            {Array.from(treeRoot.values()).map((node, idx) => (
                              <FileTreeItem key={`${node.path}-${idx}`} node={node} level={0} />
                            ))}
                          </div>
                        );
                      })()}
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {groupedVulnerabilities.map((group) => (
                        <div key={group.key} className="border border-gray-200 rounded-lg overflow-hidden">
                          <button
                            onClick={() => toggleGroup(group.key)}
                            className="w-full flex items-center justify-between p-4 bg-white hover:bg-gray-50 transition-colors"
                          >
                            <div className="flex items-center space-x-4">
                              <span className={getSeverityBadgeClass(group.severity)}>
                                {group.severity.toUpperCase()}
                              </span>
                              <span className="font-medium text-gray-900">{group.name}</span>
                              <span className="text-sm text-gray-500">({group.count} instances)</span>
                            </div>
                            <svg
                              className={`w-5 h-5 text-gray-400 transform transition-transform ${expandedGroups.has(group.key) ? 'rotate-180' : ''}`}
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </button>
                          {expandedGroups.has(group.key) && (
                            <div className="border-t border-gray-200 bg-gray-50 p-4 max-h-[300px] overflow-y-auto">
                              <ul className="space-y-2">
                                {group.vulnerabilities.map((vuln, idx) => (
                                  <li key={vuln.id || idx} className="flex items-center justify-between text-sm">
                                    <span className="text-gray-600 truncate flex-1 mr-4">
                                      {vuln.url || 'No URL'}
                                    </span>
                                    <button
                                      onClick={() => {
                                        setSelectedVulnerabilityId(vuln.id);
                                        setIsModalOpen(true);
                                      }}
                                      className="text-blue-600 hover:text-blue-800 whitespace-nowrap"
                                    >
                                      View Details
                                    </button>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
        {/* Information Section - After Vulnerabilities */}
        {
          infoFindings.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Information about Target</h2>
                  <p className="text-sm text-gray-600 mt-1">Informational findings and observations from the scan</p>
                </div>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                  {infoFindings.length} items
                </span>
              </div>

              <div className="border border-gray-200 rounded-lg bg-gray-50">
                <div className="px-4 py-3 border-b border-gray-200 bg-white rounded-t-lg">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-gray-700">
                      Information Findings ({infoFindings.length})
                    </h3>
                    <div className="text-xs text-gray-500 hidden sm:block">
                      Scroll to view all findings
                    </div>
                  </div>
                </div>
                <div
                  className="overflow-y-auto space-y-4 p-4 scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-200"
                  style={{
                    maxHeight: 'calc(100vh - 400px)', // Responsive height for info findings
                    minHeight: '250px'
                  }}
                >
                  {infoFindings.map((finding) => (
                    <div key={finding.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow bg-blue-50">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900">
                            {safeRender(finding.name, 'Information Finding')}
                          </h3>
                          <p className="mt-2 text-gray-600">
                            {safeRender(finding.description, 'No description available')}
                          </p>
                        </div>
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          INFORMATION
                        </span>
                      </div>

                      {(finding.url || finding.parameter) && (
                        <div className="border-t border-blue-200 pt-4 mt-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                            {finding.url && (
                              <div>
                                <span className="font-medium text-gray-700">Related URL:</span>
                                <a href={finding.url} target="_blank" rel="noopener noreferrer"
                                  className="ml-2 text-blue-600 hover:underline break-all">
                                  {typeof finding.url === 'string' ? finding.url : JSON.stringify(finding.url)}
                                </a>
                              </div>
                            )}
                            {finding.parameter && (
                              <div>
                                <span className="font-medium text-gray-700">Parameter:</span>
                                <span className="ml-2 text-gray-600 font-mono bg-gray-100 px-2 py-1 rounded">
                                  {typeof finding.parameter === 'string' ? finding.parameter : JSON.stringify(finding.parameter)}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {finding.evidence && (
                        <details className="mt-4">
                          <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 py-2">
                            View Details
                          </summary>
                          <div className="mt-2 bg-white rounded-lg p-4 border border-gray-200">
                            <pre className="text-xs text-gray-700 whitespace-pre-wrap overflow-x-auto">
                              {typeof finding.evidence === 'string' ? finding.evidence : JSON.stringify(finding.evidence, null, 2)}
                            </pre>
                          </div>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )
        }

        {/* URLs Modal */}
        {
          showUrlsModal && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {isPassiveScan ? 'Passively Discovered URLs' : 'All Discovered URLs'} ({allUrls.length})
                  </h3>
                  {isActiveScan && (
                    <span className="text-xs text-gray-500">
                      Combined from passive recon, active crawling, and enhanced discovery
                    </span>
                  )}
                  <button
                    onClick={() => setShowUrlsModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <div className="px-6 py-4 border-b border-gray-200">
                  <input
                    type="text"
                    placeholder="Search URLs..."
                    value={modalSearchTerm}
                    onChange={(e) => setModalSearchTerm(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex-1 overflow-y-auto px-6">
                  <div className="py-4 space-y-2">
                    {allUrls
                      .filter(url => url.toLowerCase().includes(modalSearchTerm.toLowerCase()))
                      .map((url, index) => (
                        <div key={index} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg hover:bg-gray-100">
                          <a
                            href={url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:text-blue-800 break-all flex-1 mr-3"
                          >
                            {url}
                          </a>
                          <div className="flex items-center space-x-2 text-xs text-gray-500">
                            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                              URL {index + 1}
                            </span>
                            <button
                              onClick={() => navigator.clipboard.writeText(url)}
                              className="text-gray-400 hover:text-gray-600"
                              title="Copy URL"
                            >
                              📋
                            </button>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>

                <div className="px-6 py-4 border-t border-gray-200 text-center text-sm text-gray-600">
                  Showing {allUrls.filter(url => url.toLowerCase().includes(modalSearchTerm.toLowerCase())).length} of {allUrls.length} URLs
                  {isActiveScan && (
                    <div className="text-xs text-gray-500 mt-1">
                      Sources: Passive reconnaissance, active crawling, enhanced discovery
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        }

        {/* Forms Modal */}
        {
          showFormsModal && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[80vh] flex flex-col">
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {isPassiveScan ? 'Forms Found in Passive Recon' : 'All Discovered Forms'} ({allForms.length})
                  </h3>
                  {isActiveScan && (
                    <span className="text-xs text-gray-500">
                      Discovered through crawling and form analysis
                    </span>
                  )}
                  <button
                    onClick={() => setShowFormsModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <div className="px-6 py-4 border-b border-gray-200">
                  <input
                    type="text"
                    placeholder="Search forms..."
                    value={modalSearchTerm}
                    onChange={(e) => setModalSearchTerm(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex-1 overflow-y-auto px-6">
                  <div className="py-4 space-y-4">
                    {allForms
                      .filter((form: any) =>
                        form.action?.toLowerCase().includes(modalSearchTerm.toLowerCase()) ||
                        form.method?.toLowerCase().includes(modalSearchTerm.toLowerCase()) ||
                        form.url?.toLowerCase().includes(modalSearchTerm.toLowerCase())
                      )
                      .map((form: any, index: number) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4 bg-gray-50 hover:bg-gray-100">
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                            <div>
                              <span className="text-sm font-medium text-gray-700">Form #{index + 1}</span>
                              <p className="text-sm text-gray-900 break-all">
                                {typeof (form.url || form.action) === 'string' ? (form.url || form.action) : JSON.stringify(form.url || form.action) || 'N/A'}
                              </p>
                            </div>
                            <div>
                              <span className="text-sm font-medium text-gray-700">Method:</span>
                              <span className={`ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${form.method === 'POST' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                                }`}>
                                {typeof form.method === 'string' ? form.method : JSON.stringify(form.method) || 'GET'}
                              </span>
                            </div>
                            <div>
                              <span className="text-sm font-medium text-gray-700">Fields:</span>
                              <p className="text-sm text-gray-600">
                                {form.fields?.length || 0} field{(form.fields?.length || 0) !== 1 ? 's' : ''}
                              </p>
                            </div>
                          </div>

                          {form.fields && form.fields.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-gray-200">
                              <span className="text-sm font-medium text-gray-700">Form Fields:</span>
                              <div className="mt-2 flex flex-wrap gap-2">
                                {(form.fields || []).map((field: any, fieldIndex: number) => (
                                  <span key={fieldIndex} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                    {safeRender(typeof field === 'object' ? (field.name || JSON.stringify(field)) : field, 'unnamed')} ({safeRender(typeof field === 'object' ? (field.type || 'text') : 'text', 'text')})
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          <div className="mt-3 flex items-center justify-between">
                            <span className="text-xs text-gray-500">
                              Action: {typeof form.action === 'string' ? form.action : JSON.stringify(form.action) || 'Same page'}
                            </span>
                            <button
                              onClick={() => navigator.clipboard.writeText(typeof (form.url || form.action) === 'string' ? (form.url || form.action) : JSON.stringify(form.url || form.action) || '')}
                              className="text-xs text-blue-600 hover:text-blue-800"
                            >
                              📋 Copy URL
                            </button>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>

                <div className="px-6 py-4 border-t border-gray-200 text-center text-sm text-gray-600">
                  Showing {allForms.filter((form: any) =>
                    form.action?.toLowerCase().includes(modalSearchTerm.toLowerCase()) ||
                    form.method?.toLowerCase().includes(modalSearchTerm.toLowerCase()) ||
                    form.url?.toLowerCase().includes(modalSearchTerm.toLowerCase())
                  ).length} of {allForms.length} forms
                  {isActiveScan && (
                    <div className="text-xs text-gray-500 mt-1">
                      Forms discovered through active crawling and page analysis
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        }

        {/* Subdomains Modal */}
        {
          showSubdomainsModal && (
            <div className="fixed top-20 right-4 w-96 max-h-[70vh] bg-white rounded-lg shadow-xl border border-gray-300 z-50 flex flex-col">
              <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-blue-900">
                  Subdomains ({safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.summary.subdomains_found', 0)})
                </h3>
                <button
                  onClick={() => setShowSubdomainsModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-3">
                <div className="space-y-2">
                  {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.subdomains.subdomains', []).map((subdomain: string, index: number) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-blue-50 rounded border border-blue-200">
                      <span className="text-blue-800 font-mono text-xs truncate">{subdomain}</span>
                      <button
                        onClick={() => navigator.clipboard.writeText(subdomain)}
                        className="text-xs text-blue-600 hover:text-blue-800 px-1 py-1 rounded bg-white ml-2 flex-shrink-0"
                        title="Copy"
                      >
                        📋
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )
        }

        {/* API Endpoints Modal */}
        {
          showApiEndpointsModal && (
            <div className="fixed top-20 right-4 w-96 max-h-[70vh] bg-white rounded-lg shadow-xl border border-gray-300 z-50 flex flex-col">
              <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-purple-900">
                  API Endpoints ({safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.summary.api_endpoints_found', 0)})
                </h3>
                <button
                  onClick={() => setShowApiEndpointsModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-3">
                <div className="space-y-2">
                  {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.api_endpoints.api_endpoints', []).map((endpoint: any, index: number) => (
                    <div key={index} className="p-2 bg-purple-50 rounded border border-purple-200">
                      <div className="flex items-center justify-between">
                        <span className="text-purple-800 font-mono text-xs truncate flex-1">{typeof endpoint === 'object' ? endpoint.url : endpoint}</span>
                        <button
                          onClick={() => navigator.clipboard.writeText(typeof endpoint === 'object' ? endpoint.url : endpoint)}
                          className="text-xs text-purple-600 hover:text-purple-800 px-1 py-1 rounded bg-white ml-2 flex-shrink-0"
                          title="Copy"
                        >
                          📋
                        </button>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {typeof endpoint === 'object' && endpoint.status ? (
                          <span className={`px-2 py-1 rounded text-xs font-medium ${endpoint.status === 200 ? 'bg-green-100 text-green-800' :
                            endpoint.status === 201 ? 'bg-green-100 text-green-800' :
                              endpoint.status === 403 ? 'bg-yellow-100 text-yellow-800' :
                                endpoint.status === 401 ? 'bg-red-100 text-red-800' :
                                  endpoint.status === 404 ? 'bg-red-100 text-red-800' :
                                    endpoint.status === 500 ? 'bg-red-100 text-red-800' :
                                      'bg-gray-100 text-gray-800'
                            }`}>
                            {endpoint.status}
                          </span>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )
        }

        {/* Historical URLs Modal */}
        {
          showHistoricalUrlsModal && (
            <div className="fixed top-20 right-4 w-96 max-h-[70vh] bg-white rounded-lg shadow-xl border border-gray-300 z-50 flex flex-col">
              <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-green-900">
                  Historical URLs ({safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.summary.wayback_urls_found', 0)})
                </h3>
                <button
                  onClick={() => setShowHistoricalUrlsModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-3">
                <div className="space-y-2">
                  {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.wayback_urls.urls', []).map((url: string, index: number) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-green-50 rounded border border-green-200">
                      <span className="text-green-800 font-mono text-xs truncate flex-1">{url}</span>
                      <button
                        onClick={() => navigator.clipboard.writeText(url)}
                        className="text-xs text-green-600 hover:text-green-800 px-1 py-1 rounded bg-white ml-2 flex-shrink-0"
                        title="Copy"
                      >
                        📋
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )
        }

        {/* Directories Modal */}
        {
          showDirectoriesModal && (
            <div className="fixed top-20 right-4 w-96 max-h-[70vh] bg-white rounded-lg shadow-xl border border-gray-300 z-50 flex flex-col">
              <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-yellow-900">
                  Directories ({safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.summary.directories_found', 0)})
                </h3>
                <button
                  onClick={() => setShowDirectoriesModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-3">
                <div className="space-y-2">
                  {safeGetNestedValue(sanitizedPassiveReconData, 'enhanced_discovery.directories.directories', []).map((dir: any, index: number) => (
                    <div key={index} className="p-2 bg-yellow-50 rounded border border-yellow-200">
                      <div className="flex items-center justify-between">
                        <span className="text-yellow-800 font-mono text-xs truncate flex-1">{typeof dir === 'object' ? dir.url : dir}</span>
                        <button
                          onClick={() => navigator.clipboard.writeText(typeof dir === 'object' ? dir.url : dir)}
                          className="text-xs text-yellow-600 hover:text-yellow-800 px-1 py-1 rounded bg-white ml-2 flex-shrink-0"
                          title="Copy"
                        >
                          📋
                        </button>
                      </div>
                      {typeof dir === 'object' && dir.status && (
                        <span className={`inline-block mt-1 px-2 py-1 rounded text-xs font-medium ${dir.status === 200 ? 'bg-green-100 text-green-800' :
                          dir.status === 403 ? 'bg-yellow-100 text-yellow-800' :
                            dir.status === 401 ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                          }`}>
                          {dir.status}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )
        }

        {/* Assets Modal */}
        {
          showAssetsModal && (
            <div className="fixed top-20 right-4 w-96 max-h-[70vh] bg-white rounded-lg shadow-xl border border-gray-300 z-50 flex flex-col">
              <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-indigo-900">
                  Assets (JS files) ({safeGetNestedValue(sanitizedPassiveReconData, 'technologies.files', []).length})
                </h3>
                <button
                  onClick={() => setShowAssetsModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-3">
                <div className="space-y-2">
                  {safeGetNestedValue(sanitizedPassiveReconData, 'technologies.files', []).map((asset: string, index: number) => (
                    <div key={index} className="p-2 bg-indigo-50 rounded border border-indigo-200">
                      <div className="flex items-center justify-between">
                        <a
                          href={asset.startsWith('http') ? asset : undefined}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-800 font-mono text-xs truncate flex-1 hover:underline"
                        >
                          {asset}
                        </a>
                        <button
                          onClick={() => navigator.clipboard.writeText(asset)}
                          className="text-xs text-indigo-600 hover:text-indigo-800 px-1 py-1 rounded bg-white ml-2 flex-shrink-0"
                          title="Copy"
                        >
                          📋
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )
        }
        {/* Vulnerability Details Modal */}
        <VulnerabilityModal
          vulnerabilityId={selectedVulnerabilityId}
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedVulnerabilityId(null);
          }}
        />
      </div >
    );
  } catch (error) {
    console.error('❌ Error rendering ScanResults component:', error);
    console.error('❌ Error details:', {
      message: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : 'No stack trace',
      scanType: effectiveScanType,
      originalScanType: scanType,
      hasActiveData: !!sanitizedActiveReconData,
      hasPassiveData: !!sanitizedPassiveReconData,
      vulnerabilityCount: sanitizedVulnerabilities.length
    });

    if (onError) {
      onError(`Error rendering scan results: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading scan results</h3>
            <p className="mt-1 text-sm text-red-700">
              There was an error displaying the scan results. Check the browser console for details.
            </p>
            {error instanceof Error && (
              <p className="mt-2 text-xs text-red-600 font-mono">
                {error.message}
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }
};

export default ScanResults;
