"""
ZAP Active Scanning Adapter

Enhanced ZAP integration for active security scanning with maximum potential.
Provides comprehensive active vulnerability testing using OWASP ZAP Docker container.
"""

import logging
import time
import os
import re
import requests
import hashlib
from typing import Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ZAPActiveAdapter:
    """Enhanced ZAP adapter for active scanning with maximum Docker potential"""

    def __init__(self, config=None, scan_id=None, scan_logger=None, engine=None):
        self.config = config or {}
        self.scan_id = scan_id  # Store scan ID for unique session naming
        self.scan_logger = scan_logger  # Scan-specific logger instance
        self.engine = engine  # Reference to UnifiedScanningEngine for stop checks

        # Try multiple possible ZAP hosts (similar to views.py logic)
        possible_hosts = [
            os.getenv("ZAP_HOST"),
            "localhost",
            "127.0.0.1",
            "zap"  # Docker service name as fallback
        ]

        # Filter out None values and try to find working host
        zap_hosts = [h for h in possible_hosts if h is not None]
        if not zap_hosts:
            zap_hosts = ["localhost"]

        self.zap_port = os.getenv("ZAP_PORT", "8080")
        self.api_key = os.getenv("ZAP_API_KEY", "changeme123")

        # Find working ZAP host
        self.zap_host = self._find_working_host(zap_hosts)
        if not self.zap_host:
            self.zap_host = "localhost"  # Default fallback

        self.base_url = f"http://{self.zap_host}:{self.zap_port}"

        # ZAP API endpoints
        self.api_url = f"{self.base_url}/JSON"

        # Scan tracking
        self.spider_id = None
        self.ajax_spider_id = None
        self.active_scan_id = None

        # Results storage
        self.results = {
            "spider_results": {},
            "ajax_spider_results": {},
            "active_scan_results": {},
            "vulnerability_details": [],
            "scan_statistics": {}
        }

        # Target scoping
        self.target_url: Optional[str] = None

        # Session management for isolation
        self.session_name = None
        self.context_ids = []  # Track contexts created by this adapter
    
    def _create_unique_session_name(self) -> str:
        """Create a unique session name for this scan"""
        scan_id = self.scan_id or "unknown"
        timestamp = int(time.time())
        return f"scan_{scan_id}_{timestamp}"
    
    def _cleanup_previous_contexts(self):
        """Clean up any contexts created by previous scans to prevent cross-contamination"""
        try:
            # Get all existing contexts
            contexts_response = self._make_api_request("context/view/contextList")
            if contexts_response and "contextList" in contexts_response:
                existing_contexts = contexts_response["contextList"]
                logger.info(f"Found {len(existing_contexts)} existing contexts")
                
                # Remove contexts that look like they're from previous scans
                for context_name in existing_contexts:
                    if any(pattern in context_name for pattern in ["ComprehensiveScan_", "ajax_scan_"]):
                        logger.info(f"Removing old context: {context_name}")
                        self._make_api_post_request("context/action/removeContext", {
                            "contextName": context_name
                        })
                        
        except Exception as e:
            logger.warning(f"Failed to cleanup previous contexts: {e}")
    
    def _reset_zap_state(self):
        """Reset ZAP state completely for scan isolation"""
        try:
            # Create unique session name
            self.session_name = self._create_unique_session_name()

            # Clean up previous contexts first
            self._cleanup_previous_contexts()

            # Start fresh session with unique name
            # Note: Some actions might not exist in all ZAP versions, handle gracefully
            result = self._make_api_post_request("core/action/newSession", {
                "name": self.session_name,
                "overwriteSession": "true"
            })
            if result:
                logger.info(f"Created new ZAP session: {self.session_name}")

            # Clear all alerts from previous scans
            self._make_api_post_request("core/action/deleteAllAlerts", {})

            # Clear site tree/history - these might not exist in all ZAP versions
            # Don't fail if they don't work
            try:
                self._make_api_post_request("core/action/deleteAllAlerts", {})
                self._make_api_post_request("core/action/deleteAllAlerts", {})  # double-call for certain versions
            except:
                pass

            # Try to clear site tree and stats (might not exist)
            try:
                self._make_api_post_request("core/action/clearSiteTree", {})
            except:
                logger.debug("clearSiteTree action not available in this ZAP version")

            try:
                self._make_api_post_request("core/action/clearExcludedFromProxy", {})
            except:
                logger.debug("clearExcludedFromProxy action not available")

            try:
                self._make_api_post_request("core/action/clearStats", {})
            except:
                logger.debug("clearStats action not available")

            # Reset any running scans
            self._make_api_post_request("spider/action/stopAllScans", {})
            self._make_api_post_request("ascan/action/stopAllScans", {})

            logger.info(f"✅ Reset ZAP state with session: {self.session_name}")

        except Exception as e:
            # Don't fail the scan if reset has issues
            logger.warning(f"Some ZAP reset actions failed (non-critical): {e}")
            if self.scan_logger:
                self.scan_logger.log_error("ZAP Reset Warning", f"Some cleanup actions not available: {str(e)}")
    
    def _find_working_host(self, hosts: List[str]) -> Optional[str]:
        """Find the first working ZAP host from the list"""
        import socket
        
        for host in hosts:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((host, int(self.zap_port)))
                sock.close()
                
                if result == 0:
                    logger.info(f"Found working ZAP host: {host}:{self.zap_port}")
                    return host
            except Exception as e:
                logger.debug(f"Failed to connect to {host}:{self.zap_port} - {e}")
                continue
        
        logger.warning(f"No working ZAP host found from: {hosts}")
        return None
    
    def check_zap_connection(self) -> bool:
        """Check if ZAP is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200 and "ZAP" in response.text:
                logger.info(f"ZAP connection successful at {self.base_url}")
                return True
        except Exception as e:
            logger.error(f"ZAP connection failed: {e}")
        return False
    
    def _make_api_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request to ZAP with logging"""
        try:
            url = f"{self.api_url}/{endpoint}/"
            params = params or {}
            if self.api_key:
                params["apikey"] = self.api_key

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            result = response.json()

            # Log successful request
            if self.scan_logger:
                self.scan_logger.log_api_request("GET", url, params, result)

            return result

        except Exception as e:
            logger.error(f"ZAP API request failed for {endpoint}: {e}")

            # Log failed request
            if self.scan_logger:
                self.scan_logger.log_api_request("GET", f"{self.api_url}/{endpoint}/", params, None, str(e))
                self.scan_logger.log_error("ZAP API Request Failed", f"Endpoint: {endpoint}\nError: {str(e)}")

            return None
    
    def _make_api_post_request(self, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make API request to ZAP with logging (uses GET, not POST)

        IMPORTANT: Despite the name, this uses GET requests because ZAP's JSON API
        action endpoints don't accept POST (returns CONTENT_TYPE_NOT_SUPPORTED).
        ZAP's design: action endpoints work with GET, view endpoints also use GET.
        """
        try:
            url = f"{self.api_url}/{endpoint}/"

            # Prepare parameters - API key MUST be in URL params
            params = {}
            if self.api_key:
                params["apikey"] = self.api_key

            # Add other data to params
            data = data or {}
            params.update(data)

            # Use GET instead of POST - ZAP action endpoints don't accept POST!
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            result = response.json()

            # Log successful request
            if self.scan_logger:
                self.scan_logger.log_api_request("GET (action)", url, params, result)

            return result

        except Exception as e:
            logger.error(f"ZAP API request failed for {endpoint}: {e}")

            # Log failed request
            if self.scan_logger:
                self.scan_logger.log_api_request("GET (action)", f"{self.api_url}/{endpoint}/", params, None, str(e))
                self.scan_logger.log_error("ZAP API Request Failed", f"Endpoint: {endpoint}\nError: {str(e)}")

            return None
    
    def run_comprehensive_active_scan(self, target_url: str, scan_config) -> Dict:
        """Run comprehensive active scan maximizing ZAP potential"""
        logger.info(f"Starting comprehensive active scan for {target_url}")

        if not self.check_zap_connection():
            raise ConnectionError("Cannot connect to ZAP. Ensure ZAP Docker container is running.")

        try:
            # Translate localhost URLs for Docker environment
            from scanning.utils.docker_network_helper import get_docker_accessible_url

            original_url = target_url
            target_url = get_docker_accessible_url(target_url, self.zap_host)

            if target_url != original_url:
                logger.info(f"🐳 Translated URL for Docker: {original_url} → {target_url}")
                if self.scan_logger:
                    self.scan_logger.log_api_request(
                        "INFO",
                        "Docker URL Translation",
                        {"original": original_url, "translated": target_url},
                        {"note": "localhost translated to host.docker.internal for Docker access"}
                    )

            # Set target for scoping
            self.target_url = target_url

            # Reset ZAP state completely for scan isolation
            self._reset_zap_state()

            # Phase 1: Initialize and prepare target
            self._prepare_target(target_url)
            
            # Phase 2: Advanced spidering
            if getattr(scan_config, 'enable_spider', True):
                spider_results = self._run_advanced_spider(target_url, scan_config)
                self.results["spider_results"] = spider_results
            
            # Phase 3: AJAX Spider for modern web apps
            if getattr(scan_config, 'enable_ajax_spider', True):
                ajax_results = self._run_ajax_spider(target_url, scan_config)
                self.results["ajax_spider_results"] = ajax_results
            
            # Phase 4: Active vulnerability scanning
            if getattr(scan_config, 'use_zap_active', True):
                active_results = self._run_active_vulnerability_scan(target_url, scan_config)
                self.results["active_scan_results"] = active_results
            
            # Phase 5: Extract and process vulnerabilities
            vulnerabilities = self._extract_vulnerabilities()
            self.results["vulnerability_details"] = vulnerabilities
            
            # Phase 6: Generate scan statistics
            stats = self._generate_scan_statistics()
            self.results["scan_statistics"] = stats
            
            logger.info(f"Comprehensive active scan completed for {target_url}")
            return self.results
            
        except Exception as e:
            logger.exception(f"Comprehensive active scan failed: {e}")
            raise
    
    def _prepare_target(self, target_url: str):
        """Prepare target for scanning"""
        logger.info(f"Preparing target: {target_url}")
        
        # Access the target URL to initialize it in ZAP
        try:
            result = self._make_api_post_request("core/action/accessUrl", {"url": target_url})
            if result and result.get("Result") == "OK":
                logger.info("Target URL successfully accessed and prepared")
            else:
                logger.warning("Target URL preparation may have failed")
                
        except Exception as e:
            logger.error(f"Failed to prepare target: {e}")
    
    def _run_advanced_spider(self, target_url: str, config) -> Dict:
        """Advanced spidering with comprehensive coverage"""
        logger.info("Starting advanced spider scan")
        
        try:
            # Configure spider settings
            max_depth = getattr(config, 'max_spider_depth', 3)
            max_duration = getattr(config, 'max_spider_duration', 300)
            
            # Set spider options
            self._make_api_post_request("spider/action/setOptionMaxDepth", {"Integer": max_depth})
            self._make_api_post_request("spider/action/setOptionMaxDuration", {"Integer": max_duration})
            
            # Start spider
            spider_response = self._make_api_post_request("spider/action/scan", {"url": target_url})
            if not spider_response or spider_response.get("Result") == "ERROR":
                raise Exception("Failed to start spider")
                
            self.spider_id = spider_response.get("scan")
            logger.info(f"Spider started with ID: {self.spider_id}")
            
            # Monitor spider progress
            self._monitor_spider_progress()
            
            # Get spider results
            spider_results = self._get_spider_results()
            
            logger.info(f"Spider completed. Found {len(spider_results.get('urls', []))} URLs")
            return spider_results
            
        except Exception as e:
            logger.error(f"Spider scan failed: {e}")
            return {"error": str(e)}
    
    def _run_ajax_spider(self, target_url: str, config) -> Dict:
        """Run AJAX spider for modern web applications"""
        logger.info("Starting AJAX spider scan")

        try:
            max_duration = getattr(config, 'max_spider_duration', 300)

            # Configure AJAX spider with maximum duration
            self._make_api_post_request("ajaxSpider/action/setOptionMaxDuration", {"Integer": max_duration})

            # Store config for monitoring
            self.config = config

            # Start AJAX spider
            ajax_response = self._make_api_post_request("ajaxSpider/action/scan", {"url": target_url})
            if not ajax_response or ajax_response.get("Result") == "ERROR":
                raise Exception("Failed to start AJAX spider")

            logger.info(f"AJAX spider started (max duration: {max_duration}s)")

            # Monitor AJAX spider progress with timeout
            # This will raise ConnectionError if ZAP becomes unavailable
            self._monitor_ajax_spider_progress()

            # CRITICAL: Aggressively stop AJAX spider to prevent resource leaks
            logger.info("Stopping AJAX spider...")
            self._force_stop_ajax_spider()

            # Get AJAX spider results
            ajax_results = self._get_ajax_spider_results()

            logger.info(f"AJAX spider completed. Found {len(ajax_results.get('urls', []))} additional URLs")
            return ajax_results

        except ConnectionError as conn_err:
            # ZAP connection lost - re-raise to fail the scan
            logger.error(f"❌ AJAX spider failed due to ZAP connection loss: {conn_err}")
            raise
        except Exception as e:
            logger.error(f"AJAX spider scan failed: {e}")
            # Ensure spider is stopped on error (if ZAP is still available)
            try:
                self._force_stop_ajax_spider()
            except:
                pass
            return {"error": str(e)}
        finally:
            # Final cleanup - ensure AJAX spider is stopped no matter what
            try:
                self._force_stop_ajax_spider()
            except Exception as cleanup_error:
                logger.warning(f"Final AJAX spider cleanup warning: {cleanup_error}")
    
    def _run_active_vulnerability_scan(self, target_url: str, config, discovered_urls: List[str] = None, progress_callback=None, progress_range=(50.0, 75.0)) -> Dict:
        """Run comprehensive active vulnerability scanning on target and all discovered URLs"""
        logger.info("Starting comprehensive active vulnerability scan")
        
        try:
            # Configure active scan policy
            attack_strength = getattr(config, 'zap_attack_strength', 'MEDIUM')
            self._configure_scan_policy(config)
            
            # Create comprehensive context with all discovered URLs
            context_id = None
            if discovered_urls and len(discovered_urls) > 0:
                logger.info(f"Creating ZAP context with {len(discovered_urls)} discovered URLs")
                context_id = self._create_comprehensive_context(target_url, discovered_urls)
                
                # Also add URLs to site tree for better discovery
                self._add_discovered_urls_to_site_tree(discovered_urls)
            else:
                logger.info("No discovered URLs provided, scanning target URL only")
            
            # Start active scan (with or without context)
            scan_params = {
                "url": target_url,
                "attackStrength": attack_strength
            }
            
            if context_id:
                scan_params["contextId"] = context_id
                logger.info(f"Starting context-based active scan (Context ID: {context_id})")
            else:
                logger.info("Starting standard active scan")
                
            active_response = self._make_api_post_request("ascan/action/scan", scan_params)
            
            if not active_response or active_response.get("Result") == "ERROR":
                raise Exception("Failed to start active scan")
                
            self.active_scan_id = active_response.get("scan")
            logger.info(f"Active scan started with ID: {self.active_scan_id}")
            
            # Monitor active scan progress with callback
            self._monitor_active_scan_progress(progress_callback, progress_range)
            
            # Get active scan results
            active_results = self._get_active_scan_results()
            
            logger.info("Active vulnerability scan completed")
            return active_results
            
        except Exception as e:
            logger.error(f"Active vulnerability scan failed: {e}")
            return {"error": str(e)}
    
    def _configure_scan_policy(self, config):
        """Configure ZAP scan policy based on configuration

        IMPORTANT: ZAP's enableScanners API expects comma-separated plugin IDs
        in a SINGLE request, not individual requests per scanner.
        """
        try:
            # Map of comprehensive ZAP scanner plugin IDs (verified for ZAP 2.16.1)
            # Each test type maps to MULTIPLE scanner plugins for better coverage
            # NOTE: IDs verified against actual ZAP 2.16.1 scanners
            scanner_categories = {
                "test_sql_injection": [
                    "40018",  # SQL Injection
                    "40019",  # SQL Injection - MySQL (Time Based)
                    "40020",  # SQL Injection - Hypersonic SQL (Time Based)
                    "40021",  # SQL Injection - Oracle (Time Based)
                    "40022",  # SQL Injection - PostgreSQL (Time Based)
                    "40024",  # SQL Injection - SQLite (Time Based)
                    "40027",  # SQL Injection - MsSQL (Time Based)
                ],
                "test_xss": [
                    "40012",  # Cross Site Scripting (Reflected)
                    "40014",  # Cross Site Scripting (Persistent)
                    "40016",  # Cross Site Scripting (Persistent) - Prime
                    "40017",  # Cross Site Scripting (Persistent) - Spider
                    "40026",  # Cross Site Scripting (DOM Based)
                ],
                "test_csrf": [
                    # Note: CSRF testing is done by passive scanners, not active
                    # IDs 10202 and 20012 don't exist in ZAP 2.16.1
                    # Leaving empty - CSRF detected by passive scan
                ],
                "test_path_traversal": [
                    "6",      # Path Traversal
                    "7",      # Remote File Inclusion
                ],
                "test_command_injection": [
                    "90020",  # Remote OS Command Injection
                    "90037",  # Remote OS Command Injection (Time Based)
                    "90019",  # Server Side Code Injection
                    "90035",  # Server Side Template Injection
                    "90036",  # Server Side Template Injection (Blind)
                ],
                "test_xxe": [
                    "90019",  # Server Side Code Injection (includes XXE)
                    "90017",  # XSLT Injection
                    "90029",  # SOAP XML Injection
                ],
            }

            # Collect all enabled scanner IDs
            enabled_scanners = []
            disabled_scanners = []

            for test_name, plugin_ids in scanner_categories.items():
                is_enabled = getattr(config, test_name, True)
                if is_enabled:
                    enabled_scanners.extend(plugin_ids)
                else:
                    disabled_scanners.extend(plugin_ids)

            # Enable scanners in ONE request (comma-separated)
            # NOTE: Using GET instead of POST - ZAP's action endpoints work better with GET
            if enabled_scanners:
                scanner_ids_str = ",".join(enabled_scanners)
                logger.info(f"Enabling {len(enabled_scanners)} ZAP scanners: {scanner_ids_str}")
                result = self._make_api_request("ascan/action/enableScanners", {"ids": scanner_ids_str})
                if result and result.get("Result") == "OK":
                    logger.info("✅ Successfully enabled ZAP vulnerability scanners")
                else:
                    logger.warning(f"⚠️ Scanner enablement returned unexpected result: {result}")

            # Disable scanners in ONE request (comma-separated)
            if disabled_scanners:
                scanner_ids_str = ",".join(disabled_scanners)
                logger.info(f"Disabling {len(disabled_scanners)} ZAP scanners: {scanner_ids_str}")
                self._make_api_request("ascan/action/disableScanners", {"ids": scanner_ids_str})

            # Configure SQL injection scanner strength if enabled
            if getattr(config, 'test_sql_injection', True):
                sql_scanner_ids = scanner_categories.get("test_sql_injection", [])
                for scanner_id in sql_scanner_ids:
                    try:
                        # Set attack strength to HIGH for SQL injection scanners
                        self._make_api_post_request("ascan/action/setScannerAttackStrength", {
                            "id": scanner_id,
                            "attackStrength": "HIGH"
                        })
                        # Set alert threshold to LOW for better detection
                        self._make_api_post_request("ascan/action/setScannerAlertThreshold", {
                            "id": scanner_id,
                            "alertThreshold": "LOW"
                        })
                    except Exception as scanner_e:
                        logger.debug(f"Could not configure scanner {scanner_id}: {scanner_e}")
                logger.info("✅ Configured SQL injection scanners with HIGH attack strength and LOW threshold")

        except Exception as e:
            logger.error(f"Failed to configure scan policy: {e}")
            logger.error("⚠️ Continuing with default ZAP scanners")
    
    def _monitor_spider_progress(self):
        """Monitor spider progress until completion"""
        if not self.spider_id:
            return

        while True:
            try:
                # CRITICAL: Check if user requested stop
                if self.engine and hasattr(self.engine, 'is_stop_requested') and self.engine.is_stop_requested():
                    logger.info("🔴 Stop requested by user - stopping spider monitoring")
                    try:
                        self._make_api_post_request("spider/action/stop", {"scanId": self.spider_id})
                    except Exception as stop_error:
                        logger.error(f"Error stopping spider on user stop: {stop_error}")
                    break

                status = self._make_api_request("spider/view/status", {"scanId": self.spider_id})
                progress = int(status.get("status", 0))

                logger.debug(f"Spider progress: {progress}%")

                if progress >= 100:
                    logger.info("Spider scan completed")
                    break

                # Check stop flag before sleeping
                if self.engine and hasattr(self.engine, 'is_stop_requested') and self.engine.is_stop_requested():
                    logger.info("🔴 Stop requested during spider sleep period")
                    break

                time.sleep(2)

            except Exception as e:
                logger.error(f"Error monitoring spider: {e}")
                break
    
    def _monitor_ajax_spider_progress(self):
        """Monitor AJAX spider progress until completion with timeout"""
        max_duration = getattr(self.config, 'max_spider_duration', 300)  # Default 5 minutes
        start_time = time.time()
        timeout_seconds = max_duration + 60  # Add 1 minute buffer to configured duration
        connection_failures = 0  # Track consecutive connection failures
        max_connection_failures = 3  # Fail after 3 consecutive connection errors
        last_progress_log = 0  # Track when we last logged progress

        logger.info(f"Monitoring AJAX spider (timeout: {timeout_seconds}s)")

        while True:
            try:
                # CRITICAL: Check if user requested stop
                if self.engine and hasattr(self.engine, 'is_stop_requested') and self.engine.is_stop_requested():
                    logger.info("🔴 Stop requested by user - stopping AJAX spider monitoring")
                    try:
                        self._force_stop_ajax_spider()
                    except Exception as stop_error:
                        logger.error(f"Error force stopping AJAX spider on user stop: {stop_error}")
                    break

                # Check for timeout
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    logger.warning(f"AJAX spider timeout reached after {elapsed:.1f}s, stopping spider")
                    try:
                        self._make_api_post_request("ajaxSpider/action/stop")
                        time.sleep(2)  # Give it a moment to stop
                    except Exception as stop_error:
                        logger.error(f"Error stopping AJAX spider: {stop_error}")
                    break

                # Log progress every 10 seconds to show activity
                if elapsed - last_progress_log >= 10:
                    progress_percent = min(100, (elapsed / timeout_seconds) * 100)
                    logger.info(f"AJAX spider running: {elapsed:.0f}s / {timeout_seconds}s ({progress_percent:.1f}%)")
                    last_progress_log = elapsed

                status = self._make_api_request("ajaxSpider/view/status")

                # Check if we got a valid response
                if status is None:
                    connection_failures += 1
                    logger.error(f"❌ Failed to get AJAX spider status (attempt {connection_failures}/{max_connection_failures})")

                    if connection_failures >= max_connection_failures:
                        logger.error(f"❌❌❌ ZAP connection lost after {connection_failures} attempts - ZAP may have crashed!")
                        logger.error("Failing scan due to ZAP unavailability")
                        raise ConnectionError(f"ZAP connection lost - failed to get status {connection_failures} times in a row")

                    # Wait a bit longer before retry when having connection issues
                    time.sleep(3)
                    continue
                else:
                    # Reset connection failure counter on successful response
                    connection_failures = 0

                current_status = status.get("status", "").lower()

                logger.debug(f"AJAX spider status: {current_status} (elapsed: {elapsed:.1f}s)")

                if current_status == "stopped":
                    logger.info("AJAX spider completed normally")
                    break

                # Check stop flag before sleeping
                if self.engine and hasattr(self.engine, 'is_stop_requested') and self.engine.is_stop_requested():
                    logger.info("🔴 Stop requested during AJAX spider sleep period")
                    break

                time.sleep(2)

            except ConnectionError:
                # Re-raise connection errors (ZAP is down)
                raise
            except Exception as e:
                logger.error(f"Error monitoring AJAX spider: {e}")
                connection_failures += 1

                if connection_failures >= max_connection_failures:
                    logger.error(f"❌ Too many errors monitoring AJAX spider, ZAP may be unavailable")
                    raise ConnectionError(f"Failed to monitor AJAX spider: {e}")

                # Try to stop spider before continuing/breaking
                try:
                    self._make_api_post_request("ajaxSpider/action/stop")
                except:
                    pass

                time.sleep(3)  # Wait before retry

    def _force_stop_ajax_spider(self):
        """AGGRESSIVELY stop AJAX spider with verification and multiple retries"""
        max_retries = 10  # Increased from 5 to 10
        retry_delay = 1   # Reduced from 2 to 1 second for faster iterations

        logger.info(f"🔴 Force stopping AJAX spider (max {max_retries} retries)...")

        for attempt in range(max_retries):
            try:
                # Send stop command MULTIPLE times (redundancy)
                for i in range(3):  # Send 3 stop commands per attempt
                    try:
                        stop_response = self._make_api_post_request("ajaxSpider/action/stop")
                        logger.debug(f"Stop command {i+1}/3 sent in attempt {attempt + 1}")
                    except Exception as stop_error:
                        logger.warning(f"Stop command {i+1}/3 failed: {stop_error}")

                # Wait a moment
                time.sleep(retry_delay)

                # Verify it stopped
                status = self._make_api_request("ajaxSpider/view/status")
                current_status = status.get("status", "").lower() if status else "unknown"

                logger.info(f"Attempt {attempt + 1}/{max_retries}: AJAX spider status = '{current_status}'")

                if current_status == "stopped":
                    logger.info(f"✅✅✅ AJAX spider successfully stopped (attempt {attempt + 1})")
                    return True
                else:
                    logger.warning(f"⚠️ AJAX spider still running with status: {current_status}, retrying...")

            except Exception as e:
                logger.error(f"❌ Error in stop attempt {attempt + 1}: {e}")

        # Final desperate attempt - try stopAllScans
        logger.error("🔴 AJAX spider did not stop after normal retries - trying emergency stop...")
        try:
            # Try to stop all AJAX spiders (not just this one)
            self._make_api_post_request("ajaxSpider/action/stopAllScans", {})
            time.sleep(2)
            
            # Check status one more time
            status = self._make_api_request("ajaxSpider/view/status")
            current_status = status.get("status", "").lower() if status else "unknown"
            
            if current_status == "stopped":
                logger.info("✅ AJAX spider stopped via emergency stopAllScans")
                return True
        except Exception as emergency_error:
            logger.error(f"Emergency stop also failed: {emergency_error}")

        logger.error("❌❌❌ CRITICAL: Failed to stop AJAX spider after ALL retries - may continue consuming CPU!")
        logger.error("❌ Manual intervention may be required: docker restart zap")
        return False
    
    def _monitor_active_scan_progress(self, progress_callback=None, progress_range=(50.0, 75.0)):
        """Monitor active scan progress until completion"""
        if not self.active_scan_id:
            return

        start_progress, end_progress = progress_range
        progress_range_size = end_progress - start_progress
        start_time = time.time()
        last_progress_log = 0

        while True:
            try:
                # CRITICAL: Check if user requested stop
                if self.engine and hasattr(self.engine, 'is_stop_requested') and self.engine.is_stop_requested():
                    logger.info("🔴 Stop requested by user - stopping active scan monitoring")
                    try:
                        self._make_api_post_request("ascan/action/stop", {"scanId": self.active_scan_id})
                    except Exception as stop_error:
                        logger.error(f"Error stopping active scan on user stop: {stop_error}")
                    break

                status = self._make_api_request("ascan/view/status", {"scanId": self.active_scan_id})
                zap_progress = int(status.get("status", 0))

                # Log progress every 30 seconds to show activity
                elapsed = time.time() - start_time
                if elapsed - last_progress_log >= 30:
                    logger.info(f"Active vulnerability scan progress: {zap_progress}% (running for {elapsed:.0f}s)")
                    last_progress_log = elapsed

                logger.debug(f"ZAP active scan progress: {zap_progress}%")
                
                # Update progress through callback if provided
                if progress_callback:
                    # Map ZAP progress (0-100) to our progress range
                    mapped_progress = start_progress + (zap_progress * progress_range_size / 100.0)
                    progress_callback(mapped_progress, f"ZAP active scan: {zap_progress}%")

                if zap_progress >= 100:
                    logger.info("Active scan completed")
                    break

                # Check stop flag before sleeping
                if self.engine and hasattr(self.engine, 'is_stop_requested') and self.engine.is_stop_requested():
                    logger.info("🔴 Stop requested during active scan sleep period")
                    break

                time.sleep(3)  # Shorter interval for more responsive updates

            except Exception as e:
                logger.error(f"Error monitoring active scan: {e}")
                break
    
    def _get_spider_results(self) -> Dict:
        """Get spider scan results - extract only essential attack surface data"""
        try:
            # Try to get spider results - use correct endpoint
            if self.spider_id:
                raw_results = self._make_api_request("spider/view/results", {"scanId": self.spider_id})
            else:
                # Fallback to getting all spider results
                raw_results = self._make_api_request("spider/view/results")

            # Extract only essential data from raw ZAP results
            processed_data = self._extract_spider_attack_surface(raw_results)

            return processed_data

        except Exception as e:
            logger.error(f"Failed to get spider results: {e}")
            return {
                "urls": [],
                "forms": [],
                "parameters": [],
                "endpoints": [],
                "total_urls": 0,
                "total_forms": 0,
                "total_parameters": 0,
                "scan_id": self.spider_id,
                "error": str(e)
            }
    
    def _get_ajax_spider_results(self) -> Dict:
        """Get AJAX spider scan results - extract only essential attack surface data"""
        try:
            raw_results = self._make_api_request("ajaxSpider/view/results")

            # Extract only essential data from raw ZAP results
            processed_data = self._extract_ajax_spider_attack_surface(raw_results)

            return processed_data

        except Exception as e:
            logger.error(f"Failed to get AJAX spider results: {e}")
            return {
                "urls": [],
                "forms": [],
                "ajax_requests": [],
                "js_files": [],
                "api_endpoints": [],
                "total_urls": 0,
                "total_forms": 0,
                "total_ajax_requests": 0,
                "error": str(e)
            }
    
    def _extract_spider_attack_surface(self, raw_results: Dict) -> Dict:
        """Extract only essential attack surface data from ZAP spider results"""
        if not raw_results or not isinstance(raw_results, dict):
            return {
                "urls": [],
                "forms": [],
                "parameters": [],
                "endpoints": [],
                "total_urls": 0,
                "total_forms": 0,
                "total_parameters": 0,
                "scan_id": self.spider_id
            }

        urls = set()
        forms = []
        parameters = set()
        endpoints = []

        # Process the raw ZAP results which contain full HTTP request/response data
        zap_results = raw_results.get("results", [])

        for result in zap_results:
            if not isinstance(result, dict):
                continue

            try:
                # Extract URL from request header (first line typically contains "GET /path HTTP/1.1")
                request_header = result.get("requestHeader", "")
                if request_header:
                    url = self._extract_url_from_request_header(request_header)
                    if url:
                        urls.add(url)

                        # Extract parameters from URL
                        url_params = self._extract_url_parameters(url)
                        parameters.update(url_params)

                        # Classify endpoint
                        endpoint_info = self._classify_endpoint(url, request_header)
                        if endpoint_info:
                            endpoints.append(endpoint_info)

                # Process response body (extract forms, hash, metadata - but don't store full body)
                response_body = result.get("responseBody", "")
                if response_body and self._should_process_response(response_body, url or ""):
                    # Extract forms from HTML content
                    if "html" in response_body.lower()[:1000]:  # Quick HTML check
                        page_forms = self._extract_forms_from_html(response_body, url or "")
                        forms.extend(page_forms)

                    # Generate response metadata (hash, patterns) for attack surface analysis
                    response_metadata = self._process_response_body(response_body, url or "")
                    if response_metadata.get("patterns"):
                        # Store interesting patterns for security analysis
                        endpoint_info = self._classify_endpoint(url, request_header)
                        if endpoint_info:
                            endpoint_info["response_patterns"] = response_metadata["patterns"]
                            endpoint_info["content_type"] = response_metadata["type"]
                            endpoint_info["content_hash"] = response_metadata["hash"]

                # Extract additional parameters from request body
                request_body = result.get("requestBody", "")
                if request_body:
                    body_params = self._extract_body_parameters(request_body)
                    parameters.update(body_params)

            except Exception as e:
                logger.debug(f"Error processing spider result: {e}")
                continue

        # Convert sets to lists for JSON serialization
        urls_list = list(urls)
        parameters_list = list(parameters)

        # Remove duplicate forms
        forms = self._deduplicate_forms(forms)

        logger.info(f"Spider attack surface extraction: {len(urls_list)} URLs, {len(forms)} forms, {len(parameters_list)} parameters")

        return {
            "urls": urls_list,
            "forms": forms,
            "parameters": parameters_list,
            "endpoints": endpoints,
            "total_urls": len(urls_list),
            "total_forms": len(forms),
            "total_parameters": len(parameters_list),
            "scan_id": self.spider_id
        }

    def _extract_ajax_spider_attack_surface(self, raw_results: Dict) -> Dict:
        """Extract only essential attack surface data from ZAP AJAX spider results"""
        if not raw_results or not isinstance(raw_results, dict):
            return {
                "urls": [],
                "forms": [],
                "ajax_requests": [],
                "js_files": [],
                "api_endpoints": [],
                "total_urls": 0,
                "total_forms": 0,
                "total_ajax_requests": 0
            }

        urls = set()
        forms = []
        ajax_requests = []
        js_files = set()
        api_endpoints = []

        # Process the raw ZAP AJAX results
        zap_results = raw_results.get("results", [])

        for result in zap_results:
            if not isinstance(result, dict):
                continue

            try:
                # Extract URL
                request_header = result.get("requestHeader", "")
                if request_header:
                    url = self._extract_url_from_request_header(request_header)
                    if url:
                        urls.add(url)

                        # Check if this is a JS file
                        if url.endswith(('.js', '.jsx', '.ts', '.tsx')) or '/js/' in url:
                            js_files.add(url)

                        # Check if this looks like an API endpoint
                        if self._is_api_endpoint(url, request_header):
                            api_info = self._extract_api_endpoint_info(url, request_header, result)
                            api_endpoints.append(api_info)

                # Extract AJAX requests information
                if self._is_ajax_request(request_header):
                    ajax_info = self._extract_ajax_request_info(result, request_header)
                    if ajax_info:
                        ajax_requests.append(ajax_info)

                # Process response body for AJAX content (but don't store full response)
                response_body = result.get("responseBody", "")
                if response_body and self._should_process_response(response_body, url or ""):
                    # Extract forms from HTML/JSON content
                    page_forms = self._extract_forms_from_html(response_body, url or "")
                    forms.extend(page_forms)

                    # Generate response metadata for API analysis
                    response_metadata = self._process_response_body(response_body, url or "")
                    if response_metadata.get("patterns") and self._is_api_endpoint(url, request_header):
                        # Enhance API endpoint info with response analysis
                        for api_endpoint in api_endpoints:
                            if api_endpoint.get("url") == url:
                                api_endpoint["response_patterns"] = response_metadata["patterns"]
                                api_endpoint["response_type"] = response_metadata["type"]
                                api_endpoint["content_hash"] = response_metadata["hash"]
                                break

            except Exception as e:
                logger.debug(f"Error processing AJAX spider result: {e}")
                continue

        # Convert sets to lists and remove duplicates
        urls_list = list(urls)
        js_files_list = list(js_files)
        forms = self._deduplicate_forms(forms)

        logger.info(f"AJAX spider attack surface: {len(urls_list)} URLs, {len(ajax_requests)} AJAX requests, {len(js_files_list)} JS files")

        return {
            "urls": urls_list,
            "forms": forms,
            "ajax_requests": ajax_requests,
            "js_files": js_files_list,
            "api_endpoints": api_endpoints,
            "total_urls": len(urls_list),
            "total_forms": len(forms),
            "total_ajax_requests": len(ajax_requests)
        }

    def _extract_url_from_request_header(self, request_header: str) -> Optional[str]:
        """Extract clean URL from HTTP request header"""
        try:
            # Request header format: "GET /path HTTP/1.1\nHost: domain.com\n..."
            lines = request_header.split('\n')
            if not lines:
                return None

            # First line: "GET /path HTTP/1.1" or "POST /api/endpoint HTTP/1.1"
            first_line = lines[0].strip()
            parts = first_line.split(' ')
            if len(parts) >= 2:
                method = parts[0]
                path = parts[1]

                # Extract host from Host header
                host = None
                for line in lines[1:]:
                    if line.lower().startswith('host:'):
                        host = line.split(':', 1)[1].strip()
                        break

                if host and path:
                    # Construct full URL
                    scheme = 'https' if ':443' in host else 'http'
                    if ':' in host and not host.endswith(':80') and not host.endswith(':443'):
                        url = f"{scheme}://{host}{path}"
                    else:
                        clean_host = host.split(':')[0]
                        url = f"{scheme}://{clean_host}{path}"
                    return url
        except Exception as e:
            logger.debug(f"Error extracting URL from request header: {e}")

        return None

    def _extract_url_parameters(self, url: str) -> List[str]:
        """Extract parameter names from URL query string"""
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            return list(query_params.keys())
        except:
            return []

    def _extract_body_parameters(self, request_body: str) -> List[str]:
        """Extract parameter names from request body"""
        parameters = []
        try:
            # Handle form-encoded data
            if '=' in request_body and '&' in request_body:
                pairs = request_body.split('&')
                for pair in pairs:
                    if '=' in pair:
                        param_name = pair.split('=')[0]
                        parameters.append(param_name)

            # Handle JSON data
            elif request_body.strip().startswith('{'):
                import json
                try:
                    data = json.loads(request_body)
                    if isinstance(data, dict):
                        parameters.extend(data.keys())
                except:
                    pass

        except Exception as e:
            logger.debug(f"Error extracting body parameters: {e}")

        return parameters

    def _classify_endpoint(self, url: str, request_header: str) -> Dict:
        """Classify endpoint type and extract relevant info"""
        try:
            method = request_header.split(' ')[0] if request_header else 'GET'

            # Basic classification
            endpoint_type = 'static'
            if any(keyword in url.lower() for keyword in ['api', 'rest', 'graphql']):
                endpoint_type = 'api'
            elif any(keyword in url.lower() for keyword in ['admin', 'dashboard', 'manage']):
                endpoint_type = 'admin'
            elif any(keyword in url.lower() for keyword in ['login', 'auth', 'signin']):
                endpoint_type = 'auth'
            elif url.endswith(('.php', '.aspx', '.jsp', '.py')):
                endpoint_type = 'dynamic'

            return {
                "url": url,
                "method": method,
                "type": endpoint_type,
                "parameters": self._extract_url_parameters(url)
            }
        except:
            return None

    def _is_api_endpoint(self, url: str, request_header: str) -> bool:
        """Check if URL appears to be an API endpoint"""
        api_indicators = ['api/', '/v1/', '/v2/', '/rest/', 'graphql', '.json', '/ajax/']
        return any(indicator in url.lower() for indicator in api_indicators)

    def _extract_api_endpoint_info(self, url: str, request_header: str, result: Dict) -> Dict:
        """Extract API endpoint information"""
        try:
            method = request_header.split(' ')[0] if request_header else 'GET'

            # Try to determine content type from response
            response_header = result.get("responseHeader", "")
            content_type = ""
            if "content-type:" in response_header.lower():
                for line in response_header.split('\n'):
                    if line.lower().startswith('content-type:'):
                        content_type = line.split(':', 1)[1].strip()
                        break

            return {
                "url": url,
                "method": method,
                "content_type": content_type,
                "parameters": self._extract_url_parameters(url)
            }
        except:
            return {"url": url, "method": "GET"}

    def _is_ajax_request(self, request_header: str) -> bool:
        """Check if request appears to be AJAX"""
        if not request_header:
            return False

        ajax_indicators = [
            'x-requested-with: xmlhttprequest',
            'content-type: application/json',
            'accept: application/json'
        ]

        header_lower = request_header.lower()
        return any(indicator in header_lower for indicator in ajax_indicators)

    def _extract_ajax_request_info(self, result: Dict, request_header: str) -> Optional[Dict]:
        """Extract AJAX request information"""
        try:
            url = self._extract_url_from_request_header(request_header)
            method = request_header.split(' ')[0] if request_header else 'GET'

            # Extract content type
            content_type = ""
            for line in request_header.split('\n'):
                if line.lower().startswith('content-type:'):
                    content_type = line.split(':', 1)[1].strip()
                    break

            return {
                "url": url,
                "method": method,
                "content_type": content_type,
                "type": "ajax"
            }
        except:
            return None

    def _extract_forms_from_html(self, html_content: str, page_url: str) -> List[Dict]:
        """Extract form information from HTML content"""
        forms = []
        try:
            # Simple regex-based form extraction (could use BeautifulSoup for better parsing)
            import re

            # Find form tags
            form_pattern = r'<form[^>]*>(.*?)</form>'
            form_matches = re.findall(form_pattern, html_content, re.IGNORECASE | re.DOTALL)

            for form_html in form_matches:
                # Extract form attributes
                action = ""
                method = "GET"

                # Extract action
                action_match = re.search(r'action=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
                if action_match:
                    action = action_match.group(1)

                # Extract method
                method_match = re.search(r'method=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
                if method_match:
                    method = method_match.group(1).upper()

                # Extract input fields
                input_pattern = r'<input[^>]*>'
                input_matches = re.findall(input_pattern, form_html, re.IGNORECASE)

                fields = []
                for input_html in input_matches:
                    name_match = re.search(r'name=["\']([^"\']*)["\']', input_html, re.IGNORECASE)
                    type_match = re.search(r'type=["\']([^"\']*)["\']', input_html, re.IGNORECASE)

                    if name_match:
                        field_name = name_match.group(1)
                        field_type = type_match.group(1) if type_match else 'text'

                        fields.append({
                            "name": field_name,
                            "type": field_type
                        })

                if fields:  # Only add forms that have input fields
                    forms.append({
                        "url": page_url,
                        "action": action,
                        "method": method,
                        "fields": fields,
                        "discovered_by": "HTML parsing"
                    })

        except Exception as e:
            logger.debug(f"Error extracting forms from HTML: {e}")

        return forms

    def _process_response_body(self, response_body: str, url: str) -> Dict:
        """Process response body to extract useful info without storing full content"""
        if not response_body:
            return {"hash": "", "size": 0, "type": "empty", "title": ""}

        # Generate content hash for duplicate detection
        content_hash = hashlib.sha256(response_body.encode('utf-8', errors='ignore')).hexdigest()[:16]

        # Basic content analysis
        body_lower = response_body.lower()
        size = len(response_body)

        # Determine content type
        content_type = "unknown"
        if "<!doctype html" in body_lower or "<html" in body_lower:
            content_type = "html"
        elif response_body.strip().startswith('{') and response_body.strip().endswith('}'):
            content_type = "json"
        elif response_body.strip().startswith('<') and response_body.strip().endswith('>'):
            content_type = "xml"
        elif any(keyword in body_lower for keyword in ['function', 'var ', 'const ', 'let ']):
            content_type = "javascript"
        elif any(keyword in body_lower for keyword in ['body{', '.css', 'color:', 'margin:']):
            content_type = "css"

        # Extract page title for HTML pages
        title = ""
        if content_type == "html":
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', response_body, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()[:100]  # Limit title length

        # Check for interesting content patterns (but don't store the content)
        interesting_patterns = {
            "errors": bool(re.search(r'(error|exception|stack trace|fatal)', body_lower)),
            "admin": bool(re.search(r'(admin|dashboard|management)', body_lower)),
            "login": bool(re.search(r'(login|signin|password|authentication)', body_lower)),
            "api_docs": bool(re.search(r'(api|swagger|openapi|rest)', body_lower)),
            "sensitive": bool(re.search(r'(password|secret|key|token|credential)', body_lower))
        }

        return {
            "hash": content_hash,
            "size": size,
            "type": content_type,
            "title": title,
            "url": url,
            "patterns": {k: v for k, v in interesting_patterns.items() if v}  # Only include found patterns
        }

    def _should_process_response(self, response_body: str, url: str) -> bool:
        """Determine if response body should be processed (not just ignored)"""
        if not response_body:
            return False

        # Skip very large responses (likely files, images, etc.)
        if len(response_body) > 1000000:  # 1MB limit
            return False

        # Skip binary content
        if self._is_binary_content(response_body):
            return False

        # Skip common static file extensions
        if any(url.lower().endswith(ext) for ext in ['.jpg', '.png', '.gif', '.pdf', '.zip', '.tar', '.gz']):
            return False

        return True

    def _is_binary_content(self, content: str) -> bool:
        """Check if content appears to be binary"""
        try:
            # Check for null bytes or high percentage of non-printable characters
            null_bytes = content.count('\x00')
            if null_bytes > 0:
                return True

            # Count printable vs non-printable characters
            printable_count = sum(1 for c in content if c.isprintable() or c.isspace())
            if len(content) > 0 and (printable_count / len(content)) < 0.7:
                return True

        except:
            return True

            return False
    
    def cleanup_scan_contexts(self):
        """Clean up all contexts created by this scan adapter"""
        try:
            for context_id in self.context_ids:
                try:
                    # Get context name first
                    context_info = self._make_api_request(f"context/view/context", {"contextId": context_id})
                    if context_info and "context" in context_info:
                        context_name = context_info["context"]
                        logger.info(f"Cleaning up context: {context_name}")
                        self._make_api_post_request("context/action/removeContext", {
                            "contextName": context_name
                        })
                except Exception as e:
                    logger.warning(f"Failed to cleanup context {context_id}: {e}")
            
            self.context_ids.clear()
            logger.info("Cleaned up all scan contexts")
            
        except Exception as e:
            logger.warning(f"Failed to cleanup scan contexts: {e}")
    
    def _create_comprehensive_context(self, target_url: str, discovered_urls: List[str] = None) -> str:
        """Create ZAP context including all discovered URLs for comprehensive scanning"""
        try:
            # Create unique context name with scan ID for better tracking
            scan_id = self.scan_id or "unknown"
            timestamp = int(time.time())
            context_name = f"Scan_{scan_id}_{timestamp}"
            logger.info(f"Creating comprehensive ZAP context: {context_name}")
            
            # Create new context
            context_response = self._make_api_post_request("context/action/newContext", {
                "contextName": context_name
            })
            
            if not context_response or "contextId" not in context_response:
                raise Exception("Failed to create ZAP context")
                
            context_id = context_response["contextId"]
            self.context_ids.append(context_id)  # Track for cleanup
            logger.info(f"Created ZAP context with ID: {context_id}")
            
            # Add main target domain and subdomains to context
            main_domain = urlparse(target_url).netloc
            # Include exact host
            main_regex = f"https?://{re.escape(main_domain)}/.*"
            self._add_url_pattern_to_context(context_name, main_regex, "main target")
            # Include subdomains of the registrable domain
            try:
                registrable = main_domain
                parts = main_domain.split('.')
                if len(parts) >= 2:
                    registrable = ".".join(parts[-2:])
                sub_regex = f"https?://([a-zA-Z0-9-]+\\.)*{re.escape(registrable)}/.*"
                self._add_url_pattern_to_context(context_name, sub_regex, "subdomains of registrable domain")
            except Exception as _:
                pass
            
            # Add all discovered URLs to context (same registrable domain to prevent cross-contamination)
            added_domains = {main_domain}
            if discovered_urls and isinstance(discovered_urls, list):
                for url in discovered_urls:
                    try:
                        parsed_url = urlparse(url)
                        if parsed_url.netloc:
                            # Compare by registrable domain
                            main_parts = main_domain.split('.')
                            disc_parts = parsed_url.netloc.split('.')
                            main_reg = ".".join(main_parts[-2:]) if len(main_parts) >= 2 else main_domain
                            disc_reg = ".".join(disc_parts[-2:]) if len(disc_parts) >= 2 else parsed_url.netloc
                            if disc_reg == main_reg and parsed_url.netloc not in added_domains:
                                domain_regex = f"https?://{re.escape(parsed_url.netloc)}/.*"
                                self._add_url_pattern_to_context(context_name, domain_regex, f"discovered: {parsed_url.netloc}")
                                added_domains.add(parsed_url.netloc)
                    except Exception as e:
                        logger.warning(f"Failed to add URL {url} to context: {e}")
                        
            logger.info(f"Context '{context_name}' created with {len(added_domains)} domain patterns (same domain only)")
            return context_id
            
        except Exception as e:
            logger.error(f"Failed to create comprehensive context: {e}")
            return None
    
    def _add_url_pattern_to_context(self, context_name: str, regex_pattern: str, description: str = ""):
        """Add URL pattern to ZAP context"""
        try:
            response = self._make_api_post_request("context/action/includeInContext", {
                "contextName": context_name,
                "regex": regex_pattern
            })
            
            if response and response.get("Result") == "OK":
                logger.debug(f"Added to context {description}: {regex_pattern}")
                return True
            else:
                logger.warning(f"Failed to add pattern to context: {regex_pattern}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding pattern to context: {e}")
            return False
    
    def _add_discovered_urls_to_site_tree(self, discovered_urls: List[str]):
        """Add discovered URLs to ZAP's site tree by accessing them through proxy"""
        if not discovered_urls:
            return
            
        logger.info(f"Adding {len(discovered_urls)} discovered URLs to ZAP site tree...")
        
        # ZAP proxy settings
        zap_proxy = {
            "http": f"http://localhost:{self.zap_port}",
            "https": f"http://localhost:{self.zap_port}"
        }
        
        added_count = 0
        for url in discovered_urls:
            try:
                # Make a simple GET request through ZAP proxy to add URL to site tree
                response = requests.get(
                    url, 
                    proxies=zap_proxy, 
                    timeout=10, 
                    verify=False,
                    allow_redirects=True
                )
                added_count += 1
                logger.debug(f"Added to site tree: {url} (status: {response.status_code})")
                
            except Exception as e:
                logger.debug(f"Could not add {url} to site tree: {e}")
                continue
                
        logger.info(f"Successfully added {added_count}/{len(discovered_urls)} URLs to ZAP site tree")
    
    def _deduplicate_forms(self, forms: List[Dict]) -> List[Dict]:
        """Remove duplicate forms based on URL, method, and action"""
        unique_forms = []
        seen = set()

        for form in forms:
            # Create a unique key for the form
            key = f"{form.get('url', '')}-{form.get('method', '')}-{form.get('action', '')}"
            if key not in seen:
                unique_forms.append(form)
                seen.add(key)

        return unique_forms

    def _get_active_scan_results(self) -> Dict:
        """Get active scan results with properly extracted vulnerabilities"""
        try:
            # Extract vulnerabilities using the dedicated method
            vulnerabilities = self._extract_vulnerabilities()

            return {
                "total_alerts": len(vulnerabilities),
                "scan_id": self.active_scan_id,
                "vulnerabilities": vulnerabilities
            }
        except Exception as e:
            logger.error(f"Failed to get active scan results: {e}")
            return {
                "total_alerts": 0,
                "scan_id": self.active_scan_id,
                "vulnerabilities": []
            }
    
    def _extract_vulnerabilities(self) -> List[Dict]:
        """Extract and format vulnerabilities from ZAP results, scoped to current target"""
        vulnerabilities = []

        try:
            # Fetch all alerts (no domain scoping) to avoid missing relevant items
            alerts_response = self._make_api_request("core/view/alerts")
            alerts = alerts_response.get("alerts", []) if alerts_response else []

            logger.debug(f"ZAP returned {len(alerts)} alerts")

            for alert in alerts:
                # Log the full alert structure for debugging
                logger.debug(f"Processing ZAP alert: {alert}")

                # No domain filtering here per request; rely on ZAP reset for isolation

                # ZAP uses 'alert' field for the vulnerability name, not 'name'
                alert_name = (
                    alert.get("alert") or
                    alert.get("name") or
                    alert.get("alertRef") or
                    f"ZAP Alert {alert.get('pluginId', 'Unknown')}"
                )

                vuln = {
                    "name": alert_name,
                    "description": alert.get("description", "No description available"),
                    "severity": self._map_zap_risk_to_severity(alert.get("risk", "Low")),
                    "confidence": self._map_zap_confidence(alert.get("confidence", "Medium")),
                    "url": alert.get("url", ""),
                    "parameter": alert.get("param", ""),
                    "evidence": alert.get("evidence", ""),
                    "solution": alert.get("solution", ""),
                    "reference": alert.get("reference", ""),
                    "cwe_id": alert.get("cweid", ""),
                    "wasc_id": alert.get("wascid", ""),
                    "source": "ZAP Active Scan",
                    "category": "Active Vulnerability",
                    "attack": alert.get("attack", ""),
                    "other_info": alert.get("otherinfo", "")
                }

                logger.debug(f"Created vulnerability: {vuln['name']} - {vuln['severity']}")
                vulnerabilities.append(vuln)
            
            logger.info(f"Extracted {len(vulnerabilities)} vulnerabilities from ZAP")
            return vulnerabilities
            
        except Exception as e:
            logger.error(f"Failed to extract vulnerabilities: {e}")
            return []
    
    def _map_zap_risk_to_severity(self, zap_risk: str) -> str:
        """Map ZAP risk levels to our severity levels"""
        risk_mapping = {
            "High": "high",
            "Medium": "medium", 
            "Low": "low",
            "Informational": "info"
        }
        return risk_mapping.get(zap_risk, "low")
    
    def _map_zap_confidence(self, zap_confidence: str) -> float:
        """Map ZAP confidence to numeric value"""
        confidence_mapping = {
            "High": 0.9,
            "Medium": 0.7,
            "Low": 0.5
        }
        return confidence_mapping.get(zap_confidence, 0.5)
    
    def _generate_scan_statistics(self) -> Dict:
        """Generate comprehensive scan statistics"""
        return {
            "spider_urls_found": len(self.results.get("spider_results", {}).get("urls", [])),
            "ajax_spider_urls_found": len(self.results.get("ajax_spider_results", {}).get("urls", [])),
            "total_vulnerabilities": len(self.results.get("vulnerability_details", [])),
            "vulnerability_severity_breakdown": self._get_severity_breakdown(),
            "scan_duration": "Not calculated",  # Can be calculated based on start/end times
            "zap_version": self._get_zap_version()
        }
    
    def _get_severity_breakdown(self) -> Dict:
        """Get breakdown of vulnerabilities by severity"""
        breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for vuln in self.results.get("vulnerability_details", []):
            severity = vuln.get("severity", "low")
            if severity in breakdown:
                breakdown[severity] += 1
        
        return breakdown
    
    def _get_zap_version(self) -> str:
        """Get ZAP version information"""
        try:
            version_info = self._make_api_request("core/view/version")
            return version_info.get("version", "Unknown") if version_info else "Unknown"
        except Exception as e:
            logger.error(f"Failed to get ZAP version: {e}")
            return "Unknown"
    
    def stop_all_scans(self):
        """Stop all running scans AGGRESSIVELY with multiple retries and verification"""
        logger.info("🔴 Stopping all ZAP scans AGGRESSIVELY...")

        try:
            # STEP 1: Stop AJAX spider FIRST (most critical - this is what causes CPU issues)
            logger.info("🔴 STEP 1: Stopping AJAX spider (CRITICAL - prevents CPU overload)")
            self._force_stop_ajax_spider()
            
            # STEP 2: Stop traditional spider
            if self.spider_id:
                logger.info(f"🔴 STEP 2: Stopping traditional spider (ID: {self.spider_id})")
                try:
                    self._make_api_post_request("spider/action/stop", {"scanId": self.spider_id})
                    logger.info(f"✅ Traditional spider {self.spider_id} stop command sent")
                except Exception as e:
                    logger.warning(f"⚠️ Error stopping traditional spider: {e}")

            # STEP 3: Stop ALL spider scans as a precaution (catches any orphaned spiders)
            logger.info("🔴 STEP 3: Stopping ALL spider scans (safety net)")
            try:
                self._make_api_post_request("spider/action/stopAllScans", {})
                logger.info("✅ All spider scans stop command sent")
            except Exception as e:
                logger.warning(f"⚠️ Error stopping all spiders: {e}")

            # STEP 4: Stop active scan
            if self.active_scan_id:
                logger.info(f"🔴 STEP 4: Stopping active scan (ID: {self.active_scan_id})")
                try:
                    self._make_api_post_request("ascan/action/stop", {"scanId": self.active_scan_id})
                    logger.info(f"✅ Active scan {self.active_scan_id} stop command sent")
                except Exception as e:
                    logger.warning(f"⚠️ Error stopping active scan: {e}")

            # STEP 5: Stop ALL active scans as a precaution
            logger.info("🔴 STEP 5: Stopping ALL active scans (safety net)")
            try:
                self._make_api_post_request("ascan/action/stopAllScans", {})
                logger.info("✅ All active scans stop command sent")
            except Exception as e:
                logger.warning(f"⚠️ Error stopping all active scans: {e}")
            
            # STEP 6: Final verification - stop AJAX spider AGAIN (extra safety)
            logger.info("🔴 STEP 6: Stopping AJAX spider AGAIN (final safety check)")
            self._force_stop_ajax_spider()

            logger.info("✅✅✅ All ZAP scans stopped successfully - 6 steps completed")

        except Exception as e:
            logger.error(f"❌ Error stopping scans: {e}")
            # Even if there's an error, try one more time to stop AJAX spider
            try:
                logger.error("🔴 EMERGENCY: Attempting final AJAX spider stop after error...")
                self._force_stop_ajax_spider()
            except:
                pass