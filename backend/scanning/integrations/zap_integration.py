"""
ZAP Integration - Passive Mode Only

Uses OWASP ZAP for passive security analysis only.
No crawling, no active scanning.
"""

from typing import Dict, List


class ZAPPassiveIntegration:
    """ZAP passive analysis integration"""

    def __init__(self, config):
        self.config = config
        # ZAP connection setup placeholder

    def analyze_headers(self, url: str) -> List[Dict]:
        """Passive header analysis using ZAP"""
        return []

    def analyze_cookies(self, url: str) -> List[Dict]:
        """Passive cookie analysis using ZAP"""
        return []

    # REMOVE: crawl_with_spider, crawl_with_ajax_spider, active_scan


