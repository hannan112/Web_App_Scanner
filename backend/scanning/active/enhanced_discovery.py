"""
Enhanced Discovery Engine

Integrates multiple mature open-source tools for comprehensive web application discovery:
- ZAP (baseline crawling and form discovery)
- Nuclei (vulnerability templates and endpoint discovery)
- httpx (fast HTTP probing and tech detection)
- Katana (modern web crawler with JS execution)
- GoSpider (fast web crawler)

This provides much better coverage than ZAP alone.
"""

import subprocess
import json
import logging
import os
import tempfile
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin
import requests

logger = logging.getLogger(__name__)


class EnhancedDiscoveryEngine:
    """Enhanced discovery using multiple open-source security tools"""
    
    def __init__(self, target_url: str, config=None):
        self.target_url = target_url
        self.config = config or {}
        self.domain = urlparse(target_url).netloc
        
        # Results storage
        self.discovered_urls = set()
        self.discovered_endpoints = set()
        self.discovered_forms = []
        self.discovered_technologies = {}
        self.discovered_subdomains = set()
        
        # Tool paths (assumes tools are in PATH or docker)
        self.tools = {
            'nuclei': self._check_tool('nuclei'),
            'httpx': self._check_tool('httpx'), 
            'katana': self._check_tool('katana'),
            'subfinder': self._check_tool('subfinder'),
            'gospider': self._check_tool('gospider')
        }
        
        logger.info(f"Enhanced discovery initialized for {target_url}")
        logger.info(f"Available tools: {[k for k, v in self.tools.items() if v]}")
    
    def _check_tool(self, tool_name: str) -> bool:
        """Check if a tool is available"""
        try:
            result = subprocess.run([tool_name, '-version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            # Try docker version
            try:
                result = subprocess.run(['docker', 'run', '--rm', f'projectdiscovery/{tool_name}', '-version'], 
                                      capture_output=True, text=True, timeout=15)
                return result.returncode == 0
            except:
                return False
    
    def run_comprehensive_discovery(self) -> Dict:
        """Run comprehensive discovery using all available tools"""
        logger.info("Starting comprehensive discovery...")
        
        # Check if this is a local application
        if self._is_local_application():
            logger.info("Detected local application, using specialized local app discovery")
            return self._run_local_app_discovery()
        
        results = {
            'urls_discovered': [],
            'endpoints_discovered': [],
            'forms_discovered': [],
            'subdomains_discovered': [],
            'technologies_discovered': {},
            'api_endpoints': [],
            'js_endpoints': [],
            'discovery_stats': {}
        }
        
        try:
            # Phase 1: Subdomain discovery
            if self.tools['subfinder']:
                self._discover_subdomains()
            
            # Phase 2: Technology detection and HTTP probing
            if self.tools['httpx']:
                self._probe_with_httpx()
            
            # Phase 3: Modern crawling with JavaScript execution
            if self.tools['katana']:
                self._crawl_with_katana()
            elif self.tools['gospider']:
                self._crawl_with_gospider()
            
            # Phase 4: Nuclei-based endpoint discovery
            if self.tools['nuclei']:
                self._discover_with_nuclei()
            
            # Phase 5: API endpoint discovery
            self._discover_api_endpoints()
            
            # Phase 6: Form analysis
            self._analyze_discovered_forms()
            
            # Compile final results
            results.update({
                'urls_discovered': list(self.discovered_urls),
                'endpoints_discovered': list(self.discovered_endpoints),
                'forms_discovered': self.discovered_forms,
                'subdomains_discovered': list(self.discovered_subdomains),
                'technologies_discovered': self.discovered_technologies,
                'api_endpoints': self._extract_api_endpoints(),
                'js_endpoints': self._extract_js_endpoints(),
                'discovery_stats': self._generate_discovery_stats()
            })
            
            logger.info(f"Discovery completed: {len(results['urls_discovered'])} URLs, "
                       f"{len(results['forms_discovered'])} forms, "
                       f"{len(results['api_endpoints'])} API endpoints")
            
            return results
            
        except Exception as e:
            logger.error(f"Enhanced discovery failed: {e}")
            return results
    
    def _discover_subdomains(self):
        """Discover subdomains using subfinder without writing temp files"""
        logger.info("Discovering subdomains with subfinder...")
        
        try:
            # Try different subfinder locations
            subfinder_paths = ['/usr/local/bin/subfinder', '/home/hannan/subfinder', 'subfinder']
            subfinder_cmd = None
            
            for path in subfinder_paths:
                try:
                    result = subprocess.run([path, '-version'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        subfinder_cmd = path
                        break
                except Exception:
                    continue
            
            if subfinder_cmd:
                # Prefer JSON/stdout to avoid file permissions
                cmd = [subfinder_cmd, '-d', self.domain, '-silent', '-json']
                logger.info(f"Using subfinder at: {subfinder_cmd}")
            else:
                # Fallback to Docker, read stdout directly
                cmd = ['docker', 'run', '--rm', 'projectdiscovery/subfinder', '-d', self.domain, '-silent', '-json']
                logger.info("Using Docker subfinder")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.warning(f"Subfinder exited with code {result.returncode}: {result.stderr.strip()}")
            
            # Parse stdout: try JSONL first, fallback to plain text lines
            stdout = result.stdout or ""
            parsed_any = False
            for line in stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                subdomain = None
                try:
                    data = json.loads(line)
                    subdomain = data.get('host') or data.get('input') or data.get('fqdn')
                except json.JSONDecodeError:
                    # Not JSON, treat as plain text subdomain
                    subdomain = line
                
                if subdomain and self.domain in subdomain:
                    parsed_any = True
                    self.discovered_subdomains.add(subdomain)
                    self.discovered_urls.add(f"https://{subdomain}")
                    self.discovered_urls.add(f"http://{subdomain}")
            
            if not parsed_any and not stdout and subfinder_cmd is None:
                logger.info("Docker subfinder produced no output; ensure Docker can access the network and image is present")
            
            logger.info(f"Found {len(self.discovered_subdomains)} subdomains")
            
        except subprocess.TimeoutExpired:
            logger.warning("Subfinder timed out after 60s")
        except Exception as e:
            logger.error(f"Subfinder discovery failed: {e}")
    
    def _probe_with_httpx(self):
        """Probe URLs and detect technologies with httpx"""
        logger.info("Probing with httpx for technology detection...")
        
        try:
            # Create target list
            targets = [self.target_url] + list(self.discovered_subdomains)
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                for target in targets:
                    f.write(f"{target}\n")
                target_file = f.name
            
            # Run httpx with technology detection
            cmd = ['httpx', '-l', target_file, '-tech-detect', '-json', '-silent', '-timeout', '10']
            if not self.tools['httpx']:
                cmd = ['docker', 'run', '--rm', '-v', f'{os.path.dirname(target_file)}:{os.path.dirname(target_file)}', 
                      'projectdiscovery/httpx', '-l', target_file, '-tech-detect', '-json', '-silent']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # Parse JSON output
            for line in result.stdout.split('\n'):
                if line.strip():
                    try:
                        data = json.loads(line)
                        url = data.get('url', '')
                        if url:
                            self.discovered_urls.add(url)
                            
                        # Extract technologies
                        techs = data.get('tech', [])
                        if techs:
                            self.discovered_technologies[url] = techs
                            
                    except json.JSONDecodeError:
                        continue
            
            # Cleanup
            os.unlink(target_file)
            
            logger.info(f"httpx detected {len(self.discovered_technologies)} tech stacks")
            
        except Exception as e:
            logger.error(f"httpx probing failed: {e}")
    
    def _crawl_with_katana(self):
        """Modern crawling with katana (includes JS execution)"""
        logger.info("Crawling with katana (JavaScript-aware)...")
        
        try:
            cmd = [
                'katana', '-u', self.target_url,
                '-js-crawl',  # Enable JavaScript crawling
                '-depth', '3',
                '-json',
                '-silent',
                '-field-scope', 'page,url,method',
                '-timeout', '30'
            ]
            
            if not self.tools['katana']:
                cmd = ['docker', 'run', '--rm', 'projectdiscovery/katana'] + cmd[1:]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Parse katana output
            for line in result.stdout.split('\n'):
                if line.strip():
                    try:
                        data = json.loads(line)
                        
                        url = data.get('url', '')
                        if url:
                            self.discovered_urls.add(url)
                            
                        method = data.get('method', 'GET')
                        if method != 'GET':
                            endpoint = {
                                'url': url,
                                'method': method,
                                'source': 'katana'
                            }
                            self.discovered_endpoints.add(json.dumps(endpoint, sort_keys=True))
                            
                    except json.JSONDecodeError:
                        continue
            
            logger.info(f"Katana discovered {len(self.discovered_urls)} URLs")
            
        except Exception as e:
            logger.error(f"Katana crawling failed: {e}")
    
    def _crawl_with_gospider(self):
        """Fallback crawling with gospider"""
        logger.info("Crawling with gospider...")
        
        try:
            cmd = [
                'gospider', '-s', self.target_url,
                '-d', '3',
                '--json',
                '--quiet',
                '-t', '10',
                '-c', '5'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            for line in result.stdout.split('\n'):
                if line.strip():
                    try:
                        data = json.loads(line)
                        url = data.get('output', '')
                        if url and url.startswith('http'):
                            self.discovered_urls.add(url)
                    except json.JSONDecodeError:
                        continue
            
            logger.info(f"GoSpider discovered {len(self.discovered_urls)} URLs")
            
        except Exception as e:
            logger.error(f"GoSpider crawling failed: {e}")
    
    def _discover_with_nuclei(self):
        """Use nuclei for endpoint and vulnerability discovery"""
        logger.info("Running nuclei for endpoint discovery...")
        
        try:
            # Create target list file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                for url in self.discovered_urls:
                    f.write(f"{url}\n")
                target_file = f.name
            
            # Run nuclei with specific templates for discovery
            cmd = [
                'nuclei', '-l', target_file,
                '-t', 'exposures/',  # Exposure detection templates
                '-t', 'misconfiguration/',  # Misconfiguration templates
                '-json', '-silent',
                '-rate-limit', '10',
                '-timeout', '15'
            ]
            
            if not self.tools['nuclei']:
                cmd = ['docker', 'run', '--rm', '-v', f'{os.path.dirname(target_file)}:{os.path.dirname(target_file)}', 
                      'projectdiscovery/nuclei'] + cmd[1:]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Parse nuclei output for discovered endpoints
            for line in result.stdout.split('\n'):
                if line.strip():
                    try:
                        data = json.loads(line)
                        url = data.get('matched-at', '')
                        if url:
                            self.discovered_endpoints.add(url)
                    except json.JSONDecodeError:
                        continue
            
            # Cleanup
            os.unlink(target_file)
            
            logger.info(f"Nuclei discovered {len(self.discovered_endpoints)} potential endpoints")
            
        except Exception as e:
            logger.error(f"Nuclei discovery failed: {e}")
    
    def _discover_api_endpoints(self):
        """Discover API endpoints through pattern analysis"""
        logger.info("Analyzing for API endpoints...")
        
        api_patterns = [
            '/api/', '/v1/', '/v2/', '/v3/', '/rest/', '/graphql',
            '/json/', '/xml/', '/service/', '/ws/', '/webhook/'
        ]
        
        base_url = f"{urlparse(self.target_url).scheme}://{urlparse(self.target_url).netloc}"
        
        for pattern in api_patterns:
            test_url = urljoin(base_url, pattern)
            try:
                response = requests.head(test_url, timeout=10, allow_redirects=False)
                if response.status_code not in [404, 403]:
                    self.discovered_endpoints.add(test_url)
            except:
                continue
    
    def _analyze_discovered_forms(self):
        """Analyze discovered URLs for forms"""
        logger.info("Analyzing discovered URLs for forms...")
        
        form_indicators = {
            'login': {
                'fields': ['username', 'password', 'email'],
                'methods': ['POST'],
                'confidence': 0.9
            },
            'register': {
                'fields': ['username', 'email', 'password', 'confirm_password'],
                'methods': ['POST'],
                'confidence': 0.8
            },
            'contact': {
                'fields': ['name', 'email', 'message', 'subject'],
                'methods': ['POST'],
                'confidence': 0.7
            },
            'search': {
                'fields': ['q', 'query', 'search', 'term'],
                'methods': ['GET', 'POST'],
                'confidence': 0.6
            },
            'upload': {
                'fields': ['file', 'upload', 'attachment'],
                'methods': ['POST'],
                'confidence': 0.8
            }
        }
        
        for url in list(self.discovered_urls)[:100]:  # Limit to prevent timeout
            url_lower = url.lower()
            
            for form_type, config in form_indicators.items():
                if form_type in url_lower or any(field in url_lower for field in config['fields']):
                    form = {
                        'url': url,
                        'action': url,
                        'method': config['methods'][0],
                        'type': form_type,
                        'fields': [{'name': field, 'type': 'text'} for field in config['fields']],
                        'discovered_by': 'Enhanced pattern analysis',
                        'confidence': config['confidence']
                    }
                    self.discovered_forms.append(form)
                    break
    
    def _extract_api_endpoints(self) -> List[str]:
        """Extract API endpoints from discovered URLs"""
        api_endpoints = []
        
        api_indicators = ['api', 'rest', 'graphql', 'json', 'xml', 'service']
        
        for url in self.discovered_urls:
            url_lower = url.lower()
            if any(indicator in url_lower for indicator in api_indicators):
                api_endpoints.append(url)
        
        return api_endpoints
    
    def _extract_js_endpoints(self) -> List[str]:
        """Extract JavaScript/AJAX endpoints"""
        js_endpoints = []
        
        js_indicators = ['ajax', 'xhr', 'fetch', 'async', 'callback']
        
        for url in self.discovered_urls:
            url_lower = url.lower()
            if any(indicator in url_lower for indicator in js_indicators):
                js_endpoints.append(url)
        
        return js_endpoints
    
    def _generate_discovery_stats(self) -> Dict:
        """Generate discovery statistics"""
        return {
            'total_urls': len(self.discovered_urls),
            'total_endpoints': len(self.discovered_endpoints),
            'total_forms': len(self.discovered_forms),
            'total_subdomains': len(self.discovered_subdomains),
            'total_technologies': len(self.discovered_technologies),
            'tools_used': [tool for tool, available in self.tools.items() if available],
            'discovery_time': time.time()  # Could track actual time
        }
    
    def _is_local_application(self) -> bool:
        """Check if this is a local application"""
        parsed = urlparse(self.target_url)
        hostname = parsed.hostname
        
        # Check for local IPs and localhost
        local_indicators = [
            'localhost', '127.0.0.1', '0.0.0.0',
            '172.', '192.168.', '10.', '169.254.'
        ]
        
        return any(hostname.startswith(indicator) for indicator in local_indicators)
    
    def _run_local_app_discovery(self) -> Dict:
        """Run specialized discovery for local applications"""
        try:
            from .local_app_discovery import LocalAppDiscoveryEngine
            
            local_discovery = LocalAppDiscoveryEngine(self.target_url, self.config)
            return local_discovery.run_comprehensive_discovery()
            
        except Exception as e:
            logger.error(f"Local app discovery failed: {e}")
            # Fallback to basic discovery
            return {
                'target_url': self.target_url,
                'urls_discovered': [self.target_url],
                'endpoints_discovered': [],
                'forms_discovered': [],
                'subdomains_discovered': [],
                'technologies_discovered': {},
                'api_endpoints': [],
                'js_endpoints': [],
                'discovery_stats': {'total_urls': 1, 'total_forms': 0}
            }


class ZAPEnhancedAdapter:
    """Enhanced ZAP adapter that combines ZAP with other discovery tools"""
    
    def __init__(self, zap_adapter, target_url: str):
        self.zap_adapter = zap_adapter
        self.target_url = target_url
        self.enhanced_discovery = EnhancedDiscoveryEngine(target_url)
    
    def run_enhanced_discovery(self) -> Dict:
        """Run enhanced discovery combining ZAP with other tools"""
        logger.info("Starting enhanced discovery with multiple tools...")
        
        # Run enhanced discovery
        enhanced_results = self.enhanced_discovery.run_comprehensive_discovery()
        
        # Run ZAP spider for comparison
        zap_results = self._run_zap_discovery()
        
        # Merge results
        merged_results = self._merge_discovery_results(enhanced_results, zap_results)
        
        logger.info(f"Enhanced discovery completed: {merged_results.get('discovery_stats', {})}")
        
        return merged_results
    
    def _run_zap_discovery(self) -> Dict:
        """Run ZAP discovery for comparison"""
        try:
            # Use existing ZAP spider functionality
            spider_results = self.zap_adapter._get_spider_results() if hasattr(self.zap_adapter, '_get_spider_results') else {}
            ajax_results = self.zap_adapter._get_ajax_spider_results() if hasattr(self.zap_adapter, '_get_ajax_spider_results') else {}
            
            return {
                'spider_results': spider_results,
                'ajax_results': ajax_results,
                'zap_urls': spider_results.get('urls', []) + ajax_results.get('urls', []),
                'zap_forms': spider_results.get('forms', []) + ajax_results.get('forms', [])
            }
        except Exception as e:
            logger.error(f"ZAP discovery failed: {e}")
            return {}
    
    def _merge_discovery_results(self, enhanced: Dict, zap: Dict) -> Dict:
        """Merge enhanced discovery with ZAP results"""
        
        # Combine all discovered URLs
        all_urls = set(enhanced.get('urls_discovered', []))
        all_urls.update(zap.get('zap_urls', []))
        
        # Combine all forms
        all_forms = enhanced.get('forms_discovered', []) + zap.get('zap_forms', [])
        
        # Remove duplicate forms
        unique_forms = []
        seen_forms = set()
        for form in all_forms:
            form_key = f"{form.get('url', '')}-{form.get('method', '')}"
            if form_key not in seen_forms:
                unique_forms.append(form)
                seen_forms.add(form_key)
        
        merged = {
            'urls': list(all_urls),
            'forms': unique_forms,
            'api_endpoints': enhanced.get('api_endpoints', []),
            'js_endpoints': enhanced.get('js_endpoints', []),
            'subdomains': enhanced.get('subdomains_discovered', []),
            'technologies': enhanced.get('technologies_discovered', {}),
            'enhanced_stats': enhanced.get('discovery_stats', {}),
            'zap_stats': {
                'zap_urls': len(zap.get('zap_urls', [])),
                'zap_forms': len(zap.get('zap_forms', []))
            },
            'total_urls': len(all_urls),
            'total_forms': len(unique_forms)
        }
        
        return merged