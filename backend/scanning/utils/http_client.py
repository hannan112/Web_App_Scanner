"""
HTTP client utilities for scanning operations
"""

import logging
import time
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


class RateLimitedHTTPClient:
    """HTTP client with rate limiting capabilities"""

    def __init__(
        self, request_delay=0.5, timeout=30, user_agent=None, custom_headers=None
    ):
        self.request_delay = request_delay
        self.timeout = timeout

        # Set up default headers
        self.headers = {"User-Agent": user_agent or "SecurityScannerBot/1.0"}

        if custom_headers:
            self.headers.update(custom_headers)

        self.last_request_time = 0

    def get(self, url, params=None, allow_redirects=True):
        """
        Make a GET request with rate limiting

        Args:
            url (str): URL to request
            params (dict, optional): Query parameters
            allow_redirects (bool): Whether to follow redirects

        Returns:
            requests.Response: Response object
        """
        self._apply_rate_limit()

        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=allow_redirects,
            )
            self.last_request_time = time.time()
            return response
        except Exception as e:
            logger.error(f"HTTP GET request to {url} failed: {str(e)}")
            raise

    def _apply_rate_limit(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.request_delay:
            sleep_time = self.request_delay - time_since_last_request
            time.sleep(sleep_time)
