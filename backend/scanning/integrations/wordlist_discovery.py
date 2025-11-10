"""
Wordlist-Based URL Discovery

Uses popular wordlists (like SecLists) to discover URLs, directories, and files
that the spider might miss. This dramatically improves vulnerability detection.
"""

import logging
import os
import requests
from typing import List, Set, Dict
from urllib.parse import urljoin, urlparse
import concurrent.futures
from pathlib import Path

logger = logging.getLogger(__name__)


class WordlistDiscovery:
    """Discover URLs using wordlists for comprehensive coverage"""

    # Popular wordlists from SecLists and other sources
    BUILT_IN_WORDLISTS = {
        'common_pages': [
            # Common web pages
            'index', 'home', 'default', 'main',
            'login', 'signin', 'signup', 'register',
            'admin', 'administrator', 'dashboard',
            'search', 'query', 'find',
            'contact', 'about', 'help',
            'profile', 'account', 'settings',
            'upload', 'download', 'file',
            'api', 'rest', 'graphql',
            'user', 'users', 'member', 'members',
            'post', 'posts', 'blog', 'news',
            'product', 'products', 'item', 'items',
            'cart', 'checkout', 'payment',
            'test', 'demo', 'example',
        ],

        'common_directories': [
            # Common directories
            'admin', 'administrator', 'administration',
            'api', 'apis', 'rest', 'v1', 'v2',
            'user', 'users', 'account', 'accounts',
            'auth', 'authentication', 'login',
            'static', 'assets', 'public',
            'uploads', 'files', 'documents',
            'images', 'img', 'css', 'js',
            'backup', 'backups', 'old', 'tmp',
            'test', 'tests', 'dev', 'debug',
            'config', 'conf', 'settings',
        ],

        'vulnerable_paths': [
            # Paths known to be vulnerable in common apps
            # DVWA
            'vulnerabilities/sqli',
            'vulnerabilities/sqli_blind',
            'vulnerabilities/xss_r',
            'vulnerabilities/xss_s',
            'vulnerabilities/csrf',
            'vulnerabilities/fi',
            'vulnerabilities/upload',
            'vulnerabilities/captcha',
            'vulnerabilities/exec',

            # bWAPP
            'sqli_1.php',
            'sqli_6.php',
            'xss_get.php',
            'xss_post.php',
            'csrf_1.php',

            # WebGoat
            'WebGoat/attack',
            'WebGoat/start.mvc',

            # Juice Shop
            'rest/user/login',
            'rest/products/search',
            'api/Users',

            # Common vulnerable endpoints
            'search.php',
            'search.jsp',
            'query.php',
            'user.php',
            'profile.php',
            'details.php',
            'view.php',
            'download.php',
            'upload.php',
        ],

        'common_parameters': [
            # Common GET parameters for SQL injection testing
            'id', 'user', 'userid', 'user_id',
            'page', 'page_id', 'pageid',
            'category', 'cat', 'catid',
            'product', 'prod', 'productid',
            'search', 'query', 'q', 'keyword',
            'file', 'filename', 'path',
            'url', 'redirect', 'return',
            'username', 'email', 'name',
            'sort', 'order', 'orderby',
            'filter', 'type', 'action',
        ],

        'file_extensions': [
            # Common file extensions
            'php', 'asp', 'aspx', 'jsp', 'do',
            'html', 'htm', 'js', 'json',
            'xml', 'txt', 'sql', 'bak',
            'old', 'backup', 'zip', 'tar.gz',
        ]
    }

    # SQL Injection test payloads (basic)
    SQLI_TEST_VALUES = [
        '1', "1'", '1"', "1' OR '1'='1", '1 OR 1=1',
        "1' AND '1'='2", '999999', '-1', '1 UNION SELECT NULL',
    ]

    def __init__(self, timeout: int = 5, max_workers: int = 10):
        """
        Initialize wordlist discovery

        Args:
            timeout: HTTP request timeout in seconds
            max_workers: Max concurrent workers for discovery
        """
        self.timeout = timeout
        self.max_workers = max_workers
        self.discovered_urls: Set[str] = set()

    def discover_urls(
        self,
        base_url: str,
        wordlist_types: List[str] = None,
        custom_wordlist_path: str = None,
        include_parameters: bool = True
    ) -> List[str]:
        """
        Discover URLs using wordlists

        Args:
            base_url: Base URL of target
            wordlist_types: List of built-in wordlist types to use
            custom_wordlist_path: Path to custom wordlist file
            include_parameters: Whether to add parameter variations

        Returns:
            List of discovered URLs
        """
        logger.info(f"Starting wordlist-based discovery for {base_url}")

        # Default to all wordlist types
        if not wordlist_types:
            wordlist_types = ['common_pages', 'common_directories', 'vulnerable_paths']

        # Collect all words from selected wordlists
        words = set()
        for wl_type in wordlist_types:
            if wl_type in self.BUILT_IN_WORDLISTS:
                words.update(self.BUILT_IN_WORDLISTS[wl_type])

        # Add custom wordlist if provided
        if custom_wordlist_path and os.path.exists(custom_wordlist_path):
            words.update(self._load_custom_wordlist(custom_wordlist_path))

        # Generate URL candidates
        url_candidates = self._generate_url_candidates(base_url, words)

        # Probe URLs to find valid ones
        valid_urls = self._probe_urls(url_candidates)

        # Add parameter variations if requested
        if include_parameters:
            param_urls = self._add_parameter_variations(valid_urls)
            valid_urls.extend(param_urls)

        logger.info(f"Discovered {len(valid_urls)} valid URLs using wordlists")
        return valid_urls

    def _load_custom_wordlist(self, filepath: str) -> List[str]:
        """Load words from custom wordlist file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                words = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            logger.info(f"Loaded {len(words)} words from {filepath}")
            return words
        except Exception as e:
            logger.error(f"Failed to load custom wordlist: {e}")
            return []

    def _generate_url_candidates(self, base_url: str, words: Set[str]) -> List[str]:
        """Generate URL candidates from wordlist"""
        candidates = []
        parsed = urlparse(base_url)
        base_path = parsed.path.rstrip('/')

        for word in words:
            # Try as directory
            candidates.append(urljoin(base_url, f"{base_path}/{word}/"))

            # Try with common extensions
            for ext in self.BUILT_IN_WORDLISTS['file_extensions']:
                candidates.append(urljoin(base_url, f"{base_path}/{word}.{ext}"))

        # Remove duplicates
        return list(set(candidates))

    def _probe_urls(self, url_candidates: List[str]) -> List[str]:
        """
        Probe URLs concurrently to find valid ones

        Args:
            url_candidates: List of URL candidates to probe

        Returns:
            List of valid URLs (returned 200, 301, 302, 403)
        """
        valid_urls = []

        logger.info(f"Probing {len(url_candidates)} URL candidates...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self._probe_single_url, url): url
                for url in url_candidates
            }

            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    is_valid, status_code = future.result()
                    if is_valid:
                        valid_urls.append(url)
                        logger.debug(f"Found: {url} [{status_code}]")
                except Exception as e:
                    logger.debug(f"Error probing {url}: {e}")

        return valid_urls

    def _probe_single_url(self, url: str) -> tuple:
        """
        Probe a single URL

        Returns:
            Tuple of (is_valid, status_code)
        """
        try:
            response = requests.head(
                url,
                timeout=self.timeout,
                allow_redirects=False,
                verify=False  # For testing environments
            )

            # Consider these status codes as "interesting"
            interesting_codes = [200, 301, 302, 401, 403, 500]

            if response.status_code in interesting_codes:
                return (True, response.status_code)

            return (False, response.status_code)

        except requests.exceptions.RequestException:
            return (False, None)

    def _add_parameter_variations(self, urls: List[str]) -> List[str]:
        """
        Add parameter variations to URLs for testing

        Args:
            urls: List of base URLs

        Returns:
            List of URLs with parameter variations
        """
        param_urls = []

        for url in urls:
            # Only add params to URLs that look like they might accept them
            if any(keyword in url.lower() for keyword in ['search', 'query', 'view', 'details', 'user', 'id', 'page']):
                for param in self.BUILT_IN_WORDLISTS['common_parameters'][:5]:  # Use top 5 params
                    for value in ['1', 'test']:  # Simple test values
                        param_url = f"{url}?{param}={value}"
                        param_urls.append(param_url)

        return param_urls

    def generate_sqli_test_urls(self, base_urls: List[str]) -> List[Dict]:
        """
        Generate SQL injection test URLs from discovered URLs

        Args:
            base_urls: List of discovered URLs

        Returns:
            List of dicts with URL and test payload info
        """
        sqli_urls = []

        for url in base_urls:
            # Check if URL has parameters or looks vulnerable
            if '?' in url or any(keyword in url.lower() for keyword in ['id', 'user', 'search', 'query', 'page']):

                # If URL has no params, add common params
                if '?' not in url:
                    for param in ['id', 'user_id', 'page_id']:
                        for payload in self.SQLI_TEST_VALUES[:3]:  # Use first 3 payloads
                            sqli_urls.append({
                                'url': f"{url}?{param}={payload}",
                                'parameter': param,
                                'payload': payload,
                                'test_type': 'sql_injection'
                            })
                else:
                    # URL already has params, inject payloads
                    for payload in self.SQLI_TEST_VALUES[:3]:
                        # Simple injection into first parameter
                        sqli_urls.append({
                            'url': url.replace('=1', f'={payload}').replace('=test', f'={payload}'),
                            'parameter': 'existing',
                            'payload': payload,
                            'test_type': 'sql_injection'
                        })

        logger.info(f"Generated {len(sqli_urls)} SQL injection test URLs")
        return sqli_urls

    def get_comprehensive_url_list(
        self,
        base_url: str,
        include_sqli_tests: bool = True,
        max_urls: int = 500
    ) -> Dict[str, List]:
        """
        Get comprehensive URL list for scanning

        Args:
            base_url: Base URL of target
            include_sqli_tests: Whether to include SQLi test URLs
            max_urls: Maximum number of URLs to return

        Returns:
            Dict with discovered URLs and test URLs
        """
        result = {
            'discovered_urls': [],
            'sqli_test_urls': [],
            'total_count': 0
        }

        # Discover URLs
        discovered = self.discover_urls(
            base_url,
            wordlist_types=['common_pages', 'common_directories', 'vulnerable_paths'],
            include_parameters=True
        )

        result['discovered_urls'] = discovered[:max_urls]

        # Generate SQLi test URLs if requested
        if include_sqli_tests:
            sqli_tests = self.generate_sqli_test_urls(discovered[:50])  # Use first 50 URLs
            result['sqli_test_urls'] = sqli_tests[:100]  # Limit to 100 tests

        result['total_count'] = len(result['discovered_urls']) + len(result['sqli_test_urls'])

        logger.info(f"Comprehensive URL list: {result['total_count']} total URLs")
        return result


def download_seclists_wordlists(destination_dir: str = '/tmp/wordlists') -> Dict[str, str]:
    """
    Download popular SecLists wordlists

    Args:
        destination_dir: Directory to save wordlists

    Returns:
        Dict mapping wordlist name to file path
    """
    os.makedirs(destination_dir, exist_ok=True)

    # Popular wordlists URLs (from SecLists GitHub)
    wordlists = {
        'common_dirs': 'https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt',
        'raft_small': 'https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/raft-small-directories.txt',
        'big_txt': 'https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/big.txt',
        'sqli_payloads': 'https://raw.githubusercontent.com/danielmiessler/SecLists/master/Fuzzing/SQLi/Generic-SQLi.txt',
    }

    downloaded = {}

    for name, url in wordlists.items():
        try:
            filepath = os.path.join(destination_dir, f'{name}.txt')

            if os.path.exists(filepath):
                logger.info(f"Wordlist already exists: {filepath}")
                downloaded[name] = filepath
                continue

            logger.info(f"Downloading {name} from {url}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                f.write(response.content)

            downloaded[name] = filepath
            logger.info(f"Downloaded {name} to {filepath}")

        except Exception as e:
            logger.error(f"Failed to download {name}: {e}")

    return downloaded
