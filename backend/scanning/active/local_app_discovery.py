"""
Local Application Discovery Engine

Specialized discovery for local vulnerable applications and test environments.
Uses web crawling, form discovery, and manual endpoint testing.
"""

import requests
import logging
import re
from typing import Dict, List, Set
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)


class LocalAppDiscoveryEngine:
    """Enhanced discovery specifically for local applications"""
    
    def __init__(self, target_url: str, config=None):
        self.target_url = target_url
        self.config = config or {}
        self.domain = urlparse(target_url).netloc
        
        # Results storage
        self.discovered_urls = set()
        self.discovered_forms = []
        self.discovered_endpoints = set()
        self.discovered_parameters = set()
        
        # Common vulnerable endpoints to test
        self.common_endpoints = [
            '/', '/login', '/admin', '/dashboard', '/search', '/api', '/api/users',
            '/api/login', '/api/search', '/user', '/profile', '/settings', '/config',
            '/test', '/debug', '/admin/login', '/admin/dashboard', '/search.php',
            '/login.php', '/admin.php', '/user.php', '/profile.php', '/api/v1',
            '/api/v2', '/api/v1/users', '/api/v1/login', '/api/v1/search',
            '/contact', '/about', '/help', '/support', '/feedback', '/register',
            '/signup', '/logout', '/session', '/auth', '/oauth', '/callback',
            '/redirect', '/error', '/404', '/500', '/robots.txt', '/sitemap.xml',
            '/.env', '/config.json', '/api.json', '/swagger', '/swagger.json',
            '/docs', '/documentation', '/api-docs', '/openapi.json',
            
            # Security-sensitive endpoints (common across applications)
            '/phpinfo.php', '/info.php', '/phpinfo/', '/server-info/', '/serverinfo/',
            '/phpmyadmin/', '/adminer.php', '/pma/', '/mysql/', '/database/',
            '/debug.php', '/debug/', '/test.php', '/test/', '/testing/',
            '/error_log/', '/error.log', '/access.log', '/logs/', '/log/',
            '/backup/', '/backup.php', '/backups/', '/backup.sql', '/database.sql',
            '/.env', '/.env.local', '/.env.production', '/config.php', '/config.json',
            '/wp-config.php', '/wp-config.php.bak', '/configuration.php',
            '/install/', '/install.php', '/setup/', '/setup.php', '/installer/',
            '/upgrade/', '/upgrade.php', '/migrate/', '/migration/',
            '/admin/', '/administrator/', '/admin.php', '/admin/login.php',
            '/manager/', '/management/', '/control/', '/controlpanel/',
            '/panel/', '/adminpanel/', '/admin-panel/', '/dashboard/',
            '/cpanel/', '/cpanel.php', '/plesk/', '/directadmin/',
            
            # Additional common web app endpoints
            '/install/', '/install.php', '/setup/', '/setup.php', '/installer/',
            '/backup/', '/backup.php', '/backups/', '/backup.sql', '/database.sql',
            '/wp-admin/', '/wp-login.php', '/wp-content/', '/wp-includes/',
            '/administrator/', '/admin.php', '/admin/', '/admin/login.php',
            '/cpanel/', '/cpanel.php', '/control/', '/controlpanel/',
            '/manager/', '/manager.php', '/management/', '/manage/',
            '/panel/', '/panel.php', '/adminpanel/', '/admin-panel/',
            '/dashboard/', '/dashboard.php', '/dash/', '/control-dashboard/',
            '/user/', '/users/', '/user.php', '/users.php', '/account/',
            '/accounts/', '/account.php', '/profile/', '/profiles/',
            '/profile.php', '/user-profile/', '/userprofile/', '/myaccount/',
            '/my-account/', '/my_account/', '/account-settings/', '/settings/',
            '/user-settings/', '/preferences/', '/prefs/', '/config/',
            '/configuration/', '/config.php', '/configuration.php', '/conf/',
            '/system/', '/system.php', '/sys/', '/system-info/', '/info/',
            '/info.php', '/phpinfo.php', '/server-info/', '/serverinfo/',
            '/status/', '/status.php', '/health/', '/health.php', '/ping/',
            '/test/', '/test.php', '/testing/', '/debug/', '/debug.php',
            '/logs/', '/log/', '/log.php', '/logs.php', '/error_log/',
            '/error.log', '/access.log', '/access_log/', '/error_logs/',
            '/tmp/', '/temp/', '/temporary/', '/cache/', '/caches/',
            '/session/', '/sessions/', '/session.php', '/sessions.php',
            '/cookie/', '/cookies/', '/cookie.php', '/cookies.php',
            '/database/', '/db/', '/database.php', '/db.php', '/mysql/',
            '/mysql.php', '/postgresql/', '/postgres/', '/sqlite/',
            '/sql/', '/sql.php', '/query/', '/queries/', '/query.php',
            '/search/', '/search.php', '/find/', '/find.php', '/lookup/',
            '/lookup.php', '/browse/', '/browse.php', '/list/', '/list.php',
            '/files/', '/file/', '/files.php', '/file.php', '/upload/',
            '/upload.php', '/uploads/', '/uploads.php', '/download/',
            '/download.php', '/downloads/', '/downloads.php', '/media/',
            '/media.php', '/images/', '/image/', '/images.php', '/image.php',
            '/css/', '/styles/', '/stylesheets/', '/js/', '/javascript/',
            '/scripts/', '/script/', '/assets/', '/static/', '/public/',
            '/private/', '/secure/', '/secure.php', '/protected/',
            '/protected.php', '/restricted/', '/restricted.php', '/hidden/',
            '/hidden.php', '/secret/', '/secret.php', '/internal/',
            '/internal.php', '/intranet/', '/intranet.php', '/local/',
            '/localhost/', '/dev/', '/development/', '/dev.php', '/stage/',
            '/staging/', '/staging.php', '/prod/', '/production/',
            '/production.php', '/live/', '/live.php', '/beta/', '/beta.php',
            '/alpha/', '/alpha.php', '/demo/', '/demo.php', '/sample/',
            '/sample.php', '/example/', '/example.php', '/test-site/',
            '/test-site.php', '/sandbox/', '/sandbox.php', '/playground/',
            '/playground.php', '/lab/', '/lab.php', '/experiment/',
            '/experiment.php', '/research/', '/research.php', '/study/',
            '/study.php', '/pilot/', '/pilot.php', '/prototype/',
            '/prototype.php', '/mockup/', '/mockup.php', '/template/',
            '/template.php', '/templates/', '/templates.php', '/layout/',
            '/layout.php', '/layouts/', '/layouts.php', '/theme/',
            '/theme.php', '/themes/', '/themes.php', '/skin/', '/skin.php',
            '/skins/', '/skins.php', '/design/', '/design.php', '/designs/',
            '/designs.php', '/style/', '/style.php', '/styles/', '/styles.php'
        ]
        
        # Common vulnerable parameters
        self.common_parameters = [
            'id', 'user', 'username', 'password', 'email', 'search', 'q', 'query',
            'page', 'limit', 'offset', 'sort', 'order', 'filter', 'category',
            'type', 'status', 'level', 'role', 'group', 'team', 'project',
            'name', 'title', 'description', 'content', 'message', 'comment',
            'date', 'time', 'year', 'month', 'day', 'from', 'to', 'start', 'end'
        ]
        
        logger.info(f"Local app discovery initialized for {target_url}")
    
    def run_comprehensive_discovery(self) -> Dict:
        """Run comprehensive discovery for local applications"""
        logger.info("Starting comprehensive local app discovery...")
        
        results = {
            'target_url': self.target_url,
            'urls_discovered': [],
            'forms_discovered': [],
            'endpoints_discovered': [],
            'parameters_discovered': [],
            'discovery_stats': {}
        }
        
        try:
            # Phase 1: Basic web crawling
            logger.info("Phase 1: Basic web crawling")
            self._crawl_main_page()
            
            # Phase 2: Common endpoint discovery
            logger.info("Phase 2: Common endpoint discovery")
            self._discover_common_endpoints()
            
            # Phase 3: Form discovery and analysis
            logger.info("Phase 3: Form discovery and analysis")
            self._discover_forms()
            
            # Phase 4: Parameter discovery
            logger.info("Phase 4: Parameter discovery")
            self._discover_parameters()
            
            # Phase 5: API endpoint discovery
            logger.info("Phase 5: API endpoint discovery")
            self._discover_api_endpoints()
            
            # Compile results
            results.update({
                'urls_discovered': list(self.discovered_urls),
                'forms_discovered': self.discovered_forms,
                'endpoints_discovered': list(self.discovered_endpoints),
                'parameters_discovered': list(self.discovered_parameters),
                'discovery_stats': self._generate_discovery_stats()
            })
            
            logger.info(f"Local app discovery completed: {len(results['urls_discovered'])} URLs, "
                       f"{len(results['forms_discovered'])} forms, "
                       f"{len(results['endpoints_discovered'])} endpoints")
            
            return results
            
        except Exception as e:
            logger.error(f"Local app discovery failed: {e}")
            return results
    
    def _crawl_main_page(self):
        """Crawl the main page for links and forms"""
        try:
            # Check if authentication is enabled
            if hasattr(self.config, 'enable_authentication') and self.config.enable_authentication:
                logger.info("🔐 Authentication enabled - attempting DVWA login")
                self._authenticate_and_crawl()
            else:
                # Standard unauthenticated crawling
                response = requests.get(self.target_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find all links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(self.target_url, href)
                        self.discovered_urls.add(full_url)
                    
                    # Find all forms
                    for form in soup.find_all('form'):
                        form_data = self._extract_form_data(form)
                        if form_data:
                            self.discovered_forms.append(form_data)
                    
                    # Find JavaScript endpoints
                    for script in soup.find_all('script', src=True):
                        src = script['src']
                        full_url = urljoin(self.target_url, src)
                        self.discovered_urls.add(full_url)
                    
                    logger.info(f"Main page crawl found {len(self.discovered_urls)} URLs and {len(self.discovered_forms)} forms")
                
        except Exception as e:
            logger.error(f"Main page crawl failed: {e}")
    
    def _authenticate_and_crawl(self):
        """Authenticate with DVWA and crawl vulnerability pages"""
        try:
            from dvwa_authenticator import DVWAAuthenticator
            
            # Get authentication settings
            username = getattr(self.config, 'auth_username', 'admin')
            password = getattr(self.config, 'auth_password', 'password')
            
            # Create authenticator
            authenticator = DVWAAuthenticator(self.target_url, username, password)
            
            # Authenticate
            if authenticator.authenticate():
                logger.info("✅ Successfully authenticated with DVWA")
                
                # Discover DVWA vulnerability pages
                dvwa_pages = authenticator.discover_dvwa_vulnerabilities()
                
                # Add discovered pages to our URLs
                for page_url in dvwa_pages:
                    self.discovered_urls.add(page_url)
                    self.discovered_endpoints.add(urlparse(page_url).path)
                
                # Also crawl the main authenticated page
                main_response = authenticator.get_authenticated_page(self.target_url)
                if main_response and main_response.status_code == 200:
                    soup = BeautifulSoup(main_response.content, 'html.parser')
                    
                    # Find additional links from authenticated page
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(self.target_url, href)
                        self.discovered_urls.add(full_url)
                    
                    # Find forms
                    for form in soup.find_all('form'):
                        form_data = self._extract_form_data(form)
                        if form_data:
                            self.discovered_forms.append(form_data)
                
                logger.info(f"🎯 DVWA authenticated crawl found {len(self.discovered_urls)} URLs")
                
            else:
                logger.error("❌ DVWA authentication failed - falling back to unauthenticated crawl")
                # Fall back to standard crawling
                response = requests.get(self.target_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(self.target_url, href)
                        self.discovered_urls.add(full_url)
                
        except Exception as e:
            logger.error(f"DVWA authentication crawl failed: {e}")
            # Fall back to standard crawling
            try:
                response = requests.get(self.target_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(self.target_url, href)
                        self.discovered_urls.add(full_url)
            except Exception as fallback_e:
                logger.error(f"Fallback crawl also failed: {fallback_e}")
    
    def _discover_common_endpoints(self):
        """Discover common vulnerable endpoints"""
        for endpoint in self.common_endpoints:
            try:
                full_url = urljoin(self.target_url, endpoint)
                response = requests.get(full_url, timeout=5)
                
                if response.status_code in [200, 301, 302, 403, 401]:
                    self.discovered_urls.add(full_url)
                    self.discovered_endpoints.add(endpoint)
                    
                    # If it's a page with content, try to find more links
                    if response.status_code == 200 and 'text/html' in response.headers.get('content-type', ''):
                        soup = BeautifulSoup(response.content, 'html.parser')
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            link_url = urljoin(full_url, href)
                            self.discovered_urls.add(link_url)
                
                # Small delay to avoid overwhelming the server
                time.sleep(0.1)
                
            except Exception as e:
                logger.debug(f"Failed to test endpoint {endpoint}: {e}")
    
    def _discover_forms(self):
        """Discover and analyze forms"""
        for url in list(self.discovered_urls):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    for form in soup.find_all('form'):
                        form_data = self._extract_form_data(form, url)
                        if form_data:
                            self.discovered_forms.append(form_data)
                            
            except Exception as e:
                logger.debug(f"Failed to analyze forms for {url}: {e}")
    
    def _extract_form_data(self, form, base_url=None):
        """Extract form data for analysis"""
        try:
            form_data = {
                'url': base_url or self.target_url,
                'method': form.get('method', 'GET').upper(),
                'action': form.get('action', ''),
                'data': {}
            }
            
            # Extract input fields
            for input_field in form.find_all(['input', 'select', 'textarea']):
                name = input_field.get('name')
                value = input_field.get('value', '')
                input_type = input_field.get('type', 'text')
                
                if name:
                    # Use common test values based on field type
                    if input_type in ['email']:
                        form_data['data'][name] = 'test@example.com'
                    elif input_type in ['password']:
                        form_data['data'][name] = 'password123'
                    elif name.lower() in ['username', 'user', 'login']:
                        form_data['data'][name] = 'admin'
                    elif name.lower() in ['id', 'user_id', 'uid']:
                        form_data['data'][name] = '1'
                    elif name.lower() in ['search', 'q', 'query']:
                        form_data['data'][name] = 'test'
                    else:
                        form_data['data'][name] = value or 'test'
            
            return form_data if form_data['data'] else None
            
        except Exception as e:
            logger.debug(f"Failed to extract form data: {e}")
            return None
    
    def _discover_parameters(self):
        """Discover common parameters by testing URLs with parameters"""
        # Get configuration limits
        enable_fuzzing = getattr(self.config, 'enable_parameter_fuzzing', True)
        max_combinations = getattr(self.config, 'max_parameter_combinations', 50)
        max_params_per_url = getattr(self.config, 'max_parameters_per_url', 10)
        custom_values = getattr(self.config, 'parameter_fuzzing_values', [])
        
        if not enable_fuzzing:
            logger.info("Parameter fuzzing disabled by configuration")
            return
        
        # Use custom values if provided, otherwise use default test values
        test_values = custom_values if custom_values else ['test', 'admin', '1']
        
        logger.info(f"Starting parameter discovery with limits: max_combinations={max_combinations}, max_params_per_url={max_params_per_url}")
        
        urls_to_test = list(self.discovered_urls)[:5]  # Limit to first 5 URLs to avoid excessive testing
        parameters_to_test = self.common_parameters[:max_params_per_url]  # Limit parameters
        
        for url in urls_to_test:
            combinations_tested = 0
            
            # Test single parameters first
            for param in parameters_to_test:
                if combinations_tested >= max_combinations:
                    break
                    
                test_url = f"{url}?{param}={test_values[0]}"
                try:
                    response = requests.get(test_url, timeout=3)
                    if response.status_code in [200, 400, 500]:  # Any response indicates parameter exists
                        self.discovered_urls.add(test_url)
                        self.discovered_parameters.add(param)
                        combinations_tested += 1
                except:
                    pass
            
            # Test limited parameter combinations (only if we haven't hit the limit)
            if combinations_tested < max_combinations:
                for i, param1 in enumerate(parameters_to_test[:3]):  # Limit to first 3 parameters
                    for j, param2 in enumerate(parameters_to_test[:3]):
                        if combinations_tested >= max_combinations:
                            break
                        if param1 != param2 and i < j:  # Avoid duplicates and test only unique pairs
                            test_url = f"{url}?{param1}={test_values[0]}&{param2}={test_values[1] if len(test_values) > 1 else test_values[0]}"
                            try:
                                response = requests.get(test_url, timeout=3)
                                if response.status_code in [200, 400, 500]:
                                    self.discovered_urls.add(test_url)
                                    combinations_tested += 1
                            except:
                                pass
        
        logger.info(f"Parameter discovery completed. Tested {combinations_tested} combinations, found {len(self.discovered_parameters)} unique parameters")
    
    def _discover_api_endpoints(self):
        """Discover API endpoints"""
        api_endpoints = [
            '/api', '/api/v1', '/api/v2', '/rest', '/graphql',
            '/swagger', '/swagger.json', '/openapi.json', '/api-docs'
        ]
        
        for endpoint in api_endpoints:
            try:
                full_url = urljoin(self.target_url, endpoint)
                response = requests.get(full_url, timeout=5)
                
                if response.status_code in [200, 301, 302, 403, 401]:
                    self.discovered_urls.add(full_url)
                    self.discovered_endpoints.add(endpoint)
                    
                    # If it's an API, try to find more endpoints
                    if 'application/json' in response.headers.get('content-type', ''):
                        try:
                            data = response.json()
                            # Look for more endpoints in JSON response
                            self._extract_endpoints_from_json(data, full_url)
                        except:
                            pass
                            
            except Exception as e:
                logger.debug(f"Failed to test API endpoint {endpoint}: {e}")
    
    def _extract_endpoints_from_json(self, data, base_url):
        """Extract endpoints from JSON API responses"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and value.startswith('/'):
                    endpoint_url = urljoin(base_url, value)
                    self.discovered_urls.add(endpoint_url)
                elif isinstance(value, (dict, list)):
                    self._extract_endpoints_from_json(value, base_url)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._extract_endpoints_from_json(item, base_url)
    
    def _generate_discovery_stats(self) -> Dict:
        """Generate discovery statistics"""
        return {
            'total_urls': len(self.discovered_urls),
            'total_forms': len(self.discovered_forms),
            'total_endpoints': len(self.discovered_endpoints),
            'total_parameters': len(self.discovered_parameters),
            'urls_with_params': len([url for url in self.discovered_urls if '?' in url]),
            'post_forms': len([form for form in self.discovered_forms if form.get('method') == 'POST']),
            'get_forms': len([form for form in self.discovered_forms if form.get('method') == 'GET'])
        }


