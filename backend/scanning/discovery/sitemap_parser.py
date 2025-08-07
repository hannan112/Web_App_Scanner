"""
Parser for sitemap.xml files

This module provides functionality for parsing sitemap.xml files to extract URLs
for crawling and analysis.
"""

import logging
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)


class SitemapParser:
    """
    Parser for sitemap.xml files

    This class handles parsing of sitemap.xml files to extract URLs for crawling
    and analysis.
    """

    def __init__(self, base_url):
        """
        Initialize the sitemap parser

        Args:
            base_url (str): Base URL of the website
        """
        self.base_url = base_url
        self.urls = []

    def parse(self, sitemap_url=None):
        """
        Parse sitemap.xml and extract URLs

        Args:
            sitemap_url (str, optional): URL of the sitemap. If None, uses /sitemap.xml
                    at the base URL.

        Returns:
            list: List of URLs found in the sitemap
        """
        if sitemap_url is None:
            sitemap_url = urljoin(self.base_url, "/sitemap.xml")

        try:
            logger.info(f"Fetching sitemap from {sitemap_url}")

            # Suppress only the InsecureRequestWarning
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            response = requests.get(sitemap_url, timeout=10, verify=False)

            if response.status_code != 200:
                logger.warning(f"Failed to fetch sitemap: HTTP {response.status_code}")
                return []

            # Try to extract URLs using multiple methods
            urls_found = []

            # Method 1: Try standard XML parsing
            try:
                root = ET.fromstring(response.text)

                # Handle namespace in sitemap
                namespaces = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

                # Try with namespace first
                loc_elements = root.findall(".//sm:loc", namespaces)

                # If no elements found with namespace, try without
                if not loc_elements:
                    loc_elements = root.findall(".//loc")

                # Extract URLs from loc elements
                for url_elem in loc_elements:
                    url = url_elem.text.strip() if url_elem.text else None
                    if url:
                        urls_found.append(url)
            except ET.ParseError as xml_error:
                logger.warning(f"XML parsing error in sitemap: {str(xml_error)}")
                # Fall through to regex method

            # Method 2: If XML parsing failed or found no URLs, try regex
            if not urls_found:
                try:
                    import re

                    # Simple regex to find URLs in <loc> tags
                    urls_found = re.findall(r"<loc>(.*?)</loc>", response.text)
                except Exception as regex_error:
                    logger.warning(f"Regex URL extraction failed: {str(regex_error)}")

            # Add all found URLs to our list
            self.urls.extend(urls_found)

            logger.info(f"Found {len(urls_found)} URLs in sitemap")
            return self.urls

        except Exception as e:
            logger.error(f"Error parsing sitemap at {sitemap_url}: {str(e)}")
            return []

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
            from scanning.discovery.sitemap_parser import SitemapParser

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
