"""
Enhanced Scan Manager

Combines authentication, wordlist discovery, and targeted scanning for maximum
vulnerability detection. Integrates with ZAP Active Adapter.
"""

import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse
from scanning.integrations.zap_auth_manager import ZAPAuthManager
from scanning.integrations.wordlist_discovery import WordlistDiscovery

logger = logging.getLogger(__name__)


class EnhancedScanManager:
    """
    Manages enhanced scanning with authentication and wordlist discovery
    """

    def __init__(self, zap_adapter, target_url: str, scan_config):
        """
        Initialize enhanced scan manager

        Args:
            zap_adapter: ZAPActiveAdapter instance
            target_url: Target URL to scan
            scan_config: ScanConfiguration object
        """
        self.zap = zap_adapter
        self.target_url = target_url
        self.config = scan_config

        # Initialize managers
        self.auth_manager = ZAPAuthManager(zap_adapter)
        self.wordlist_discovery = WordlistDiscovery(
            timeout=getattr(scan_config, 'request_timeout', 5),
            max_workers=getattr(scan_config, 'max_concurrent_requests', 10)
        )

        # Tracking
        self.authenticated = False
        self.discovered_urls = []
        self.scan_targets = []

    def setup_authentication(
        self,
        profile_name: Optional[str] = None,
        custom_credentials: Optional[Dict] = None
    ) -> bool:
        """
        Setup authentication for target site

        Args:
            profile_name: Authentication profile name (auto-detect if None)
            custom_credentials: Custom credentials dict

        Returns:
            True if authentication successful or not needed
        """
        logger.info("Setting up authentication...")

        try:
            # Check if authentication is enabled in config
            use_auth = getattr(self.config, 'use_authentication', True)

            if not use_auth:
                logger.info("Authentication disabled in configuration")
                return True

            # Try to configure authentication
            success = self.auth_manager.configure_authentication(
                self.target_url,
                profile_name=profile_name,
                custom_credentials=custom_credentials
            )

            if success:
                self.authenticated = True
                logger.info("✅ Authentication configured successfully")
            else:
                logger.info("Authentication not configured (may not be needed for this target)")

            return True  # Return True even if auth not configured (may not be needed)

        except Exception as e:
            logger.error(f"Authentication setup failed: {e}")
            return False

    def discover_scan_targets(
        self,
        use_wordlists: bool = True,
        custom_wordlist_path: Optional[str] = None,
        include_sqli_tests: bool = True
    ) -> Dict[str, List]:
        """
        Discover scan targets using wordlists and other methods

        Args:
            use_wordlists: Whether to use wordlist discovery
            custom_wordlist_path: Path to custom wordlist file
            include_sqli_tests: Whether to generate SQLi test URLs

        Returns:
            Dict with discovered targets and metadata
        """
        logger.info("Discovering scan targets...")

        results = {
            'base_urls': [self.target_url],
            'discovered_urls': [],
            'sqli_test_urls': [],
            'priority_urls': [],
            'total_targets': 0
        }

        try:
            if use_wordlists:
                # Use wordlist discovery
                max_urls = getattr(self.config, 'max_discovery_urls', 500)

                discovery_results = self.wordlist_discovery.get_comprehensive_url_list(
                    self.target_url,
                    include_sqli_tests=include_sqli_tests,
                    max_urls=max_urls
                )

                results['discovered_urls'] = discovery_results['discovered_urls']
                results['sqli_test_urls'] = discovery_results['sqli_test_urls']

                # Add discovered URLs to ZAP for scanning
                logger.info(f"Adding {len(results['discovered_urls'])} discovered URLs to ZAP context")
                for url in results['discovered_urls'][:100]:  # Limit to prevent overload
                    try:
                        self.zap._make_api_post_request("core/action/accessUrl", {"url": url})
                    except Exception as e:
                        logger.debug(f"Failed to add URL to ZAP: {url} - {e}")

            # Identify priority URLs (login, admin, etc.)
            results['priority_urls'] = self._identify_priority_urls(
                results['base_urls'] + results['discovered_urls']
            )

            # Calculate total targets
            results['total_targets'] = (
                len(results['base_urls']) +
                len(results['discovered_urls']) +
                len(results['sqli_test_urls'])
            )

            self.discovered_urls = results['discovered_urls']
            self.scan_targets = results

            logger.info(f"✅ Target discovery complete: {results['total_targets']} total targets")
            logger.info(f"   - Base URLs: {len(results['base_urls'])}")
            logger.info(f"   - Discovered URLs: {len(results['discovered_urls'])}")
            logger.info(f"   - SQLi test URLs: {len(results['sqli_test_urls'])}")
            logger.info(f"   - Priority URLs: {len(results['priority_urls'])}")

            return results

        except Exception as e:
            logger.error(f"Target discovery failed: {e}")
            return results

    def _identify_priority_urls(self, urls: List[str]) -> List[str]:
        """
        Identify priority URLs that should be scanned first

        Args:
            urls: List of URLs to analyze

        Returns:
            List of priority URLs
        """
        priority_keywords = [
            'login', 'signin', 'admin', 'administrator',
            'search', 'query', 'user', 'profile',
            'upload', 'download', 'file',
            'api', 'rest', 'graphql'
        ]

        priority_urls = []
        for url in urls:
            url_lower = url.lower()
            if any(keyword in url_lower for keyword in priority_keywords):
                priority_urls.append(url)

        return priority_urls

    def configure_scan_scope(self) -> bool:
        """
        Configure ZAP scan scope with discovered targets

        Returns:
            True if scope configured successfully
        """
        try:
            logger.info("Configuring scan scope...")

            # Get authenticated scan params if available
            auth_params = {}
            if self.authenticated:
                auth_params = self.auth_manager.get_authenticated_scan_params()

            # Configure ZAP to scan discovered URLs
            if self.discovered_urls:
                logger.info(f"Adding {len(self.discovered_urls)} URLs to scan scope")

                # Add all discovered URLs to ZAP's site tree
                for url in self.discovered_urls[:200]:  # Limit to prevent overload
                    try:
                        self.zap._make_api_post_request("core/action/accessUrl", {
                            "url": url
                        })
                    except Exception as e:
                        logger.debug(f"Failed to add URL to scope: {e}")

            logger.info("✅ Scan scope configured")
            return True

        except Exception as e:
            logger.error(f"Failed to configure scan scope: {e}")
            return False

    def get_scan_summary(self) -> Dict:
        """
        Get summary of enhanced scan setup

        Returns:
            Dict with scan summary
        """
        return {
            'target_url': self.target_url,
            'authenticated': self.authenticated,
            'auth_profile': self.auth_manager.profile['name'] if self.auth_manager.profile else None,
            'total_targets': len(self.scan_targets.get('discovered_urls', [])) if self.scan_targets else 0,
            'priority_targets': len(self.scan_targets.get('priority_urls', [])) if self.scan_targets else 0,
            'sqli_test_urls': len(self.scan_targets.get('sqli_test_urls', [])) if self.scan_targets else 0,
        }

    def run_targeted_active_scan(self, progress_callback=None) -> Dict:
        """
        Run active scan on discovered targets

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Dict with scan results
        """
        logger.info("Starting targeted active scan...")

        results = {
            'urls_scanned': 0,
            'vulnerabilities_found': [],
            'errors': []
        }

        try:
            # Get URLs to scan (prioritize important ones)
            urls_to_scan = self.scan_targets.get('priority_urls', [])[:50]  # Scan priority URLs first
            urls_to_scan.extend(self.scan_targets.get('discovered_urls', [])[:100])  # Then discovered URLs

            total_urls = len(urls_to_scan)
            logger.info(f"Scanning {total_urls} URLs")

            # Start active scan on each URL
            for idx, url in enumerate(urls_to_scan):
                try:
                    if progress_callback:
                        progress = 45 + (idx / total_urls) * 35  # Progress from 45% to 80%
                        progress_callback(progress, f"Scanning {idx+1}/{total_urls}: {url[:50]}...")

                    # Start ZAP active scan on this URL
                    scan_response = self.zap._make_api_post_request(
                        "ascan/action/scan",
                        {
                            "url": url,
                            "recurse": "false",  # Don't recurse to avoid duplicate scans
                            "inScopeOnly": "false"
                        }
                    )

                    if scan_response and 'scan' in scan_response:
                        logger.debug(f"Started active scan on {url}")
                        results['urls_scanned'] += 1

                except Exception as e:
                    logger.error(f"Failed to scan {url}: {e}")
                    results['errors'].append({'url': url, 'error': str(e)})

            # Wait for all scans to complete
            logger.info("Waiting for active scans to complete...")
            self._wait_for_scans_completion()

            logger.info(f"✅ Targeted active scan complete: {results['urls_scanned']} URLs scanned")
            return results

        except Exception as e:
            logger.error(f"Targeted active scan failed: {e}")
            results['errors'].append({'general': str(e)})
            return results

    def _wait_for_scans_completion(self, timeout: int = 600):
        """
        Wait for all active scans to complete

        Args:
            timeout: Maximum time to wait in seconds
        """
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Get list of active scans
                scans_response = self.zap._make_api_request("ascan/view/scans")

                if not scans_response or 'scans' not in scans_response:
                    break

                scans = scans_response['scans']

                # Check if any scans are still running
                active_scans = [s for s in scans if s.get('state') != 'FINISHED']

                if not active_scans:
                    logger.info("All active scans completed")
                    break

                logger.debug(f"{len(active_scans)} active scans still running...")
                time.sleep(5)

            except Exception as e:
                logger.error(f"Error checking scan status: {e}")
                break

    def get_enhanced_results(self) -> Dict:
        """
        Get enhanced scan results from ZAP

        Returns:
            Dict with vulnerabilities and scan metadata
        """
        try:
            # Get alerts from ZAP
            alerts_response = self.zap._make_api_request("core/view/alerts", {
                "baseurl": self.target_url
            })

            alerts = alerts_response.get('alerts', []) if alerts_response else []

            logger.info(f"Retrieved {len(alerts)} alerts from ZAP")

            return {
                'vulnerabilities': alerts,
                'scan_summary': self.get_scan_summary(),
                'total_alerts': len(alerts)
            }

        except Exception as e:
            logger.error(f"Failed to get enhanced results: {e}")
            return {
                'vulnerabilities': [],
                'scan_summary': self.get_scan_summary(),
                'total_alerts': 0,
                'error': str(e)
            }
