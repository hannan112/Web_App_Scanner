"""
Passive Scanner Implementation

This module implements the passive scanner functionality that performs information gathering
without actively testing the target for vulnerabilities.
"""

import logging
import requests
import dns.resolver
import socket
import ssl
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# Local imports
from scanning.discovery.crawler import Crawler
from scanning.discovery.sitemap_parser import SitemapParser

logger = logging.getLogger(__name__)

class PassiveScanner:
    """
    Passive scanner that collects information about a target without active testing
    """
    
    def __init__(self, scan_id, scan_obj, target_url, configuration):
        """
        Initialize passive scanner
        
        Args:
            scan_id (int): ID of the scan
            scan_obj (Scan): Scan model instance
            target_url (str): Target URL to scan
            configuration (ScanConfiguration): Scan configuration
        """
        self.scan_id = scan_id
        self.scan = scan_obj
        self.target_url = target_url
        self.config = configuration
        
        # Parse URL
        parsed_url = urlparse(target_url)
        self.domain = parsed_url.netloc
        self.scheme = parsed_url.scheme
        
        # Default headers
        self.headers = {
            'User-Agent': configuration.user_agent or 'SecurityScannerBot/1.0'
        }
        
        # Add custom headers if provided
        if configuration.custom_headers:
            self.headers.update(configuration.custom_headers)
        
        # Initialize result containers
        self.results = {
            'dns_records': {},
            'server_info': {},
            'technologies': {},
            'response_headers': {},
            'urls_discovered': [],
            'forms_discovered': [],
            'cookies': {},
            'robots_txt': None,
            'sitemap_xml': None
        }
        
        # For tracking progress
        self.progress = 0
    
    def update_progress(self, progress, message=None):
        """
        Update scan progress
        
        Args:
            progress (int): Progress percentage (0-100)
            message (str, optional): Progress message
        """
        self.progress = progress
        self.scan.progress = progress
        self.scan.save()
        
        if message:
            logger.info(f"Scan {self.scan_id}: {message} - {progress}%")
    
    def run_scan(self):
        """
        Run the passive scan and return results
        
        Returns:
            dict: Scan results
        """
        try:
            # Initialize scan
            self.update_progress(5, "Starting passive scan")
            
            # Check DNS information
            self._check_dns()
            self.update_progress(15, "DNS analysis completed")
            
            # Check SSL/TLS
            self._check_ssl()
            self.update_progress(25, "SSL/TLS analysis completed")
            
            # Check HTTP headers and server info
            self._check_headers()
            self.update_progress(35, "Server information analysis completed")
            
            # Check robots.txt and sitemap
            self._check_robots_sitemap()
            self.update_progress(45, "Robots.txt and sitemap analysis completed")
            
            # Check technologies used
            self._check_technologies()
            self.update_progress(55, "Technology detection completed")
            
            # Run the crawler to discover URLs and forms
            self._crawl_website()
            self.update_progress(95, "Website crawling completed")
            
            # Save final results
            self._save_results()
            self.update_progress(100, "Passive scan completed")
            
            return self.results
            
        except Exception as e:
            logger.exception(f"Error in passive scan {self.scan_id}: {str(e)}")
            self.scan.error_message = str(e)
            self.scan.save()
            raise
    
    def _check_dns(self):
        """Check DNS information for the domain"""
        dns_records = {}
        
        # Record types to query
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA']
        
        for record_type in record_types:
            try:
                answers = dns.resolver.resolve(self.domain, record_type)
                dns_records[record_type] = [str(answer) for answer in answers]
            except Exception as e:
                logger.error(f"Error resolving {record_type} records for {self.domain}: {str(e)}")
                dns_records[record_type] = []
        
        # Get IP address
        try:
            ip_address = socket.gethostbyname(self.domain)
            dns_records['IP'] = ip_address
        except socket.gaierror:
            dns_records['IP'] = "Unable to resolve IP"
        
        self.results['dns_records'] = dns_records
    
    def _check_ssl(self):
        """Check SSL/TLS certificate and configuration"""
        if self.scheme != 'https':
            self.results['server_info']['ssl'] = {
                'error': 'Not using HTTPS'
            }
            return
        
        try:
            # Get SSL certificate info
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((self.domain, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    
                    ssl_info = {
                        'protocol': cipher[1],
                        'cipher': cipher[0],
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'validity': {
                            'not_before': cert['notBefore'],
                            'not_after': cert['notAfter']
                        }
                    }
                    
                    # Check expiration
                    not_after = ssl_info['validity']['not_after']
                    expires = datetime.strptime(not_after, '%b %d %H:%M:%S %Y GMT')
                    now = datetime.now()
                    days_remaining = (expires - now).days
                    
                    ssl_info['days_remaining'] = days_remaining
                    ssl_info['is_expired'] = days_remaining < 0
                    
                    self.results['server_info']['ssl'] = ssl_info
        
        except Exception as e:
            logger.error(f"Error checking SSL for {self.domain}: {str(e)}")
            self.results['server_info']['ssl'] = {
                'error': str(e)
            }
    
    def _check_headers(self):
        """Check HTTP headers and server information"""
        try:
            # Suppress only the InsecureRequestWarning
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response = requests.get(
                self.target_url, 
                headers=self.headers, 
                timeout=10,
                verify=False  # We intentionally want to scan sites with invalid certs
            )
            
            # Store response headers
            self.results['response_headers'] = dict(response.headers)
            
            # Extract server information
            server_info = {
                'server': response.headers.get('Server', 'Unknown'),
                'x_powered_by': response.headers.get('X-Powered-By', 'Not disclosed'),
                'content_type': response.headers.get('Content-Type', 'Unknown'),
                'status_code': response.status_code
            }
            
            # Check security headers
            security_headers = [
                'Strict-Transport-Security',
                'Content-Security-Policy',
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Referrer-Policy'
            ]
            
            server_info['security_headers'] = {
                header: response.headers.get(header, 'Not set') 
                for header in security_headers
            }
            
            # Update server info
            self.results['server_info'].update(server_info)
            
            # Store cookies
            if response.cookies:
                self.results['cookies'] = {
                    name: str(value) for name, value in response.cookies.items()
                }
            
            # Keep the response for later technology detection
            self.response = response
            
        except Exception as e:
            logger.error(f"Error checking headers for {self.target_url}: {str(e)}")
            self.results['server_info']['error'] = str(e)
    
    def _check_robots_sitemap(self):
        """Check robots.txt and sitemap.xml"""
        # Check robots.txt
        robots_url = f"{self.scheme}://{self.domain}/robots.txt"
        try:
            response = requests.get(robots_url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                self.results['robots_txt'] = response.text
        except Exception as e:
            logger.error(f"Error checking robots.txt: {str(e)}")
        
        # Check sitemap.xml
        sitemap_url = f"{self.scheme}://{self.domain}/sitemap.xml"
        try:
            response = requests.get(sitemap_url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                # Parse sitemap
                parser = SitemapParser(self.target_url)
                urls = parser.parse(sitemap_url)
                self.results['sitemap_xml'] = urls
        except Exception as e:
            logger.error(f"Error checking sitemap.xml: {str(e)}")
    
    def _check_technologies(self):
        """Check technologies used by the website"""
        if not hasattr(self, 'response'):
            return
        
        try:
            response_text = self.response.text
            response_headers = self.response.headers
            
            technologies = {
                'server': response_headers.get('Server', 'Unknown'),
                'frameworks': [],
                'cms': None,
                'javascript_libraries': []
            }
            
            # Check for common frameworks and CMS
            frameworks_signatures = {
                'WordPress': ['wp-content', 'wp-includes'],
                'Drupal': ['Drupal.settings', 'drupal.org'],
                'Joomla': ['joomla!', '/components/com_'],
                'Laravel': ['laravel', 'laravel-token'],
                'Django': ['csrfmiddlewaretoken', '__admin_media_prefix__'],
                'Express.js': ['expressjs'],
                'Ruby on Rails': ['rails', 'data-turbolinks-track'],
                'ASP.NET': ['asp.net', '__VIEWSTATE']
            }
            
            js_libraries = {
                'jQuery': ['jquery'],
                'React': ['react', 'reactjs'],
                'Vue.js': ['vue.js', 'vuejs'],
                'Angular': ['angular', 'ng-app'],
                'Bootstrap': ['bootstrap'],
                'Tailwind CSS': ['tailwindcss', 'tailwind.css']
            }
            
            # Check for framework signatures in response
            for framework, signatures in frameworks_signatures.items():
                for signature in signatures:
                    if signature.lower() in response_text.lower():
                        if framework in ['WordPress', 'Drupal', 'Joomla']:
                            technologies['cms'] = framework
                        else:
                            technologies['frameworks'].append(framework)
                        break
            
            # Check for JavaScript libraries
            for library, signatures in js_libraries.items():
                for signature in signatures:
                    if signature.lower() in response_text.lower():
                        technologies['javascript_libraries'].append(library)
                        break
            
            # Detect technologies from headers
            if 'X-Powered-By' in response_headers:
                powered_by = response_headers['X-Powered-By']
                if 'PHP' in powered_by:
                    technologies['frameworks'].append('PHP')
                if 'ASP.NET' in powered_by:
                    technologies['frameworks'].append('ASP.NET')
            
            # Remove duplicates
            technologies['frameworks'] = list(set(technologies['frameworks']))
            technologies['javascript_libraries'] = list(set(technologies['javascript_libraries']))
            
            self.results['technologies'] = technologies
            
        except Exception as e:
            logger.error(f"Error checking technologies: {str(e)}")
    
    def _crawl_website(self):
        """
        Crawl the website to discover URLs, forms, and cookies
        """
        try:
            # Configure crawler based on scan config
            crawler = Crawler(
                self.target_url,
                max_depth=self.config.crawl_depth,
                respect_robots_txt=self.config.respect_robots_txt,
                max_pages=self.config.crawl_max_pages,
                request_delay=getattr(self.config, 'request_delay', 0.5),
                timeout=getattr(self.config, 'crawl_timeout', 30),
                user_agent=self.config.user_agent,
                custom_headers=self.config.custom_headers
            )
            
            # Define progress callback
            def progress_callback(progress, urls, forms, cookies):
                # Map crawler progress (0-100) to overall scan progress (55-95)
                scan_progress = 55 + (progress * 0.4)
                self.update_progress(scan_progress, f"Crawling: {len(urls)} URLs discovered")
            
            # Start crawling
            crawl_results = crawler.start(progress_callback)
            
            # Update scan results with crawl data
            self.results['urls_discovered'] = crawl_results['urls_discovered']
            self.results['forms_discovered'] = crawl_results['forms_discovered']
            
            # Merge cookies
            if crawl_results['cookies']:
                self.results['cookies'].update(crawl_results['cookies'])
            
        except Exception as e:
            logger.error(f"Error crawling website {self.target_url}: {str(e)}")
            raise
    
    def _save_results(self):
        """Save scan results to database"""
        # Import models here to avoid circular imports
        from scanning.models.scan import PassiveReconResult, CrawlResult
        from scanning.models.vulnerability import Vulnerability
        
        try:
            # Save passive recon results
            passive_result = PassiveReconResult.objects.create(
                scan=self.scan,
                dns_records=self.results['dns_records'],
                server_info=self.results['server_info'],
                robots_txt=self.results['robots_txt'],
                sitemap_xml=self.results['sitemap_xml'],
                technologies=self.results['technologies'],
                response_headers=self.results['response_headers']
            )
            
            # Save crawl results
            crawl_result = CrawlResult.objects.create(
                scan=self.scan,
                urls_discovered=self.results['urls_discovered'],
                forms_discovered=self.results['forms_discovered'],
                cookies=self.results['cookies'],
                pages_crawled=len(self.results['urls_discovered'])
            )
            
            # Generate vulnerabilities based on findings
            self._generate_vulnerabilities()
            
        except Exception as e:
            logger.error(f"Error saving scan results: {str(e)}")
            raise
    
    def _generate_vulnerabilities(self):
        """Generate vulnerabilities based on findings"""
        # Import here to avoid circular imports
        from scanning.models.vulnerability import Vulnerability
        
        # Check SSL issues
        ssl_info = self.results['server_info'].get('ssl', {})
        if 'error' in ssl_info:
            if self.scheme == 'https':
                Vulnerability.objects.create(
                    scan=self.scan,
                    name="SSL/TLS Configuration Issue",
                    description=f"SSL configuration error: {ssl_info['error']}",
                    severity="high",
                    url=self.target_url,
                    remediation="Check your SSL/TLS configuration and certificates.",
                    confidence=0.9
                )
        elif ssl_info.get('is_expired'):
            Vulnerability.objects.create(
                scan=self.scan,
                name="Expired SSL Certificate",
                description=f"The SSL certificate has expired. It expired {abs(ssl_info['days_remaining'])} days ago.",
                severity="critical",
                url=self.target_url,
                remediation="Renew the SSL certificate immediately.",
                confidence=1.0
            )
        elif ssl_info.get('days_remaining', 100) < 30:
            Vulnerability.objects.create(
                scan=self.scan,
                name="SSL Certificate Expiring Soon",
                description=f"The SSL certificate will expire in {ssl_info['days_remaining']} days.",
                severity="medium",
                url=self.target_url,
                remediation="Plan to renew the SSL certificate soon.",
                confidence=1.0
            )
        
        # Check for weak protocols
        if ssl_info.get('protocol') in ['SSLv2', 'SSLv3', 'TLSv1', 'TLSv1.1']:
            Vulnerability.objects.create(
                scan=self.scan,
                name="Weak SSL/TLS Protocol",
                description=f"The server is using {ssl_info['protocol']}, which is considered insecure.",
                severity="high",
                url=self.target_url,
                remediation="Configure the server to use TLSv1.2 or TLSv1.3 only.",
                confidence=0.9
            )
        
        # Check missing security headers
        security_headers = self.results['server_info'].get('security_headers', {})
        for header, value in security_headers.items():
            if value == 'Not set':
                severity = "medium" if header == 'Strict-Transport-Security' else "low"
                Vulnerability.objects.create(
                    scan=self.scan,
                    name=f"Missing {header} Header",
                    description=f"The {header} security header is not set. This can lead to various security issues depending on the header.",
                    severity=severity,
                    url=self.target_url,
                    remediation=f"Add the {header} header to your server responses to improve security.",
                    confidence=1.0
                )
        
        # Check for HTTP instead of HTTPS
        if self.scheme == 'http':
            Vulnerability.objects.create(
                scan=self.scan,
                name="Site Not Using HTTPS",
                description="The website is not using HTTPS encryption. This means that all data transmitted between users and the site is unencrypted and vulnerable to interception.",
                severity="high",
                url=self.target_url,
                remediation="Implement HTTPS by obtaining an SSL certificate and configuring your server to use it.",
                confidence=1.0
            )
        
        # Check forms for security issues
        for form in self.results.get('forms_discovered', []):
            # Check for CSRF protection
            if form.get('method', '').upper() == 'POST':
                has_csrf = False
                for input_field in form.get('inputs', []):
                    if any(token in input_field.get('name', '').lower() for token in ['csrf', 'token', '_token']):
                        has_csrf = True
                        break
                
                if not has_csrf:
                    Vulnerability.objects.create(
                        scan=self.scan,
                        name="Form without CSRF Protection",
                        description="A form was found without CSRF protection. This could allow attackers to perform actions on behalf of authenticated users.",
                        severity="medium",
                        url=form.get('url'),
                        evidence=f"Form action: {form.get('action')}",
                        remediation="Implement CSRF protection for all forms by adding anti-CSRF tokens.",
                        confidence=0.8
                    )
            
            # Check for password fields with autocomplete enabled
            for input_field in form.get('inputs', []):
                if input_field.get('type') == 'password' and 'autocomplete="off"' not in str(input_field):
                    Vulnerability.objects.create(
                        scan=self.scan,
                        name="Password Field with Autocomplete Enabled",
                        description="A password field with autocomplete enabled was found. This could allow saved passwords to be stolen from shared computers.",
                        severity="low",
                        url=form.get('url'),
                        remediation="Add autocomplete='off' to password fields or autocomplete='new-password' for new password fields.",
                        confidence=0.7
                    )
        
        # Check cookies for security issues
        for name, value in self.results.get('cookies', {}).items():
            if any(keyword in name.lower() for keyword in ['session', 'auth', 'token', 'id', 'user']):
                # Check for sensitive cookies without secure flag (approximation)
                Vulnerability.objects.create(
                    scan=self.scan,
                    name="Sensitive Cookie without Secure Flag",
                    description="A sensitive cookie was found without the Secure flag set. This could allow the cookie to be transmitted over unencrypted connections.",
                    severity="medium",
                    url=self.target_url,
                    parameter=name,
                    remediation="Set the Secure flag on all cookies containing sensitive information.",
                    confidence=0.8
                )
                
                # Check for sensitive cookies without HttpOnly flag (approximation)
                Vulnerability.objects.create(
                    scan=self.scan,
                    name="Sensitive Cookie without HttpOnly Flag",
                    description="A sensitive cookie was found without the HttpOnly flag set. This allows JavaScript to access the cookie.",
                    severity="medium",
                    url=self.target_url,
                    parameter=name,
                    remediation="Set the HttpOnly flag on all cookies containing sensitive information.",
                    confidence=0.8
                )