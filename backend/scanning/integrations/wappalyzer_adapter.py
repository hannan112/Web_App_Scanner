# scanning/integrations/wappalyzer_adapter.py
import logging
import json
import subprocess
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class WappalyzerAdapter:
    """Adapter for Wappalyzer technology detection"""
    
    def __init__(self, config=None):
        self.config = config or {}
    
    def detect_technologies(self, url: str) -> Dict[str, Any]:
        """
        Detect technologies used by a website

        Args:
            url (str): URL to analyze

        Returns:
            Dict: Detected technologies
        """
        # Initialize technologies with defaults
        technologies = {
            'server': 'Unknown',
            'frameworks': [],
            'cms': None,
            'javascript_libraries': [],
            'programming_languages': [],
            'web_servers': [],
            'analytics': [],
            'cdn': None
        }

        try:
            # Use Python Wappalyzer
            from Wappalyzer import Wappalyzer, WebPage
            import requests

            # Create webpage object - add headers and timeout
            custom_headers = self.config.get('headers', {})
            response = requests.get(
                url, 
                headers=custom_headers if custom_headers else {'User-Agent': 'Mozilla/5.0'},
                timeout=30
            )

            # Extract server information from HTTP headers
            server_header = response.headers.get('Server', '')
            if server_header:
                technologies['server'] = server_header
                logger.info(f"Detected server from HTTP headers: {server_header}")

            # Also check for X-Powered-By header
            powered_by = response.headers.get('X-Powered-By', '')
            if powered_by:
                technologies['programming_languages'].append(powered_by)
                logger.info(f"Detected technology from X-Powered-By: {powered_by}")

            # Check for CDN-specific headers
            if 'Vercel' in server_header or any(h.startswith('x-vercel-') for h in response.headers.keys()):
                technologies['cdn'] = 'Vercel'
            elif 'Cloudflare' in server_header or 'cf-ray' in response.headers:
                technologies['cdn'] = 'Cloudflare'
            elif 'Fastly' in server_header or 'Fastly' in response.headers.get('Via', ''):
                technologies['cdn'] = 'Fastly'

            # Now continue with Wappalyzer analysis to enhance our basic header detection
            webpage = WebPage.new_from_response(response)

            # Initialize Wappalyzer and analyze
            wappalyzer = Wappalyzer.latest()
            result = wappalyzer.analyze(webpage)
            logger.info(f"Raw Wappalyzer result type: {type(result)}")

            # Process results based on the type
            if isinstance(result, dict):
                for tech_name, tech_info in result.items():
                    self._process_technology(tech_name, tech_info, technologies)
            elif isinstance(result, list):
                for tech in result:
                    if isinstance(tech, str):
                        self._add_technology(tech, technologies)
                    elif isinstance(tech, dict) and 'name' in tech:
                        self._add_technology(tech['name'], technologies)
            elif isinstance(result, set):
                for tech_name in result:
                    self._add_technology(tech_name, technologies)

            # Log the final results
            logger.info(f"Wappalyzer detection completed: Server: {technologies['server']}, " +
                        f"CMS: {technologies['cms']}, Frameworks: {', '.join(technologies['frameworks'])}")

        except Exception as e:
            logger.error(f"Error using Wappalyzer: {str(e)}")
            # Still return the technologies we detected from headers

        return technologies

    def _add_technology(self, tech_name: str, technologies: Dict[str, Any]):
        """Add a detected technology to the results"""
        # Categorize based on common technology names
        tech_lower = tech_name.lower()

        # Server technologies
        if tech_lower in ['apache', 'nginx', 'iis', 'microsoft-iis', 'lighttpd', 'caddy', 'vercel']:
            technologies['web_servers'].append(tech_name)
            # Only override server if it's still unknown
            if technologies['server'] == 'Unknown':
                technologies['server'] = tech_name

        # Content Management Systems
        elif tech_lower in ['wordpress', 'drupal', 'joomla', 'magento', 'shopify', 'wix']:
            technologies['cms'] = tech_name

        # Programming languages
        elif tech_lower in ['php', 'python', 'ruby', 'node.js', 'java', 'asp.net', '.net']:
            if tech_name not in technologies['programming_languages']:
                technologies['programming_languages'].append(tech_name)

        # JavaScript libraries
        elif tech_lower in ['jquery', 'bootstrap', 'react', 'vue.js', 'angular', 'd3.js', 'lodash']:
            if tech_name not in technologies['javascript_libraries']:
                technologies['javascript_libraries'].append(tech_name)

        # Frameworks
        elif tech_lower in ['laravel', 'django', 'rails', 'spring', 'express', 'flask', 'next.js']:
            if tech_name not in technologies['frameworks']:
                technologies['frameworks'].append(tech_name)

        # Analytics
        elif tech_lower in ['google analytics', 'hotjar', 'matomo', 'piwik', 'google tag manager']:
            if tech_name not in technologies['analytics']:
                technologies['analytics'].append(tech_name)

        # CDN services
        elif tech_lower in ['cloudflare', 'akamai', 'fastly', 'aws cloudfront', 'vercel']:
            # Only override if not already set
            if not technologies['cdn']:
                technologies['cdn'] = tech_name

    def _process_technology(self, tech_name, tech_info, technologies):
        """Process technology from the original Wappalyzer format"""
        # Try to extract categories
        categories = []

        if isinstance(tech_info, dict) and 'categories' in tech_info:
            categories = tech_info['categories']

        # If we have categories, use them for more precise categorization
        if categories:
            for category in categories:
                cat_name = category if isinstance(category, str) else category.get('name', '')
                cat_lower = cat_name.lower()

                if 'server' in cat_lower or 'web server' in cat_lower:
                    technologies['web_servers'].append(tech_name)
                    if technologies['server'] == 'Unknown':
                        technologies['server'] = tech_name

                if 'cms' in cat_lower:
                    technologies['cms'] = tech_name

                if 'framework' in cat_lower:
                    if tech_name not in technologies['frameworks']:
                        technologies['frameworks'].append(tech_name)

                if 'javascript' in cat_lower and 'librar' in cat_lower:
                    if tech_name not in technologies['javascript_libraries']:
                        technologies['javascript_libraries'].append(tech_name)

                if 'programming' in cat_lower:
                    if tech_name not in technologies['programming_languages']:
                        technologies['programming_languages'].append(tech_name)

                if 'analytics' in cat_lower:
                    if tech_name not in technologies['analytics']:
                        technologies['analytics'].append(tech_name)

                if 'cdn' in cat_lower:
                    if not technologies['cdn']:
                        technologies['cdn'] = tech_name
        else:
            # If no categories, use the simpler approach
            self._add_technology(tech_name, technologies)