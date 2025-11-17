"""
Unified Scanning Engine

Orchestrates all types of security scanning operations:
- Passive scanning (reconnaissance)
- Active scanning (vulnerability testing)
- Comprehensive scanning (passive + active)
"""

import logging
import threading
import time
from typing import Dict
from django.utils import timezone

logger = logging.getLogger(__name__)


class UnifiedScanningEngine:
    """Unified scanning engine that handles all scan types"""

    def __init__(self, scan_id: int):
        self.scan_id = scan_id
        self.scan = None
        self.target_url = None
        self.configuration = None
        self._stop_event = threading.Event()  # Use Event instead of boolean for better responsiveness
        self._running_threads = []
        self._active_adapters = []
        self._start_time = None  # Track scan start time for timeout
        self._max_scan_duration = 3600  # Default: 1 hour timeout

    def start(self):
        """Start scanning based on configuration type"""
        try:
            # Record start time for timeout tracking
            self._start_time = time.time()

            # Register this engine with the tracker
            from scanning.scan_tracker import get_scan_tracker
            tracker = get_scan_tracker()
            tracker.register_scan(self.scan_id, self)

            # Lazy import to avoid circular dependencies
            from scanning.models.scan import Scan

            # Load scan details
            self.scan = Scan.objects.get(id=self.scan_id)
            self.target_url = self.scan.target_url or self.scan.configuration.project.target_url
            self.configuration = self.scan.configuration

            # Route to appropriate scanning engine based on scan type
            if self.configuration.scan_type == 'passive':
                result = self._run_passive_scan()
            elif self.configuration.scan_type == 'active':
                result = self._run_active_with_passive_scan()
            elif self.configuration.scan_type == 'comprehensive':
                result = self._run_comprehensive_scan()
            else:
                raise ValueError(f"Unsupported scan type: {self.configuration.scan_type}")

            # Unregister when done (if not already stopped)
            tracker.unregister_scan(self.scan_id)
            return result

        except Exception as e:
            logger.exception(f"Unified scan engine failed: {e}")
            self._fail_scan(str(e))
            return False

        finally:
            # CRITICAL: Always cleanup and unregister in finally block
            # This ensures the scan is removed from tracker even if there's an exception
            try:
                # Stop all adapters
                logger.info(f"Finally block: Cleaning up scan {self.scan_id}...")
                for adapter in self._active_adapters:
                    try:
                        if hasattr(adapter, 'stop_all_scans'):
                            adapter.stop_all_scans()
                            logger.debug(f"Finally block: Stopped adapter {type(adapter).__name__}")
                    except Exception as adapter_error:
                        logger.warning(f"Finally block: Error stopping adapter: {adapter_error}")
                
                # Always try to stop ZAP as final precaution
                try:
                    from scanning.active.zap_active_adapter import ZAPActiveAdapter
                    zap_adapter = ZAPActiveAdapter()
                    zap_adapter.stop_all_scans()
                    logger.info("Finally block: ZAP scans stopped")
                except Exception as zap_error:
                    logger.debug(f"Finally block: ZAP stop error (may not be running): {zap_error}")
                
                # Unregister from tracker
                from scanning.scan_tracker import get_scan_tracker
                get_scan_tracker().unregister_scan(self.scan_id)
                logger.info(f"Finally block: Scan {self.scan_id} unregistered from tracker")
                
            except Exception as cleanup_error:
                logger.error(f"Finally block cleanup error: {cleanup_error}")

    def _run_passive_scan(self):
        """Run passive scanning using existing passive engine"""
        try:
            logger.info(f"Starting passive scan for scan ID: {self.scan_id}")
            
            # Use the existing passive scanning engine
            from scanning.engine import PassiveScanningEngine
            
            passive_engine = PassiveScanningEngine(self.scan_id)
            success = passive_engine.start()
            
            if success:
                logger.info(f"Passive scan completed successfully for scan ID: {self.scan_id}")
            else:
                logger.error(f"Passive scan failed for scan ID: {self.scan_id}")
                
            return success
            
        except Exception as e:
            logger.exception(f"Error in passive scan: {e}")
            return False

    def _run_active_scan(self):
        """Run active scanning using active engine"""
        try:
            logger.info(f"Starting active scan for scan ID: {self.scan_id}")
            
            # Use the active scanning engine
            from scanning.active.engines.active_engine import ActiveScanningEngine
            
            active_engine = ActiveScanningEngine(self.scan_id)
            success = active_engine.start()
            
            if success:
                logger.info(f"Active scan completed successfully for scan ID: {self.scan_id}")
            else:
                logger.error(f"Active scan failed for scan ID: {self.scan_id}")
                
            return success
            
        except Exception as e:
            logger.exception(f"Error in active scan: {e}")
            return False

    def _run_active_with_passive_scan(self):
        """Run active scanning with passive reconnaissance phase first"""
        try:
            logger.info(f"Starting active scan with passive reconnaissance for scan ID: {self.scan_id}")
            
            # Update scan status
            self.scan.status = 'running'
            self.scan.start_time = timezone.now()
            self.scan.progress = 0.0
            self.scan.save()
            
            self._update_progress(5.0, "Starting active scan with passive reconnaissance")

            # Check for stop request
            if self.is_stop_requested():
                logger.info("Scan stop requested during initialization")
                return False

            # Phase 1: Passive reconnaissance (first 40% of progress)
            self._update_progress(10.0, "Running passive reconnaissance phase")
            passive_success = self._run_passive_phase()
            
            # Check for stop request
            if self.is_stop_requested():
                logger.info("Scan stop requested after passive phase")
                return False
            
            if not passive_success:
                logger.warning("Passive phase failed, but continuing with active phase")
            
            # Phase 2: Active scanning (next 50% of progress)  
            self._update_progress(45.0, "Running active vulnerability testing phase")
            active_success = self._run_active_phase()
            
            # Check for stop request
            if self.is_stop_requested():
                logger.info("Scan stop requested after active phase")
                return False
            
            if not active_success:
                logger.warning("Active phase failed")
            
            # Phase 3: Results integration (final 10%)
            self._update_progress(90.0, "Integrating and finalizing results")
            self._integrate_comprehensive_results()
            
            # Final stop check
            if self.is_stop_requested():
                logger.info("Scan stop requested during finalization")
                return False
            
            # Mark as completed
            self._complete_scan()
            self._update_progress(100.0, "Active scan with passive reconnaissance completed")
            
            # Return success if either phase succeeded
            overall_success = passive_success or active_success
            
            if overall_success:
                logger.info(f"Active scan with passive reconnaissance completed for scan ID: {self.scan_id}")
            else:
                logger.error(f"Both passive and active phases failed for scan ID: {self.scan_id}")
                
            return overall_success
            
        except Exception as e:
            logger.exception(f"Error in active scan with passive reconnaissance: {e}")
            self._fail_scan(str(e))
            return False

    def _run_comprehensive_scan(self):
        """Run comprehensive scanning (passive + active)"""
        try:
            logger.info(f"Starting comprehensive scan for scan ID: {self.scan_id}")
            
            # Update scan status
            self.scan.status = 'running'
            self.scan.start_time = timezone.now()
            self.scan.progress = 0.0
            self.scan.save()
            
            self._update_progress(5.0, "Starting comprehensive scan")

            # Check for stop request
            if self.is_stop_requested():
                logger.info("Scan stop requested during initialization")
                return False

            # Phase 1: Passive scanning (first 45% of progress)
            self._update_progress(10.0, "Running passive reconnaissance phase")
            passive_success = self._run_passive_phase()
            
            # Check for stop request
            if self.is_stop_requested():
                logger.info("Scan stop requested after passive phase")
                return False
            
            if not passive_success:
                logger.warning("Passive phase failed, but continuing with active phase")
            
            # Phase 2: Active scanning (next 45% of progress)  
            self._update_progress(50.0, "Running active vulnerability testing phase")
            active_success = self._run_active_phase()
            
            # Check for stop request
            if self.is_stop_requested():
                logger.info("Scan stop requested after active phase")
                return False
            
            if not active_success:
                logger.warning("Active phase failed")
            
            # Phase 3: Results integration (final 10%)
            self._update_progress(90.0, "Integrating and finalizing results")
            self._integrate_comprehensive_results()
            
            # Final stop check
            if self.is_stop_requested():
                logger.info("Scan stop requested during finalization")
                return False
            
            # Mark as completed
            self._complete_scan()
            self._update_progress(100.0, "Comprehensive scan completed")
            
            # Return success if either phase succeeded
            overall_success = passive_success or active_success
            
            if overall_success:
                logger.info(f"Comprehensive scan completed for scan ID: {self.scan_id}")
            else:
                logger.error(f"Both passive and active phases failed for scan ID: {self.scan_id}")
                
            return overall_success
            
        except Exception as e:
            logger.exception(f"Error in comprehensive scan: {e}")
            self._fail_scan(str(e))
            return False

    def _run_passive_phase(self):
        """Run the passive phase of comprehensive scanning"""
        try:
            # Check for stop request before starting
            if self.is_stop_requested():
                logger.info("Scan stop requested before passive phase")
                return False
                
            from scanning.passive.scanner import PassiveScanner
            
            # Create and run passive scanner
            scanner = PassiveScanner(
                self.scan_id,
                self.target_url,
                self.configuration
            )
            
            # Set progress callback for passive phase 
            # For comprehensive: maps 0-100% to 10-50% (40% range)
            # For active: maps 0-100% to 10-45% (35% range)  
            def passive_progress_callback(percent, message):
                # Check for stop request during progress updates
                if self.is_stop_requested():
                    return
                    
                if self.configuration.scan_type == 'comprehensive':
                    mapped_percent = 10 + (percent * 0.4)  # Map to 10-50%
                else:  # active scan
                    mapped_percent = 10 + (percent * 0.35)  # Map to 10-45%
                self._update_progress(mapped_percent, f"Passive: {message}")
            
            scanner.set_progress_callback(passive_progress_callback)
            
            # Check for stop request before running scan
            if self.is_stop_requested():
                logger.info("Scan stop requested before passive scan execution")
                return False
                
            passive_results = scanner.run_scan()
            
            # Check for stop request after scan completion
            if self.is_stop_requested():
                logger.info("Scan stop requested after passive scan completion")
                return False
            
            # Save passive results
            self._save_passive_results(passive_results)
            
            return True
            
        except Exception as e:
            logger.error(f"Passive phase failed: {e}")
            return False

    def _run_active_phase(self):
        """Run the active phase with enhanced discovery integration"""
        try:
            # Check for stop request before starting
            if self.is_stop_requested():
                logger.info("Scan stop requested before active phase")
                return False
                
            logger.info("Starting enhanced active phase with passive discovery integration")
            
            # Use the enhanced active scanning engine for ALL active scans
            from scanning.active.engines.active_engine import ActiveScanningEngine
            
            # Create enhanced active engine
            active_engine = ActiveScanningEngine(self.scan_id)
            
            # Register the active engine for proper cleanup
            self.register_adapter(active_engine)
            
            # Check for stop request before starting active scan
            if self.is_stop_requested():
                logger.info("Scan stop requested before active scan execution")
                return False
            
            # Run the enhanced active scan which includes:
            # - Passive discovery integration (loads enhanced discovery results)
            # - Enhanced discovery (multiple tools)
            # - URL and form discovery  
            # - API endpoint detection
            # - ZAP vulnerability testing
            success = active_engine.start()
            
            # Check for stop request after active scan completion
            if self.is_stop_requested():
                logger.info("Scan stop requested after active scan completion")
                return False
            
            if success:
                logger.info("Enhanced active phase completed successfully")
            else:
                logger.error("Enhanced active phase failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Enhanced active phase failed: {e}")
            # Fallback to basic ZAP only
            return self._run_basic_zap_active_phase()
    
    def _run_basic_zap_active_phase(self):
        """Fallback to basic ZAP-only active phase with passive discovery integration"""
        try:
            # Check for stop request before starting
            if self.is_stop_requested():
                logger.info("Scan stop requested before basic ZAP active phase")
                return False
                
            from scanning.active.zap_active_adapter import ZAPActiveAdapter
            
            # Create ZAP adapter with engine reference for stop checks
            zap_adapter = ZAPActiveAdapter(
                config=self.configuration,
                scan_id=self.scan_id,
                scan_logger=None,
                engine=self
            )
            
            # Register the ZAP adapter for proper cleanup
            self.register_adapter(zap_adapter)
            
            # Check ZAP connection
            if not zap_adapter.check_zap_connection():
                logger.error("ZAP not available for active phase")
                return False
            
            # Check for stop request before integrating discovery
            if self.is_stop_requested():
                logger.info("Scan stop requested before passive discovery integration")
                return False
            
            # Integrate passive discovery results with ZAP
            self._integrate_passive_discovery_with_zap_fallback(zap_adapter)
            
            # Check for stop request before running active scan
            if self.is_stop_requested():
                logger.info("Scan stop requested before active scan execution")
                return False
            
            # Run basic active scan
            active_results = zap_adapter.run_comprehensive_active_scan(self.target_url, self.configuration)
            
            # Check for stop request after active scan completion
            if self.is_stop_requested():
                logger.info("Scan stop requested after active scan completion")
                return False
            
            # Save active results
            self._save_active_results(active_results)
            
            return True
            
        except Exception as e:
            logger.error(f"Basic ZAP active phase failed: {e}")
            return False

    def _integrate_passive_discovery_with_zap_fallback(self, zap_adapter):
        """Integrate passive discovery results with ZAP fallback"""
        try:
            from scanning.models.scan import PassiveReconResult
            
            # Get passive recon results for this scan
            passive_results = PassiveReconResult.objects.get(scan_id=self.scan_id)
            enhanced_discovery = passive_results.enhanced_discovery or {}
            
            # Extract all discovered URLs
            all_urls = []
            
            # Add subdomains
            if enhanced_discovery.get("subdomains", {}).get("subdomains"):
                for subdomain in enhanced_discovery["subdomains"]["subdomains"]:
                    if subdomain.startswith('http'):
                        all_urls.append(subdomain)
                    else:
                        protocol = 'https' if self.target_url.startswith('https://') else 'http'
                        all_urls.append(f"{protocol}://{subdomain}")
            
            # Add wayback URLs
            if enhanced_discovery.get("wayback_urls", {}).get("urls"):
                all_urls.extend(enhanced_discovery["wayback_urls"]["urls"])
            
            # Add discovered directories
            if enhanced_discovery.get("directories", {}).get("directories"):
                for directory in enhanced_discovery["directories"]["directories"]:
                    if isinstance(directory, dict) and directory.get("url"):
                        all_urls.append(directory["url"])
                    elif isinstance(directory, str):
                        all_urls.append(directory)
            
            # Add API endpoints
            if enhanced_discovery.get("api_endpoints", {}).get("api_endpoints"):
                for endpoint in enhanced_discovery["api_endpoints"]["api_endpoints"]:
                    if isinstance(endpoint, dict) and endpoint.get("url"):
                        all_urls.append(endpoint["url"])
                    elif isinstance(endpoint, str):
                        all_urls.append(endpoint)
            
            # Remove duplicates
            unique_urls = list(set(all_urls))
            
            if unique_urls:
                logger.info(f"Integrating {len(unique_urls)} URLs from passive discovery with ZAP fallback")
                
                # Add each URL to ZAP context
                for url in unique_urls:
                    try:
                        result = zap_adapter._make_api_post_request("core/action/accessUrl", {"url": url})
                        if result and result.get("Result") == "OK":
                            logger.debug(f"Added URL to ZAP context: {url}")
                        else:
                            logger.warning(f"Failed to add URL to ZAP context: {url}")
                    except Exception as e:
                        logger.warning(f"Error adding URL {url} to ZAP context: {e}")
                        continue
                
                logger.info(f"Successfully integrated {len(unique_urls)} URLs with ZAP fallback")
            else:
                logger.info("No passive discovery URLs found for ZAP fallback integration")
                
        except PassiveReconResult.DoesNotExist:
            logger.warning(f"No passive recon results found for scan {self.scan_id}")
        except Exception as e:
            logger.error(f"Failed to integrate passive discovery with ZAP fallback: {e}")

    def _save_passive_results(self, results):
        """Save passive scan results"""
        try:
            from scanning.models.scan import PassiveReconResult, ScanLog
            from scanning.models.vulnerability import Vulnerability
            from scanning.utils.url_discovery_logger import URLDiscoveryLogger
            
            # Ensure scan object is loaded
            if self.scan is None:
                from scanning.models.scan import Scan
                self.scan = Scan.objects.get(id=self.scan_id)
            
            logger.info(f"Saving passive results with keys: {list(results.keys())}")
            logger.info(f"Enhanced discovery in results: {bool(results.get('enhanced_discovery'))}")
            
            # Save comprehensive results to PassiveReconResult
            recon_result, created = PassiveReconResult.objects.get_or_create(
                scan=self.scan,
                defaults={
                    'dns_records': results.get('dns_analysis', {}),
                    'server_info': results.get('target_info', {}),
                    'technologies': results.get('technology_detection', {}),
                    'response_headers': results.get('security_headers', {}),
                    'enhanced_discovery': results.get('enhanced_discovery', {}),
                }
            )
            
            # Update existing record if not created
            if not created:
                recon_result.dns_records = results.get('dns_analysis', {})
                recon_result.server_info = results.get('target_info', {})
                recon_result.technologies = results.get('technology_detection', {})
                recon_result.response_headers = results.get('security_headers', {})
                recon_result.enhanced_discovery = results.get('enhanced_discovery', {})
                recon_result.save()
            
            logger.info(f"Passive results saved successfully. Enhanced discovery: {bool(recon_result.enhanced_discovery)}")
            
            # Log URL discoveries to files
            try:
                url_logger = URLDiscoveryLogger(self.scan_id, self.target_url)
                url_logger.log_url_discoveries(results, "passive")
                logger.info("URL discoveries logged to files for passive scan")
            except Exception as e:
                logger.error(f"Failed to log URL discoveries for passive scan: {e}")
            
            # Save passive vulnerabilities with deduplication
            vulnerabilities = results.get('vulnerabilities', [])
            saved_count = 0
            for vuln_data in vulnerabilities:
                try:
                    vuln, created = Vulnerability.objects.get_or_create(
                        scan=self.scan,
                        name=vuln_data.get('type', 'Unknown Vulnerability'),
                        url=vuln_data.get('url', self.target_url),
                        defaults={
                            'description': vuln_data.get('description', 'No description available'),
                            'severity': vuln_data.get('severity', 'low'),
                            'parameter': vuln_data.get('parameter', ''),
                            'evidence': str(vuln_data.get('details', '')),
                            'confidence': vuln_data.get('confidence', 1.0),
                            'remediation': vuln_data.get('remediation', '')
                        }
                    )
                    if created:
                        saved_count += 1
                    else:
                        logger.debug(f"Vulnerability already exists: {vuln.name} for {vuln.url}")
                except Exception as e:
                    logger.error(f"Failed to save passive vulnerability: {e}")
                    
            logger.info(f"Saved {saved_count} new passive vulnerabilities ({len(vulnerabilities) - saved_count} already existed)")
            
        except Exception as e:
            logger.error(f"Failed to save passive results: {e}")
            logger.error(f"Enhanced discovery data type: {type(results.get('enhanced_discovery'))}")
            logger.error(f"Enhanced discovery data: {results.get('enhanced_discovery')}")
            import traceback
            logger.error(f"Passive results save traceback: {traceback.format_exc()}")

    def _save_active_results(self, results):
        """Save active scan results"""
        try:
            from scanning.models.scan import ActiveScanResult
            from scanning.models.vulnerability import Vulnerability
            from scanning.utils.url_discovery_logger import URLDiscoveryLogger
            
            # Save comprehensive results to ActiveScanResult
            active_result, created = ActiveScanResult.objects.get_or_create(
                scan=self.scan,
                defaults={
                    'spider_results': self._optimize_spider_data(results.get('spider_results', {})),
                    'ajax_spider_results': self._optimize_ajax_data(results.get('ajax_spider_results', {})),
                    'raw_findings': results.get('active_scan_results', {}),
                    'urls_discovered': self._extract_urls_from_results(results),
                }
            )
            
            # Log URL discoveries to files
            try:
                url_logger = URLDiscoveryLogger(self.scan_id, self.target_url)
                url_logger.log_url_discoveries(results, "active")
                logger.info("URL discoveries logged to files for active scan")
            except Exception as e:
                logger.error(f"Failed to log URL discoveries for active scan: {e}")
            
            # Save active vulnerabilities with deduplication
            vulnerabilities = results.get('vulnerability_details', [])
            for vuln_data in vulnerabilities:
                try:
                    vuln, created = Vulnerability.objects.get_or_create(
                        scan=self.scan,
                        name=vuln_data.get('name', 'Unknown Vulnerability'),
                        url=vuln_data.get('url', self.target_url),
                        defaults={
                            'description': vuln_data.get('description', 'No description available'),
                            'severity': vuln_data.get('severity', 'low'),
                            'parameter': vuln_data.get('parameter', ''),
                            'evidence': vuln_data.get('evidence', ''),
                            'confidence': vuln_data.get('confidence', 1.0),
                            'remediation': vuln_data.get('solution', '')
                        }
                    )
                    if not created:
                        logger.debug(f"Vulnerability already exists: {vuln.name} for {vuln.url}")
                except Exception as e:
                    logger.error(f"Failed to save active vulnerability: {e}")
                    
            logger.info(f"Saved {len(vulnerabilities)} active vulnerabilities")
            
        except Exception as e:
            logger.error(f"Failed to save active results: {e}")

    def _extract_urls_from_results(self, results):
        """Extract discovered URLs from active scan results"""
        urls = []
        
        # Extract from spider results
        spider_urls = results.get('spider_results', {}).get('urls', [])
        urls.extend(spider_urls)
        
        # Extract from AJAX spider results
        ajax_urls = results.get('ajax_spider_results', {}).get('urls', [])
        urls.extend(ajax_urls)
        
        # Clean malformed URLs
        cleaned_urls = []
        for url in urls:
            cleaned_url = self._clean_malformed_url(url)
            if cleaned_url:
                cleaned_urls.append(cleaned_url)
        
        return list(set(cleaned_urls))  # Remove duplicates

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
            
            logger.debug(f"Cleaned malformed URL: {url[:60]}... -> {cleaned_url[:60]}...")
            return cleaned_url
        
        # Fix URLs that have malformed domains with https: in the middle
        # e.g., www.domain.comhttps://www.domain.com/path
        malformed_domain_pattern = r'^([^/]+)(https?://)([^/]+)(.*)$'
        match = re.match(malformed_domain_pattern, url)
        
        if match:
            domain_part, protocol, correct_domain, path = match.groups()
            cleaned_url = f"{protocol}{correct_domain}{path}"
            logger.debug(f"Cleaned malformed domain URL: {url[:60]}... -> {cleaned_url[:60]}...")
            return cleaned_url
        
        # Return original URL if no malformation detected
        return url

    def _optimize_spider_data(self, spider_data: Dict) -> Dict:
        """Optimize spider data - keep all discovery data but remove response bodies"""
        if not spider_data or not isinstance(spider_data, dict):
            return {}

        # Keep ALL discovery data but optimize heavy content
        optimized = {
            "summary": {
                "total_urls": len(spider_data.get("urls", [])),
                "total_forms": len(spider_data.get("forms", [])),
                "total_parameters": len(spider_data.get("parameters", [])),
                "total_endpoints": len(spider_data.get("endpoints", [])),
                "optimized": True
            },
            # Keep ALL discovered URLs - these are lightweight
            "urls": spider_data.get("urls", []),
            # Keep ALL forms - essential for attack surface mapping
            "forms": spider_data.get("forms", []),
            # Keep ALL parameters - important for input validation testing
            "parameters": spider_data.get("parameters", []),
            # Keep ALL endpoints - crucial for API analysis
            "endpoints": spider_data.get("endpoints", []),
            # Keep scan metadata
            "scan_id": spider_data.get("scan_id")
        }

        return optimized

    def _optimize_ajax_data(self, ajax_data: Dict) -> Dict:
        """Optimize AJAX spider data - keep all discovery data but remove heavy response bodies"""
        if not ajax_data or not isinstance(ajax_data, dict):
            return {}

        # Keep ALL discovery data but optimize heavy content
        optimized = {
            "summary": {
                "total_urls": len(ajax_data.get("urls", [])),
                "total_ajax_requests": len(ajax_data.get("ajax_requests", [])),
                "total_js_files": len(ajax_data.get("js_files", [])),
                "total_api_endpoints": len(ajax_data.get("api_endpoints", [])),
                "total_forms": len(ajax_data.get("forms", [])),
                "optimized": True
            },
            # Keep ALL discovered URLs - these are lightweight
            "urls": ajax_data.get("urls", []),
            # Keep ALL forms - essential for attack surface mapping
            "forms": ajax_data.get("forms", []),
            # Keep ALL API endpoints - crucial for security analysis
            "api_endpoints": ajax_data.get("api_endpoints", []),
            # Keep ALL JS files - important for modern web app analysis
            "js_files": ajax_data.get("js_files", []),
            # Optimize AJAX requests - keep essential info but remove response bodies
            "ajax_requests": self._optimize_ajax_requests(ajax_data.get("ajax_requests", []))
        }

        return optimized

    def _optimize_ajax_requests(self, ajax_requests: list) -> list:
        """Optimize AJAX requests by keeping essential data but removing large response bodies"""
        optimized_requests = []

        for request in ajax_requests:
            if not isinstance(request, dict):
                continue

            # Keep essential request info but remove response body
            optimized_request = {
                "url": request.get("url"),
                "method": request.get("method", "GET"),
                "content_type": request.get("content_type"),
                "type": request.get("type"),
                # Keep response metadata but not the full body
                "response_size": len(str(request.get("response_body", ""))) if request.get("response_body") else 0,
                "response_type": request.get("response_type"),
                "status_code": request.get("status_code"),
                # Remove the actual response_body to save space
                # "response_body": "... removed to save space ..."  # Don't store this
            }
            optimized_requests.append(optimized_request)

        return optimized_requests

    def _integrate_comprehensive_results(self):
        """Integrate results from both passive and active phases"""
        try:
            # This is where you could apply ML algorithms to:
            # 1. Deduplicate vulnerabilities
            # 2. Cross-reference findings
            # 3. Enhance confidence scores
            # 4. Reduce false positives
            
            from scanning.models.scan import ScanLog
            from scanning.utils.url_discovery_logger import URLDiscoveryLogger
            
            # Get total vulnerability count
            total_vulns = self.scan.vulnerabilities.count()
            
            # Log comprehensive scan summary with all discovered URLs
            try:
                # Collect all discovered URLs from both phases
                comprehensive_results = {
                    'enhanced_discovery': {},
                    'spider_results': {},
                    'ajax_spider_results': {},
                    'urls_discovered': []
                }
                
                # Get passive results
                try:
                    from scanning.models.scan import PassiveReconResult
                    passive_result = PassiveReconResult.objects.get(scan=self.scan)
                    comprehensive_results['enhanced_discovery'] = passive_result.enhanced_discovery or {}
                except PassiveReconResult.DoesNotExist:
                    logger.warning("No passive results found for comprehensive integration")
                
                # Get active results
                try:
                    from scanning.models.scan import ActiveScanResult
                    active_result = ActiveScanResult.objects.get(scan=self.scan)
                    comprehensive_results['spider_results'] = active_result.spider_results or {}
                    comprehensive_results['ajax_spider_results'] = active_result.ajax_spider_results or {}
                    comprehensive_results['urls_discovered'] = active_result.urls_discovered or []
                except ActiveScanResult.DoesNotExist:
                    logger.warning("No active results found for comprehensive integration")
                
                # Log comprehensive URL discoveries
                url_logger = URLDiscoveryLogger(self.scan_id, self.target_url)
                url_logger.log_url_discoveries(comprehensive_results, "comprehensive")
                
                # Log scan summary
                scan_summary = {
                    'vulnerabilities': list(self.scan.vulnerabilities.values()),
                    'urls_discovered': comprehensive_results.get('urls_discovered', []),
                    'forms': comprehensive_results.get('spider_results', {}).get('forms', []),
                    'parameters': comprehensive_results.get('spider_results', {}).get('parameters', [])
                }
                url_logger.log_scan_summary(scan_summary, "comprehensive")
                
                logger.info("Comprehensive URL discoveries and scan summary logged to files")
                
            except Exception as e:
                logger.error(f"Failed to log comprehensive URL discoveries: {e}")
            
            ScanLog.objects.create(
                scan=self.scan,
                level='INFO',
                message=f"Comprehensive scan integration completed. Total vulnerabilities: {total_vulns}"
            )
            
            logger.info(f"Comprehensive scan integration completed for scan {self.scan_id}")
            
        except Exception as e:
            logger.error(f"Failed to integrate comprehensive results: {e}")

    def _complete_scan(self):
        """Mark scan as completed"""
        try:
            # CRITICAL: Stop all running scans and cleanup resources BEFORE marking as complete
            # This prevents ZAP AJAX spider from continuing to run
            logger.info("Stopping all running scans and cleaning up resources...")
            
            # Stop all active adapters
            for adapter in self._active_adapters:
                try:
                    if hasattr(adapter, 'stop_all_scans'):
                        adapter.stop_all_scans()
                        logger.info(f"Stopped all scans for adapter: {type(adapter).__name__}")
                except Exception as e:
                    logger.warning(f"Error stopping adapter {type(adapter).__name__}: {e}")
            
            # Also try to stop ZAP directly as a precaution
            try:
                from scanning.active.zap_active_adapter import ZAPActiveAdapter
                zap_adapter = ZAPActiveAdapter()
                zap_adapter.stop_all_scans()
                logger.info("ZAP scans stopped directly")
            except Exception as e:
                logger.warning(f"Error stopping ZAP scans directly: {e}")
            
            # Now mark as complete
            self.scan.status = 'completed'
            self.scan.end_time = timezone.now()
            self.scan.progress = 100.0
            self.scan.save()

            from scanning.models.scan import ScanLog
            ScanLog.objects.create(
                scan=self.scan,
                level='INFO',
                message="Scan completed successfully"
            )

            logger.info(f"Scan {self.scan_id} completed successfully")

        except Exception as e:
            logger.error(f"Error completing scan: {e}")

    def _fail_scan(self, error_message: str):
        """Mark scan as failed with error message"""
        if not self.scan:
            return
            
        try:
            # CRITICAL: Stop all running scans and cleanup resources BEFORE marking as failed
            # This prevents ZAP AJAX spider from continuing to run
            logger.info("Stopping all running scans before marking as failed...")
            
            # Stop all active adapters
            for adapter in self._active_adapters:
                try:
                    if hasattr(adapter, 'stop_all_scans'):
                        adapter.stop_all_scans()
                        logger.info(f"Stopped all scans for adapter: {type(adapter).__name__}")
                except Exception as e:
                    logger.warning(f"Error stopping adapter {type(adapter).__name__}: {e}")
            
            # Also try to stop ZAP directly as a precaution
            try:
                from scanning.active.zap_active_adapter import ZAPActiveAdapter
                zap_adapter = ZAPActiveAdapter()
                zap_adapter.stop_all_scans()
                logger.info("ZAP scans stopped directly")
            except Exception as e:
                logger.warning(f"Error stopping ZAP scans directly: {e}")
            
            # Now mark as failed
            self.scan.status = 'failed'
            self.scan.error_message = error_message
            self.scan.end_time = timezone.now()
            self.scan.save()
            
            from scanning.models.scan import ScanLog
            ScanLog.objects.create(
                scan=self.scan,
                level='ERROR',
                message=f"Scan failed: {error_message}"
            )
            
            logger.error(f"Scan {self.scan_id} failed: {error_message}")
            
        except Exception as e:
            logger.error(f"Error failing scan: {e}")

    def _update_progress(self, percent: float, message: str):
        """Update scan progress and log message"""
        try:
            if self.scan:
                # Refresh scan object to avoid stale data
                self.scan.refresh_from_db()
                
                # Ensure progress only moves forward (never decreases)
                current_progress = self.scan.progress
                if percent < current_progress:
                    logger.warning(f"Progress would decrease from {current_progress}% to {percent}%, keeping current progress")
                    percent = current_progress
                
                # Update progress
                self.scan.progress = percent
                self.scan.save(update_fields=['progress', 'updated_at'])
                
                # Create log entry
                from scanning.models.scan import ScanLog
                ScanLog.objects.create(
                    scan=self.scan,
                    level='INFO',
                    message=f"{percent:.1f}% - {message}"
                )
            
            logger.info(f"Scan {self.scan_id}: {percent:.1f}% - {message}")
            
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")

    def stop_scan(self):
        """Stop the running scan and all associated processes"""
        try:
            logger.info(f"⛔ Stopping scan {self.scan_id} - User requested stop")

            # Set the stop event immediately (allows monitoring loops to exit)
            self._stop_event.set()

            # STEP 1: Update scan status to 'stopping' immediately
            logger.info("🔴 STEP 1: Marking scan as 'stopping' in database...")
            if self.scan:
                try:
                    self.scan.refresh_from_db()
                    if self.scan.status == 'running':
                        self.scan.status = 'stopping'
                        self.scan.save(update_fields=['status', 'updated_at'])
                        logger.info(f"✅ Scan {self.scan_id} marked as 'stopping' in database")
                except Exception as e:
                    logger.warning(f"⚠️ Error updating status to 'stopping': {e}")

            # STEP 2: Wait briefly for monitoring loops to detect stop event
            logger.info("🔴 STEP 2: Waiting for monitoring loops to detect stop event...")
            time.sleep(2)  # Give loops time to check event and exit gracefully

            # STEP 3: Aggressively stop ZAP FIRST before anything else
            # This is the most important step to prevent AJAX spider from continuing
            logger.info("🔴 STEP 3: Aggressively stopping ZAP (AJAX spider, traditional spider, active scan)...")
            try:
                from scanning.active.zap_active_adapter import ZAPActiveAdapter
                zap_adapter = ZAPActiveAdapter()
                zap_adapter.stop_all_scans()
                logger.info("✅ ZAP scans stopped successfully")
            except Exception as e:
                logger.error(f"❌ Error stopping ZAP scans: {e}")

            # STEP 4: Stop all active adapters (may include ZAP adapter with session)
            logger.info("🔴 STEP 4: Stopping all registered adapters...")
            for adapter in self._active_adapters:
                try:
                    if hasattr(adapter, 'stop_all_scans'):
                        adapter.stop_all_scans()
                        logger.info(f"✅ Stopped adapter (stop_all_scans): {type(adapter).__name__}")
                    elif hasattr(adapter, 'stop'):
                        adapter.stop()
                        logger.info(f"✅ Stopped adapter (stop): {type(adapter).__name__}")
                except Exception as e:
                    logger.warning(f"⚠️ Error stopping adapter {type(adapter).__name__}: {e}")

            # STEP 5: Extra precaution - stop ZAP again with fresh instance
            logger.info("🔴 STEP 5: Stopping ZAP again as extra precaution...")
            try:
                from scanning.active.zap_active_adapter import ZAPActiveAdapter
                fresh_zap = ZAPActiveAdapter()
                fresh_zap.stop_all_scans()
                logger.info("✅ ZAP scans stopped again (fresh instance)")
            except Exception as e:
                logger.warning(f"⚠️ Second ZAP stop attempt error: {e}")

            # STEP 6: Try Docker-level stop as last resort
            logger.info("🔴 STEP 6: Attempting Docker-level stop as last resort...")
            try:
                self._docker_level_stop()
                logger.info("✅ Docker-level stop completed")
            except Exception as e:
                logger.warning(f"⚠️ Docker-level stop error: {e}")

            # STEP 7: Verify ZAP actually stopped, update scan status in database
            logger.info("🔴 STEP 7: Verifying ZAP stopped and updating scan status...")
            zap_stopped = self._verify_zap_stopped()

            if self.scan:
                try:
                    self.scan.refresh_from_db()
                    self.scan.status = 'stopped'
                    self.scan.end_time = timezone.now()
                    self.scan.save()

                    from scanning.models.scan import ScanLog
                    status_msg = "Scan stopped by user" + (" (ZAP verified stopped)" if zap_stopped else " (ZAP may still be running)")
                    ScanLog.objects.create(
                        scan=self.scan,
                        level='INFO',
                        message=status_msg
                    )

                    logger.info(f"✅ Scan {self.scan_id} marked as stopped in database")
                except Exception as e:
                    logger.error(f"❌ Error updating scan status: {e}")

            # STEP 8: Unregister from tracker (only after database update)
            logger.info("🔴 STEP 8: Unregistering scan from tracker...")
            try:
                from scanning.scan_tracker import get_scan_tracker
                get_scan_tracker().unregister_scan(self.scan_id)
                logger.info(f"✅ Scan {self.scan_id} unregistered from tracker")
            except Exception as e:
                logger.warning(f"⚠️ Error unregistering scan from tracker: {e}")

            logger.info(f"✅✅✅ Scan {self.scan_id} stopped successfully - All 8 steps completed")
            return True

        except Exception as e:
            logger.error(f"❌ Error stopping scan: {e}")
            return False

    def _docker_level_stop(self):
        """Attempt to stop ZAP processes at Docker container level"""
        try:
            import subprocess

            # Try to kill Firefox/Chrome processes (AJAX spider browsers)
            logger.info("Attempting to kill AJAX spider browser processes in ZAP container...")
            try:
                subprocess.run(
                    ["docker", "exec", "zap", "pkill", "-f", "firefox"],
                    capture_output=True,
                    timeout=5
                )
                logger.info("Sent kill signal to firefox processes")
            except Exception as e:
                logger.debug(f"Firefox kill failed (may not be running): {e}")

            try:
                subprocess.run(
                    ["docker", "exec", "zap", "pkill", "-f", "chrome"],
                    capture_output=True,
                    timeout=5
                )
                logger.info("Sent kill signal to chrome processes")
            except Exception as e:
                logger.debug(f"Chrome kill failed (may not be running): {e}")

        except Exception as e:
            logger.warning(f"Docker-level stop failed: {e}")

    def _verify_zap_stopped(self) -> bool:
        """Verify that ZAP scans have actually stopped"""
        try:
            from scanning.active.zap_active_adapter import ZAPActiveAdapter
            zap_adapter = ZAPActiveAdapter()

            # Check AJAX spider status
            ajax_status = zap_adapter._make_api_request("ajaxSpider/view/status")
            if ajax_status:
                status = ajax_status.get("status", "").lower()
                if status != "stopped":
                    logger.warning(f"⚠️ AJAX spider still running with status: {status}")
                    return False

            # Check active scan status
            active_scans = zap_adapter._make_api_request("ascan/view/scans")
            if active_scans and active_scans.get("scans"):
                for scan in active_scans["scans"]:
                    if scan.get("state") == "running":
                        logger.warning(f"⚠️ Active scan still running: {scan.get('id')}")
                        return False

            logger.info("✅ Verified: All ZAP scans stopped")
            return True

        except Exception as e:
            logger.warning(f"Could not verify ZAP stopped: {e}")
            return False

    def is_stop_requested(self):
        """Check if stop has been requested"""
        # Check event (fast, non-blocking)
        if self._stop_event.is_set():
            return True

        # Also check for scan timeout
        if self._start_time and self._max_scan_duration:
            elapsed = time.time() - self._start_time
            if elapsed > self._max_scan_duration:
                logger.warning(f"Scan {self.scan_id} exceeded timeout ({elapsed:.0f}s > {self._max_scan_duration}s)")
                self._stop_event.set()  # Trigger stop
                return True

        return False
    
    def register_adapter(self, adapter):
        """Register an active adapter for proper cleanup"""
        self._active_adapters.append(adapter)
        logger.debug(f"Registered adapter: {type(adapter).__name__}")
    
    def register_thread(self, thread):
        """Register a running thread for proper cleanup"""
        self._running_threads.append(thread)
        logger.debug(f"Registered thread: {thread.name}")
    
    def cleanup_resources(self):
        """Clean up all registered resources"""
        try:
            # Stop all adapters
            for adapter in self._active_adapters:
                try:
                    if hasattr(adapter, 'cleanup'):
                        adapter.cleanup()
                except Exception as e:
                    logger.warning(f"Error cleaning up adapter {type(adapter).__name__}: {e}")
            
            # Clear registered resources
            self._active_adapters.clear()
            self._running_threads.clear()
            
            logger.info(f"Cleaned up resources for scan {self.scan_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up resources: {e}")