# scanning/integrations/enhanced_discovery_adapter.py
import json
import logging
import subprocess
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin
import requests
import re

logger = logging.getLogger(__name__)


class EnhancedDiscoveryAdapter:
    """Enhanced discovery adapter for comprehensive reconnaissance"""

    def __init__(self, config=None):
        self.config = config or {}
        self.timeout = self.config.get("timeout", 30)
        self.max_subdomains = self.config.get("max_subdomains", 100)
        self.max_wayback_urls = self.config.get("max_wayback_urls", 200)
        self.max_directories = self.config.get("max_directories", 50)
        self.user_agent = self.config.get("user_agent", "SecurityScanner/1.0")

    def discover_subdomains(self, domain: str) -> Dict:
        """Discover subdomains using subfinder"""
        try:
            logger.info(f"Starting subdomain discovery for {domain}")
            
            # Run subfinder
            cmd = [
                "subfinder",
                "-d", domain,
                "-silent",
                "-json"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            subdomains = []
            if result.returncode == 0 and result.stdout.strip():
                try:
                    # Parse JSON output
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            data = json.loads(line)
                            subdomains.append(data.get('host', ''))
                except json.JSONDecodeError:
                    # Fallback to plain text parsing
                    subdomains = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            
            # Remove duplicates and filter
            subdomains = list(set([sub for sub in subdomains if sub and domain in sub]))
            
            # Limit results
            if len(subdomains) > self.max_subdomains:
                subdomains = subdomains[:self.max_subdomains]
            
            logger.info(f"Found {len(subdomains)} subdomains for {domain}")
            
            return {
                "domain": domain,
                "subdomains": subdomains,
                "count": len(subdomains),
                "source": "subfinder"
            }
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Subfinder timeout for {domain}")
            return {"domain": domain, "subdomains": [], "error": "Timeout"}
        except Exception as e:
            logger.error(f"Subdomain discovery failed for {domain}: {e}")
            return {"domain": domain, "subdomains": [], "error": str(e)}

    def discover_wayback_urls(self, domain: str) -> Dict:
        """Discover historical URLs using waybackurls"""
        try:
            logger.info(f"Starting wayback URL discovery for {domain}")
            
            # Run waybackurls
            cmd = [
                "waybackurls",
                domain
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            urls = []
            if result.returncode == 0 and result.stdout.strip():
                urls = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            
            # Remove duplicates and filter
            urls = list(set([url for url in urls if url and domain in url]))
            
            # Limit results
            if len(urls) > self.max_wayback_urls:
                urls = urls[:self.max_wayback_urls]
            
            # Categorize URLs
            categorized = self._categorize_urls(urls)
            
            logger.info(f"Found {len(urls)} wayback URLs for {domain}")
            
            return {
                "domain": domain,
                "urls": urls,
                "count": len(urls),
                "categorized": categorized,
                "source": "waybackurls"
            }
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Waybackurls timeout for {domain}")
            return {"domain": domain, "urls": [], "error": "Timeout"}
        except Exception as e:
            logger.error(f"Wayback URL discovery failed for {domain}: {e}")
            return {"domain": domain, "urls": [], "error": str(e)}

    def discover_directories(self, url: str) -> Dict:
        """Discover directories using feroxbuster"""
        try:
            logger.info(f"Starting directory discovery for {url}")
            
            # Run feroxbuster with common wordlist
            cmd = [
                "feroxbuster",
                "--url", url,
                "--wordlist", "/usr/share/wordlists/dirb/common.txt",  # Common wordlist
                "--threads", "10",
                "--timeout", "5",
                "--status-codes", "200,204,301,302,307,401,403",
                "--json",
                "--quiet"
            ]
            
            # If common wordlist doesn't exist, use built-in
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
            except FileNotFoundError:
                # Use feroxbuster's built-in wordlist
                cmd = [
                    "feroxbuster",
                    "--url", url,
                    "--threads", "10",
                    "--timeout", "5",
                    "--status-codes", "200,204,301,302,307,401,403",
                    "--json",
                    "--quiet"
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
            
            directories = []
            if result.returncode == 0 and result.stdout.strip():
                try:
                    # Parse JSON output
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            data = json.loads(line)
                            if data.get('type') == 'response':
                                directories.append({
                                    "url": data.get('url', ''),
                                    "status": data.get('status', 0),
                                    "size": data.get('size', 0),
                                    "method": data.get('method', 'GET')
                                })
                except json.JSONDecodeError:
                    # Fallback parsing
                    directories = [{"url": line.strip(), "status": 200} for line in result.stdout.strip().split('\n') if line.strip()]
            
            # Limit results
            if len(directories) > self.max_directories:
                directories = directories[:self.max_directories]
            
            logger.info(f"Found {len(directories)} directories for {url}")
            
            return {
                "url": url,
                "directories": directories,
                "count": len(directories),
                "source": "feroxbuster"
            }
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Feroxbuster timeout for {url}")
            return {"url": url, "directories": [], "error": "Timeout"}
        except Exception as e:
            logger.error(f"Directory discovery failed for {url}: {e}")
            return {"url": url, "directories": [], "error": str(e)}

    def discover_api_endpoints(self, url: str) -> Dict:
        """Discover API endpoints from various sources"""
        try:
            logger.info(f"Starting API endpoint discovery for {url}")
            
            api_endpoints = []
            
            # Common API endpoint patterns
            common_endpoints = [
                "/api/",
                "/api/v1/",
                "/api/v2/",
                "/api/v3/",
                "/rest/",
                "/graphql",
                "/swagger",
                "/swagger-ui",
                "/swagger.json",
                "/openapi.json",
                "/api-docs",
                "/docs",
                "/admin/api/",
                "/internal/api/",
                "/webhook",
                "/webhooks"
            ]
            
            # Test common endpoints
            for endpoint in common_endpoints:
                test_url = urljoin(url, endpoint)
                try:
                    response = requests.get(
                        test_url,
                        headers={'User-Agent': self.user_agent},
                        timeout=5,
                        allow_redirects=True,
                        verify=False
                    )
                    
                    if response.status_code in [200, 401, 403]:
                        api_endpoints.append({
                            "url": test_url,
                            "status": response.status_code,
                            "type": "common_endpoint",
                            "content_type": response.headers.get('Content-Type', ''),
                            "server": response.headers.get('Server', '')
                        })
                        
                except Exception:
                    continue
            
            # Extract from wayback URLs if available
            domain = urlparse(url).netloc
            wayback_result = self.discover_wayback_urls(domain)
            if wayback_result.get('urls'):
                for wayback_url in wayback_result['urls']:
                    if any(pattern in wayback_url.lower() for pattern in ['/api/', '/rest/', '/graphql', '/swagger']):
                        api_endpoints.append({
                            "url": wayback_url,
                            "status": "historical",
                            "type": "wayback_discovery",
                            "source": "wayback"
                        })
            
            logger.info(f"Found {len(api_endpoints)} API endpoints for {url}")
            
            return {
                "url": url,
                "api_endpoints": api_endpoints,
                "count": len(api_endpoints),
                "source": "enhanced_discovery"
            }
            
        except Exception as e:
            logger.error(f"API endpoint discovery failed for {url}: {e}")
            return {"url": url, "api_endpoints": [], "error": str(e)}

    def _categorize_urls(self, urls: List[str]) -> Dict:
        """Categorize discovered URLs by type"""
        categories = {
            "admin": [],
            "api": [],
            "backup": [],
            "test": [],
            "dev": [],
            "staging": [],
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

    def run_comprehensive_discovery(self, target_url: str) -> Dict:
        """Run comprehensive discovery for a target"""
        try:
            logger.info(f"Starting comprehensive discovery for {target_url}")
            
            parsed_url = urlparse(target_url)
            domain = parsed_url.netloc
            base_url = f"{parsed_url.scheme}://{domain}"
            
            results = {
                "target_url": target_url,
                "domain": domain,
                "base_url": base_url,
                "subdomains": {},
                "wayback_urls": {},
                "directories": {},
                "api_endpoints": {},
                "summary": {}
            }
            
            # Run subdomain discovery
            results["subdomains"] = self.discover_subdomains(domain)
            
            # Run wayback URL discovery
            results["wayback_urls"] = self.discover_wayback_urls(domain)
            
            # Run directory discovery on main URL
            results["directories"] = self.discover_directories(target_url)
            
            # Run API endpoint discovery
            results["api_endpoints"] = self.discover_api_endpoints(target_url)
            
            # Create summary
            results["summary"] = {
                "subdomains_found": len(results["subdomains"].get("subdomains", [])),
                "wayback_urls_found": len(results["wayback_urls"].get("urls", [])),
                "directories_found": len(results["directories"].get("directories", [])),
                "api_endpoints_found": len(results["api_endpoints"].get("api_endpoints", [])),
                "total_discoveries": (
                    len(results["subdomains"].get("subdomains", [])) +
                    len(results["wayback_urls"].get("urls", [])) +
                    len(results["directories"].get("directories", [])) +
                    len(results["api_endpoints"].get("api_endpoints", []))
                )
            }
            
            logger.info(f"Comprehensive discovery completed for {target_url}")
            logger.info(f"Summary: {results['summary']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Comprehensive discovery failed for {target_url}: {e}")
            return {
                "target_url": target_url,
                "error": str(e),
                "summary": {"total_discoveries": 0}
            }

