# scanning/integrations/zap_adapter.py
import logging
import time
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


class ZAPAdapter:
    """Adapter for OWASP ZAP scanner integration using the UI API endpoint"""

    def __init__(self, config=None):
        self.config = config or {}
        self.host = self.config.get("zap_host", "localhost")
        self.port = self.config.get("zap_port", 8080)
        self.api_key = self.config.get("zap_api_key", "changeme123")
        self.timeout = self.config.get("zap_timeout", 120)
        self.browser_path = self.config.get("zap_browser_path", None)
        self.browser_type = self.config.get("zap_browser_type", "chrome")
        # Use the JSON endpoint instead of UI
        self.base_url = f"http://{self.host}:{self.port}/JSON"

    def initialize(self) -> bool:
        """Initialize connection to ZAP"""
        try:
            # Test connection with version API - use correct URL format
            url = f"{self.base_url}/core/view/version/"
            if self.api_key:
                url += f"?apikey={self.api_key}"

            # Add detailed logging
            logger.info(f"Attempting to connect to ZAP at: {url}")

            response = requests.get(url, timeout=10)

            logger.info(f"ZAP response status code: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    version = data.get("version", "unknown")
                    logger.info(f"ZAP connection successful: version {version}")
                    return True
                except ValueError:
                    logger.warning(
                        f"ZAP returned non-JSON response: {response.text[:100]}"
                    )
                    return False
            else:
                logger.error(
                    f"ZAP API returned status code {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error initializing ZAP connection: {str(e)}")
            return False

    def configure_browser(self):
        """Configure browser for AJAX spider"""
        try:
            # Auto-detect browser if not specified
            if not self.browser_path:
                # Try to detect available browsers
                import subprocess
                browsers = [
                    ("/usr/bin/firefox", "firefox-headless"),
                    ("/usr/bin/chromium-browser", "chrome-headless"),
                    ("/usr/bin/google-chrome", "chrome-headless"),
                    ("/usr/bin/chrome", "chrome-headless")
                ]
                
                for browser_path, browser_type in browsers:
                    try:
                        # Check if browser exists
                        result = subprocess.run(["which", browser_path.split("/")[-1]], 
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            self.browser_path = browser_path
                            self.browser_type = browser_type
                            logger.info(f"Auto-detected browser: {browser_path} ({browser_type})")
                            break
                    except:
                        continue
                
                # Default to firefox-headless if nothing found
                if not self.browser_path:
                    self.browser_type = "firefox-headless"
                    logger.info("No browser detected, using firefox-headless")
            
            # Set browser type first (this is more important than path)
            browser_type_endpoints = [
                f"{self.base_url}/ajaxSpider/action/setOptionBrowserId/",
                f"{self.base_url}/ajaxSpider/action/setBrowserId/",
                f"{self.base_url}/ajaxSpider/action/setBrowserType/"
            ]
            
            for endpoint in browser_type_endpoints:
                try:
                    params = {"String": self.browser_type}
                    if self.api_key:
                        params["apikey"] = self.api_key
                    
                    response = requests.get(endpoint, params=params, timeout=10)
                    if response.status_code == 200:
                        logger.info(f"Browser type set to: {self.browser_type}")
                        break
                except Exception as e:
                    logger.debug(f"Failed to set browser type via {endpoint}: {str(e)}")
                    continue
            
            # Set browser path if provided
            if self.browser_path:
                # Try different API endpoints for setting browser path
                browser_endpoints = [
                    f"{self.base_url}/ajaxSpider/action/setOptionBrowserPath/",
                    f"{self.base_url}/ajaxSpider/action/setBrowserPath/",
                    f"{self.base_url}/ajaxSpider/action/setBrowser/"
                ]
                
                for endpoint in browser_endpoints:
                    try:
                        params = {"String": self.browser_path}
                        if self.api_key:
                            params["apikey"] = self.api_key
                        
                        response = requests.get(endpoint, params=params, timeout=10)
                        if response.status_code == 200:
                            logger.info(f"Browser path set to: {self.browser_path}")
                            break
                    except Exception as e:
                        logger.debug(f"Failed to set browser path via {endpoint}: {str(e)}")
                        continue
                
            return True
        except Exception as e:
            logger.warning(f"Error configuring browser: {str(e)}")
            return False

    def start_ajax_spider(self, url: str, max_duration: int = 300, max_depth: int = 5) -> Dict[str, Any]:
        """Start ZAP AJAX spider crawling (better for JavaScript-heavy sites)"""
        if not self.initialize():
            return {
                "success": False,
                "error": "Could not connect to ZAP",
                "urls_discovered": [],
                "forms_discovered": [],
                "pages_crawled": 0
            }

        try:
            # Configure browser first
            self.configure_browser()
            
            # Create context for the scan to avoid scope issues
            context_name = f"ajax_scan_{int(time.time())}"
            context_url = f"{self.base_url}/context/action/newContext/"
            params = {"contextName": context_name}
            if self.api_key:
                params["apikey"] = self.api_key
            
            context_response = requests.get(context_url, params=params, timeout=10)
            if context_response.status_code != 200:
                logger.warning(f"Could not create context: {context_response.text}")
            else:
                logger.info(f"Created ZAP context: {context_name}")
            
            # Add URL domain to context scope
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain_pattern = f".*{parsed_url.netloc}.*"
            
            include_url = f"{self.base_url}/context/action/includeInContext/"
            params = {
                "contextName": context_name,
                "regex": domain_pattern
            }
            if self.api_key:
                params["apikey"] = self.api_key
            
            include_response = requests.get(include_url, params=params, timeout=10)
            if include_response.status_code == 200:
                logger.info(f"Added domain {parsed_url.netloc} to context scope")
            
            # Access the URL through ZAP first
            access_url = f"{self.base_url}/core/action/accessUrl/"
            params = {"url": url}
            if self.api_key:
                params["apikey"] = self.api_key

            access_response = requests.get(access_url, params=params, timeout=30)
            if access_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"ZAP could not access the URL: {access_response.text}",
                    "urls_discovered": [],
                    "forms_discovered": [],
                    "pages_crawled": 0
                }

            # Start AJAX spider with context
            logger.info("Starting AJAX spider with proper context...")
            
            ajax_spider_url = f"{self.base_url}/ajaxSpider/action/scan/"
            ajax_spider_params = {
                "url": url,
                "maxDuration": max_duration,
                "inScope": "true",
                "contextName": context_name
            }
            if self.api_key:
                ajax_spider_params["apikey"] = self.api_key

            ajax_spider_response = requests.get(ajax_spider_url, params=ajax_spider_params, timeout=30)
            
            # If AJAX spider fails, try traditional spider instead
            if ajax_spider_response.status_code != 200 or "internal_error" in ajax_spider_response.text:
                logger.info("AJAX spider failed, trying traditional spider...")
                return self.start_traditional_spider(url, max_depth, max_duration * 2)
            
            ajax_spider_data = ajax_spider_response.json()
            scan_id = ajax_spider_data.get("scan", "")
            
            if not scan_id:
                logger.info("AJAX spider scan ID not returned, trying traditional spider...")
                return self.start_traditional_spider(url, max_depth, max_duration * 2)

            logger.info(f"ZAP AJAX spider started with scan ID: {scan_id}")
            return {
                "success": True,
                "scan_id": scan_id,
                "context_name": context_name,
                "spider_type": "ajax",
                "urls_discovered": [],
                "forms_discovered": [],
                "pages_crawled": 0
            }

        except Exception as e:
            logger.error(f"Error starting ZAP AJAX spider: {str(e)}")
            logger.info("Falling back to traditional spider...")
            return self.start_traditional_spider(url, max_depth, max_duration * 2)

    def start_traditional_spider(self, url: str, max_depth: int = 5, max_children: int = 100) -> Dict[str, Any]:
        """Start ZAP traditional spider crawling"""
        if not self.initialize():
            return {
                "success": False,
                "error": "Could not connect to ZAP",
                "urls_discovered": [],
                "forms_discovered": [],
                "pages_crawled": 0
            }

        try:
            # Access the URL through ZAP
            access_url = f"{self.base_url}/core/action/accessUrl/"
            params = {"url": url}
            if self.api_key:
                params["apikey"] = self.api_key

            access_response = requests.get(access_url, params=params, timeout=30)
            if access_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"ZAP could not access the URL: {access_response.text}",
                    "urls_discovered": [],
                    "forms_discovered": [],
                    "pages_crawled": 0
                }

            # Start the traditional spider
            spider_url = f"{self.base_url}/spider/action/scan/"
            spider_params = {
                "url": url,
                "maxChildren": max_children,
                "recurse": "true",
                "subtreeOnly": "false"
            }
            if self.api_key:
                spider_params["apikey"] = self.api_key

            spider_response = requests.get(spider_url, params=spider_params, timeout=30)
            if spider_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to start ZAP spider: {spider_response.text}",
                    "urls_discovered": [],
                    "forms_discovered": [],
                    "pages_crawled": 0
                }

            spider_data = spider_response.json()
            scan_id = spider_data.get("scan", "")
            
            if not scan_id:
                return {
                    "success": False,
                    "error": "ZAP spider scan ID not returned",
                    "urls_discovered": [],
                    "forms_discovered": [],
                    "pages_crawled": 0
                }

            logger.info(f"ZAP traditional spider started with scan ID: {scan_id}")
            return {
                "success": True,
                "scan_id": scan_id,
                "spider_type": "traditional",
                "urls_discovered": [],
                "forms_discovered": [],
                "pages_crawled": 0
            }

        except Exception as e:
            logger.error(f"Error starting ZAP traditional spider: {str(e)}")
            return {
                "success": False,
                "error": f"Error starting ZAP traditional spider: {str(e)}",
                "urls_discovered": [],
                "forms_discovered": [],
                "pages_crawled": 0
            }

    def check_ajax_spider_status(self, scan_id: str) -> Dict[str, Any]:
        """Check the status of a ZAP AJAX spider scan"""
        try:
            status_url = f"{self.base_url}/ajaxSpider/view/status/"
            params = {"scanId": scan_id}
            if self.api_key:
                params["apikey"] = self.api_key

            response = requests.get(status_url, params=params, timeout=10)
            if response.status_code != 200:
                return {
                    "status": "error",
                    "progress": 0,
                    "error": f"Failed to get AJAX spider status: {response.text}"
                }

            status_data = response.json()
            status = status_data.get("status", "unknown")
            progress = status_data.get("progress", 0)

            return {
                "status": status,
                "progress": progress
            }

        except Exception as e:
            logger.error(f"Error checking AJAX spider status: {str(e)}")
            return {
                "status": "error",
                "progress": 0,
                "error": str(e)
            }

    def get_ajax_spider_results(self, scan_id: str, context_name: str = None) -> Dict[str, Any]:
        """Get comprehensive AJAX spider results"""
        try:
            results = {
                "success": True,
                "urls_discovered": [],
                "forms_discovered": [],
                "pages_crawled": 0,
                "ajax_requests": [],
                "javascript_objects": []
            }
            
            # Get URLs discovered from AJAX spider results
            urls_url = f"{self.base_url}/ajaxSpider/view/results/"
            params = {}
            if self.api_key:
                params["apikey"] = self.api_key
            
            urls_response = requests.get(urls_url, params=params, timeout=30)
            if urls_response.status_code == 200:
                urls_data = urls_response.json()
                if "results" in urls_data:
                    # Extract URLs from the complex objects
                    urls = []
                    for result in urls_data["results"]:
                        if isinstance(result, dict):
                            # Extract URL from request header
                            request_header = result.get("requestHeader", "")
                            if request_header:
                                # Parse URL from "GET https://example.com/path HTTP/1.1"
                                import re
                                url_match = re.search(r'(GET|POST|PUT|DELETE|PATCH)\s+(https?://[^\s]+)', request_header)
                                if url_match:
                                    url = url_match.group(2)
                                    if url not in urls:
                                        urls.append(url)
                            # Also check if there's a direct URL field
                            elif "url" in result:
                                url = result["url"]
                                if url not in urls:
                                    urls.append(url)
                    
                    results["urls_discovered"] = urls
                    results["pages_crawled"] = len(urls)
                else:
                    # Fallback: get URLs from core/view/urls
                    fallback_url = f"{self.base_url}/core/view/urls/"
                    fallback_params = {}
                    if context_name:
                        fallback_params["contextName"] = context_name
                    if self.api_key:
                        fallback_params["apikey"] = self.api_key
                    
                    fallback_response = requests.get(fallback_url, params=fallback_params, timeout=30)
                    if fallback_response.status_code == 200:
                        fallback_data = fallback_response.json()
                        if "urls" in fallback_data:
                            results["urls_discovered"] = fallback_data["urls"]
                            results["pages_crawled"] = len(fallback_data["urls"])
            
            # Get forms discovered using context if available
            forms_url = f"{self.base_url}/core/view/urls/"
            params = {"baseurl": ""}
            if context_name:
                params["contextName"] = context_name
            if self.api_key:
                params["apikey"] = self.api_key
            
            forms_response = requests.get(forms_url, params=params, timeout=30)
            if forms_response.status_code == 200:
                forms_data = forms_response.json()
                if "urls" in forms_data:
                    # Extract forms from URLs using pattern matching
                    for url_info in forms_data["urls"]:
                        url_str = str(url_info).lower()
                        if any(keyword in url_str for keyword in ['form', 'login', 'register', 'contact', 'search', 'submit']):
                            results["forms_discovered"].append({
                                "url": url_str,
                                "method": "GET",  # Default assumption
                                "action": url_str,
                                "fields": [],
                                "discovered_by": "AJAX spider pattern analysis"
                            })
            
            # Get AJAX requests from core URLs
            ajax_url = f"{self.base_url}/core/view/urls/"
            params = {"baseurl": ""}
            if context_name:
                params["contextName"] = context_name
            if self.api_key:
                params["apikey"] = self.api_key
            
            ajax_response = requests.get(ajax_url, params=params, timeout=30)
            if ajax_response.status_code == 200:
                ajax_data = ajax_response.json()
                if "urls" in ajax_data:
                    # Filter for AJAX-like requests (JSON, API endpoints, etc.)
                    for url in ajax_data["urls"]:
                        url_str = str(url).lower()
                        if any(keyword in url_str for keyword in ['api', 'json', 'ajax', 'xhr', 'rest']):
                            results["ajax_requests"].append(url)
            
            logger.info(f"ZAP AJAX spider found {results['pages_crawled']} pages, {len(results['forms_discovered'])} forms, and {len(results['ajax_requests'])} AJAX requests")
            return results
            
        except Exception as e:
            logger.error(f"Error getting AJAX spider results: {str(e)}")
            return {
                "success": False,
                "error": f"Error getting AJAX spider results: {str(e)}",
                "urls_discovered": [],
                "forms_discovered": [],
                "pages_crawled": 0
            }

    def check_spider_status(self, scan_id: str) -> Dict[str, Any]:
        """Check the status of a ZAP traditional spider scan"""
        try:
            status_url = f"{self.base_url}/spider/view/status/"
            params = {"scanId": scan_id}
            if self.api_key:
                params["apikey"] = self.api_key

            response = requests.get(status_url, params=params, timeout=10)
            if response.status_code != 200:
                return {
                    "status": "error",
                    "progress": 0,
                    "error": f"Failed to get spider status: {response.text}"
                }

            status_data = response.json()
            status = status_data.get("status", "unknown")
            progress = status_data.get("progress", 0)

            return {
                "status": status,
                "progress": progress
            }

        except Exception as e:
            logger.error(f"Error checking spider status: {str(e)}")
            return {
                "status": "error",
                "progress": 0,
                "error": str(e)
            }

    def get_spider_results(self, scan_id: str) -> Dict[str, Any]:
        """Get results from a completed ZAP traditional spider scan"""
        try:
            # Get URLs discovered by spider - use the correct endpoint without scanId parameter
            urls_url = f"{self.base_url}/spider/view/results/"
            urls_params = {}
            if self.api_key:
                urls_params["apikey"] = self.api_key

            logger.debug(f"Fetching spider results from: {urls_url}")
            urls_response = requests.get(urls_url, params=urls_params, timeout=30)
            urls_discovered = []
            
            if urls_response.status_code == 200:
                logger.debug(f"Spider results response: {urls_response.text[:200]}")
                try:
                    urls_data = urls_response.json()
                    if isinstance(urls_data, dict):
                        # ZAP returns results in 'results' field
                        urls_discovered = urls_data.get("results", [])
                    elif isinstance(urls_data, list):
                        urls_discovered = urls_data
                    else:
                        logger.warning(f"Unexpected spider results format: {type(urls_data)}")
                        urls_discovered = []
                except ValueError as e:
                    logger.warning(f"Spider results not in JSON format: {urls_response.text[:100]}")
                    urls_discovered = []
            else:
                logger.error(f"Spider results API failed with status {urls_response.status_code}: {urls_response.text}")
                # Fallback: try to get URLs from the core/view/urls endpoint
                fallback_url = f"{self.base_url}/core/view/urls/"
                fallback_params = {}
                if self.api_key:
                    fallback_params["apikey"] = self.api_key
                
                fallback_response = requests.get(fallback_url, params=fallback_params, timeout=30)
                if fallback_response.status_code == 200:
                    try:
                        fallback_data = fallback_response.json()
                        if isinstance(fallback_data, dict) and "urls" in fallback_data:
                            urls_discovered = fallback_data["urls"]
                        logger.info(f"Used fallback endpoint, found {len(urls_discovered)} URLs")
                    except ValueError:
                        logger.warning("Fallback endpoint also returned invalid JSON")

            # Get forms discovered using multiple approaches
            forms_discovered = []
            
            # Try to get forms from ZAP's context
            try:
                # First try to get forms from ZAP's form detection
                forms_url = f"{self.base_url}/core/view/urls/"
                forms_params = {}
                if self.api_key:
                    forms_params["apikey"] = self.api_key

                forms_response = requests.get(forms_url, params=forms_params, timeout=30)
                if forms_response.status_code == 200:
                    logger.debug(f"Forms response status: {forms_response.status_code}")
                    try:
                        forms_data = forms_response.json()
                        if isinstance(forms_data, dict) and "urls" in forms_data:
                            urls = forms_data["urls"]
                            # Simple form detection - look for URLs that might contain forms
                            for url in urls:
                                url_str = str(url)
                                if any(keyword in url_str.lower() for keyword in ['form', 'login', 'register', 'contact', 'search']):
                                    forms_discovered.append({
                                        "url": url_str,
                                        "method": "GET",  # Default - would need deeper analysis for POST
                                        "action": url_str,
                                        "fields": []  # Would need to crawl the page to get actual form fields
                                    })
                    except ValueError as e:
                        logger.debug(f"Forms data parsing error: {e}")
                        
            except Exception as e:
                logger.debug(f"Error getting forms from ZAP: {e}")
                
            # If no forms found through ZAP API, create a basic form entry if we have URLs
            if not forms_discovered and urls_discovered:
                # Assume at least one potential form based on common patterns
                for url in urls_discovered[:5]:  # Check first 5 URLs
                    url_str = str(url)
                    if any(keyword in url_str.lower() for keyword in ['form', 'login', 'contact', 'search', 'register']):
                        forms_discovered.append({
                            "url": url_str,
                            "method": "GET",
                            "action": url_str,
                            "fields": []
                        })
                        break

            # Get pages crawled count
            pages_crawled = len(urls_discovered)

            logger.info(f"ZAP spider found {pages_crawled} URLs and {len(forms_discovered)} forms")
            return {
                "success": True,
                "urls_discovered": urls_discovered,
                "forms_discovered": forms_discovered,
                "pages_crawled": pages_crawled
            }

        except Exception as e:
            logger.error(f"Error getting spider results: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "urls_discovered": [],
                "forms_discovered": [],
                "pages_crawled": 0
            }

    def crawl_with_ajax_spider(self, url: str, max_duration: int = 300, max_depth: int = 5,
                              timeout: int = 600, progress_callback=None) -> Dict[str, Any]:
        """Complete AJAX spider crawling process with fallback to traditional spider"""
        logger.info(f"Starting ZAP spider crawl for {url}")
        
        # Start AJAX spider (with fallback to traditional)
        start_result = self.start_ajax_spider(url, max_duration, max_depth)
        if not start_result["success"]:
            return start_result

        scan_id = start_result["scan_id"]
        spider_type = start_result.get("spider_type", "ajax")
        start_time = time.time()

        # Monitor spider progress based on type
        if spider_type == "ajax":
            while time.time() - start_time < timeout:
                status_result = self.check_ajax_spider_status(scan_id)
                
                if status_result["status"] == "error":
                    return {
                        "success": False,
                        "error": status_result.get("error", "AJAX spider status check failed"),
                        "urls_discovered": [],
                        "forms_discovered": [],
                        "pages_crawled": 0
                    }

                progress = status_result["progress"]
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(progress, [], [], {})

                # Check if AJAX spider is complete
                if status_result["status"] == "100":
                    logger.info("ZAP AJAX spider completed")
                    break

                # Wait before checking again
                time.sleep(3)  # AJAX spider typically takes longer

            # Get final results
            context_name = start_result.get("context_name")
            results = self.get_ajax_spider_results(scan_id, context_name)
        else:
            # Traditional spider
            while time.time() - start_time < timeout:
                status_result = self.check_spider_status(scan_id)
                
                if status_result["status"] == "error":
                    return {
                        "success": False,
                        "error": status_result.get("error", "Traditional spider status check failed"),
                        "urls_discovered": [],
                        "forms_discovered": [],
                        "pages_crawled": 0
                    }

                progress = status_result["progress"]
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(progress, [], [], {})

                # Check if traditional spider is complete
                if status_result["status"] == "100":
                    logger.info("ZAP traditional spider completed")
                    break

                # Wait before checking again
                time.sleep(2)

            # Get final results
            results = self.get_spider_results(scan_id)
        
        logger.info(f"ZAP {spider_type} spider found {results.get('pages_crawled', 0)} pages")
        
        return results

    def crawl_with_spider(self, url: str, max_depth: int = 5, max_children: int = 100, 
                         timeout: int = 300, progress_callback=None) -> Dict[str, Any]:
        """Complete traditional spider crawling process"""
        logger.info(f"Starting ZAP traditional spider crawl for {url}")
        
        # Start traditional spider
        start_result = self.start_traditional_spider(url, max_depth, max_children)
        if not start_result["success"]:
            return start_result

        scan_id = start_result["scan_id"]
        start_time = time.time()

        # Monitor spider progress
        while time.time() - start_time < timeout:
            status_result = self.check_spider_status(scan_id)
            
            if status_result["status"] == "error":
                return {
                    "success": False,
                    "error": status_result.get("error", "Traditional spider status check failed"),
                    "urls_discovered": [],
                    "forms_discovered": [],
                    "pages_crawled": 0
                }

            progress = status_result["progress"]
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(progress, [], [], {})

            # Check if traditional spider is complete
            if status_result["status"] == "100":
                logger.info("ZAP traditional spider completed")
                break

            # Wait before checking again
            time.sleep(2)

        # Get final results
        results = self.get_spider_results(scan_id)
        logger.info(f"ZAP traditional spider found {results.get('pages_crawled', 0)} pages")
        
        return results

    def check_headers(self, url: str) -> List[Dict[str, Any]]:
        """Check security headers using ZAP"""
        findings = []

        if not self.initialize():
            return [
                {
                    "name": "ZAP Connection Error",
                    "description": "Could not connect to ZAP. Check if ZAP is running and accessible.",
                    "severity": "info",
                    "url": url,
                    "confidence": 1.0,
                    "remediation": "Ensure ZAP is running and correctly configured.",
                }
            ]

        try:
            # First, access the URL through ZAP
            access_url = f"{self.base_url}/core/action/accessUrl/"
            params = {"url": url}
            if self.api_key:
                params["apikey"] = self.api_key

            access_response = requests.get(access_url, params=params, timeout=30)
            if access_response.status_code != 200:
                return [
                    {
                        "name": "ZAP Error Accessing URL",
                        "description": f"ZAP could not access the URL: {access_response.text}",
                        "severity": "info",
                        "url": url,
                        "confidence": 1.0,
                        "remediation": "Check ZAP proxy settings and ensure the URL is accessible.",
                    }
                ]

            # Wait a bit for passive scan to complete
            import time

            time.sleep(5)

            # Get passive scan results
            alerts_url = f"{self.base_url}/core/view/alerts/"
            alerts_params = {"baseurl": url}
            if self.api_key:
                alerts_params["apikey"] = self.api_key

            alerts_response = requests.get(alerts_url, params=alerts_params, timeout=30)
            if alerts_response.status_code != 200:
                return [
                    {
                        "name": "ZAP Error Getting Alerts",
                        "description": f"ZAP could not retrieve alerts: {alerts_response.text}",
                        "severity": "info",
                        "url": url,
                        "confidence": 1.0,
                        "remediation": "Check ZAP configuration.",
                    }
                ]

            # Process alerts
            alerts_data = alerts_response.json()
            if "alerts" in alerts_data:
                for alert in alerts_data["alerts"]:
                    # Check if this is a header-related alert
                    if "header" in alert.get("name", "").lower():
                        findings.append(
                            {
                                "name": alert.get("name", "Header Issue"),
                                "description": alert.get("description", ""),
                                "severity": self._map_risk_to_severity(
                                    alert.get("risk", "")
                                ),
                                "url": url,
                                "confidence": self._map_confidence(
                                    alert.get("confidence", "")
                                ),
                                "remediation": alert.get("solution", ""),
                            }
                        )

            # If no findings but connection worked, return success indicator
            if not findings:
                findings.append(
                    {
                        "name": "ZAP Analysis Complete",
                        "description": "ZAP analyzed the URL but found no header issues.",
                        "severity": "info",
                        "url": url,
                        "confidence": 1.0,
                        "remediation": "None needed.",
                    }
                )

        except Exception as e:
            logger.error(f"Error checking headers with ZAP: {str(e)}")
            findings.append(
                {
                    "name": "ZAP Header Check Error",
                    "description": f"Error using ZAP to check headers: {str(e)}",
                    "severity": "info",
                    "url": url,
                    "confidence": 1.0,
                    "remediation": "Check ZAP configuration and try again.",
                }
            )

        return findings

    def _get_comprehensive_forms(self) -> List[Dict[str, Any]]:
        """Get comprehensive forms data as fallback when API calls fail"""
        forms = []
        try:
            # Try to get all URLs from ZAP
            urls_endpoint = f"{self.base_url}/core/view/urls/"
            params = {}
            if self.api_key:
                params["apikey"] = self.api_key
            
            response = requests.get(urls_endpoint, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                urls = data.get("urls", [])
                
                # Simple heuristic form detection based on URL patterns
                for url in urls:
                    url_str = str(url).lower()
                    if any(pattern in url_str for pattern in [
                        'form', 'login', 'register', 'signup', 'contact', 
                        'search', 'feedback', 'submit', 'post'
                    ]):
                        forms.append({
                            "url": str(url),
                            "method": "GET",  # Would need page analysis for accurate method
                            "action": str(url),
                            "fields": [],  # Would need page parsing for actual fields
                            "source": "heuristic_detection"
                        })
                        
                logger.info(f"Found {len(forms)} potential forms using comprehensive discovery")
                
        except Exception as e:
            logger.debug(f"Error in comprehensive forms extraction: {e}")
            
        return forms

    def check_cookies(self, url: str) -> List[Dict[str, Any]]:
        """
        Check cookies for security issues using ZAP
        
        Args:
            url (str): URL to check cookies for
            
        Returns:
            List[Dict[str, Any]]: List of cookie-related findings
        """
        findings = []
        
        try:
            if not self.initialize():
                return [
                    {
                        "name": "ZAP Cookie Check Error",
                        "description": "Could not connect to ZAP",
                        "severity": "info",
                        "url": url,
                        "confidence": 1.0,
                        "remediation": "Ensure ZAP is running and accessible.",
                    }
                ]

            # First, access the URL through ZAP
            access_url = f"{self.base_url}/core/action/accessUrl/"
            params = {"url": url}
            if self.api_key:
                params["apikey"] = self.api_key

            access_response = requests.get(access_url, params=params, timeout=30)
            if access_response.status_code != 200:
                return [
                    {
                        "name": "ZAP Error Accessing URL",
                        "description": f"ZAP could not access the URL: {access_response.text}",
                        "severity": "info",
                        "url": url,
                        "confidence": 1.0,
                        "remediation": "Check ZAP proxy settings and ensure the URL is accessible.",
                    }
                ]

            # Wait a bit for passive scan to complete
            import time
            time.sleep(5)

            # Get passive scan results
            alerts_url = f"{self.base_url}/core/view/alerts/"
            alerts_params = {"baseurl": url}
            if self.api_key:
                alerts_params["apikey"] = self.api_key

            alerts_response = requests.get(alerts_url, params=alerts_params, timeout=30)
            if alerts_response.status_code != 200:
                return [
                    {
                        "name": "ZAP Error Getting Alerts",
                        "description": f"ZAP could not retrieve alerts: {alerts_response.text}",
                        "severity": "info",
                        "url": url,
                        "confidence": 1.0,
                        "remediation": "Check ZAP configuration.",
                    }
                ]

            # Process alerts for cookie-related issues
            alerts_data = alerts_response.json()
            if "alerts" in alerts_data:
                for alert in alerts_data["alerts"]:
                    # Check if this is a cookie-related alert
                    alert_name = alert.get("name", "").lower()
                    if any(keyword in alert_name for keyword in ["cookie", "session", "httponly", "secure", "samesite"]):
                        findings.append(
                            {
                                "name": alert.get("name", "Cookie Issue"),
                                "description": alert.get("description", ""),
                                "severity": self._map_risk_to_severity(
                                    alert.get("risk", "")
                                ),
                                "url": url,
                                "confidence": self._map_confidence(
                                    alert.get("confidence", "")
                                ),
                                "remediation": alert.get("solution", ""),
                            }
                        )

            # If no findings but connection worked, return success indicator
            if not findings:
                findings.append(
                    {
                        "name": "ZAP Cookie Analysis Complete",
                        "description": "ZAP analyzed the URL but found no cookie-related issues.",
                        "severity": "info",
                        "url": url,
                        "confidence": 1.0,
                        "remediation": "None needed.",
                    }
                )

        except Exception as e:
            logger.error(f"Error checking cookies with ZAP: {str(e)}")
            findings.append(
                {
                    "name": "ZAP Cookie Check Error",
                    "description": f"Error using ZAP to check cookies: {str(e)}",
                    "severity": "info",
                    "url": url,
                    "confidence": 1.0,
                    "remediation": "Check ZAP configuration and try again.",
                }
            )

        return findings

    def _map_risk_to_severity(self, risk: str) -> str:
        """Map ZAP risk to severity level"""
        risk_map = {
            "High": "high",
            "Medium": "medium",
            "Low": "low",
            "Informational": "info",
        }
        return risk_map.get(risk, "info")

    def _map_confidence(self, confidence: str) -> float:
        """Map ZAP confidence to float value"""
        confidence_map = {"High": 0.9, "Medium": 0.7, "Low": 0.5}
        return confidence_map.get(confidence, 0.5)
