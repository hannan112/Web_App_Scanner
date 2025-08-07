"""
Crawler implementation for the scanning module

This module provides the core functionality for crawling websites as part of the
passive scanning module. It uses BeautifulSoup for HTML parsing and handles
rate limiting, robots.txt, and different depth levels.
"""

import logging
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class Crawler:
    """
    Web crawler for discovering website structure and content

    This crawler handles:
    - Respecting robots.txt
    - Rate limiting
    - Depth control
    - Form detection
    - Cookie collection
    - URL discovery
    """

    def __init__(
        self,
        start_url,
        max_depth=2,
        respect_robots_txt=True,
        max_pages=100,
        request_delay=0.5,
        timeout=30,
        user_agent=None,
        custom_headers=None,
    ):
        """
        Initialize the crawler

        Args:
            start_url (str): Starting URL for crawling
            max_depth (int): Maximum depth to crawl
            respect_robots_txt (bool): Whether to respect robots.txt
            max_pages (int): Maximum number of pages to crawl
            request_delay (float): Delay between requests in seconds
            timeout (int): Request timeout in seconds
            user_agent (str): Custom User-Agent string
            custom_headers (dict): Custom HTTP headers
        """
        self.start_url = start_url
        self.base_url = self._get_base_url(start_url)
        self.max_depth = max_depth
        self.respect_robots_txt = respect_robots_txt
        self.max_pages = max_pages
        self.request_delay = request_delay
        self.timeout = timeout

        # Initialize crawl data structures
        self.visited_urls = set()
        self.discovered_urls = []
        self.discovered_forms = []
        self.cookies = {}
        self.disallowed_paths = []
        self.pages_crawled = 0

        # Set up headers
        self.headers = {"User-Agent": user_agent or "SecurityScannerBot/1.0"}

        if custom_headers:
            self.headers.update(custom_headers)

        # Parse robots.txt if needed
        if self.respect_robots_txt:
            self._parse_robots_txt()

    def _apply_rate_limit(self):
        """Apply rate limiting to prevent aggressive crawling"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.request_delay:
            sleep_time = self.request_delay - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _crawl_url(self, url, depth):
        """Crawl a single URL with improved performance"""
        if url in self.visited_urls:
            return []

        self.visited_urls.add(url)

        try:
            logger.info(f"Crawling: {url} (depth: {depth})")

            # Apply rate limiting
            self._apply_rate_limit()

            # Use conditional GET if supported
            headers = self.headers.copy()

            response = requests.get(
                url, headers=headers, timeout=self.timeout, allow_redirects=True
            )

            # Update last request time
            self.last_request_time = time.time()
            return response
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
            return None

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

            # Import and use the crawler
            from scanning.discovery.crawler import Crawler

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

    def _get_base_url(self, url):
        """Extract base URL from the starting URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _parse_robots_txt(self):
        """Parse robots.txt to get disallowed paths"""
        robots_url = urljoin(self.base_url, "/robots.txt")
        try:
            response = requests.get(
                robots_url, headers=self.headers, timeout=self.timeout
            )
            if response.status_code == 200:
                lines = response.text.split("\n")
                user_agent_match = False

                for line in lines:
                    line = line.strip().lower()

                    # Check for user agent
                    if line.startswith("user-agent:"):
                        agent = line.split(":", 1)[1].strip()
                        user_agent_match = (
                            agent == "*"
                            or agent in self.headers.get("User-Agent", "").lower()
                        )

                    # Get disallowed paths for matching user agent
                    if user_agent_match and line.startswith("disallow:"):
                        path = line.split(":", 1)[1].strip()
                        if path:
                            self.disallowed_paths.append(path)

                logger.info(
                    f"Found {len(self.disallowed_paths)} disallowed paths in robots.txt"
                )
            else:
                logger.info(
                    f"No robots.txt found at {robots_url} (Status code: {response.status_code})"
                )
        except Exception as e:
            logger.error(f"Error parsing robots.txt: {str(e)}")

    def _is_allowed(self, url):
        """Check if a URL is allowed according to robots.txt"""
        if not self.respect_robots_txt or not self.disallowed_paths:
            return True

        parsed = urlparse(url)
        path = parsed.path

        for disallowed in self.disallowed_paths:
            if path.startswith(disallowed):
                return False

        return True

    def _is_same_domain(self, url):
        """Check if a URL is from the same domain as the base URL"""
        parsed_base = urlparse(self.base_url)
        parsed_url = urlparse(url)
        return parsed_base.netloc == parsed_url.netloc

    def _is_valid_url(self, url):
        """Check if a URL is valid and should be crawled"""
        # Skip URLs with fragments or query params for de-duplication
        parsed = urlparse(url)
        if parsed.fragment:
            url = url.split("#")[0]

        # Basic validation
        if not url.startswith(("http://", "https://")):
            return False

        # Skip already visited URLs
        if url in self.visited_urls:
            return False

        # Check same domain
        if not self._is_same_domain(url):
            return False

        # Check robots.txt rules
        if not self._is_allowed(url):
            return False

        # Skip common non-HTML resources
        skip_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".pdf",
            ".zip",
            ".tar",
            ".mp3",
            ".mp4",
            ".avi",
            ".mov",
            ".flv",
            ".wmv",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".exe",
            ".svg",
            ".ico",
            ".css",
            ".js",
        ]

        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False

        return True

    def _extract_urls(self, html, current_url):
        """Extract URLs from HTML content"""
        soup = BeautifulSoup(html, "html.parser")
        urls = set()

        # Extract links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()

            # Skip empty and javascript links
            if not href or href.startswith("javascript:"):
                continue

            # Resolve relative URLs
            absolute_url = urljoin(current_url, href)

            if self._is_valid_url(absolute_url):
                urls.add(absolute_url)

        return list(urls)

    def _extract_forms(self, html, page_url):
        """Extract forms from HTML content"""
        soup = BeautifulSoup(html, "html.parser")
        forms = []

        for form in soup.find_all("form"):
            form_info = {
                "url": page_url,
                "action": urljoin(page_url, form.get("action", "")),
                "method": form.get("method", "get").upper(),
                "inputs": [],
            }

            # Extract inputs, including hidden fields
            for input_field in form.find_all(["input", "textarea", "select"]):
                input_info = {
                    "name": input_field.get("name", ""),
                    "type": input_field.get("type", "text"),
                    "value": input_field.get("value", ""),
                    "required": input_field.has_attr("required"),
                }
                form_info["inputs"].append(input_info)

            forms.append(form_info)

        return forms

    def _crawl_url(self, url, depth):
        """
        Crawl a single URL and extract information

        Args:
            url (str): URL to crawl
            depth (int): Current crawl depth

        Returns:
            list: Discovered URLs
        """
        if url in self.visited_urls:
            return []

        self.visited_urls.add(url)

        try:
            logger.info(f"Crawling: {url} (depth: {depth})")
            response = requests.get(
                url, headers=self.headers, timeout=self.timeout, allow_redirects=True
            )

            # Update cookies
            if response.cookies:
                for key, value in response.cookies.items():
                    self.cookies[key] = str(value)

            # Skip non-HTML responses
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type.lower():
                return []

            # Record the page
            self.discovered_urls.append(url)
            self.pages_crawled += 1

            # Extract forms
            forms = self._extract_forms(response.text, url)
            for form in forms:
                if form not in self.discovered_forms:
                    self.discovered_forms.append(form)

            # Extract URLs for further crawling if not at max depth
            if depth < self.max_depth:
                return self._extract_urls(response.text, url)

            return []

        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
            return []

    def start(self, progress_callback=None):
        """
        Start the crawling process

        Args:
            progress_callback (callable): Optional callback for progress updates
                Function that takes (progress_percentage, urls, forms, cookies)

        Returns:
            dict: Crawl results containing discovered URLs, forms, and cookies
        """
        logger.info(
            f"Starting crawl at {self.start_url} with max depth {self.max_depth}"
        )

        # Queue of URLs to crawl: (url, depth)
        queue = [(self.start_url, 0)]

        while queue and self.pages_crawled < self.max_pages:
            # Get next URL from queue
            current_url, current_depth = queue.pop(0)

            # Crawl the URL
            new_urls = self._crawl_url(current_url, current_depth)

            # Add new URLs to the queue
            for url in new_urls:
                if url not in self.visited_urls and self.pages_crawled < self.max_pages:
                    queue.append((url, current_depth + 1))

            # Wait between requests
            time.sleep(self.request_delay)

            # Calculate progress and call callback if provided
            if progress_callback:
                progress = min(100, (self.pages_crawled / self.max_pages) * 100)
                progress_callback(
                    progress, self.discovered_urls, self.discovered_forms, self.cookies
                )

        logger.info(f"Crawling completed: {self.pages_crawled} pages crawled")

        # Return crawl results
        return {
            "pages_crawled": self.pages_crawled,
            "urls_discovered": self.discovered_urls,
            "forms_discovered": self.discovered_forms,
            "cookies": self.cookies,
        }


# Usage example:
# crawler = Crawler("https://example.com", max_depth=3)
# results = crawler.start()
