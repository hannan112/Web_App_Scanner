"""
Parser for sitemap.xml files

This module provides functionality for parsing sitemap.xml files to extract URLs
for crawling and analysis.
"""
import logging
import requests
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

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
            sitemap_url = urljoin(self.base_url, '/sitemap.xml')
        
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
                namespaces = {
                    'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'
                }
                
                # Try with namespace first
                loc_elements = root.findall('.//sm:loc', namespaces)
                
                # If no elements found with namespace, try without
                if not loc_elements:
                    loc_elements = root.findall('.//loc')
                
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
                    urls_found = re.findall(r'<loc>(.*?)</loc>', response.text)
                except Exception as regex_error:
                    logger.warning(f"Regex URL extraction failed: {str(regex_error)}")
            
            # Add all found URLs to our list
            self.urls.extend(urls_found)
            
            logger.info(f"Found {len(urls_found)} URLs in sitemap")
            return self.urls
                
        except Exception as e:
            logger.error(f"Error parsing sitemap at {sitemap_url}: {str(e)}")
            return []