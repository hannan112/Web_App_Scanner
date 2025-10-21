# scanning/active/enhanced_discovery_integration.py
"""
Enhanced Discovery Integration for Active Scanning

This module integrates enhanced discovery results from passive scanning
into the active ZAP scanning process.
"""

import logging
from typing import Dict, List
from scanning.models.scan import PassiveReconResult

logger = logging.getLogger(__name__)


class EnhancedDiscoveryIntegration:
    """Integrates enhanced discovery results with ZAP active scanning"""

    def __init__(self, zap_adapter, scan_id: int):
        self.zap_adapter = zap_adapter
        self.scan_id = scan_id
        self.discovered_urls = []

    def load_enhanced_discovery_results(self) -> Dict:
        """Load enhanced discovery results from passive scan"""
        try:
            # Get passive recon results for this scan
            passive_results = PassiveReconResult.objects.get(scan_id=self.scan_id)
            
            enhanced_discovery = passive_results.enhanced_discovery or {}
            
            # Extract all discovered URLs
            all_urls = []
            
            # Add subdomains
            if enhanced_discovery.get("subdomains", {}).get("subdomains"):
                for subdomain in enhanced_discovery["subdomains"]["subdomains"]:
                    if subdomain.startswith('http'):
                        all_urls.append(subdomain)
                    else:
                        # Determine protocol based on target
                        protocol = 'https' if self._is_https_target() else 'http'
                        all_urls.append(f"{protocol}://{subdomain}")
            
            # Add wayback URLs
            if enhanced_discovery.get("wayback_urls", {}).get("urls"):
                all_urls.extend(enhanced_discovery["wayback_urls"]["urls"])
            
            # Add discovered directories
            if enhanced_discovery.get("directories", {}).get("directories"):
                for directory in enhanced_discovery["directories"]["directories"]:
                    if isinstance(directory, dict) and directory.get("url"):
                        all_urls.append(directory["url"])
                    elif isinstance(directory, str):
                        all_urls.append(directory)
            
            # Add API endpoints
            if enhanced_discovery.get("api_endpoints", {}).get("api_endpoints"):
                for endpoint in enhanced_discovery["api_endpoints"]["api_endpoints"]:
                    if isinstance(endpoint, dict) and endpoint.get("url"):
                        all_urls.append(endpoint["url"])
                    elif isinstance(endpoint, str):
                        all_urls.append(endpoint)
            
            # Remove duplicates
            unique_urls = list(set(all_urls))
            self.discovered_urls = unique_urls
            
            logger.info(f"Loaded {len(unique_urls)} URLs from enhanced discovery")
            
            return {
                "urls": unique_urls,
                "subdomains": enhanced_discovery.get("subdomains", {}).get("subdomains", []),
                "wayback_urls": enhanced_discovery.get("wayback_urls", {}).get("urls", []),
                "directories": enhanced_discovery.get("directories", {}).get("directories", []),
                "api_endpoints": enhanced_discovery.get("api_endpoints", {}).get("api_endpoints", []),
                "summary": enhanced_discovery.get("summary", {})
            }
            
        except PassiveReconResult.DoesNotExist:
            logger.warning(f"No passive recon results found for scan {self.scan_id}")
            return {"urls": [], "error": "No passive results found"}
        except Exception as e:
            logger.error(f"Failed to load enhanced discovery results: {e}")
            return {"urls": [], "error": str(e)}

    def add_urls_to_zap_context(self, urls: List[str]) -> bool:
        """Add discovered URLs to ZAP context for active scanning"""
        try:
            if not urls:
                logger.info("No URLs to add to ZAP context")
                return True
            
            logger.info(f"Adding {len(urls)} discovered URLs to ZAP context")
            
            # Add each URL to ZAP context
            for url in urls:
                try:
                    # Access the URL to add it to ZAP's context
                    result = self.zap_adapter._make_api_post_request("core/action/accessUrl", {"url": url})
                    if result and result.get("Result") == "OK":
                        logger.debug(f"Successfully added URL to ZAP context: {url}")
                    else:
                        logger.warning(f"Failed to add URL to ZAP context: {url}")
                except Exception as e:
                    logger.warning(f"Error adding URL {url} to ZAP context: {e}")
                    continue
            
            logger.info(f"Successfully added {len(urls)} URLs to ZAP context")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add URLs to ZAP context: {e}")
            return False

    def enhance_zap_spider_with_discovered_urls(self, target_url: str) -> Dict:
        """Enhance ZAP spider with discovered URLs"""
        try:
            logger.info("Enhancing ZAP spider with discovered URLs")
            
            # First, add all discovered URLs to ZAP context
            self.add_urls_to_zap_context(self.discovered_urls)
            
            # Configure spider to include discovered URLs
            spider_config = {
                "url": target_url,
                "maxChildren": 1000,  # Increase to handle more URLs
                "recurse": True,
                "contextName": "",  # Use default context
                "subtreeOnly": False
            }
            
            # Start spider with enhanced configuration
            spider_response = self.zap_adapter._make_api_post_request("spider/action/scan", spider_config)
            
            if spider_response and spider_response.get("Result") == "OK":
                spider_id = spider_response.get("scan")
                logger.info(f"Enhanced spider started with ID: {spider_id}")
                
                # Monitor spider progress
                self._monitor_enhanced_spider_progress(spider_id)
                
                # Get enhanced spider results
                spider_results = self._get_enhanced_spider_results()
                
                return {
                    "spider_id": spider_id,
                    "results": spider_results,
                    "discovered_urls_count": len(self.discovered_urls),
                    "enhanced": True
                }
            else:
                logger.error("Failed to start enhanced spider")
                return {"error": "Failed to start enhanced spider"}
                
        except Exception as e:
            logger.error(f"Enhanced spider failed: {e}")
            return {"error": str(e)}

    def _monitor_enhanced_spider_progress(self, spider_id: str):
        """Monitor enhanced spider progress"""
        try:
            import time
            
            while True:
                # Check spider status
                status_response = self.zap_adapter._make_api_get_request(f"spider/view/status/{spider_id}")
                
                if status_response and "status" in status_response:
                    status = status_response["status"]
                    
                    if status == "100":  # Completed
                        logger.info("Enhanced spider completed")
                        break
                    elif status == "ERROR":
                        logger.error("Enhanced spider encountered an error")
                        break
                    else:
                        logger.debug(f"Enhanced spider progress: {status}%")
                        time.sleep(2)
                else:
                    logger.warning("Could not get spider status")
                    time.sleep(2)
                    
        except Exception as e:
            logger.error(f"Error monitoring enhanced spider: {e}")

    def _get_enhanced_spider_results(self) -> Dict:
        """Get enhanced spider results"""
        try:
            # Get spider results
            results_response = self.zap_adapter._make_api_get_request("spider/view/results")
            
            if results_response and "results" in results_response:
                urls = results_response["results"]
                
                # Filter and categorize URLs
                categorized_urls = self._categorize_discovered_urls(urls)
                
                return {
                    "urls": urls,
                    "categorized": categorized_urls,
                    "total_count": len(urls),
                    "enhanced_discovery_urls": len(self.discovered_urls)
                }
            else:
                return {"urls": [], "total_count": 0}
                
        except Exception as e:
            logger.error(f"Failed to get enhanced spider results: {e}")
            return {"urls": [], "error": str(e)}

    def _categorize_discovered_urls(self, urls: List[str]) -> Dict:
        """Categorize discovered URLs"""
        categories = {
            "admin": [],
            "api": [],
            "backup": [],
            "test": [],
            "dev": [],
            "files": [],
            "images": [],
            "scripts": [],
            "other": []
        }
        
        for url in urls:
            url_lower = url.lower()
            
            if any(keyword in url_lower for keyword in ['admin', 'administrator', 'login', 'auth']):
                categories["admin"].append(url)
            elif any(keyword in url_lower for keyword in ['api', 'rest', 'graphql', 'swagger']):
                categories["api"].append(url)
            elif any(keyword in url_lower for keyword in ['backup', 'bak', 'old', 'archive']):
                categories["backup"].append(url)
            elif any(keyword in url_lower for keyword in ['test', 'testing', 'qa']):
                categories["test"].append(url)
            elif any(keyword in url_lower for keyword in ['dev', 'development', 'staging']):
                categories["dev"].append(url)
            elif any(keyword in url_lower for keyword in ['.jpg', '.png', '.gif', '.svg', 'image']):
                categories["images"].append(url)
            elif any(keyword in url_lower for keyword in ['.js', '.css', 'script']):
                categories["scripts"].append(url)
            elif any(keyword in url_lower for keyword in ['.pdf', '.doc', '.zip', '.txt', 'file']):
                categories["files"].append(url)
            else:
                categories["other"].append(url)
        
        return categories

    def _is_https_target(self) -> bool:
        """Check if target uses HTTPS"""
        try:
            # Get scan details
            from scanning.models.scan import Scan
            scan = Scan.objects.get(id=self.scan_id)
            target_url = scan.target_url or scan.configuration.project.target_url
            
            return target_url.startswith('https://')
        except:
            return True  # Default to HTTPS

