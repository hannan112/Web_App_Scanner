/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect } from 'react';
import { PassiveReconResult, ScanResult } from '@/types/project';

interface ScanResultsProps {
  scanId: string;
  projectId?: number | string;
  vulnerabilities: ScanResult[];
  passiveReconData?: PassiveReconResult;
  crawlData?: {
    pages_crawled: number;
    urls_count: number;
    forms_count: number;
  };
  onError?: (message: string) => void;
}

const ScanResults: React.FC<ScanResultsProps> = ({ 
  scanId,
  projectId,
  vulnerabilities = [], 
  passiveReconData, 
  crawlData,
  onError
}) => {
  // State for filtering vulnerabilities
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showUrls, setShowUrls] = useState<boolean>(false);
  const [showForms, setShowForms] = useState<boolean>(false);
  const [showCookies, setShowCookies] = useState<boolean>(false);

  // Initialize with empty arrays/objects if data is missing
  useEffect(() => {
    // Validate passive recon data
    if (passiveReconData) {
      if (!passiveReconData.technologies) {
        passiveReconData.technologies = {};
      }
      if (!passiveReconData.dns_records) {
        passiveReconData.dns_records = {};
      }
      if (!passiveReconData.server_info) {
        passiveReconData.server_info = {};
      }
      if (!passiveReconData.response_headers) {
        passiveReconData.response_headers = {};
      }
    }
  }, [passiveReconData]);

  // Get filtered vulnerabilities based on severity
  const filteredVulnerabilities = severityFilter === 'all' 
    ? vulnerabilities 
    : vulnerabilities.filter(v => v.severity === severityFilter);

  // Helper to get CSS classes for severity badges
  const getSeverityBadgeClass = (severity: string): string => {
    const baseClasses = 'px-2 py-1 rounded-full text-xs font-medium';
    switch (severity.toLowerCase()) {
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

  // Handle error condition
  const handleError = (message: string) => {
    if (onError) {
      onError(message);
    } else {
      console.error(message);
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

  // Toggle sections
  const toggleUrls = () => setShowUrls(!showUrls);
  const toggleForms = () => setShowForms(!showForms);
  const toggleCookies = () => setShowCookies(!showCookies);

  return (
    <div className="space-y-8">
      {/* Passive Reconnaissance Summary Section */}
      {passiveReconData && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Passive Reconnaissance Summary</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Technologies Detected */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-medium text-gray-700">Technologies Detected</h3>
              {passiveReconData.technologies && Object.keys(passiveReconData.technologies).length > 0 ? (
                <div className="mt-2 space-y-1">
                  {safeGetNestedValue(passiveReconData, 'technologies.server') && (
                    <div>
                      <span className="text-sm font-medium">Server:</span>
                      <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {safeGetNestedValue(passiveReconData, 'technologies.server')}
                      </span>
                    </div>
                  )}
                  
                  {safeGetNestedValue(passiveReconData, 'technologies.frameworks') && 
                   Array.isArray(safeGetNestedValue(passiveReconData, 'technologies.frameworks')) && 
                   safeGetNestedValue(passiveReconData, 'technologies.frameworks').length > 0 && (
                    <div>
                      <span className="text-sm font-medium">Frameworks:</span>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {safeGetNestedValue(passiveReconData, 'technologies.frameworks', []).map((framework: string, idx: number) => (
                          <span key={idx} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                            {framework}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {safeGetNestedValue(passiveReconData, 'technologies.cms') && (
                    <div>
                      <span className="text-sm font-medium">CMS:</span>
                      <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {safeGetNestedValue(passiveReconData, 'technologies.cms')}
                      </span>
                    </div>
                  )}
                  
                  {safeGetNestedValue(passiveReconData, 'technologies.javascript_libraries') && 
                   Array.isArray(safeGetNestedValue(passiveReconData, 'technologies.javascript_libraries')) && 
                   safeGetNestedValue(passiveReconData, 'technologies.javascript_libraries').length > 0 && (
                    <div>
                      <span className="text-sm font-medium">JavaScript Libraries:</span>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {safeGetNestedValue(passiveReconData, 'technologies.javascript_libraries', []).map((library: string, idx: number) => (
                          <span key={idx} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            {library}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="mt-2 text-sm text-gray-500">No technologies detected</p>
              )}
            </div>
            
            {/* Server Information */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-medium text-gray-700">Server Information</h3>
              {passiveReconData.server_info && Object.keys(passiveReconData.server_info).length > 0 ? (
                <div className="mt-2 text-sm text-gray-600 space-y-1">
                  <p>
                    <span className="font-medium">Server:</span>{" "}
                    {safeGetNestedValue(passiveReconData, 'server_info.server', 'Unknown')}
                  </p>
                  <p>
                    <span className="font-medium">Powered By:</span>{" "}
                    {safeGetNestedValue(passiveReconData, 'server_info.x_powered_by', 'Not disclosed')}
                  </p>
                  <p>
                    <span className="font-medium">Status Code:</span>{" "}
                    {safeGetNestedValue(passiveReconData, 'server_info.status_code', 'Unknown')}
                  </p>
                  {safeGetNestedValue(passiveReconData, 'server_info.ssl') && 
                   typeof safeGetNestedValue(passiveReconData, 'server_info.ssl') === 'object' &&
                   !safeGetNestedValue(passiveReconData, 'server_info.ssl.error') && (
                    <div>
                      <span className="font-medium">SSL/TLS:</span>{" "}
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        ['TLSv1.2', 'TLSv1.3'].includes(safeGetNestedValue(passiveReconData, 'server_info.ssl.protocol', '')) 
                          ? "bg-green-100 text-green-800" 
                          : "bg-orange-100 text-orange-800"
                      }`}>
                        {safeGetNestedValue(passiveReconData, 'server_info.ssl.protocol', 'Unknown')}
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <p className="mt-2 text-sm text-gray-500">No server information available</p>
              )}
            </div>
            
            {/* DNS Information */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-medium text-gray-700">DNS Records</h3>
              {passiveReconData.dns_records && Object.keys(passiveReconData.dns_records).length > 0 ? (
                <div className="mt-2 text-sm text-gray-600">
                  <p>
                    <span className="font-medium">IP:</span>{" "}
                    {safeGetNestedValue(passiveReconData, 'dns_records.IP', 'Unknown')}
                  </p>
                  <p className="mt-1">
                    {Object.keys(passiveReconData.dns_records).filter(key => key !== 'IP').length} record types found
                  </p>
                  <button 
                    className="mt-2 text-blue-600 hover:text-blue-800 text-xs font-medium"
                    onClick={() => {
                      alert("DNS Records: " + JSON.stringify(passiveReconData.dns_records, null, 2));
                    }}
                  >
                    View All DNS Records
                  </button>
                </div>
              ) : (
                <p className="mt-2 text-sm text-gray-500">No DNS records available</p>
              )}
            </div>
          </div>
          
          {/* Crawler Summary (if available) */}
          {crawlData && (
            <div className="mt-6">
              <h3 className="font-medium text-gray-700 mb-2">Crawl Summary</h3>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Pages Crawled:</span>
                    <span className="ml-2 text-gray-600">{crawlData.pages_crawled}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">URLs Discovered:</span>
                    <span className="ml-2 text-gray-600">{crawlData.urls_count}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Forms Found:</span>
                    <span className="ml-2 text-gray-600">{crawlData.forms_count}</span>
                  </div>
                </div>
                
                {/* Toggle buttons for detailed crawl data */}
                <div className="mt-4 flex flex-wrap gap-2">
                  {passiveReconData.urls_discovered && Array.isArray(passiveReconData.urls_discovered) && passiveReconData.urls_discovered.length > 0 && (
                    <button
                      onClick={toggleUrls}
                      className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 flex items-center"
                    >
                      <span>{showUrls ? "Hide" : "Show"} Discovered URLs</span>
                      <svg 
                        className={`ml-1 w-4 h-4 transition-transform ${showUrls ? "rotate-180" : ""}`} 
                        fill="none" 
                        viewBox="0 0 24 24" 
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                  )}
                  
                  {passiveReconData.forms_discovered && Array.isArray(passiveReconData.forms_discovered) && passiveReconData.forms_discovered.length > 0 && (
                    <button
                      onClick={toggleForms}
                      className="px-3 py-1 text-xs bg-purple-100 text-purple-700 rounded hover:bg-purple-200 flex items-center"
                    >
                      <span>{showForms ? "Hide" : "Show"} Discovered Forms</span>
                      <svg 
                        className={`ml-1 w-4 h-4 transition-transform ${showForms ? "rotate-180" : ""}`} 
                        fill="none" 
                        viewBox="0 0 24 24" 
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                  )}
                  
                  {passiveReconData.cookies && typeof passiveReconData.cookies === 'object' && Object.keys(passiveReconData.cookies).length > 0 && (
                    <button
                      onClick={toggleCookies}
                      className="px-3 py-1 text-xs bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 flex items-center"
                    >
                      <span>{showCookies ? "Hide" : "Show"} Cookies</span>
                      <svg 
                        className={`ml-1 w-4 h-4 transition-transform ${showCookies ? "rotate-180" : ""}`} 
                        fill="none" 
                        viewBox="0 0 24 24" 
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                  )}
                </div>
                
                {/* Discovered URLs */}
                {showUrls && passiveReconData.urls_discovered && Array.isArray(passiveReconData.urls_discovered) && passiveReconData.urls_discovered.length > 0 && (
                  <div className="mt-4 p-3 bg-white rounded-lg border border-gray-200 max-h-80 overflow-y-auto">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Discovered URLs ({passiveReconData.urls_discovered.length})</h4>
                    <ul className="text-xs space-y-1">
                      {passiveReconData.urls_discovered.map((url: string, idx: number) => (
                        <li key={idx} className="text-gray-700 hover:text-gray-900">
                          <a href={url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                            {url}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {/* Discovered Forms */}
                {showForms && passiveReconData.forms_discovered && Array.isArray(passiveReconData.forms_discovered) && passiveReconData.forms_discovered.length > 0 && (
                  <div className="mt-4 p-3 bg-white rounded-lg border border-gray-200 max-h-80 overflow-y-auto">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Discovered Forms ({passiveReconData.forms_discovered.length})</h4>
                    <div className="space-y-3">
                      {passiveReconData.forms_discovered.map((form: any, idx: number) => (
                        <div key={idx} className="p-2 border border-gray-100 rounded">
                          <div className="flex justify-between text-xs">
                            <span className="font-medium text-gray-700">URL: <a href={form.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{form.url}</a></span>
                            <span className={`px-1.5 py-0.5 rounded ${form.method === 'POST' ? 'bg-orange-100 text-orange-700' : 'bg-green-100 text-green-700'}`}>
                              {form.method || 'GET'}
                            </span>
                          </div>
                          <div className="mt-1 text-xs">
                            <span className="font-medium text-gray-700">Action: </span>
                            <span className="text-gray-600">{form.action || 'Current Page'}</span>
                          </div>
                          {form.inputs && form.inputs.length > 0 && (
                            <div className="mt-2">
                              <span className="text-xs font-medium text-gray-700">Fields:</span>
                              <div className="mt-1 grid grid-cols-1 md:grid-cols-2 gap-1">
                                {form.inputs.map((input: any, inputIdx: number) => (
                                  <div key={inputIdx} className="text-xs flex items-center">
                                    <span className={`px-1.5 rounded ${input.type === 'password' ? 'bg-red-100 text-red-700' : 'bg-blue-50 text-blue-700'}`}>
                                      {input.type || 'text'}
                                    </span>
                                    <span className="ml-1 text-gray-800">{input.name || 'unnamed'}</span>
                                    {input.required && (
                                      <span className="ml-1 text-red-500">*</span>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Cookies */}
                {showCookies && passiveReconData.cookies && typeof passiveReconData.cookies === 'object' && Object.keys(passiveReconData.cookies).length > 0 && (
                  <div className="mt-4 p-3 bg-white rounded-lg border border-gray-200 max-h-80 overflow-y-auto">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Cookies ({Object.keys(passiveReconData.cookies).length})</h4>
                    <table className="w-full border-collapse text-xs">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-2 py-1 text-left font-medium text-gray-700 border border-gray-200">Name</th>
                          <th className="px-2 py-1 text-left font-medium text-gray-700 border border-gray-200">Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(passiveReconData.cookies).map(([name, value], idx) => (
                          <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                            <td className="px-2 py-1 border border-gray-200 font-medium">
                              {name}
                            </td>
                            <td className="px-2 py-1 border border-gray-200 truncate max-w-xs">
                              {String(value)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* SSL Certificate Details */}
          {passiveReconData.server_info && 
           passiveReconData.server_info.ssl && 
           typeof passiveReconData.server_info.ssl === 'object' &&
           !passiveReconData.server_info.ssl.error && (
            <div className="mt-6">
              <h3 className="font-medium text-gray-700 mb-2">SSL/TLS Certificate</h3>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Protocol:</span>
                    <span className="ml-2 text-gray-600">{safeGetNestedValue(passiveReconData, 'server_info.ssl.protocol', 'Unknown')}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Cipher:</span>
                    <span className="ml-2 text-gray-600">{safeGetNestedValue(passiveReconData, 'server_info.ssl.cipher', 'Unknown')}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Issuer:</span>
                    <span className="ml-2 text-gray-600">
                      {typeof safeGetNestedValue(passiveReconData, 'server_info.ssl.issuer', {}) === 'object' 
                        ? safeGetNestedValue(passiveReconData, 'server_info.ssl.issuer.commonName', 'Unknown')
                        : 'Unknown'
                      }
                    </span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Valid Until:</span>
                    <span className="ml-2 text-gray-600">{safeGetNestedValue(passiveReconData, 'server_info.ssl.validity.not_after', 'Unknown')}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Vulnerabilities Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-800">Vulnerabilities</h2>
          
          {/* Severity filter */}
          <div className="flex items-center">
            <label htmlFor="severity-filter" className="mr-2 text-sm text-gray-700">
              Filter by severity:
            </label>
            <select
              id="severity-filter"
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="border border-gray-300 rounded-md text-sm p-1"
            >
              <option value="all">All ({vulnerabilities.length})</option>
              <option value="critical">Critical ({vulnerabilities.filter(v => v.severity === 'critical').length})</option>
              <option value="high">High ({vulnerabilities.filter(v => v.severity === 'high').length})</option>
              <option value="medium">Medium ({vulnerabilities.filter(v => v.severity === 'medium').length})</option>
              <option value="low">Low ({vulnerabilities.filter(v => v.severity === 'low').length})</option>
              <option value="info">Info ({vulnerabilities.filter(v => v.severity === 'info').length})</option>
            </select>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-10">
            <div className="inline-block animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
            <p className="mt-2 text-gray-600">Loading vulnerabilities...</p>
          </div>
        ) : filteredVulnerabilities.length === 0 ? (
          <div className="text-center py-10 border border-gray-100 rounded-lg bg-gray-50">
            <p className="text-gray-500">
              No vulnerabilities {severityFilter !== 'all' ? `with ${severityFilter} severity ` : ''}found.
            </p>
            {passiveReconData && (
              <p className="text-sm text-gray-400 mt-2 max-w-md mx-auto">
                Passive scans examine the target without active testing and might not detect all security issues.
                Consider running an active scan for more comprehensive results.
              </p>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredVulnerabilities.map((vuln) => (
              <div key={vuln.id} className="p-4 bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-medium text-gray-900">{vuln.name}</h3>
                    <p className="mt-1 text-sm text-gray-600">{vuln.description}</p>
                    {vuln.url && (
                      <p className="mt-2 text-xs text-gray-500">
                        <span className="font-medium">URL:</span> {vuln.url}
                      </p>
                    )}
                    {vuln.parameter && (
                      <p className="mt-1 text-xs text-gray-500">
                        <span className="font-medium">Parameter:</span> {vuln.parameter}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col items-end">
                    <span className={getSeverityBadgeClass(vuln.severity)}>
                      {vuln.severity.toUpperCase()}
                    </span>
                    <span className="mt-1 text-xs text-gray-500">
                      Confidence: {Math.round((vuln.confidence || 0) * 100)}%
                    </span>
                  </div>
                </div>
                
                {vuln.evidence && (
                  <div className="mt-3">
                    <h4 className="text-sm font-medium text-gray-900">Evidence</h4>
                    <pre className="mt-1 text-sm text-gray-600 bg-gray-50 p-2 rounded overflow-x-auto whitespace-pre-wrap">
                      {vuln.evidence}
                    </pre>
                  </div>
                )}
                
                {vuln.remediation && (
                  <div className="mt-3">
                    <h4 className="text-sm font-medium text-gray-900">Remediation</h4>
                    <p className="mt-1 text-sm text-gray-600">{vuln.remediation}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* HTTP Headers Section (if available) */}
      {passiveReconData?.response_headers && Object.keys(passiveReconData.response_headers).length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-800">HTTP Response Headers</h2>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Header</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {Object.entries(passiveReconData.response_headers).map(([header, value]) => (
                  <tr key={header} className="hover:bg-gray-50">
                    <td className="px-4 py-2 text-sm font-medium text-gray-700">{header}</td>
                    <td className="px-4 py-2 text-sm text-gray-500 break-all">{String(value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScanResults;