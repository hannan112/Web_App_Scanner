"""
Unified Passive Scanner Implementation

Combines the best of custom analyzers and mature security tools
for comprehensive passive reconnaissance.
"""

import logging
import shutil
import socket
import subprocess
import time
from urllib.parse import urlparse

import requests
from django.db import transaction

from scanning.discovery.ajax_spider import AjaxSpider
# Discovery components
from scanning.discovery.crawler import Crawler
from scanning.discovery.sitemap_parser import SitemapParser
from scanning.integrations.nuclei_adapter import NucleiAdapter
from scanning.integrations.sslyze_adapter import SSLyzeAdapter
from scanning.integrations.wappalyzer_adapter import WappalyzerAdapter
# Tool adapters
from scanning.integrations.zap_adapter import ZAPAdapter
# Model imports
from scanning.models.scan import CrawlResult, PassiveReconResult, ScanLog
from scanning.models.vulnerability import Vulnerability
from scanning.passive.analyzers.content_analyzer import \
    analyze_information_disclosure
from scanning.passive.analyzers.cookie_analyzer import analyze_cookies
from scanning.passive.analyzers.cors_analyzer import check_cors_policy
# Import analyzer functions
from scanning.passive.analyzers.domain_analyzer import _analyze_dns
from scanning.passive.analyzers.form_analyzer import (
    analyze_forms, check_login_form_security)
from scanning.passive.analyzers.header_analyzer import analyze_security_headers
from scanning.passive.analyzers.ssl_analyzer import (analyze_ssl_certificate,
                                                     check_certificate_issues)
from scanning.passive.analyzers.tech_detector import detect_technologies

logger = logging.getLogger(__name__)


class UnifiedPassiveScanner:
    """
    Unified Passive Scanner that combines the best of custom analyzers and mature tools
    to perform comprehensive passive reconnaissance without active testing.
    """

    def __init__(self, scan_id, scan_obj, target_url, configuration):
        """
        Initialize the unified passive scanner

        Args:
            scan_id (int): The ID of the scan
            scan_obj (Scan): The scan model object
            target_url (str): The target URL to scan
            configuration (ScanConfiguration): The scan configuration
        """
        self.scan_id = scan_id
        self.scan = scan_obj
        self.target_url = target_url
        self.config = configuration

        # Parse URL components
        parsed_url = urlparse(target_url)
        self.domain = parsed_url.netloc
        self.scheme = parsed_url.scheme

        # Set default host/port for ZAP
        self.host = "localhost"  # Default to localhost
        self.port = 8080  # Default ZAP port

        # Override with custom values if provided in configuration
        if hasattr(self.config, "zap_host"):
            self.host = self.config.zap_host
        if hasattr(self.config, "zap_port"):
            self.port = self.config.zap_port

        # Initialize whether to allow fallbacks for analyzers
        self.allow_fallbacks = getattr(self.config, "allow_analyzer_fallbacks", True)

        # Configure headers for HTTP requests
        self.headers = {
            "User-Agent": getattr(configuration, "user_agent", None)
            or "SecurityScannerBot/1.0"
        }
        if hasattr(configuration, "custom_headers") and configuration.custom_headers:
            self.headers.update(configuration.custom_headers)

        # Initialize results dictionary with required structure
        self.results = {
            "dns_records": {},
            "server_info": {},
            "technologies": {},
            "response_headers": {},
            "urls_discovered": [],
            "forms_discovered": [],
            "cookies": {},
            "robots_txt": None,
            "sitemap_xml": None,
        }

        # Initialize findings list
        self.findings = []

        # Initialize progress tracking
        self.progress = 0

        # Initialize response object
        self.response = None

        # Check which tools are available (SSLyze, ZAP, Nuclei, Wappalyzer)
        self.available_tools = self._check_available_tools()
        logger.info(f"Available tools for scan {scan_id}: {self.available_tools}")

    def run_scan(self):
        """
        Execute the passive scan using the best available methods

        This is the main method that coordinates the entire scanning process.
        It executes each analysis component in sequence, updates progress,
        and processes the findings.

        Returns:
            dict: Scan results
        """
        try:
            # Start scan
            logger.info(f"Starting unified passive scan for {self.target_url}")
            self.update_progress(5, "Starting passive scan")

            # 1. Basic HTTP request to get initial information
            self._analyze_basic_http()
            self.update_progress(15, "Basic HTTP analysis completed")

            # 2. DNS analysis
            self._analyze_dns()
            self.update_progress(25, "DNS analysis completed")

            # 3. Check robots.txt and sitemap
            self._analyze_robots_sitemap()
            self.update_progress(30, "Robots.txt and sitemap analysis completed")

            # 4. Technology detection (Wappalyzer preferred)
            self._detect_technologies()
            self.update_progress(40, "Technology detection completed")

            # 5. SSL/TLS analysis (SSLyze preferred)
            self._analyze_ssl_tls()
            self.update_progress(50, "SSL/TLS analysis completed")

            # 6. Security headers analysis (ZAP preferred)
            self._analyze_headers()
            self.update_progress(60, "Security headers analysis completed")

            # 7. Cookie analysis (ZAP or custom analyzer)
            self._analyze_cookies()
            self.update_progress(65, "Cookie analysis completed")

            # 8. Crawl website to discover URLs and forms
            self._crawl_website()
            self.update_progress(75, "Website crawling completed")

            # 9. Form analysis (custom analyzer preferred)
            self._analyze_forms()
            self.update_progress(80, "Form analysis completed")

            # 10. CORS analysis (custom analyzer)
            self._analyze_cors()
            self.update_progress(85, "CORS analysis completed")

            # 11. Content analysis for information disclosure
            self._analyze_content()
            self.update_progress(90, "Content analysis completed")

            # 12. Run Nuclei passive templates if available
            self._run_nuclei_passive()
            self.update_progress(95, "Nuclei scan completed")

            # Process and save all findings
            self._process_findings()
            self.update_progress(98, "Processing findings")

            # Save all results to database
            self._save_results()
            self.update_progress(100, "Passive scan completed")

            logger.info(f"Passive scan completed for {self.target_url}")
            return self.results

        except Exception as e:
            logger.exception(f"Error in unified passive scan {self.scan_id}: {str(e)}")
            self.scan.error_message = str(e)
            self.scan.save()

            # Create an error log
            ScanLog.objects.create(
                scan=self.scan, level="ERROR", message=f"Scan failed: {str(e)}"
            )
            raise

    def _analyze_dns(self):
        """
        Analyze DNS records for the target domain - Uses the imported function
        """
        # Call the imported function, passing self as an argument
        _analyze_dns(self)

    def _analyze_basic_http(self):
        logger.info(f"Performing basic HTTP analysis for {self.target_url}")

        try:
            # Create a session with more robust handling of insecure connections
            session = requests.Session()

            # First try with verification enabled
            try:
                response = session.get(
                    self.target_url,
                    headers=self.headers,
                    timeout=10,
                    verify=True,  # Try with verification first
                )
            except requests.exceptions.SSLError as ssl_err:
                # Log the SSL error and retry with verification disabled
                logger.warning(
                    f"SSL verification failed for {self.target_url}: {str(ssl_err)}"
                )

                # Suppress InsecureRequestWarning
                import urllib3

                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

                # Retry without verification
                response = session.get(
                    self.target_url, headers=self.headers, timeout=10, verify=False
                )

                # Add a finding for SSL verification failure
                self._add_finding(
                    {
                        "name": "SSL Certificate Validation Failed",
                        "description": f"The site's SSL certificate could not be validated: {str(ssl_err)}",
                        "severity": "medium",
                        "url": self.target_url,
                        "confidence": 0.9,
                        "source": "unified_scanner",
                    }
                )

            # Store the response for later use
            self.response = response

            # Store response headers
            self.results["response_headers"] = dict(response.headers)

            # Extract basic server information
            server_info = {
                "server": response.headers.get("Server", "Unknown"),
                "x_powered_by": response.headers.get("X-Powered-By", "Not disclosed"),
                "content_type": response.headers.get("Content-Type", "Unknown"),
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
            }

            # Update server info
            self.results["server_info"].update(server_info)

            # Store cookies
            if response.cookies:
                self.results["cookies"] = {
                    name: str(value) for name, value in response.cookies.items()
                }

            logger.info(
                f"Basic HTTP analysis completed: status {response.status_code}, server: {server_info['server']}"
            )

        except Exception as e:
            logger.error(
                f"Error in basic HTTP analysis for {self.target_url}: {str(e)}"
            )
            self.results["server_info"]["error"] = str(e)
            self._add_error_finding("HTTP Request Error", str(e))

    def _analyze_headers(self):
        """
        Analyze HTTP security headers
        """
        # ... existing code ...

        # Try to use ZAP if available for more comprehensive header analysis
        if self.available_tools.get("zap", {}).get("available", False):
            try:
                # Create the adapter with proper configuration
                adapter = ZAPAdapter(
                    config={
                        "zap_host": self.available_tools["zap"].get(
                            "host", "localhost"
                        ),
                        "zap_port": self.available_tools["zap"].get("port", 8080),
                        "zap_api_key": "",  # No API key for now
                    }
                )

                # Check if connection works
                if adapter.initialize():
                    header_findings = adapter.check_headers(self.target_url)
                    if header_findings:
                        logger.info(
                            f"ZAP found {len(header_findings)} header-related issues"
                        )
                        for finding in header_findings:
                            finding["source"] = "zap"
                            self._add_finding(finding)
                else:
                    logger.warning("ZAP connection failed during initialization")
            except Exception as zap_err:
                logger.warning(f"Error using ZAP for header analysis: {str(zap_err)}")

    def _analyze_ssl_tls(self):
        """
        Analyze SSL/TLS configuration using best available method
        """
        logger.info(f"Starting SSL/TLS analysis for {self.target_url}")

        # Skip if not HTTPS
        if self.scheme != "https":
            logger.info(f"Target {self.target_url} is not using HTTPS - adding finding")
            self._add_finding(
                {
                    "name": "Site Not Using HTTPS",
                    "description": "The website is not using HTTPS encryption. This means that all data transmitted between users and the site is unencrypted and vulnerable to interception.",
                    "severity": "high",
                    "url": self.target_url,
                    "confidence": 1.0,
                    "remediation": "Implement HTTPS by obtaining an SSL certificate and configuring your server to use it.",
                    "source": "unified_scanner",
                }
            )
            return

        try:
            # Get SSL tool availability
            has_sslyze = self.available_tools.get("sslyze", {}).get("available", False)

            if has_sslyze:
                # Use SSLyze for more comprehensive analysis
                logger.info(f"Using SSLyze for SSL/TLS analysis of {self.target_url}")
                adapter = SSLyzeAdapter()
                findings = adapter.scan_ssl(self.target_url)

                # Add findings
                if findings:
                    logger.info(f"SSLyze found {len(findings)} SSL/TLS issues")
                    for finding in findings:
                        finding["source"] = "sslyze"
                        self._add_finding(finding)
                else:
                    logger.info("SSLyze analysis completed with no findings")
            else:
                # Fall back to built-in SSL analyzer
                logger.info(
                    f"Using built-in SSL analyzer for {self.target_url} (SSLyze not available)"
                )

                ssl_result = analyze_ssl_certificate(self.scan, self.target_url)
                self.results["ssl_info"] = ssl_result

                # Check for certificate issues
                check_certificate_issues(self.scan, ssl_result, self.target_url)

                logger.info("Built-in SSL analysis completed")

        except Exception as e:
            logger.error(f"Error in SSL/TLS analysis: {str(e)}")
            self._add_error_finding("SSL/TLS Analysis Error", str(e))

    def _detect_technologies(self):
        """
        Detect technologies used by the website
        """
        logger.info(f"Starting technology detection for {self.target_url}")

        try:
            # Check if Wappalyzer is available
            has_wappalyzer = self.available_tools.get("wappalyzer", {}).get(
                "available", False
            )

            if has_wappalyzer:
                # Use Wappalyzer for better technology detection
                logger.info(f"Using Wappalyzer for technology detection")
                adapter = WappalyzerAdapter()
                self.results["technologies"] = adapter.detect_technologies(
                    self.target_url
                )

                # Log detected technologies
                techs = self.results["technologies"]
                logger.info(
                    f"Wappalyzer detected: Server: {techs.get('server')}, "
                    + f"CMS: {techs.get('cms')}, "
                    + f"Frameworks: {', '.join(techs.get('frameworks', []))}"
                )
            else:
                # Use built-in technology detector
                logger.info(
                    f"Using built-in technology detector (Wappalyzer not available)"
                )
                if hasattr(self, "response") and self.response:
                    self.results["technologies"] = detect_technologies(
                        self.response.text if self.response.text else "",
                        self.response.headers,
                    )

                    # Log detected technologies
                    techs = self.results["technologies"]
                    logger.info(
                        f"Built-in detector found: Server: {techs.get('server')}, "
                        + f"CMS: {techs.get('cms')}, "
                        + f"Frameworks: {', '.join(techs.get('frameworks', []))}"
                    )
                else:
                    logger.warning("Cannot detect technologies - no response available")

        except Exception as e:
            logger.error(f"Error in technology detection: {str(e)}")
            # Not adding as a finding since it's not a security issue
            self.results["technologies"] = {
                "error": f"Error detecting technologies: {str(e)}"
            }

    def _analyze_robots_sitemap(self):
        """
        Analyze robots.txt and sitemap.xml files
        """
        logger.info(f"Analyzing robots.txt and sitemap for {self.target_url}")

        try:
            # Parse robots.txt
            robots_url = f"{self.scheme}://{self.domain}/robots.txt"
            try:
                response = requests.get(robots_url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    self.results["robots_txt"] = response.text
                    logger.info(f"Successfully retrieved robots.txt")

                    # Check for disallowed paths that might indicate sensitive areas
                    disallowed_paths = []
                    for line in response.text.splitlines():
                        if line.lower().startswith("disallow:"):
                            path = line.split(":", 1)[1].strip()
                            if path:
                                disallowed_paths.append(path)

                    if disallowed_paths:
                        self._add_finding(
                            {
                                "name": "Sensitive Paths in Robots.txt",
                                "description": f"Found {len(disallowed_paths)} disallowed paths in robots.txt that might indicate sensitive areas of the application.",
                                "severity": "info",
                                "confidence": 0.7,
                                "evidence": f"Paths: {', '.join(disallowed_paths[:10])}",
                                "remediation": "Review robots.txt to ensure it doesn't disclose sensitive paths.",
                            }
                        )
                else:
                    logger.info(f"No robots.txt found at {robots_url}")
            except Exception as e:
                logger.warning(f"Error retrieving robots.txt: {str(e)}")

            # Parse sitemap using SitemapParser
            parser = SitemapParser(self.target_url)
            try:
                sitemap_urls = parser.parse()
                if sitemap_urls:
                    self.results["sitemap_xml"] = sitemap_urls
                    logger.info(
                        f"Successfully retrieved sitemap with {len(sitemap_urls)} URLs"
                    )
            except Exception as e:
                logger.warning(f"Error parsing sitemap: {str(e)}")

            # Update progress
            self.update_progress(30, "Robots.txt and sitemap analysis completed")

        except Exception as e:
            logger.error(f"Error in robots.txt and sitemap analysis: {str(e)}")
            self.update_progress(30, "Robots.txt and sitemap analysis failed")

    def _analyze_cookies(self):
        """
        Analyze cookies for security issues
        """
        logger.info(f"Analyzing cookies for {self.target_url}")

        try:
            # Get cookies from previous response or make a new request
            if hasattr(self, "response") and self.response:
                cookies = dict(self.response.cookies)
            else:
                response = requests.get(
                    self.target_url, headers=self.headers, timeout=10
                )
                cookies = dict(response.cookies)

            # Store cookies in results
            self.results["cookies"] = {k: str(v) for k, v in cookies.items()}

            # Use imported cookie analyzer
            if hasattr(self, "response"):
                analyze_cookies(self.scan, cookies, dict(self.response.headers))
            else:
                analyze_cookies(self.scan, cookies)

            # Try to use ZAP if available for more comprehensive cookie analysis
            if self.available_tools.get("zap", {}).get("available", False):
                try:
                    adapter = ZAPAdapter(
                        config={
                            "zap_host": self.available_tools["zap"]["host"],
                            "zap_port": self.available_tools["zap"]["port"],
                            "zap_api_key": (
                                self.config.zap_config.get("api_key", "")
                                if hasattr(self.config, "zap_config")
                                else ""
                            ),
                        }
                    )

                    cookie_findings = adapter.check_cookies(self.target_url)
                    if cookie_findings:
                        logger.info(
                            f"ZAP found {len(cookie_findings)} cookie-related issues"
                        )
                        for finding in cookie_findings:
                            finding["source"] = "zap"
                            self._add_finding(finding)
                except Exception as zap_err:
                    logger.warning(
                        f"Error using ZAP for cookie analysis: {str(zap_err)}"
                    )

            # Update progress
            self.update_progress(65, "Cookie analysis completed")

        except Exception as e:
            logger.error(f"Error in cookie analysis: {str(e)}")
            self._add_error_finding("Cookie Analysis Error", str(e))
            self.update_progress(65, "Cookie analysis failed")

    def _crawl_website(self):
        """
        Crawl website to discover URLs, forms, and cookies
        """
        logger.info(f"Starting website crawling for {self.target_url}")

        try:
            # Ensure the results dictionary has the required keys
            if "urls_discovered" not in self.results:
                self.results["urls_discovered"] = []
            if "forms_discovered" not in self.results:
                self.results["forms_discovered"] = []
            if "cookies" not in self.results:
                self.results["cookies"] = {}

            # Get crawler configuration from scan config with safe defaults
            crawl_depth = getattr(self.config, "crawl_depth", 2)
            respect_robots_txt = getattr(self.config, "respect_robots_txt", True)
            crawl_max_pages = getattr(self.config, "crawl_max_pages", 100)
            crawl_timeout = getattr(self.config, "crawl_timeout", 30)
            user_agent = getattr(self.config, "user_agent", None)

            # Create crawler instance with safe defaults for headers
            headers = getattr(self, "headers", {"User-Agent": "SecurityScannerBot/1.0"})
            crawler = Crawler(
                start_url=self.target_url,
                max_depth=crawl_depth,
                respect_robots_txt=respect_robots_txt,
                max_pages=crawl_max_pages,
                timeout=crawl_timeout,
                user_agent=user_agent or headers.get("User-Agent"),
            )

            # Define progress callback to update scan progress
            def progress_callback(progress, urls, forms, cookies):
                # Transform progress 0-100 to our scale of 65-75
                adjusted_progress = 65 + (progress / 100 * 10)
                self.update_progress(
                    adjusted_progress,
                    f"Website crawling in progress - {len(urls)} URLs discovered",
                )

            # Run the crawler
            crawl_results = crawler.start(progress_callback)

            # Store discovered URLs, forms, and cookies
            if crawl_results.get("urls_discovered"):
                self.results["urls_discovered"] = crawl_results.get(
                    "urls_discovered", []
                )
            if crawl_results.get("forms_discovered"):
                self.results["forms_discovered"] = crawl_results.get(
                    "forms_discovered", []
                )

            # Merge cookies with any existing cookies
            if crawl_results.get("cookies"):
                if self.results.get("cookies"):
                    self.results["cookies"].update(crawl_results["cookies"])
                else:
                    self.results["cookies"] = crawl_results["cookies"]

            # Create CrawlResult object in database
            from scanning.models.scan import CrawlResult

            CrawlResult.objects.create(
                scan=self.scan,
                urls_discovered=self.results.get("urls_discovered", []),
                forms_discovered=self.results.get("forms_discovered", []),
                cookies=self.results.get("cookies", {}),
                pages_crawled=crawl_results.get("pages_crawled", 0),
            )

            logger.info(
                f"Website crawling completed - discovered {len(self.results.get('urls_discovered', []))} URLs and {len(self.results.get('forms_discovered', []))} forms"
            )
            self.update_progress(75, "Website crawling completed")

        except Exception as e:
            logger.error(f"Error in website crawling: {str(e)}")
            self._add_error_finding("Website Crawling Error", str(e))
            self.update_progress(75, "Website crawling failed")

    def _analyze_forms(self):
        """
        Analyze discovered forms for security issues
        """
        logger.info(f"Analyzing forms for {self.target_url}")

        try:
            # Check if we have forms from crawling
            forms = self.results.get("forms_discovered", [])

            if not forms:
                logger.info("No forms discovered to analyze")
                self.update_progress(80, "Form analysis completed - no forms found")
                return

            # Use imported form analyzer functions
            analyze_forms(self.scan, forms)

            # Specific analysis for login forms
            check_login_form_security(self.scan, forms)

            # Try to use ZAP if available
            if self.available_tools.get("zap", {}).get("available", False):
                try:
                    adapter = ZAPAdapter(
                        config={
                            "zap_host": self.available_tools["zap"]["host"],
                            "zap_port": self.available_tools["zap"]["port"],
                            "zap_api_key": (
                                self.config.zap_config.get("api_key", "")
                                if hasattr(self.config, "zap_config")
                                else ""
                            ),
                        }
                    )

                    form_findings = adapter.check_forms(self.target_url)
                    if form_findings:
                        logger.info(
                            f"ZAP found {len(form_findings)} form-related issues"
                        )
                        for finding in form_findings:
                            finding["source"] = "zap"
                            self._add_finding(finding)
                except Exception as zap_err:
                    logger.warning(f"Error using ZAP for form analysis: {str(zap_err)}")

            # Update progress
            self.update_progress(80, "Form analysis completed")

        except Exception as e:
            logger.error(f"Error in form analysis: {str(e)}")
            self._add_error_finding("Form Analysis Error", str(e))
            self.update_progress(80, "Form analysis failed")

    def _analyze_cors(self):
        """
        Analyze CORS policy for security issues
        """
        logger.info(f"Analyzing CORS policy for {self.target_url}")

        try:
            # Use imported CORS analyzer
            check_cors_policy(self.scan, self.target_url)

            # Update progress
            self.update_progress(85, "CORS analysis completed")

        except Exception as e:
            logger.error(f"Error in CORS analysis: {str(e)}")
            self._add_error_finding("CORS Analysis Error", str(e))
            self.update_progress(85, "CORS analysis failed")

    def _analyze_content(self):
        """
        Analyze content for information disclosure
        """
        logger.info(f"Analyzing content for {self.target_url}")

        try:
            # Check if we have response content from earlier requests
            if hasattr(self, "response") and self.response:
                content = self.response.text
                headers = dict(self.response.headers)
            else:
                # Make a new request
                response = requests.get(
                    self.target_url, headers=self.headers, timeout=10
                )
                content = response.text
                headers = dict(response.headers)

            # Use imported content analyzer
            analyze_information_disclosure(self.scan, self.target_url, content, headers)

            # Update progress
            self.update_progress(90, "Content analysis completed")

        except Exception as e:
            logger.error(f"Error in content analysis: {str(e)}")
            self._add_error_finding("Content Analysis Error", str(e))
            self.update_progress(90, "Content analysis failed")

    def _run_nuclei_passive(self):
        """
        Run Nuclei passive templates if available
        """
        logger.info(f"Checking for Nuclei passive templates for {self.target_url}")

        try:
            # Check if Nuclei is available
            nuclei_available = self.available_tools.get("nuclei", {}).get(
                "available", False
            )

            # Check if nuclei is required by config
            nuclei_required = False
            if hasattr(self.config, "use_nuclei"):
                nuclei_required = self.config.use_nuclei

            if not nuclei_available:
                if nuclei_required:
                    logger.warning("Nuclei was requested but is not available")
                    self._add_finding(
                        {
                            "name": "Nuclei Not Available",
                            "description": "Nuclei scanner was requested in the configuration but is not available on the system.",
                            "severity": "info",
                            "confidence": 1.0,
                            "remediation": "Install Nuclei to use this feature: https://github.com/projectdiscovery/nuclei",
                        }
                    )
                self.update_progress(95, "Nuclei scan skipped - tool not available")
                return

            # Create adapter instance
            adapter = NucleiAdapter(
                config=(
                    getattr(self.config, "nuclei_config", {})
                    if hasattr(self.config, "nuclei_config")
                    else {}
                )
            )

            # Run passive scan
            findings = adapter.scan_url(self.target_url)

            if findings:
                logger.info(f"Nuclei found {len(findings)} issues")
                for finding in findings:
                    finding["source"] = "nuclei"
                    self._add_finding(finding)

            # Update progress
            self.update_progress(95, "Nuclei scan completed")

        except Exception as e:
            logger.error(f"Error in Nuclei scan: {str(e)}")
            self._add_error_finding("Nuclei Scan Error", str(e))
            self.update_progress(95, "Nuclei scan failed")

    def _add_finding(self, finding):
        """
        Add a finding to the findings list with validation

        Args:
            finding (dict): The finding to add
        """
        # Ensure required fields are present
        required_fields = ["name", "description", "severity"]
        for field in required_fields:
            if field not in finding:
                logger.warning(f"Finding missing required field: {field}")
                return

        # Validate severity
        valid_severities = ["critical", "high", "medium", "low", "info"]
        if finding["severity"] not in valid_severities:
            logger.warning(f"Finding has invalid severity: {finding['severity']}")
            finding["severity"] = "info"  # Default to info

        # Ensure required fields have values
        if not finding["name"] or not finding["description"]:
            logger.warning("Finding has empty required fields")
            return

        # Add default values for optional fields
        if "url" not in finding:
            finding["url"] = self.target_url
        if "confidence" not in finding:
            finding["confidence"] = 0.8  # Default confidence
        if "source" not in finding:
            finding["source"] = "unified_scanner"

        # Add a timestamp
        import datetime

        finding["timestamp"] = datetime.datetime.now().isoformat()

        # Add to findings list
        self.findings.append(finding)

        logger.info(
            f"Added finding: {finding['name']} ({finding['severity']}, confidence: {finding['confidence']})"
        )

    def _add_error_finding(self, name, error_message):
        """
        Add an error finding with standard format

        Args:
            name (str): Name of the error
            error_message (str): Error message
        """
        self._add_finding(
            {
                "name": name,
                "description": f"Error during analysis: {error_message}",
                "severity": "info",
                "url": self.target_url,
                "confidence": 1.0,
                "source": "error_handler",
            }
        )

        logger.error(f"{name}: {error_message}")

    def update_progress(self, progress, message=None):
        """
        Update scan progress and log message

        Args:
            progress (int): Progress percentage (0-100)
            message (str, optional): Progress message
        """
        self.progress = progress
        self.scan.progress = progress
        self.scan.save()

        if message:
            logger.info(f"Scan {self.scan_id}: {message} - {progress}%")

            # Log to database
            ScanLog.objects.create(
                scan=self.scan, level="INFO", message=f"{message} - {progress}%"
            )

    def _process_findings(self):
        """
        Process findings, apply confidence threshold and remove duplicates

        This method:
        1. Filters findings based on confidence threshold
        2. Groups similar findings to reduce duplication
        3. Converts findings to Vulnerability objects in the database
        """
        logger.info(f"Processing {len(self.findings)} findings from scan")

        # Get minimum confidence threshold from configuration
        min_confidence = float(getattr(self.config, "min_confidence", 0.7))
        logger.info(f"Applying confidence threshold: {min_confidence}")

        # Filter findings based on confidence
        filtered_findings = [
            finding
            for finding in self.findings
            if finding.get("confidence", 0) >= min_confidence
        ]

        logger.info(
            f"After confidence filtering: {len(filtered_findings)} findings remain"
        )

        # Group similar findings to eliminate duplicates
        grouped_findings = self._group_similar_findings(filtered_findings)

        logger.info(f"After deduplication: {len(grouped_findings)} unique findings")

        # Save findings as vulnerabilities
        saved_count = 0
        for finding in grouped_findings:
            try:
                # Create vulnerability record
                Vulnerability.objects.create(
                    scan=self.scan,
                    name=finding["name"],
                    description=finding["description"],
                    severity=finding["severity"],
                    url=finding.get("url", self.target_url),
                    parameter=finding.get("parameter", ""),
                    evidence=finding.get("evidence", ""),
                    confidence=finding.get("confidence", 0.5),
                    remediation=finding.get("remediation", ""),
                )
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving finding {finding['name']}: {str(e)}")

        logger.info(f"Saved {saved_count} findings as vulnerabilities")

    def _group_similar_findings(self, findings):
        """
        Group similar findings to reduce duplicates

        Args:
            findings (list): List of finding dictionaries

        Returns:
            list: Deduplicated findings
        """
        groups = {}

        for finding in findings:
            # Create a key based on name and URL
            key = f"{finding.get('name')}|{finding.get('url', '')}"

            if key in groups:
                # Update existing finding
                existing = groups[key]

                # Keep the higher severity
                sev_rank = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}

                if sev_rank.get(finding.get("severity"), 0) > sev_rank.get(
                    existing.get("severity"), 0
                ):
                    existing["severity"] = finding.get("severity")

                # Keep the higher confidence
                existing["confidence"] = max(
                    existing.get("confidence", 0), finding.get("confidence", 0)
                )

                # Combine evidence
                if finding.get("evidence") and finding.get("evidence") != existing.get(
                    "evidence"
                ):
                    existing["evidence"] = (
                        f"{existing.get('evidence', '')} | {finding.get('evidence', '')}"
                    )

                # Track sources
                sources = existing.get("sources", [existing.get("source")])
                if finding.get("source") and finding.get("source") not in sources:
                    sources.append(finding.get("source"))
                existing["sources"] = sources

                # Take most detailed remediation
                if finding.get("remediation") and len(
                    finding.get("remediation", "")
                ) > len(existing.get("remediation", "")):
                    existing["remediation"] = finding.get("remediation")

            else:
                # Create new group
                finding["sources"] = (
                    [finding.get("source")] if finding.get("source") else []
                )
                groups[key] = finding

        # Enhance findings with source information in description
        result = []
        for finding in groups.values():
            sources = finding.get("sources", [])
            if len(sources) > 1:
                sources = [s for s in sources if s]  # Remove None/empty
                if sources:
                    finding["description"] = (
                        f"{finding.get('description')}\n\nDetected by multiple scanners: {', '.join(sources)}"
                    )
            result.append(finding)

        return result

    def _save_results(self):
        """Save scan results to database with transaction management"""
        try:
            # Use transaction.atomic to ensure all or nothing
            from django.db import transaction
            from django.utils import \
                timezone  # Import django.utils.timezone, not time.timezone

            with transaction.atomic():
                logger.info(f"Saving scan results to database for scan {self.scan_id}")

                # Save passive recon results
                passive_result, created = PassiveReconResult.objects.update_or_create(
                    scan=self.scan,
                    defaults={
                        "dns_records": self.results["dns_records"],
                        "server_info": self.results["server_info"],
                        "robots_txt": self.results.get("robots_txt"),
                        "sitemap_xml": self.results.get("sitemap_xml"),
                        "technologies": self.results.get("technologies", {}),
                        "response_headers": self.results.get("response_headers", {}),
                    },
                )

                # Save crawl results if we have URLs
                if self.results.get("urls_discovered"):
                    crawl_result, created = CrawlResult.objects.update_or_create(
                        scan=self.scan,
                        defaults={
                            "urls_discovered": self.results.get("urls_discovered", []),
                            "forms_discovered": self.results.get(
                                "forms_discovered", []
                            ),
                            "cookies": self.results.get("cookies", {}),
                            "pages_crawled": len(
                                self.results.get("urls_discovered", [])
                            ),
                        },
                    )

                # Update scan status
                self.scan.status = "completed"
                self.scan.end_time = (
                    timezone.now()
                )  # Use the correctly imported timezone module
                self.scan.save()

                logger.info(f"Scan results saved successfully for scan {self.scan_id}")

        except Exception as e:
            logger.error(f"Error saving scan results: {str(e)}")
            self.scan.status = "failed"
            self.scan.error_message = f"Error saving scan results: {str(e)}"

            # Don't try to use timezone.now() again here since that's what caused the error
            # Instead, use Python's standard datetime
            import datetime

            self.scan.end_time = datetime.datetime.now()

            self.scan.save()
            raise

    def _check_available_tools(self):
        """
        Check which external security tools are available on the system

        Returns:
            dict: Dictionary of tool availability status
        """
        available = {}

        # Check for SSLyze - Python package
        try:
            import sslyze

            available["sslyze"] = {
                "available": True,
                "version": getattr(sslyze, "__version__", "unknown"),
            }
            logger.info(
                f"SSLyze is available (version: {available['sslyze']['version']})"
            )
        except ImportError:
            available["sslyze"] = {
                "available": False,
                "reason": "Package not installed",
            }
            logger.info("SSLyze is not available - package not installed")

        # Check for ZAP
        try:
            # Use our custom ZAPAdapter to check availability
            from scanning.integrations.zap_adapter import ZAPAdapter

            # Create adapter with hardcoded API key for availability check
            adapter = ZAPAdapter({"zap_host": "localhost", "zap_port": 8080})

            # Try to initialize the connection
            logger.info("Checking ZAP availability using ZAPAdapter")
            if adapter.initialize():
                available["zap"] = {
                    "available": True,
                    "host": adapter.host,
                    "port": adapter.port,
                }
                logger.info(f"ZAP is available at {adapter.host}:{adapter.port}")
            else:
                available["zap"] = {
                    "available": False,
                    "reason": "Failed to initialize ZAP connection",
                }
                logger.info("Failed to initialize ZAP connection")
        except Exception as e:
            available["zap"] = {
                "available": False,
                "reason": f"Error checking ZAP: {str(e)}",
            }
            logger.info(f"Error checking ZAP: {str(e)}")

        # Check for Nuclei - external binary
        try:
            nuclei_path = getattr(self.config, "nuclei_path", "nuclei")

            # Check if binary exists
            path = shutil.which(nuclei_path)
            if not path:
                available["nuclei"] = {"available": False, "reason": "Binary not found"}
                logger.info("Nuclei is not available - binary not found in PATH")
            else:
                # Check version
                try:
                    process = subprocess.run(
                        [nuclei_path, "-version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if process.returncode == 0:
                        version = process.stdout.strip()
                        available["nuclei"] = {
                            "available": True,
                            "version": version,
                            "path": path,
                        }
                        logger.info(f"Nuclei is available: {version}")
                    else:
                        available["nuclei"] = {
                            "available": False,
                            "reason": f"Error checking version: {process.stderr}",
                        }
                        logger.info(f"Nuclei error: {process.stderr}")
                except Exception as e:
                    available["nuclei"] = {
                        "available": False,
                        "reason": f"Error checking version: {str(e)}",
                    }
                    logger.info(f"Error checking Nuclei version: {str(e)}")
        except Exception as e:
            available["nuclei"] = {"available": False, "reason": str(e)}
            logger.info(f"Nuclei check error: {str(e)}")

        # Check for Wappalyzer - try Python package first, then npm package
        try:
            from Wappalyzer import Wappalyzer

            available["wappalyzer"] = {
                "available": True,
                "type": "python",
                "version": getattr(Wappalyzer, "__version__", "unknown"),
            }
            logger.info(f"Wappalyzer Python package is available")
        except ImportError:
            # Try node.js package
            try:
                process = subprocess.run(
                    ["wappalyzer", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if process.returncode == 0:
                    available["wappalyzer"] = {
                        "available": True,
                        "type": "node",
                        "version": process.stdout.strip(),
                    }
                    logger.info(
                        f"Wappalyzer Node.js package is available: {process.stdout.strip()}"
                    )
                else:
                    available["wappalyzer"] = {
                        "available": False,
                        "reason": "Not installed or error running",
                    }
                    logger.info("Wappalyzer is not available")
            except Exception:
                available["wappalyzer"] = {
                    "available": False,
                    "reason": "Not installed",
                }
                logger.info(
                    "Wappalyzer is not available - neither Python nor Node.js package found"
                )

        # Log overall availability
        available_count = sum(
            1 for tool in available.values() if tool.get("available", False)
        )
        logger.info(
            f"Tool availability check completed: {available_count} of {len(available)} tools available"
        )

        return available
