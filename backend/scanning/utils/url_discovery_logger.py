"""
URL Discovery Logger Utility

Handles logging of discovered URLs to the logs directory after scans.
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class URLDiscoveryLogger:
    """Utility class for logging URL discoveries to files"""
    
    def __init__(self, scan_id: int, target_url: str):
        self.scan_id = scan_id
        self.target_url = target_url
        self.logs_dir = self._get_logs_directory()
        
    def _get_logs_directory(self) -> str:
        """Get the logs directory path"""
        # Use the backend logs directory
        logs_dir = os.path.join(settings.BASE_DIR, 'logs')
        
        # Create logs directory if it doesn't exist
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create scan-specific subdirectory
        scan_logs_dir = os.path.join(logs_dir, f'scan_{self.scan_id}')
        os.makedirs(scan_logs_dir, exist_ok=True)
        
        return scan_logs_dir
    
    def log_url_discoveries(self, discovery_data: Dict[str, Any], scan_type: str = "unknown"):
        """
        Log URL discoveries to a JSON file
        
        Args:
            discovery_data: Dictionary containing discovered URLs and metadata
            scan_type: Type of scan (passive, active, comprehensive)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"url_discoveries_{scan_type}_{timestamp}.json"
            filepath = os.path.join(self.logs_dir, filename)
            
            # Prepare the data structure
            log_data = {
                "scan_info": {
                    "scan_id": self.scan_id,
                    "target_url": self.target_url,
                    "scan_type": scan_type,
                    "timestamp": datetime.now().isoformat(),
                    "total_urls_discovered": 0
                },
                "discovered_urls": {
                    "all_urls": [],
                    "subdomains": [],
                    "wayback_urls": [],
                    "directories": [],
                    "api_endpoints": [],
                    "forms": [],
                    "parameters": []
                },
                "metadata": {
                    "discovery_sources": [],
                    "tools_used": [],
                    "scan_duration": None
                }
            }
            
            # Extract URLs from various sources
            all_urls = []
            
            # Extract from enhanced discovery
            enhanced_discovery = discovery_data.get('enhanced_discovery', {})
            if enhanced_discovery:
                # Subdomains
                subdomains = enhanced_discovery.get('subdomains', {}).get('subdomains', [])
                log_data["discovered_urls"]["subdomains"] = subdomains
                all_urls.extend(subdomains)
                
                # Wayback URLs
                wayback_urls = enhanced_discovery.get('wayback_urls', {}).get('urls', [])
                log_data["discovered_urls"]["wayback_urls"] = wayback_urls
                all_urls.extend(wayback_urls)
                
                # Directories
                directories = enhanced_discovery.get('directories', {}).get('directories', [])
                log_data["discovered_urls"]["directories"] = directories
                for directory in directories:
                    if isinstance(directory, dict) and directory.get('url'):
                        all_urls.append(directory['url'])
                    elif isinstance(directory, str):
                        all_urls.append(directory)
                
                # API endpoints
                api_endpoints = enhanced_discovery.get('api_endpoints', {}).get('api_endpoints', [])
                log_data["discovered_urls"]["api_endpoints"] = api_endpoints
                for endpoint in api_endpoints:
                    if isinstance(endpoint, dict) and endpoint.get('url'):
                        all_urls.append(endpoint['url'])
                    elif isinstance(endpoint, str):
                        all_urls.append(endpoint)
            
            # Extract from spider results (active scans)
            spider_results = discovery_data.get('spider_results', {})
            if spider_results:
                spider_urls = spider_results.get('urls', [])
                all_urls.extend(spider_urls)
                
                # Forms
                forms = spider_results.get('forms', [])
                log_data["discovered_urls"]["forms"] = forms
                
                # Parameters
                parameters = spider_results.get('parameters', [])
                log_data["discovered_urls"]["parameters"] = parameters
            
            # Extract from AJAX spider results
            ajax_results = discovery_data.get('ajax_spider_results', {})
            if ajax_results:
                ajax_urls = ajax_results.get('urls', [])
                all_urls.extend(ajax_urls)
            
            # Extract from URLs discovered field
            urls_discovered = discovery_data.get('urls_discovered', [])
            if urls_discovered:
                all_urls.extend(urls_discovered)
            
            # Clean and deduplicate URLs
            cleaned_urls = self._clean_and_deduplicate_urls(all_urls)
            log_data["discovered_urls"]["all_urls"] = cleaned_urls
            log_data["scan_info"]["total_urls_discovered"] = len(cleaned_urls)
            
            # Add metadata
            log_data["metadata"]["discovery_sources"] = self._identify_discovery_sources(discovery_data)
            log_data["metadata"]["tools_used"] = self._identify_tools_used(discovery_data)
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"URL discoveries logged to {filepath} - {len(cleaned_urls)} URLs discovered")
            
            # Also create a simple text file with just the URLs for easy access
            self._create_urls_text_file(cleaned_urls, scan_type, timestamp)
            
        except Exception as e:
            logger.error(f"Failed to log URL discoveries: {e}")
    
    def _clean_and_deduplicate_urls(self, urls: List[str]) -> List[str]:
        """Clean and deduplicate URLs"""
        cleaned_urls = []
        seen = set()
        
        for url in urls:
            if not url or not isinstance(url, str):
                continue
                
            # Clean malformed URLs
            cleaned_url = self._clean_malformed_url(url)
            if cleaned_url and cleaned_url not in seen:
                cleaned_urls.append(cleaned_url)
                seen.add(cleaned_url)
        
        return sorted(cleaned_urls)
    
    def _clean_malformed_url(self, url: str) -> str:
        """Clean malformed URLs that have double protocols or domains"""
        if not url or not isinstance(url, str):
            return ""
        
        # Fix double protocol issue: http://domainhttps://domain/path -> https://domain/path
        import re
        
        # Pattern to match double protocol URLs
        double_protocol_pattern = r'^(https?://)([^/]+)(https?://)([^/]+)(.*)$'
        match = re.match(double_protocol_pattern, url)
        
        if match:
            # Use the second protocol and domain (usually the correct one)
            protocol1, domain1, protocol2, domain2, path = match.groups()
            
            # Prefer https over http
            if protocol2 == 'https://':
                cleaned_url = f"{protocol2}{domain2}{path}"
            else:
                cleaned_url = f"{protocol1}{domain1}{path}"
            
            return cleaned_url
        
        # Fix URLs that have malformed domains with https: in the middle
        # e.g., www.domain.comhttps://www.domain.com/path
        malformed_domain_pattern = r'^([^/]+)(https?://)([^/]+)(.*)$'
        match = re.match(malformed_domain_pattern, url)
        
        if match:
            domain_part, protocol, correct_domain, path = match.groups()
            cleaned_url = f"{protocol}{correct_domain}{path}"
            return cleaned_url
        
        # Return original URL if no malformation detected
        return url
    
    def _identify_discovery_sources(self, discovery_data: Dict[str, Any]) -> List[str]:
        """Identify which discovery sources were used"""
        sources = []
        
        if discovery_data.get('enhanced_discovery'):
            sources.append('enhanced_discovery')
        if discovery_data.get('spider_results'):
            sources.append('zap_spider')
        if discovery_data.get('ajax_spider_results'):
            sources.append('zap_ajax_spider')
        if discovery_data.get('urls_discovered'):
            sources.append('manual_discovery')
        
        return sources
    
    def _identify_tools_used(self, discovery_data: Dict[str, Any]) -> List[str]:
        """Identify which tools were used for discovery"""
        tools = []
        
        enhanced_discovery = discovery_data.get('enhanced_discovery', {})
        if enhanced_discovery.get('subdomains'):
            tools.append('subdomain_enumeration')
        if enhanced_discovery.get('wayback_urls'):
            tools.append('wayback_machine')
        if enhanced_discovery.get('directories'):
            tools.append('directory_discovery')
        if enhanced_discovery.get('api_endpoints'):
            tools.append('api_discovery')
        
        if discovery_data.get('spider_results'):
            tools.append('zap_spider')
        if discovery_data.get('ajax_spider_results'):
            tools.append('zap_ajax_spider')
        
        return tools
    
    def _create_urls_text_file(self, urls: List[str], scan_type: str, timestamp: str):
        """Create a simple text file with just the URLs"""
        try:
            filename = f"discovered_urls_{scan_type}_{timestamp}.txt"
            filepath = os.path.join(self.logs_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# URL Discoveries for Scan {self.scan_id}\n")
                f.write(f"# Target: {self.target_url}\n")
                f.write(f"# Scan Type: {scan_type}\n")
                f.write(f"# Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"# Total URLs: {len(urls)}\n\n")
                
                for i, url in enumerate(urls, 1):
                    f.write(f"{i:4d}. {url}\n")
            
            logger.info(f"URL list saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to create URLs text file: {e}")
    
    def log_scan_summary(self, scan_results: Dict[str, Any], scan_type: str):
        """Log a summary of the entire scan"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scan_summary_{scan_type}_{timestamp}.json"
            filepath = os.path.join(self.logs_dir, filename)
            
            summary_data = {
                "scan_info": {
                    "scan_id": self.scan_id,
                    "target_url": self.target_url,
                    "scan_type": scan_type,
                    "timestamp": datetime.now().isoformat()
                },
                "results_summary": {
                    "vulnerabilities_found": len(scan_results.get('vulnerabilities', [])),
                    "urls_discovered": len(scan_results.get('urls_discovered', [])),
                    "forms_discovered": len(scan_results.get('forms', [])),
                    "parameters_discovered": len(scan_results.get('parameters', []))
                },
                "scan_status": "completed"
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Scan summary logged to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to log scan summary: {e}")


