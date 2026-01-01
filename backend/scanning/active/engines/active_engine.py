"""
Active Scanning Engine

Orchestrates active security scanning operations using ZAP and other tools.
Handles the complete active scanning workflow from discovery to vulnerability detection.
"""

import logging
from django.utils import timezone
from scanning.active.zap_active_adapter import ZAPActiveAdapter
from scanning.active.enhanced_discovery import ZAPEnhancedAdapter
from scanning.utils.url_parser import is_same_domain
from scanning.utils.scan_logger import create_scan_logger

logger = logging.getLogger(__name__)


class ActiveScanningEngine:
    """Active scanning engine for comprehensive vulnerability testing"""

    def __init__(self, scan_id: int, progress_range: tuple = (0.0, 100.0)):
        self.scan_id = scan_id
        self.scan = None
        self.target_url = None
        self.configuration = None
        self.zap_adapter = None
        self.scan_logger = None  # Per-scan logger instance
        self._stop_requested = False  # Flag for user-requested stop
        self.progress_range = progress_range  # Range to map progress to (start, end)

    def start(self):
        """Start active scanning process with comprehensive logging"""
        # Initialize scan-specific logger
        self.scan_logger = create_scan_logger(self.scan_id)

        try:
            # Start Docker log capture in background
            self.scan_logger.start_docker_log_capture()
            logger.info(f"🔍 Started Docker log capture for scan {self.scan_id}")

            # Lazy import to avoid circular dependencies
            from scanning.models.scan import Scan

            # Load scan details
            self.scan = Scan.objects.get(id=self.scan_id)
            self.target_url = self.scan.target_url or self.scan.configuration.project.target_url
            self.configuration = self.scan.configuration

            # Validate scan type - note: active scans now include passive reconnaissance
            if self.configuration.scan_type not in ['active', 'comprehensive']:
                raise ValueError(f"Engine only supports active/comprehensive scans, got: {self.configuration.scan_type}")

            # Initialize ZAP adapter with scan ID, logger, and engine reference for proper isolation
            self.zap_adapter = ZAPActiveAdapter(
                config=self.configuration,
                scan_id=self.scan_id,
                scan_logger=self.scan_logger,
                engine=self  # Pass engine reference for stop checks
            )

            # Initialize enhanced discovery adapter
            self.enhanced_adapter = ZAPEnhancedAdapter(self.zap_adapter, self.target_url)

            # Perform a full ZAP reset to ensure clean state before any scanning
            try:
                self.zap_adapter._reset_zap_state()
            except Exception as e:
                logger.warning(f"Could not fully reset ZAP state at scan start: {e}")
                if self.scan_logger:
                    self.scan_logger.log_error("ZAP Reset Warning", f"Could not fully reset ZAP: {str(e)}")

            # Run active scan
            self._run_active_scan()

            return True

        except Exception as e:
            logger.exception(f"Active scan engine failed: {e}")
            if self.scan_logger:
                import traceback
                self.scan_logger.log_error("Active Scan Engine Failed", str(e), traceback.format_exc())
            
            # Mark scan as failed
            self._fail_scan(str(e))
            return False

        finally:
            # CRITICAL: Always stop all ZAP scans in finally block to prevent resource leaks
            # This ensures AJAX spider is stopped even if there's an exception
            if self.zap_adapter:
                try:
                    logger.info("Finally block: Ensuring all ZAP scans are stopped...")
                    self.zap_adapter.stop_all_scans()
                    logger.info("Finally block: ZAP scans stopped successfully")
                except Exception as cleanup_error:
                    logger.error(f"Finally block: Error stopping ZAP scans: {cleanup_error}")
            
            # Always stop Docker log capture and create summary
            if self.scan_logger:
                try:
                    self.scan_logger.stop_docker_log_capture()
                    summary_file = self.scan_logger.create_summary()
                    logger.info(f"📊 Scan logs saved: {summary_file}")

                    # Save scan metadata
                    self.scan_logger.save_metadata({
                        'target_url': self.target_url,
                        'scan_type': self.configuration.scan_type if self.configuration else 'unknown',
                        'status': self.scan.status if self.scan else 'unknown'
                    })
                except Exception as logger_error:
                    logger.error(f"Error in scan logger cleanup: {logger_error}")

    def _run_active_scan(self):
        """Execute active scanning workflow"""
        try:
            # Update scan status
            self.scan.status = 'running'
            self.scan.start_time = timezone.now()
            # Initialize progress to the start of the configured range
            self.scan.progress = self.progress_range[0]
            self.scan.save()

            self._update_progress(5.0, "Initializing active scan")

            # Phase 1: Pre-scan validation
            self._update_progress(10.0, "Validating target and ZAP connection")
            self._validate_prerequisites()

            # Phase 2: Discovery phase (spidering)
            self._update_progress(20.0, "Starting discovery phase")
            discovery_results = self._discovery_phase()

            # Phase 3: Active vulnerability testing (45% to 80%)
            self._update_progress(45.0, "Starting active vulnerability testing")
            vulnerability_results = self._vulnerability_testing_phase(discovery_results)
            
            # Phase 3.5: SQL Injection testing (if enabled)
            if self.configuration.test_sql_injection:
                self._update_progress(65.0, "Running SQL injection tests")
                sql_injection_results = self._sql_injection_testing_phase(discovery_results)
                vulnerability_results.update(sql_injection_results)

            # Phase 4: Results processing (80% to 100%)
            self._update_progress(80.0, "Processing and saving results")
            self._process_and_save_results({
                "discovery": discovery_results,
                "vulnerabilities": vulnerability_results
            })

            # Complete scan
            self._complete_scan()
            self._update_progress(100.0, "Active scan completed")

        except Exception as e:
            logger.exception(f"Active scan workflow failed: {e}")
            self._fail_scan(str(e))

    def _validate_prerequisites(self):
        """Validate that all prerequisites are met for active scanning"""
        try:
            # Check ZAP connection
            if not self.zap_adapter.check_zap_connection():
                raise ConnectionError("Cannot connect to ZAP. Ensure ZAP Docker container is running on port 8080.")
            
            # Validate target URL
            if not self.target_url:
                raise ValueError("No target URL specified for active scan")
            
            # Check if target is accessible
            import requests
            try:
                response = requests.get(self.target_url, timeout=10, verify=False)
                if response.status_code >= 400:
                    logger.warning(f"Target returned status {response.status_code}, but continuing scan")
            except requests.RequestException as e:
                logger.warning(f"Target accessibility check failed: {e}, but continuing scan")

            logger.info("Prerequisites validation completed successfully")

        except Exception as e:
            logger.error(f"Prerequisites validation failed: {e}")
            raise

    def _discovery_phase(self) -> dict:
        """Run enhanced discovery phase using multiple tools and passive discovery results"""
        try:
            logger.info("Starting enhanced discovery phase with passive discovery integration")
            
            # Phase 1: Load enhanced discovery results from passive scan
            self._update_progress(20.0, "Loading enhanced discovery results from passive scan")
            passive_discovery_results = self._load_passive_discovery_results()
            
            # Phase 2: Enhanced discovery with multiple tools
            self._update_progress(25.0, "Running enhanced discovery with multiple security tools")
            enhanced_results = self.enhanced_adapter.run_enhanced_discovery()
            
            # Phase 3: Integrate passive discovery with ZAP context
            self._update_progress(30.0, "Integrating passive discovery results with ZAP")
            if passive_discovery_results.get("urls"):
                self._integrate_passive_discovery_with_zap(passive_discovery_results["urls"])
            
            # Phase 4: Traditional ZAP discovery for completeness
            self._update_progress(35.0, "Running ZAP traditional spider")
            zap_spider_results = {}
            if self.configuration.enable_spider:
                try:
                    zap_spider_results = self.zap_adapter._run_advanced_spider(self.target_url, self.configuration)
                except Exception as e:
                    logger.warning(f"ZAP spider failed: {e}")
                    zap_spider_results = {"error": str(e), "urls": [], "forms": []}

            # Phase 5: ZAP AJAX spider for SPAs
            self._update_progress(40.0, "Running ZAP AJAX spider for modern web apps")
            zap_ajax_results = {}
            if self.configuration.enable_ajax_spider:
                try:
                    zap_ajax_results = self.zap_adapter._run_ajax_spider(self.target_url, self.configuration)
                except ConnectionError as conn_err:
                    # ZAP connection lost - fail the entire scan
                    logger.error(f"❌ ZAP connection lost during AJAX spider: {conn_err}")
                    raise Exception(f"ZAP service unavailable: {conn_err}")
                except Exception as e:
                    logger.warning(f"ZAP AJAX spider failed: {e}")
                    zap_ajax_results = {"error": str(e), "urls": [], "forms": []}

            # Combine all results
            discovery_results = {
                "passive_discovery": passive_discovery_results,
                "enhanced_discovery": enhanced_results,
                "spider_results": zap_spider_results,
                "ajax_spider_results": zap_ajax_results,
                "total_urls_discovered": (
                    len(passive_discovery_results.get("urls", [])) +
                    enhanced_results.get('total_urls', 0)
                ),
                "total_forms_discovered": enhanced_results.get('total_forms', 0),
                "total_api_endpoints": len(enhanced_results.get('api_endpoints', [])),
                "discovery_stats": enhanced_results.get('enhanced_stats', {}),
                "tools_used": enhanced_results.get('enhanced_stats', {}).get('tools_used', []),
                "passive_integration": True
            }

            self._update_progress(45.0, 
                f"Enhanced discovery completed: {discovery_results['total_urls_discovered']} URLs, "
                f"{discovery_results['total_forms_discovered']} forms, "
                f"{discovery_results['total_api_endpoints']} API endpoints found")
            
            logger.info(f"Enhanced discovery summary: {discovery_results['discovery_stats']}")
            logger.info(f"Passive discovery integration: {len(passive_discovery_results.get('urls', []))} URLs loaded")
            return discovery_results

        except Exception as e:
            logger.error(f"Enhanced discovery phase failed: {e}")
            # Fallback to basic discovery
            return self._fallback_discovery()

    def _load_passive_discovery_results(self) -> dict:
        """Load enhanced discovery results from passive scan"""
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
                        # Determine protocol based on target
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
            
            logger.info(f"Loaded {len(unique_urls)} URLs from passive enhanced discovery")
            
            return {
                "urls": unique_urls,
                "subdomains": enhanced_discovery.get("subdomains", {}).get("subdomains", []),
                "wayback_urls": enhanced_discovery.get("wayback_urls", {}).get("urls", []),
                "directories": enhanced_discovery.get("directories", {}).get("directories", []),
                "api_endpoints": enhanced_discovery.get("api_endpoints", {}).get("api_endpoints", []),
                "summary": enhanced_discovery.get("summary", {})
            }
            
        except PassiveReconResult.DoesNotExist:
            logger.warning(f"No passive recon results found for scan {self.scan_id}")
            return {"urls": [], "error": "No passive results found"}
        except Exception as e:
            logger.error(f"Failed to load passive discovery results: {e}")
            return {"urls": [], "error": str(e)}

    def _integrate_passive_discovery_with_zap(self, urls: list) -> bool:
        """Add discovered URLs to ZAP context for active scanning"""
        try:
            if not urls:
                logger.info("No URLs to add to ZAP context")
                return True
            
            logger.info(f"Adding {len(urls)} discovered URLs to ZAP context")
            
            # Add each URL to ZAP context
            for url in urls:
                try:
                    # Access the URL to add it to ZAP's context
                    result = self.zap_adapter._make_api_post_request("core/action/accessUrl", {"url": url})
                    if result and result.get("Result") == "OK":
                        logger.debug(f"Successfully added URL to ZAP context: {url}")
                    else:
                        logger.warning(f"Failed to add URL to ZAP context: {url}. Result: {result}")
                except Exception as e:
                    logger.warning(f"Error adding URL {url} to ZAP context: {e}")
                    continue
            
            logger.info(f"Successfully added {len(urls)} URLs to ZAP context")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add URLs to ZAP context: {e}")
            return False
    
    def _fallback_discovery(self) -> dict:
        """Fallback to basic ZAP discovery if enhanced discovery fails"""
        logger.warning("Using fallback ZAP-only discovery")
        
        try:
            discovery_results = {
                "spider_results": {},
                "ajax_spider_results": {},
                "total_urls_discovered": 0,
                "total_forms_discovered": 0,
                "fallback_mode": True
            }

            # Traditional spider
            if self.configuration.enable_spider:
                spider_results = self.zap_adapter._run_advanced_spider(self.target_url, self.configuration)
                discovery_results["spider_results"] = spider_results
                spider_urls = spider_results.get("urls", [])
                discovery_results["total_urls_discovered"] += len(spider_urls)

            # AJAX spider
            if self.configuration.enable_ajax_spider:
                ajax_results = self.zap_adapter._run_ajax_spider(self.target_url, self.configuration)
                discovery_results["ajax_spider_results"] = ajax_results
                ajax_urls = ajax_results.get("urls", [])
                discovery_results["total_urls_discovered"] += len(ajax_urls)

            return discovery_results
            
        except Exception as e:
            logger.error(f"Even fallback discovery failed: {e}")
            return {"error": str(e), "total_urls_discovered": 0, "total_forms_discovered": 0}

    def _vulnerability_testing_phase(self, discovery_results: dict = None) -> dict:
        """Run active vulnerability testing with discovered URLs"""
        try:
            logger.info("Starting active vulnerability testing phase")

            # Extract all discovered URLs from discovery results
            discovered_urls = self._extract_all_discovered_urls(discovery_results)
            
            # Run comprehensive ZAP active scan with discovered URLs (45% to 75%)
            if discovered_urls:
                logger.info(f"Including {len(discovered_urls)} discovered URLs in vulnerability testing")
                zap_results = self.zap_adapter._run_active_vulnerability_scan(
                    self.target_url, 
                    self.configuration, 
                    discovered_urls,
                    progress_callback=self._update_progress,
                    progress_range=(45.0, 75.0)
                )
            else:
                logger.info("No external URLs discovered, testing target URL only")
                zap_results = self.zap_adapter._run_active_vulnerability_scan(
                    self.target_url, 
                    self.configuration,
                    progress_callback=self._update_progress,
                    progress_range=(45.0, 75.0)
                )
            
            # Extract vulnerabilities (75% to 80%)
            self._update_progress(75.0, "Extracting and processing vulnerabilities")
            vulnerabilities = self.zap_adapter._extract_vulnerabilities()
            
            # Generate statistics
            self._update_progress(80.0, "Generating scan statistics")
            statistics = self.zap_adapter._generate_scan_statistics()

            vulnerability_results = {
                "zap_scan_results": zap_results,
                "vulnerabilities": vulnerabilities,
                "statistics": statistics,
                "total_vulnerabilities_found": len(vulnerabilities)
            }

            logger.info(f"Vulnerability testing completed: {len(vulnerabilities)} vulnerabilities found")
            return vulnerability_results

        except Exception as e:
            logger.error(f"Vulnerability testing phase failed: {e}")
            return {"error": str(e)}

    def _process_and_save_results(self, results: dict):
        """Process and save scan results to database"""
        try:
            # Lazy import to avoid circular dependencies
            from scanning.models.scan import ActiveScanResult, ScanLog
            from scanning.models.vulnerability import Vulnerability
            
            # Save comprehensive results to ActiveScanResult
            active_result, created = ActiveScanResult.objects.get_or_create(
                scan=self.scan,
                defaults={
                    'spider_results': results.get('discovery', {}).get('spider_results', {}),
                    'ajax_spider_results': results.get('discovery', {}).get('ajax_spider_results', {}),
                    'urls_discovered': self._extract_discovered_urls(results.get('discovery', {})),
                    'forms_discovered': self._extract_discovered_forms(results.get('discovery', {})),
                    'raw_findings': results.get('vulnerabilities', {}).get('zap_scan_results', {}),
                    'zap_spider_id': getattr(self.zap_adapter, 'spider_id', None),
                    'zap_ajax_spider_id': getattr(self.zap_adapter, 'ajax_spider_id', None),
                    'zap_active_scan_id': getattr(self.zap_adapter, 'active_scan_id', None),
                    'total_requests_made': results.get('vulnerabilities', {}).get('statistics', {}).get('requests_made', 0),
                    'total_responses_received': results.get('vulnerabilities', {}).get('statistics', {}).get('responses_received', 0)
                }
            )
            
            if not created:
                # Update existing result
                active_result.spider_results = results.get('discovery', {}).get('spider_results', {})
                active_result.ajax_spider_results = results.get('discovery', {}).get('ajax_spider_results', {})
                active_result.urls_discovered = self._extract_discovered_urls(results.get('discovery', {}))
                active_result.forms_discovered = self._extract_discovered_forms(results.get('discovery', {}))
                active_result.raw_findings = results.get('vulnerabilities', {}).get('zap_scan_results', {})
                active_result.zap_spider_id = getattr(self.zap_adapter, 'spider_id', None)
                active_result.zap_ajax_spider_id = getattr(self.zap_adapter, 'ajax_spider_id', None)
                active_result.zap_active_scan_id = getattr(self.zap_adapter, 'active_scan_id', None)
                active_result.save()

            # Save vulnerabilities to the Vulnerability model
            vulnerabilities = results.get('vulnerabilities', {}).get('vulnerabilities', [])
            vulnerability_count = 0
            
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
                            'remediation': vuln_data.get('solution', ''),
                            # New metadata fields for ML / FP reduction
                            'plugin_id': vuln_data.get('plugin_id', ''),
                            'source': vuln_data.get('source', ''),
                            'category': vuln_data.get('category', ''),
                            'cwe_id': vuln_data.get('cwe_id', ''),
                            'wasc_id': vuln_data.get('wasc_id', ''),
                            'attack': vuln_data.get('attack', ''),
                            'other_info': vuln_data.get('other_info', ''),
                        }
                    )
                    if created:
                        vulnerability_count += 1
                    else:
                        # Update metadata on existing vulnerabilities if any new data is present
                        updated = False
                        for field in ['plugin_id', 'source', 'category', 'cwe_id', 'wasc_id', 'attack', 'other_info']:
                            new_val = vuln_data.get(field)
                            if new_val and getattr(vuln, field) != new_val:
                                setattr(vuln, field, new_val)
                                updated = True
                        if updated:
                            vuln.save(update_fields=['plugin_id', 'source', 'category', 'cwe_id', 'wasc_id', 'attack', 'other_info'])
                        logger.debug(f"Vulnerability already exists: {vuln.name} for {vuln.url}")
                except Exception as e:
                    logger.error(f"Failed to save vulnerability: {e}")
                    continue

            # Calculate actual discovery counts
            discovered_urls = self._extract_discovered_urls(results.get('discovery', {}))
            discovered_forms = self._extract_discovered_forms(results.get('discovery', {}))
            
            # Log results summary
            results_summary = {
                'discovery_urls': len(discovered_urls),
                'discovery_forms': len(discovered_forms),
                'vulnerabilities_saved': vulnerability_count,
                'spider_success': bool(results.get('discovery', {}).get('spider_results')),
                'ajax_spider_success': bool(results.get('discovery', {}).get('ajax_spider_results')),
                'active_scan_success': bool(results.get('vulnerabilities', {}).get('zap_scan_results'))
            }
            
            ScanLog.objects.create(
                scan=self.scan,
                level='INFO',
                message=f"Active scan results processed and saved: {results_summary}"
            )
            
            logger.info(f"Active scan results saved successfully: {results_summary}")

        except Exception as e:
            logger.exception(f"Failed to process and save results: {e}")
            raise

    def _extract_discovered_urls(self, discovery_results: dict) -> list:
        """Extract all discovered URLs from enhanced discovery results"""
        all_urls = []

        # Extract from enhanced discovery (primary source)
        enhanced_data = discovery_results.get('enhanced_discovery', {})
        enhanced_urls = enhanced_data.get('urls', [])
        all_urls.extend(self._normalize_urls(enhanced_urls))

        # Extract from traditional spider (fallback/additional)
        spider_urls = discovery_results.get('spider_results', {}).get('urls', [])
        all_urls.extend(self._normalize_urls(spider_urls))

        # Extract from AJAX spider (fallback/additional)
        ajax_urls = discovery_results.get('ajax_spider_results', {}).get('urls', [])
        all_urls.extend(self._normalize_urls(ajax_urls))

        # If no URLs found from discovery, use the target URL as fallback
        if not all_urls and self.target_url:
            logger.warning("No URLs discovered, using target URL as fallback for SQL injection testing")
            all_urls = [self.target_url]

        # Remove duplicates and filter to target domain (including subdomains)
        unique_urls = []
        seen = set()
        for url in all_urls:
            if not url or not isinstance(url, str):
                continue
            if url in seen:
                continue
            try:
                if self.target_url and is_same_domain(url, self.target_url):
                    unique_urls.append(url)
                    seen.add(url)
            except Exception:
                # If domain check fails, skip the URL to avoid cross-target bleed
                continue
        
        # Final fallback: if still no URLs, use target URL
        if not unique_urls and self.target_url:
            logger.warning("No valid URLs found after filtering, using target URL as final fallback")
            unique_urls = [self.target_url]
            
        logger.info(f"Extracted {len(unique_urls)} unique URLs from discovery results")
        return unique_urls

    def _normalize_urls(self, urls_data):
        """Normalize URL data to ensure we get strings, not dicts"""
        normalized_urls = []

        if not urls_data:
            return normalized_urls

        for item in urls_data:
            if isinstance(item, str):
                # Clean malformed URLs before adding
                cleaned_url = self._clean_malformed_url(item)
                if cleaned_url:
                    normalized_urls.append(cleaned_url)
            elif isinstance(item, dict):
                # Extract URL from dict - try common keys
                url = item.get('url') or item.get('href') or item.get('link') or item.get('address')
                if url and isinstance(url, str):
                    cleaned_url = self._clean_malformed_url(url)
                    if cleaned_url:
                        normalized_urls.append(cleaned_url)
                # If the dict itself represents a URL structure, convert it
                elif 'scheme' in item and 'netloc' in item:
                    try:
                        from urllib.parse import urlunparse
                        url = urlunparse((
                            item.get('scheme', 'http'),
                            item.get('netloc', ''),
                            item.get('path', ''),
                            item.get('params', ''),
                            item.get('query', ''),
                            item.get('fragment', '')
                        ))
                        cleaned_url = self._clean_malformed_url(url)
                        if cleaned_url:
                            normalized_urls.append(cleaned_url)
                    except Exception as e:
                        logger.debug(f"Could not normalize URL dict: {item}, error: {e}")
            else:
                logger.debug(f"Skipping non-string, non-dict URL item: {type(item)} - {item}")

        return normalized_urls
    
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
    
    def _extract_all_discovered_urls(self, discovery_results: dict) -> list:
        """Extract ALL discovered URLs from all discovery sources for ZAP context"""
        if not discovery_results:
            return []

        all_urls = set()

        try:
            # 1. Extract from passive discovery (integration)
            passive_data = discovery_results.get('passive_discovery', {})
            passive_urls = passive_data.get('urls', [])
            if passive_urls:
                normalized_passive = self._normalize_urls(passive_urls)
                all_urls.update(normalized_passive)
                logger.info(f"Found {len(normalized_passive)} URLs from passive discovery")

            # 2. Extract from enhanced discovery (external tools like subfinder, nuclei)
            enhanced_data = discovery_results.get('enhanced_discovery', {})
            if enhanced_data:
                # URLs discovered (fix: use 'urls' key, not 'urls_discovered')
                enhanced_urls = enhanced_data.get('urls', [])
                if enhanced_urls:
                    normalized_enhanced = self._normalize_urls(enhanced_urls)
                    all_urls.update(normalized_enhanced)
                    logger.info(f"Found {len(normalized_enhanced)} URLs from enhanced discovery")

                # Subdomains discovered
                subdomains = enhanced_data.get('subdomains', [])
                for subdomain in subdomains:
                    if subdomain and isinstance(subdomain, str):
                        # Convert subdomain to full URL
                        subdomain_url = f"https://{subdomain}" if not subdomain.startswith('http') else subdomain
                        all_urls.add(subdomain_url)

                # API endpoints discovered
                api_endpoints = enhanced_data.get('api_endpoints', [])
                if api_endpoints:
                    normalized_api = self._normalize_urls(api_endpoints)
                    all_urls.update(normalized_api)
                    logger.info(f"Found {len(normalized_api)} API endpoints from enhanced discovery")

            # 3. Extract from ZAP spider results
            spider_data = discovery_results.get('spider_results', {})
            # Fix: use 'urls' key
            spider_urls = spider_data.get('urls', [])
            if spider_urls:
                normalized_spider = self._normalize_urls(spider_urls)
                all_urls.update(normalized_spider)
                logger.info(f"Found {len(normalized_spider)} URLs from ZAP spider")

            # 4. Extract from ZAP AJAX spider results
            ajax_data = discovery_results.get('ajax_spider_results', {})
            # Fix: use 'urls' key
            ajax_urls = ajax_data.get('urls', [])
            if ajax_urls:
                normalized_ajax = self._normalize_urls(ajax_urls)
                all_urls.update(normalized_ajax)
                logger.info(f"Found {len(normalized_ajax)} URLs from ZAP AJAX spider")

            # Filter out invalid URLs and convert to list
            valid_urls = []
            for url in all_urls:
                if url and isinstance(url, str) and (url.startswith('http://') or url.startswith('https://')):
                    valid_urls.append(url.strip())

            logger.info(f"Extracted {len(valid_urls)} total valid URLs for comprehensive vulnerability testing")

            # Log first few URLs for debugging
            if valid_urls:
                sample_urls = valid_urls[:5]
                logger.info(f"Sample discovered URLs: {sample_urls}")
                if len(valid_urls) > 5:
                    logger.info(f"... and {len(valid_urls) - 5} more URLs")

            return valid_urls

        except Exception as e:
            logger.error(f"Error extracting discovered URLs: {e}")
            return []
    
    def _extract_discovered_forms(self, discovery_results: dict) -> list:
        """Extract all discovered forms from enhanced discovery results"""
        all_forms = []
        
        # Extract from enhanced discovery (primary source)
        enhanced_data = discovery_results.get('enhanced_discovery', {})
        enhanced_forms = enhanced_data.get('forms', [])
        all_forms.extend(enhanced_forms)
        
        # Extract from traditional spider (additional)
        spider_forms = discovery_results.get('spider_results', {}).get('forms', [])
        all_forms.extend(spider_forms)
        
        # Extract from AJAX spider (additional)
        ajax_forms = discovery_results.get('ajax_spider_results', {}).get('forms', [])
        all_forms.extend(ajax_forms)
        
        # Get comprehensive forms using ZAP adapter as fallback
        if not enhanced_forms and hasattr(self, 'zap_adapter') and self.zap_adapter:
            try:
                # Check if the adapter has the method
                if hasattr(self.zap_adapter, '_get_comprehensive_forms'):
                    zap_forms = self.zap_adapter._get_comprehensive_forms()
                    all_forms.extend(zap_forms)
                else:
                    logger.warning("ZAP adapter does not have _get_comprehensive_forms method")
            except Exception as e:
                logger.error(f"Error getting ZAP comprehensive forms: {e}")
        
        # Remove duplicates
        unique_forms = []
        seen_forms = set()
        for form in all_forms:
            form_key = f"{form.get('url', '')}-{form.get('action', '')}-{form.get('method', '')}"
            if form_key not in seen_forms:
                unique_forms.append(form)
                seen_forms.add(form_key)
        
        logger.info(f"Extracted {len(unique_forms)} unique forms from discovery results")
        return unique_forms

    def _complete_scan(self):
        """Mark scan as completed"""
        try:
            # CRITICAL: Stop all ZAP scans BEFORE marking as complete
            # This prevents AJAX spider from continuing to run after completion
            if self.zap_adapter:
                try:
                    logger.info("Stopping all ZAP scans before marking scan as complete...")
                    self.zap_adapter.stop_all_scans()
                    logger.info("ZAP scans stopped successfully")
                except Exception as e:
                    logger.error(f"Failed to stop ZAP scans during completion: {e}")
            
            self.scan.status = 'completed'
            self.scan.end_time = timezone.now()
            self.scan.progress = 100.0
            self.scan.save()

            # Clean up ZAP contexts to prevent cross-contamination
            if self.zap_adapter:
                try:
                    self.zap_adapter.cleanup_scan_contexts()
                except Exception as e:
                    logger.warning(f"Failed to cleanup ZAP contexts: {e}")

            # Create completion log
            from scanning.models.scan import ScanLog
            ScanLog.objects.create(
                scan=self.scan,
                level='INFO',
                message="Active scan completed successfully"
            )

            logger.info(f"Active scan {self.scan_id} completed successfully")
            
            # Send email notification
            try:
                from notifications.services import send_scan_completion_email
                if self.scan.configuration and self.scan.configuration.project:
                    user = self.scan.configuration.project.owner
                    send_scan_completion_email(self.scan, user)
            except Exception as e:
                logger.warning(f"Failed to send completion email: {e}")

        except Exception as e:
            logger.error(f"Error completing scan: {e}")

    def _fail_scan(self, error_message: str):
        """Mark scan as failed with error message"""
        if not self.scan:
            return
            
        try:
            # CRITICAL: Stop any running ZAP scans FIRST before marking as failed
            # This prevents AJAX spider from continuing to run after failure
            if self.zap_adapter:
                try:
                    logger.info("Stopping all ZAP scans before marking scan as failed...")
                    self.zap_adapter.stop_all_scans()
                    logger.info("ZAP scans stopped successfully")
                except Exception as e:
                    logger.error(f"Failed to stop ZAP scans during failure: {e}")
            
            self.scan.status = 'failed'
            self.scan.error_message = error_message
            self.scan.end_time = timezone.now()
            
            # Clean up ZAP contexts even on failure to prevent cross-contamination
            if self.zap_adapter:
                try:
                    self.zap_adapter.cleanup_scan_contexts()
                except Exception as e:
                    logger.warning(f"Failed to cleanup ZAP contexts on failure: {e}")
            
            self.scan.save()
            
            # Create error log
            from scanning.models.scan import ScanLog
            ScanLog.objects.create(
                scan=self.scan,
                level='ERROR',
                message=f"Active scan failed: {error_message}"
            )
            
            logger.error(f"Active scan {self.scan_id} failed: {error_message}")
            
            # Send email notification for failure
            try:
                from notifications.services import send_scan_completion_email
                if self.scan.configuration and self.scan.configuration.project:
                    user = self.scan.configuration.project.owner
                    send_scan_completion_email(self.scan, user)
            except Exception as e:
                logger.warning(f"Failed to send failure email: {e}")
            
        except Exception as e:
            logger.error(f"Error failing scan: {e}")

    def _update_progress(self, percent: float, message: str):
        """Update scan progress and log message"""
        try:
            # Map internal percentage (0-100) to configured range
            start_range, end_range = self.progress_range
            range_size = end_range - start_range
            mapped_percent = start_range + (percent * range_size / 100.0)
            
            if self.scan:
                # Refresh scan object to avoid stale data
                self.scan.refresh_from_db()
                
                # Ensure progress only moves forward (never decreases)
                current_progress = self.scan.progress
                if mapped_percent < current_progress:
                    logger.warning(f"Progress would decrease from {current_progress}% to {mapped_percent}%, keeping current progress")
                    mapped_percent = current_progress
                
                # Update progress
                self.scan.progress = mapped_percent
                self.scan.save(update_fields=['progress', 'updated_at'])
                
                # Create log entry
                from scanning.models.scan import ScanLog
                ScanLog.objects.create(
                    scan=self.scan,
                    level='INFO',
                    message=f"{mapped_percent:.1f}% - {message}"
                )
            
            logger.info(f"Active scan {self.scan_id}: {mapped_percent:.1f}% - {message}")
            
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")

    def stop_scan(self):
        """Stop the active scan"""
        try:
            # Set stop flag FIRST so monitoring loops can detect it
            self._stop_requested = True
            logger.info(f"🔴 Stop requested for active scan {self.scan_id}")
            
            if self.zap_adapter:
                self.zap_adapter.stop_all_scans()
            
            if self.scan and self.scan.status == 'running':
                self.scan.status = 'stopped'
                self.scan.end_time = timezone.now()
                self.scan.save()
                
                # Create stop log
                from scanning.models.scan import ScanLog
                ScanLog.objects.create(
                    scan=self.scan,
                    level='INFO',
                    message="Active scan stopped by user"
                )
            
            logger.info(f"Active scan {self.scan_id} stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping active scan: {e}")
    
    def is_stop_requested(self):
        """Check if stop has been requested"""
        return self._stop_requested

    def _sql_injection_testing_phase(self, discovery_results: dict) -> dict:
        """Run SQL injection testing using specialized tools"""
        try:
            logger.info("Starting SQL injection testing phase")
            sql_results = {
                "sqlmap_results": [],
                "sql_injection_vulnerabilities": []
            }
            
            # Get discovered URLs and forms
            discovered_urls = self._extract_discovered_urls(discovery_results)
            discovered_forms = self._extract_discovered_forms(discovery_results)
            
            # Test with SQLMap if enabled
            if self.configuration.use_sqlmap:
                try:
                    from scanning.integrations.sqlmap_adapter import SQLMapAdapter
                    
                    # Use shorter timeout for faster scanning, especially for vulnerable apps like DVWA
                    sqlmap_timeout = min(self.configuration.sqlmap_timeout, 30)  # Cap at 30 seconds
                    sqlmap_config = {
                        "risk_level": self.configuration.sqlmap_risk_level,
                        "level": self.configuration.sqlmap_level,
                        "timeout": sqlmap_timeout
                    }
                    
                    sqlmap_adapter = SQLMapAdapter(sqlmap_config)
                    
                    # Filter URLs to only test those with parameters (more likely to be vulnerable)
                    urls_with_params = [url for url in discovered_urls if '?' in url and '=' in url]
                    urls_to_test = urls_with_params[:3]  # Limit to first 3 URLs with parameters
                    
                    if not urls_to_test:
                        # Fallback to first 3 URLs if no parameterized URLs found
                        urls_to_test = discovered_urls[:3]
                    
                    logger.info(f"Testing {len(urls_to_test)} URLs with SQLMap (filtered for parameters)")
                    
                    # Test each discovered URL
                    for i, url in enumerate(urls_to_test):
                        logger.info(f"Testing {i+1}/{len(urls_to_test)}: {url} with SQLMap")
                        try:
                            sqlmap_findings = sqlmap_adapter.scan_url(url, discovered_forms)
                            sql_results["sqlmap_results"].extend(sqlmap_findings)
                            
                            # Add to vulnerabilities if found
                            for finding in sqlmap_findings:
                                if finding.get("severity") in ["critical", "high", "medium"]:
                                    sql_results["sql_injection_vulnerabilities"].append(finding)
                            
                            logger.info(f"Completed SQLMap test for {url} - found {len(sqlmap_findings)} findings")
                        except Exception as e:
                            logger.error(f"SQLMap test failed for {url}: {e}")
                            sql_results["sqlmap_results"].append({
                                "name": "SQLMap Test Error",
                                "description": f"SQLMap test failed: {str(e)}",
                                "severity": "info",
                                "url": url,
                                "confidence": 0.0,
                                "source": "sqlmap"
                            })
                    
                    logger.info(f"SQLMap testing completed. Found {len(sql_results['sqlmap_results'])} findings")
                    
                except Exception as e:
                    logger.error(f"SQLMap testing failed: {e}")
                    sql_results["sqlmap_error"] = str(e)
            
            # NoSQLMap testing disabled - only SQLMap is used for SQL injection testing
            
            # Save SQL injection vulnerabilities to database
            if sql_results["sql_injection_vulnerabilities"]:
                self._save_sql_injection_vulnerabilities(sql_results["sql_injection_vulnerabilities"])
            
            logger.info(f"SQL injection testing phase completed. Found {len(sql_results['sql_injection_vulnerabilities'])} vulnerabilities")
            return sql_results
            
        except Exception as e:
            logger.error(f"SQL injection testing phase failed: {e}")
            return {"sql_injection_error": str(e)}

    def _save_sql_injection_vulnerabilities(self, vulnerabilities: list):
        """Save SQL injection vulnerabilities to database"""
        try:
            from scanning.models.vulnerability import Vulnerability
            
            saved_count = 0
            for vuln_data in vulnerabilities:
                try:
                    vuln, created = Vulnerability.objects.get_or_create(
                        scan=self.scan,
                        name=vuln_data.get("name", "SQL Injection"),
                        url=vuln_data.get("url", self.target_url),
                        defaults={
                            "description": vuln_data.get("description", "SQL injection vulnerability detected"),
                            "severity": vuln_data.get("severity", "high"),
                            "parameter": vuln_data.get("parameter", ""),
                            "evidence": vuln_data.get("evidence", ""),
                            "confidence": vuln_data.get("confidence", 0.9),
                            "remediation": vuln_data.get("remediation", "Use parameterized queries to prevent SQL injection")
                        }
                    )
                    if created:
                        saved_count += 1
                        logger.info(f"Saved SQL injection vulnerability: {vuln.name}")
                except Exception as e:
                    logger.error(f"Failed to save SQL injection vulnerability: {e}")
            
            logger.info(f"Saved {saved_count} SQL injection vulnerabilities")
            
        except Exception as e:
            logger.error(f"Error saving SQL injection vulnerabilities: {e}")