import logging
from urllib.parse import urlparse

import requests

from scanning.passive.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class HttpAnalyzer(BaseAnalyzer):
    """Analyzer for basic HTTP responses"""

    def __init__(self, scan, config, target_url):
        """
        Initialize the HTTP analyzer

        Args:
            scan (Scan): The scan model object
            config (ScanConfiguration): The scan configuration
            target_url (str): The target URL
        """
        super().__init__(scan, config)
        self.target_url = target_url

        # Configure headers for HTTP requests
        self.headers = {
            "User-Agent": getattr(config, "user_agent", None)
            or "SecurityScannerBot/1.0"
        }
        if hasattr(config, "custom_headers") and config.custom_headers:
            self.headers.update(config.custom_headers)

    def analyze(self):
        """
        Analyze HTTP response

        Returns:
            dict: HTTP analysis results including response object
        """
        logger.info(f"Performing basic HTTP analysis for {self.target_url}")
        results = {
            "response_headers": {},
            "server_info": {},
            "cookies": {},
            "response": None,
        }

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
                self.add_finding(
                    {
                        "name": "SSL Certificate Validation Failed",
                        "description": f"The site's SSL certificate could not be validated: {str(ssl_err)}",
                        "severity": "medium",
                        "url": self.target_url,
                        "confidence": 0.9,
                    }
                )

            # Store the response for later use
            results["response"] = response

            # Store response headers
            results["response_headers"] = dict(response.headers)

            # Extract basic server information
            server_info = {
                "server": response.headers.get("Server", "Unknown"),
                "x_powered_by": response.headers.get("X-Powered-By", "Not disclosed"),
                "content_type": response.headers.get("Content-Type", "Unknown"),
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
            }

            # Update server info
            results["server_info"] = server_info

            # Store cookies
            if response.cookies:
                results["cookies"] = {
                    name: str(value) for name, value in response.cookies.items()
                }

            logger.info(
                f"Basic HTTP analysis completed: status {response.status_code}, server: {server_info['server']}"
            )

        except Exception as e:
            logger.error(
                f"Error in basic HTTP analysis for {self.target_url}: {str(e)}"
            )
            results["server_info"]["error"] = str(e)
            self.add_error_finding("HTTP Request Error", str(e))

        return results
