"""
Passive Security Scanner

Performs comprehensive passive reconnaissance without active testing.
Uses tool priority system: external tools → custom analyzers.
"""

import logging
from urllib.parse import urlparse
from typing import Dict
import time

logger = logging.getLogger(__name__)


class PassiveScanner:
    """
    Passive security scanner for single URL analysis
    No crawling, no active testing, only passive reconnaissance
    """

    def __init__(self, scan_id: int, target_url: str, configuration):
        self.scan_id = scan_id
        self.target_url = target_url
        self.config = configuration
        self.domain = urlparse(target_url).netloc
        self.progress_callback = None

        # Results storage
        self.results = {
            "target_info": {},
            "dns_analysis": {},
            "ssl_analysis": {},
            "technology_detection": {},
            "security_headers": {},
            "content_analysis": {},
            "cookie_analysis": {},
            "enhanced_discovery": {},
            "vulnerabilities": [],
        }

        # Tool availability
        self.available_tools = self._check_tool_availability()
    
    def set_progress_callback(self, callback):
        """Set progress callback function for real-time updates"""
        self.progress_callback = callback

    def run_scan(self) -> Dict:
        """Run complete passive scan"""
        try:
            self._update_progress(5.0, "Starting passive reconnaissance")
            time.sleep(0.5)  # Small delay to make progress visible

            # Phase 1: Target Analysis
            self._update_progress(15.0, "Analyzing target URL")
            self._analyze_target()
            time.sleep(0.3)  # Small delay

            # Phase 2: DNS Analysis
            self._update_progress(25.0, "Performing DNS analysis")
            self._analyze_dns()
            time.sleep(0.5)  # Small delay

            # Phase 3: SSL/TLS Analysis
            self._update_progress(40.0, "Analyzing SSL/TLS configuration")
            self._analyze_ssl()
            time.sleep(0.4)  # Small delay

            # Phase 4: Technology Detection
            self._update_progress(55.0, "Detecting technologies")
            self._detect_technologies()
            time.sleep(0.4)  # Small delay

            # Phase 5: Security Headers
            self._update_progress(70.0, "Analyzing security headers")
            self._analyze_headers()
            time.sleep(0.3)  # Small delay

            # Phase 6: Content Analysis
            self._update_progress(85.0, "Analyzing content for information disclosure")
            self._analyze_content()
            time.sleep(0.4)  # Small delay

            # Phase 7: Cookie Analysis
            self._update_progress(95.0, "Analyzing cookies")
            self._analyze_cookies()
            time.sleep(0.3)  # Small delay

            # Phase 8: Enhanced Discovery
            self._update_progress(98.0, "Running enhanced discovery")
            self._run_enhanced_discovery()
            time.sleep(0.2)  # Small delay

            # Phase 9: Aggregate vulnerabilities
            self._update_progress(99.0, "Aggregating security findings")
            self._aggregate_vulnerabilities()
            time.sleep(0.2)  # Small delay

            self._update_progress(100.0, "Passive scan completed")

            return self.results

        except Exception as e:
            logger.exception(f"Passive scan failed: {e}")
            raise
    
    def _aggregate_vulnerabilities(self):
        """Aggregate all vulnerabilities found during scanning"""
        try:
            all_vulnerabilities = []
            
            # Collect vulnerabilities from SSL analysis
            if "ssl_analysis" in self.results and "vulnerabilities" in self.results["ssl_analysis"]:
                for vuln in self.results["ssl_analysis"]["vulnerabilities"]:
                    vuln["source"] = "SSL/TLS Analysis"
                    vuln["category"] = "Transport Security"
                    all_vulnerabilities.append(vuln)
            
            # Collect vulnerabilities from security headers
            if "security_headers" in self.results and "recommendations" in self.results["security_headers"]:
                for rec in self.results["security_headers"]["recommendations"]:
                    if "header" in rec.lower():
                        all_vulnerabilities.append({
                            "type": "missing_security_header",
                            "severity": "medium",
                            "description": rec,
                            "source": "Security Headers Analysis",
                            "category": "Security Headers"
                        })
            
            # Collect vulnerabilities from content analysis
            if "content_analysis" in self.results and "information_disclosure" in self.results["content_analysis"]:
                for info in self.results["content_analysis"]["information_disclosure"]:
                    all_vulnerabilities.append({
                        "type": "information_disclosure",
                        "severity": "low",
                        "description": f"{info['type']}: {info['count']} instances found",
                        "source": "Content Analysis",
                        "category": "Information Disclosure",
                        "details": info
                    })
            
            # Collect vulnerabilities from cookie analysis
            if "cookie_analysis" in self.results and "security_issues" in self.results["cookie_analysis"]:
                for issue in self.results["cookie_analysis"]["security_issues"]:
                    issue["source"] = "Cookie Analysis"
                    issue["category"] = "Cookie Security"
                    all_vulnerabilities.append(issue)
            
            # Update the main results
            self.results["vulnerabilities"] = all_vulnerabilities
            
            # Add summary statistics
            severity_counts = {"high": 0, "medium": 0, "low": 0}
            category_counts = {}
            
            for vuln in all_vulnerabilities:
                severity = vuln.get("severity", "low")
                category = vuln.get("category", "Unknown")
                
                if severity in severity_counts:
                    severity_counts[severity] += 1
                
                if category not in category_counts:
                    category_counts[category] = 0
                category_counts[category] += 1
            
            self.results["vulnerability_summary"] = {
                "total_count": len(all_vulnerabilities),
                "severity_distribution": severity_counts,
                "category_distribution": category_counts,
                "risk_score": self._calculate_risk_score(severity_counts)
            }
            
            logger.info(f"Vulnerability aggregation completed: {len(all_vulnerabilities)} findings")
            
        except Exception as e:
            logger.error(f"Error in vulnerability aggregation: {e}")
            self.results["vulnerabilities"] = []
            self.results["vulnerability_summary"] = {"error": str(e)}
    
    def _calculate_risk_score(self, severity_counts):
        """Calculate overall risk score based on vulnerability severity"""
        try:
            # Weighted scoring: High=10, Medium=5, Low=1
            score = (severity_counts.get("high", 0) * 10 + 
                    severity_counts.get("medium", 0) * 5 + 
                    severity_counts.get("low", 0) * 1)
            
            # Normalize to 0-100 scale
            if score == 0:
                return 0
            elif score <= 10:
                return score * 5  # 0-50
            elif score <= 30:
                return 50 + (score - 10) * 2.5  # 50-100
            else:
                return 100
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 0

    def _analyze_target(self):
        """Analyze target URL basic information"""
        try:
            from urllib.parse import urlparse
            
            parsed_url = urlparse(self.target_url)
            
            self.results["target_info"] = {
                "url": self.target_url,
                "protocol": parsed_url.scheme,
                "domain": parsed_url.netloc,
                "path": parsed_url.path,
                "query": parsed_url.query,
                "fragment": parsed_url.fragment,
                "port": parsed_url.port or (443 if parsed_url.scheme == 'https' else 80),
                "is_https": parsed_url.scheme == 'https',
                "is_http": parsed_url.scheme == 'http',
                "has_path": bool(parsed_url.path and parsed_url.path != '/'),
                "has_query": bool(parsed_url.query),
                "has_fragment": bool(parsed_url.fragment)
            }
            
            logger.info(f"Target analysis completed for {self.target_url}")
            
        except Exception as e:
            logger.error(f"Error in target analysis: {e}")
            self.results["target_info"] = {"error": str(e)}

    def _analyze_dns(self):
        """DNS information gathering"""
        try:
            import socket
            import dns.resolver
            import dns.reversename
            
            domain = self.domain
            dns_results = {
                "domain": domain,
                "a_records": [],
                "aaaa_records": [],
                "mx_records": [],
                "ns_records": [],
                "txt_records": [],
                "cname_records": [],
                "ptr_records": [],
                "soa_record": None,
                "resolved_ips": [],
                "reverse_dns": {}
            }
            
            # Resolve A records (IPv4)
            try:
                a_records = dns.resolver.resolve(domain, 'A')
                dns_results["a_records"] = [str(record) for record in a_records]
                dns_results["resolved_ips"].extend(dns_results["a_records"])
            except Exception as e:
                logger.debug(f"No A records found: {e}")
            
            # Resolve AAAA records (IPv6)
            try:
                aaaa_records = dns.resolver.resolve(domain, 'AAAA')
                dns_results["aaaa_records"] = [str(record) for record in aaaa_records]
                dns_results["resolved_ips"].extend(dns_results["aaaa_records"])
            except Exception as e:
                logger.debug(f"No AAAA records found: {e}")
            
            # Resolve MX records
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                dns_results["mx_records"] = [{"priority": record.preference, "host": str(record.exchange)} for record in mx_records]
            except Exception as e:
                logger.debug(f"No MX records found: {e}")
            
            # Resolve NS records
            try:
                ns_records = dns.resolver.resolve(domain, 'NS')
                dns_results["ns_records"] = [str(record) for record in ns_records]
            except Exception as e:
                logger.debug(f"No NS records found: {e}")
            
            # Resolve TXT records
            try:
                txt_records = dns.resolver.resolve(domain, 'TXT')
                dns_results["txt_records"] = [str(record) for record in txt_records]
            except Exception as e:
                logger.debug(f"No TXT records found: {e}")
            
            # Resolve SOA record
            try:
                soa_records = dns.resolver.resolve(domain, 'SOA')
                if soa_records:
                    soa = soa_records[0]
                    dns_results["soa_record"] = {
                        "mname": str(soa.mname),
                        "rname": str(soa.rname),
                        "serial": soa.serial,
                        "refresh": soa.refresh,
                        "retry": soa.retry,
                        "expire": soa.expire,
                        "minimum": soa.minimum
                    }
            except Exception as e:
                logger.debug(f"No SOA record found: {e}")
            
            # Reverse DNS lookup for resolved IPs
            for ip in dns_results["resolved_ips"]:
                try:
                    reverse_name = dns.reversename.from_address(ip)
                    reverse_records = dns.resolver.resolve(reverse_name, 'PTR')
                    dns_results["reverse_dns"][ip] = [str(record) for record in reverse_records]
                except Exception as e:
                    dns_results["reverse_dns"][ip] = None
            
            self.results["dns_analysis"] = dns_results
            logger.info(f"DNS analysis completed for {domain}")
            
        except ImportError:
            logger.warning("dnspython not available, using basic socket resolution")
            self._analyze_dns_basic()
        except Exception as e:
            logger.error(f"Error in DNS analysis: {e}")
            self.results["dns_analysis"] = {"error": str(e)}
    
    def _analyze_dns_basic(self):
        """Basic DNS analysis using socket when dnspython is not available"""
        try:
            domain = self.domain
            dns_results = {
                "domain": domain,
                "resolved_ips": [],
                "error": "Basic resolution only (dnspython not available)"
            }
            
            # Basic IP resolution
            try:
                ip = socket.gethostbyname(domain)
                dns_results["resolved_ips"].append(ip)
            except Exception as e:
                logger.debug(f"Could not resolve {domain}: {e}")
            
            self.results["dns_analysis"] = dns_results
            
        except Exception as e:
            logger.error(f"Error in basic DNS analysis: {e}")
            self.results["dns_analysis"] = {"error": str(e)}

    def _analyze_ssl(self):
        """SSL/TLS certificate analysis"""
        try:
            import socket
            import ssl
            from datetime import datetime
            
            if not self.results["target_info"].get("is_https"):
                self.results["ssl_analysis"] = {"error": "Target is not HTTPS"}
                return
            
            domain = self.domain
            port = self.results["target_info"].get("port", 443)
            
            ssl_results = {
                "domain": domain,
                "port": port,
                "certificate": {},
                "cipher_suite": {},
                "security_headers": {},
                "protocols": [],
                "vulnerabilities": []
            }
            
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            try:
                with socket.create_connection((domain, port), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        # Get certificate
                        cert = ssock.getpeercert()
                        if cert:
                            ssl_results["certificate"] = {
                                "subject": dict(x[0] for x in cert['subject']),
                                "issuer": dict(x[0] for x in cert['issuer']),
                                "version": cert.get('version'),
                                "serial_number": cert.get('serialNumber'),
                                "not_before": cert.get('notBefore'),
                                "not_after": cert.get('notAfter'),
                                "san": cert.get('subjectAltName', []),
                                "key_size": cert.get('keySize'),
                                "signature_algorithm": cert.get('signatureAlgorithm', ''),
                                "ocsp": cert.get('OCSP', []),
                                "ca_issuers": cert.get('caIssuers', [])
                            }
                        
                        # Get cipher info
                        cipher = ssock.cipher()
                        if cipher:
                            ssl_results["cipher_suite"] = {
                                "name": cipher[0],
                                "version": cipher[1],
                                "bits": cipher[2]
                            }
                        
                        # Get protocol version
                        protocol = ssock.version()
                        ssl_results["protocols"].append(protocol)
                        
                        # Check for weak protocols
                        if protocol in ['SSLv2', 'SSLv3', 'TLSv1.0', 'TLSv1.1']:
                            ssl_results["vulnerabilities"].append({
                                "type": "weak_protocol",
                                "severity": "high",
                                "description": f"Server supports weak protocol: {protocol}",
                                "recommendation": "Disable support for this protocol version"
                            })
                        
                        # Check for weak ciphers
                        weak_ciphers = ['NULL', 'EXPORT', 'LOW', 'MEDIUM', 'RC4', 'DES', '3DES']
                        if any(weak in cipher[0].upper() for weak in weak_ciphers):
                            ssl_results["vulnerabilities"].append({
                                "type": "weak_cipher",
                                "severity": "medium",
                                "description": f"Server uses weak cipher: {cipher[0]}",
                                "recommendation": "Use strong ciphers only (AES, ChaCha20)"
                            })
                        
                        # Certificate validation checks
                        if cert:
                            # Check expiration
                            try:
                                not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                                days_until_expiry = (not_after - datetime.now()).days
                                
                                if days_until_expiry < 0:
                                    ssl_results["vulnerabilities"].append({
                                        "type": "expired_certificate",
                                        "severity": "high",
                                        "description": "SSL certificate has expired",
                                        "recommendation": "Renew the SSL certificate immediately"
                                    })
                                elif days_until_expiry < 30:
                                    ssl_results["vulnerabilities"].append({
                                        "type": "expiring_certificate",
                                        "severity": "medium",
                                        "description": f"SSL certificate expires in {days_until_expiry} days",
                                        "recommendation": "Renew the SSL certificate soon"
                                    })
                            except Exception as e:
                                logger.debug(f"Could not parse certificate dates: {e}")
                            
                            # Check for self-signed certificates
                            if cert.get('issuer') == cert.get('subject'):
                                ssl_results["vulnerabilities"].append({
                                    "type": "self_signed_certificate",
                                    "severity": "medium",
                                    "description": "SSL certificate is self-signed",
                                    "recommendation": "Use a certificate from a trusted CA"
                                })
            
            except Exception as e:
                logger.error(f"SSL connection failed: {e}")
                ssl_results["error"] = str(e)
            
            self.results["ssl_analysis"] = ssl_results
            logger.info(f"SSL analysis completed for {domain}")
            
        except Exception as e:
            logger.error(f"Error in SSL analysis: {e}")
            self.results["ssl_analysis"] = {"error": str(e)}

    def _detect_technologies(self):
        """Technology stack detection"""
        try:
            import requests
            import re
            
            domain = self.domain
            target_url = self.target_url if self.target_url.startswith('http') else f'https://{domain}'
            
            tech_results = {
                "url": target_url,
                "technologies": [],
                "frameworks": [],
                "cms": [],
                "servers": [],
                "languages": [],
                "databases": [],
                "cloud_services": [],
                "analytics": [],
                "cdn": [],
                "security_tools": []
            }
            
            try:
                # Get configuration values safely
                user_agent = getattr(self.config, 'user_agent', None) or 'SecurityScanner/1.0'
                timeout = getattr(self.config, 'request_timeout', None) or 30
                
                # Try to use Wappalyzer if configured and available
                wappalyzer_used = False
                if hasattr(self.config, 'use_wappalyzer') and self.config.use_wappalyzer:
                    if self.available_tools.get("wappalyzer", False):
                        try:
                            from scanning.integrations.wappalyzer_adapter import WappalyzerAdapter
                            
                            # Create Wappalyzer adapter
                            wappalyzer_config = {}
                            if hasattr(self.config, 'wappalyzer_config'):
                                wappalyzer_config = self.config.wappalyzer_config
                            
                            adapter = WappalyzerAdapter(config=wappalyzer_config)
                            wappalyzer_results = adapter.detect_technologies(target_url)
                            
                            # Merge Wappalyzer results
                            if wappalyzer_results:
                                logger.info(f"Wappalyzer detected technologies: {wappalyzer_results}")
                                
                                # Map Wappalyzer results to our format
                                if wappalyzer_results.get("server") and wappalyzer_results["server"] != "Unknown":
                                    tech_results["servers"].append(wappalyzer_results["server"])
                                
                                if wappalyzer_results.get("frameworks"):
                                    tech_results["frameworks"].extend(wappalyzer_results["frameworks"])
                                
                                if wappalyzer_results.get("cms"):
                                    tech_results["cms"].append(wappalyzer_results["cms"])
                                
                                if wappalyzer_results.get("javascript_libraries"):
                                    tech_results["technologies"].extend(wappalyzer_results["javascript_libraries"])
                                
                                if wappalyzer_results.get("programming_languages"):
                                    tech_results["languages"].extend(wappalyzer_results["programming_languages"])
                                
                                if wappalyzer_results.get("analytics"):
                                    tech_results["analytics"].extend(wappalyzer_results["analytics"])
                                
                                if wappalyzer_results.get("cdn"):
                                    tech_results["cdn"].append(wappalyzer_results["cdn"])
                                
                                wappalyzer_used = True
                                logger.info("Wappalyzer technology detection completed successfully")
                            
                        except Exception as e:
                            logger.warning(f"Error using Wappalyzer: {str(e)}")
                
                # Make HTTP request
                response = requests.get(
                    target_url, 
                    headers={'User-Agent': user_agent},
                    timeout=timeout,
                    allow_redirects=True,
                    verify=False
                )
                
                html_content = response.text
                headers = response.headers
                
                # Server detection from headers
                if 'Server' in headers:
                    server = headers['Server']
                    tech_results["servers"].append(server)
                    
                    # Detect server type
                    if 'nginx' in server.lower():
                        tech_results["technologies"].append('Nginx')
                    elif 'apache' in server.lower():
                        tech_results["technologies"].append('Apache')
                    elif 'iis' in server.lower():
                        tech_results["technologies"].append('IIS')
                    elif 'cloudflare' in server.lower():
                        tech_results["technologies"].append('Cloudflare')
                
                # Technology detection patterns
                tech_patterns = {
                    # Frameworks
                    'React': [r'react', r'react-dom', r'__REACT_DEVTOOLS_GLOBAL_HOOK__'],
                    'Angular': [r'ng-', r'angular', r'angular\.js'],
                    'Vue.js': [r'vue', r'vue\.js', r'__VUE__'],
                    'jQuery': [r'jquery', r'jquery\.js', r'\$\('],
                    'Bootstrap': [r'bootstrap', r'bootstrap\.css', r'bootstrap\.js'],
                    'Tailwind': [r'tailwind', r'tailwind\.css'],
                    
                    # CMS
                    'WordPress': [r'wp-content', r'wp-includes', r'wordpress', r'/wp-admin/'],
                    'Drupal': [r'drupal', r'drupal\.js', r'/drupal/'],
                    'Joomla': [r'joomla', r'joomla\.js', r'/joomla/'],
                    'Magento': [r'magento', r'mage\.js'],
                    'Shopify': [r'shopify', r'shopify\.com'],
                    
                    # Backend
                    'PHP': [r'\.php', r'php_', r'X-Powered-By.*PHP'],
                    'ASP.NET': [r'\.aspx', r'\.asp', r'aspnet', r'X-AspNet'],
                    'Java': [r'\.jsp', r'\.java', r'servlet', r'jsessionid'],
                    'Python': [r'\.py', r'python', r'django', r'flask', r'wsgi'],
                    'Ruby': [r'\.rb', r'ruby', r'rails', r'rack'],
                    'Node.js': [r'node', r'express', r'next\.js'],
                    
                    # Databases
                    'MySQL': [r'mysql', r'mysqli'],
                    'PostgreSQL': [r'postgresql', r'postgres'],
                    'MongoDB': [r'mongodb', r'mongo'],
                    'Redis': [r'redis'],
                    
                    # Cloud Services
                    'AWS': [r'aws', r'amazonaws', r'cloudfront'],
                    'Azure': [r'azure', r'microsoft'],
                    'Google Cloud': [r'googleapis', r'gcp', r'google-cloud'],
                    'Cloudflare': [r'cloudflare', r'cf-ray'],
                    
                    # Analytics
                    'Google Analytics': [r'google-analytics', r'gtag', r'ga\('],
                    'Google Tag Manager': [r'googletagmanager', r'gtm'],
                    'Facebook Pixel': [r'facebook', r'fbq'],
                    'Hotjar': [r'hotjar'],
                    
                    # CDN
                    'Cloudflare': [r'cloudflare', r'cf-ray'],
                    'Akamai': [r'akamai'],
                    'Fastly': [r'fastly'],
                    'AWS CloudFront': [r'cloudfront'],
                    
                    # Security
                    'reCAPTCHA': [r'recaptcha', r'g-recaptcha'],
                    'hCaptcha': [r'hcaptcha'],
                    'Cloudflare Security': [r'cloudflare', r'cf-ray'],
                    'Imperva': [r'incapsula', r'imperva']
                }
                
                # Check each technology
                for tech_name, patterns in tech_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, html_content, re.IGNORECASE):
                            if tech_name not in tech_results["technologies"]:
                                tech_results["technologies"].append(tech_name)
                            
                            # Categorize
                            if tech_name in ['WordPress', 'Drupal', 'Joomla', 'Magento', 'Shopify']:
                                if tech_name not in tech_results["cms"]:
                                    tech_results["cms"].append(tech_name)
                            elif tech_name in ['React', 'Angular', 'Vue.js', 'jQuery', 'Bootstrap', 'Tailwind']:
                                if tech_name not in tech_results["frameworks"]:
                                    tech_results["frameworks"].append(tech_name)
                            elif tech_name in ['PHP', 'ASP.NET', 'Java', 'Python', 'Ruby', 'Node.js']:
                                if tech_name not in tech_results["languages"]:
                                    tech_results["languages"].append(tech_name)
                            elif tech_name in ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis']:
                                if tech_name not in tech_results["databases"]:
                                    tech_results["databases"].append(tech_name)
                            elif tech_name in ['AWS', 'Azure', 'Google Cloud']:
                                if tech_name not in tech_results["cloud_services"]:
                                    tech_results["cloud_services"].append(tech_name)
                            elif tech_name in ['Google Analytics', 'Google Tag Manager', 'Facebook Pixel', 'Hotjar']:
                                if tech_name not in tech_results["analytics"]:
                                    tech_results["analytics"].append(tech_name)
                            elif tech_name in ['Cloudflare', 'Akamai', 'Fastly', 'AWS CloudFront']:
                                if tech_name not in tech_results["cdn"]:
                                    tech_results["cdn"].append(tech_name)
                            elif tech_name in ['reCAPTCHA', 'hCaptcha', 'Cloudflare Security', 'Imperva']:
                                if tech_name not in tech_results["security_tools"]:
                                    tech_results["security_tools"].append(tech_name)
                            break
                
                # Check for common file extensions
                file_extensions = re.findall(r'["\']([^"\']*\.(?:js|css|php|asp|jsp|html|xml|json))["\']', html_content)
                if file_extensions:
                    tech_results["files"] = list(set(file_extensions))
                
            except Exception as e:
                logger.error(f"Technology detection failed: {e}")
                tech_results["error"] = str(e)
            
            self.results["technology_detection"] = tech_results
            logger.info(f"Technology detection completed for {target_url}")
            
        except Exception as e:
            logger.error(f"Error in technology detection: {e}")
            self.results["technology_detection"] = {"error": str(e)}
    
    def _analyze_headers(self):
        """Security headers analysis"""
        try:
            import requests
            from urllib.parse import urljoin
            
            domain = self.domain
            target_url = self.target_url if self.target_url.startswith('http') else f'https://{domain}'
            
            headers_results = {
                "url": target_url,
                "response_headers": {},
                "security_headers": {},
                "server_info": {},
                "missing_security_headers": [],
                "recommendations": []
            }
            
            # Security headers to check
            security_headers = {
                'Strict-Transport-Security': 'HSTS',
                'X-Content-Type-Options': 'Content Type Options',
                'X-Frame-Options': 'Frame Options',
                'X-XSS-Protection': 'XSS Protection',
                'Content-Security-Policy': 'CSP',
                'Referrer-Policy': 'Referrer Policy',
                'Permissions-Policy': 'Permissions Policy',
                'Cross-Origin-Embedder-Policy': 'COEP',
                'Cross-Origin-Opener-Policy': 'COOP',
                'Cross-Origin-Resource-Policy': 'CORP'
            }
            
            try:
                # Get configuration values safely
                user_agent = getattr(self.config, 'user_agent', None) or 'SecurityScanner/1.0'
                timeout = getattr(self.config, 'request_timeout', None) or 30
                
                # Make HTTP request
                response = requests.get(
                    target_url, 
                    headers={'User-Agent': user_agent},
                    timeout=timeout,
                    allow_redirects=True,
                    verify=False
                )
                
                # Store all response headers
                headers_results["response_headers"] = dict(response.headers)
                
                # Check security headers
                for header, description in security_headers.items():
                    if header in response.headers:
                        headers_results["security_headers"][header] = response.headers[header]
                    else:
                        headers_results["missing_security_headers"].append(header)
                        headers_results["recommendations"].append(f"Add {header} header for better security")
                
                # Server information
                if 'Server' in response.headers:
                    headers_results["server_info"]["server"] = response.headers['Server']
                
                if 'X-Powered-By' in response.headers:
                    headers_results["server_info"]["powered_by"] = response.headers['X-Powered-By']
                
                # Check for information disclosure
                sensitive_headers = ['X-Powered-By', 'Server', 'X-AspNet-Version', 'X-AspNetMvc-Version']
                for header in sensitive_headers:
                    if header in response.headers:
                        headers_results["recommendations"].append(f"Consider removing {header} header to prevent information disclosure")
                
                # Check HSTS configuration
                if 'Strict-Transport-Security' in response.headers:
                    hsts = response.headers['Strict-Transport-Security']
                    if 'max-age=0' in hsts:
                        headers_results["recommendations"].append("HSTS max-age is set to 0, which disables HSTS")
                    elif 'max-age=' in hsts:
                        try:
                            max_age = int(hsts.split('max-age=')[1].split(';')[0])
                            if max_age < 31536000:  # 1 year
                                headers_results["recommendations"].append(f"HSTS max-age ({max_age}) should be at least 1 year (31536000)")
                        except:
                            pass
                
                # Check CSP configuration
                if 'Content-Security-Policy' in response.headers:
                    csp = response.headers['Content-Security-Policy']
                    if 'unsafe-inline' in csp:
                        headers_results["recommendations"].append("CSP contains 'unsafe-inline' which reduces security")
                    if 'unsafe-eval' in csp:
                        headers_results["recommendations"].append("CSP contains 'unsafe-eval' which reduces security")
                
                # Try to use ZAP if configured and available
                if hasattr(self.config, 'use_zap_passive') and self.config.use_zap_passive:
                    if self.available_tools.get("zap", False):
                        try:
                            from scanning.integrations.zap_adapter import ZAPAdapter
                            
                            # Create ZAP adapter
                            zap_config = {}
                            if hasattr(self.config, 'zap_config'):
                                zap_config = self.config.zap_config
                            
                            adapter = ZAPAdapter(config=zap_config)
                            zap_header_findings = adapter.check_headers(target_url)
                            
                            if zap_header_findings:
                                logger.info(f"ZAP found {len(zap_header_findings)} header-related issues")
                                for finding in zap_header_findings:
                                    if finding.get("name") and finding.get("description"):
                                        headers_results["recommendations"].append(f"ZAP: {finding['name']} - {finding['description']}")
                            
                        except Exception as e:
                            logger.warning(f"Error using ZAP for header analysis: {str(e)}")
                
            except Exception as e:
                logger.error(f"HTTP request failed: {e}")
                headers_results["error"] = str(e)
            
            self.results["security_headers"] = headers_results
            logger.info(f"Headers analysis completed for {target_url}")
            
        except Exception as e:
            logger.error(f"Error in headers analysis: {e}")
            self.results["security_headers"] = {"error": str(e)}
    
    def _analyze_content(self):
        """Content analysis for information disclosure"""
        try:
            import requests
            from urllib.parse import urljoin
            import re
            
            domain = self.domain
            target_url = self.target_url if self.target_url.startswith('http') else f'https://{domain}'
            
            content_results = {
                "url": target_url,
                "content_type": "",
                "content_length": 0,
                "technologies_detected": [],
                "information_disclosure": [],
                "comments_found": [],
                "email_addresses": [],
                "phone_numbers": [],
                "internal_paths": [],
                "api_endpoints": [],
                "recommendations": []
            }
            
            try:
                # Get configuration values safely
                user_agent = getattr(self.config, 'user_agent', None) or 'SecurityScanner/1.0'
                timeout = getattr(self.config, 'request_timeout', None) or 30
                
                # Make HTTP request
                response = requests.get(
                    target_url, 
                    headers={'User-Agent': user_agent},
                    timeout=timeout,
                    allow_redirects=True,
                    verify=False
                )
                
                content_results["content_type"] = response.headers.get('Content-Type', '')
                content_results["content_length"] = len(response.content)
                
                # Parse HTML content
                if 'text/html' in content_results["content_type"]:
                    html_content = response.text
                    
                    # Look for HTML comments
                    html_comments = re.findall(r'<!--(.*?)-->', html_content, re.DOTALL)
                    content_results["comments_found"] = [comment.strip() for comment in html_comments if comment.strip()]
                    
                    # Look for email addresses
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    emails = re.findall(email_pattern, html_content)
                    content_results["email_addresses"] = list(set(emails))
                    
                    # Look for phone numbers
                    phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
                    phones = re.findall(phone_pattern, html_content)
                    content_results["phone_numbers"] = list(set(phones))
                    
                    # Look for internal paths
                    internal_paths = re.findall(r'["\'](/[^"\']*?\.(?:php|asp|jsp|html|js|css))["\']', html_content)
                    content_results["internal_paths"] = list(set(internal_paths))
                    
                    # Look for API endpoints
                    api_patterns = [
                        r'["\'](/api/[^"\']*)["\']',
                        r'["\'](/v\d+/[^"\']*)["\']',
                        r'["\'](/rest/[^"\']*)["\']',
                        r'["\'](/graphql[^"\']*)["\']'
                    ]
                    for pattern in api_patterns:
                        api_endpoints = re.findall(pattern, html_content)
                        content_results["api_endpoints"].extend(api_endpoints)
                    
                    # Check for information disclosure
                    sensitive_patterns = [
                        (r'error|exception|stack trace', 'Error messages or stack traces'),
                        (r'debug|debugging', 'Debug information'),
                        (r'admin|administrator', 'Admin references'),
                        (r'password|passwd|pwd', 'Password references'),
                        (r'database|db_|mysql|postgresql', 'Database references'),
                        (r'config|configuration', 'Configuration references'),
                        (r'version|ver\.|v\d+\.\d+', 'Version information')
                    ]
                    
                    for pattern, description in sensitive_patterns:
                        matches = re.findall(pattern, html_content, re.IGNORECASE)
                        if matches:
                            content_results["information_disclosure"].append({
                                "type": description,
                                "count": len(matches),
                                "examples": matches[:5]  # Limit to first 5 examples
                            })
                    
                    # Technology detection from HTML
                    tech_patterns = {
                        'WordPress': r'wp-content|wp-includes|wordpress',
                        'Drupal': r'drupal|drupal\.js',
                        'Joomla': r'joomla|joomla\.js',
                        'React': r'react|react-dom',
                        'Angular': r'ng-|angular',
                        'Vue.js': r'vue|vue\.js',
                        'jQuery': r'jquery|jquery\.js',
                        'Bootstrap': r'bootstrap|bootstrap\.css',
                        'PHP': r'\.php|php_',
                        'ASP.NET': r'\.aspx|\.asp|aspnet',
                        'Java': r'\.jsp|\.java|servlet',
                        'Python': r'\.py|python|django|flask'
                    }
                    
                    for tech, pattern in tech_patterns.items():
                        if re.search(pattern, html_content, re.IGNORECASE):
                            content_results["technologies_detected"].append(tech)
                    
                    # Recommendations
                    if content_results["comments_found"]:
                        content_results["recommendations"].append("Remove HTML comments that may contain sensitive information")
                    
                    if content_results["email_addresses"]:
                        content_results["recommendations"].append("Consider obfuscating email addresses to prevent scraping")
                    
                    if content_results["information_disclosure"]:
                        content_results["recommendations"].append("Review and remove sensitive information from HTML content")
                
            except Exception as e:
                logger.error(f"Content analysis failed: {e}")
                content_results["error"] = str(e)
            
            self.results["content_analysis"] = content_results
            logger.info(f"Content analysis completed for {target_url}")
            
        except Exception as e:
            logger.error(f"Error in content analysis: {e}")
            self.results["content_analysis"] = {"error": str(e)}

    def _analyze_cookies(self):
        """Cookie security analysis"""
        try:
            import requests
            
            domain = self.domain
            target_url = self.target_url if self.target_url.startswith('http') else f'https://{domain}'
            
            cookie_results = {
                "url": target_url,
                "cookies": [],
                "security_issues": [],
                "recommendations": []
            }
            
            try:
                # Get configuration values safely
                user_agent = getattr(self.config, 'user_agent', None) or 'SecurityScanner/1.0'
                timeout = getattr(self.config, 'request_timeout', None) or 30
                
                # Make HTTP request
                response = requests.get(
                    target_url, 
                    headers={'User-Agent': user_agent},
                    timeout=timeout,
                    allow_redirects=True,
                    verify=False
                )
                
                # Get cookies from response
                cookies = response.cookies
                
                for cookie in cookies:
                    cookie_info = {
                        "name": cookie.name,
                        "value": cookie.value[:50] + "..." if len(cookie.value) > 50 else cookie.value,
                        "domain": cookie.domain,
                        "path": cookie.path,
                        "expires": cookie.expires,
                        "secure": cookie.secure,
                        "http_only": cookie.has_nonstandard_attr('HttpOnly'),
                        "same_site": getattr(cookie, 'SameSite', None)
                    }
                    
                    cookie_results["cookies"].append(cookie_info)
                    
                    # Security analysis
                    if not cookie.secure and self.results["target_info"].get("is_https"):
                        cookie_results["security_issues"].append({
                            "cookie": cookie.name,
                            "issue": "Cookie not marked as secure",
                            "severity": "medium",
                            "recommendation": "Add Secure flag for HTTPS sites"
                        })
                    
                    if not cookie.has_nonstandard_attr('HttpOnly'):
                        cookie_results["security_issues"].append({
                            "cookie": cookie.name,
                            "issue": "Cookie not marked as HttpOnly",
                            "severity": "medium",
                            "recommendation": "Add HttpOnly flag to prevent XSS access"
                        })
                    
                    if getattr(cookie, 'SameSite', None) is None:
                        cookie_results["security_issues"].append({
                            "cookie": cookie.name,
                            "issue": "Cookie SameSite attribute not set",
                            "severity": "low",
                            "recommendation": "Set SameSite=Strict or SameSite=Lax"
                        })
                    
                    # Check for sensitive cookie names
                    sensitive_names = ['session', 'token', 'auth', 'login', 'password', 'secret', 'key']
                    if any(name in cookie.name.lower() for name in sensitive_names):
                        if not cookie.secure:
                            cookie_results["security_issues"].append({
                                "cookie": cookie.name,
                                "issue": "Sensitive cookie not secure",
                                "severity": "high",
                                "recommendation": "Mark sensitive cookies as Secure and HttpOnly"
                            })
                
                # General recommendations
                if not cookie_results["cookies"]:
                    cookie_results["recommendations"].append("No cookies found - consider if this is expected")
                else:
                    if any(not cookie["secure"] for cookie in cookie_results["cookies"]):
                        cookie_results["recommendations"].append("All cookies should be marked as Secure for HTTPS sites")
                    
                    if any(not cookie["http_only"] for cookie in cookie_results["cookies"]):
                        cookie_results["recommendations"].append("All cookies should be marked as HttpOnly to prevent XSS")
                    
                    if any(cookie["same_site"] is None for cookie in cookie_results["cookies"]):
                        cookie_results["recommendations"].append("All cookies should have SameSite attribute set")
                
            except Exception as e:
                logger.error(f"Cookie analysis failed: {e}")
                cookie_results["error"] = str(e)
            
            self.results["cookie_analysis"] = cookie_results
            logger.info(f"Cookie analysis completed for {target_url}")
            
        except Exception as e:
            logger.error(f"Error in cookie analysis: {e}")
            self.results["cookie_analysis"] = {"error": str(e)}

    def _run_enhanced_discovery(self):
        """Run enhanced discovery using external tools"""
        try:
            logger.info(f"Starting enhanced discovery for {self.target_url}")
            
            # Check if enhanced discovery is enabled
            if not getattr(self.config, 'use_enhanced_discovery', True):
                logger.info("Enhanced discovery disabled in configuration")
                self.results["enhanced_discovery"] = {"disabled": True}
                return
            
            # Import enhanced discovery adapter
            from scanning.integrations.enhanced_discovery_adapter import EnhancedDiscoveryAdapter
            
            # Create adapter with configuration from database
            discovery_config = {
                "timeout": getattr(self.config, 'discovery_timeout', 30),
                "max_subdomains": getattr(self.config, 'max_subdomains', 100),
                "max_wayback_urls": getattr(self.config, 'max_wayback_urls', 200),
                "max_directories": getattr(self.config, 'max_directories', 50),
                "user_agent": getattr(self.config, 'user_agent', 'SecurityScanner/1.0')
            }
            
            adapter = EnhancedDiscoveryAdapter(config=discovery_config)
            
            # Run comprehensive discovery
            discovery_results = adapter.run_comprehensive_discovery(self.target_url)
            
            # Store results
            self.results["enhanced_discovery"] = discovery_results
            
            # Extract URLs for integration with existing systems
            all_urls = []
            
            # Add subdomains as URLs
            if discovery_results.get("subdomains", {}).get("subdomains"):
                for subdomain in discovery_results["subdomains"]["subdomains"]:
                    if subdomain.startswith('http'):
                        all_urls.append(subdomain)
                    else:
                        # Determine protocol
                        protocol = 'https' if self.results["target_info"].get("is_https") else 'http'
                        all_urls.append(f"{protocol}://{subdomain}")
            
            # Add wayback URLs
            if discovery_results.get("wayback_urls", {}).get("urls"):
                all_urls.extend(discovery_results["wayback_urls"]["urls"])
            
            # Add discovered directories
            if discovery_results.get("directories", {}).get("directories"):
                for directory in discovery_results["directories"]["directories"]:
                    if isinstance(directory, dict) and directory.get("url"):
                        all_urls.append(directory["url"])
                    elif isinstance(directory, str):
                        all_urls.append(directory)
            
            # Add API endpoints
            if discovery_results.get("api_endpoints", {}).get("api_endpoints"):
                for endpoint in discovery_results["api_endpoints"]["api_endpoints"]:
                    if isinstance(endpoint, dict) and endpoint.get("url"):
                        all_urls.append(endpoint["url"])
                    elif isinstance(endpoint, str):
                        all_urls.append(endpoint)
            
            # Remove duplicates and store
            unique_urls = list(set(all_urls))
            self.results["enhanced_discovery"]["all_discovered_urls"] = unique_urls
            self.results["enhanced_discovery"]["total_urls_discovered"] = len(unique_urls)
            
            logger.info(f"Enhanced discovery completed: {len(unique_urls)} URLs discovered")
            logger.info(f"Enhanced discovery results stored: {bool(self.results.get('enhanced_discovery'))}")
            
        except ImportError:
            logger.warning("Enhanced discovery adapter not available")
            self.results["enhanced_discovery"] = {"error": "Enhanced discovery adapter not available"}
        except Exception as e:
            logger.error(f"Enhanced discovery failed: {e}")
            logger.error(f"Enhanced discovery error details: {str(e)}")
            import traceback
            logger.error(f"Enhanced discovery traceback: {traceback.format_exc()}")
            self.results["enhanced_discovery"] = {"error": str(e)}
    
    def _check_tool_availability(self) -> Dict:
        """Check external tool availability"""
        tools_status = {
            "sslyze": False,
            "nuclei": False,
            "wappalyzer": False,
            "zap": False,
            "subfinder": False,
            "waybackurls": False,
            "feroxbuster": False
        }
        
        try:
            # Check SSLyze
            try:
                import sslyze
                tools_status["sslyze"] = True
            except ImportError:
                logger.debug("SSLyze not available")
            
            # Check Nuclei
            try:
                import subprocess
                result = subprocess.run(['nuclei', '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    tools_status["nuclei"] = True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.debug("Nuclei not available")
            
            # Check Wappalyzer
            try:
                import subprocess
                result = subprocess.run(['wappalyzer', '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    tools_status["wappalyzer"] = True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.debug("Wappalyzer not available")
            
            # Check ZAP (Docker container via API)
            try:
                import requests
                zap_url = "http://localhost:8080"
                response = requests.get(f"{zap_url}/", timeout=5)
                if response.status_code == 200 and "ZAP" in response.text:
                    tools_status["zap"] = True
                    logger.debug("ZAP available via Docker container")
            except Exception:
                logger.debug("ZAP not available")
            
            # Check Subfinder
            try:
                result = subprocess.run(['subfinder', '-version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    tools_status["subfinder"] = True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.debug("Subfinder not available")
            
            # Check Waybackurls
            try:
                result = subprocess.run(['waybackurls', '-h'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    tools_status["waybackurls"] = True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.debug("Waybackurls not available")
            
            # Check Feroxbuster
            try:
                result = subprocess.run(['feroxbuster', '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    tools_status["feroxbuster"] = True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.debug("Feroxbuster not available")
            
        except Exception as e:
            logger.error(f"Error checking tool availability: {e}")
        
        return tools_status

    def _update_progress(self, percent: float, message: str) -> None:
        """Update progress and call callback if available"""
        logger.info(f"Scan {self.scan_id}: {percent}% - {message}")
        
        # Call progress callback if available
        if self.progress_callback:
            try:
                self.progress_callback(percent, message)
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")
    
    def update_progress(self, percent: float, message: str) -> None:
        """Update progress with protection against backward movement"""
        # This method is called by analyzer functions to prevent backward progress
        logger.info(f"Analyzer progress update: {percent}% - {message}")
        
        # For now, just delegate to _update_progress since analyzers use fixed percentages
        # If we need backward protection here too, we'd need to track current progress
        self._update_progress(percent, message)