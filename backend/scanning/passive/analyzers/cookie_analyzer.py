"""
Cookie security analyzer for passive scanning
"""
import logging
import re
from http.cookies import SimpleCookie
from urllib.parse import urlparse

import requests
from scanning.models.vulnerability import Vulnerability

logger = logging.getLogger(__name__)

def analyze_cookies(scan, cookies, headers=None):
    """
    Analyze cookies for security issues.
    
    Args:
        scan (Scan): Scan object
        cookies (dict): Cookies discovered during scanning
        headers (dict, optional): HTTP response headers
    """
    # Convert cookies to a dictionary if they are in a different format
    if not isinstance(cookies, dict):
        try:
            cookies_dict = {}
            if isinstance(cookies, str):
                # Parse from Cookie header
                cookie = SimpleCookie()
                cookie.load(cookies)
                for key, morsel in cookie.items():
                    cookies_dict[key] = morsel.value
            elif hasattr(cookies, 'items'):
                # Convert from requests.cookies
                cookies_dict = {name: value for name, value in cookies.items()}
            else:
                logger.error("Unsupported cookie format")
                return
            cookies = cookies_dict
        except Exception as e:
            logger.error(f"Error parsing cookies: {str(e)}")
            return
    
    # Lists to track security issues
    insecure_cookies = []
    httponly_missing = []
    samesite_missing = []
    sensitive_cookies = []
    
    # Get Set-Cookie headers if provided
    cookie_headers = []
    if headers:
        for key, value in headers.items():
            if key.lower() == 'set-cookie':
                cookie_headers.append(value)
    
    # Analyze cookies
    for name, value in cookies.items():
        # Check for sensitive cookie names
        sensitive_keywords = ['sess', 'auth', 'token', 'id', 'jwt', 'key', 'secret', 'pass', 'login']
        is_sensitive = any(keyword in name.lower() for keyword in sensitive_keywords)
        
        if is_sensitive:
            sensitive_cookies.append(name)
            
            # Try to find this cookie in Set-Cookie headers to check for security flags
            secure_flag = False
            httponly_flag = False
            samesite_flag = False
            
            for header in cookie_headers:
                if name in header:
                    secure_flag = 'secure' in header.lower()
                    httponly_flag = 'httponly' in header.lower()
                    samesite_flag = 'samesite' in header.lower()
                    break
            
            # Check for missing Secure flag
            if not secure_flag:
                insecure_cookies.append(name)
            
            # Check for missing HttpOnly flag
            if not httponly_flag:
                httponly_missing.append(name)
            
            # Check for missing SameSite attribute
            if not samesite_flag:
                samesite_missing.append(name)
        
    # Create vulnerability records
    create_cookie_vulnerability_reports(scan, insecure_cookies, httponly_missing, samesite_missing, sensitive_cookies)

def create_cookie_vulnerability_reports(scan, insecure_cookies, httponly_missing, samesite_missing, sensitive_cookies):
    """
    Create vulnerability records for cookie issues
    
    Args:
        scan (Scan): Scan object
        insecure_cookies (list): Cookies without Secure flag
        httponly_missing (list): Cookies without HttpOnly flag
        samesite_missing (list): Cookies without SameSite attribute
        sensitive_cookies (list): Sensitive cookies
    """
    # Report cookies without Secure flag
    if insecure_cookies:
        Vulnerability.objects.create(
            scan=scan,
            name="Cookies Without Secure Flag",
            description=f"Found {len(insecure_cookies)} cookies that don't have the Secure flag set. These cookies may be transmitted over unencrypted connections, allowing attackers to intercept sensitive data.",
            severity="medium",
            evidence=f"Affected cookies: {', '.join(insecure_cookies[:5])}",
            remediation="Set the Secure flag on all cookies containing sensitive information to ensure they are only transmitted over HTTPS.",
            confidence=0.8
        )
        logger.info(f"Found {len(insecure_cookies)} cookies without Secure flag")
    
    # Report cookies without HttpOnly flag
    if httponly_missing:
        Vulnerability.objects.create(
            scan=scan,
            name="Cookies Without HttpOnly Flag",
            description=f"Found {len(httponly_missing)} cookies that don't have the HttpOnly flag set. These cookies can be accessed by client-side scripts, making them vulnerable to cross-site scripting (XSS) attacks.",
            severity="medium",
            evidence=f"Affected cookies: {', '.join(httponly_missing[:5])}",
            remediation="Set the HttpOnly flag on all cookies containing sensitive information to prevent access from client-side scripts.",
            confidence=0.8
        )
        logger.info(f"Found {len(httponly_missing)} cookies without HttpOnly flag")
    
    # Report cookies without SameSite attribute
    if samesite_missing:
        Vulnerability.objects.create(
            scan=scan,
            name="Cookies Without SameSite Attribute",
            description=f"Found {len(samesite_missing)} cookies that don't have the SameSite attribute set. These cookies may be vulnerable to cross-site request forgery (CSRF) attacks.",
            severity="low",
            evidence=f"Affected cookies: {', '.join(samesite_missing[:5])}",
            remediation="Set the SameSite attribute (Strict or Lax) on cookies to prevent them from being sent in cross-site requests.",
            confidence=0.7
        )
        logger.info(f"Found {len(samesite_missing)} cookies without SameSite attribute")
    
    # Report on session cookies
    session_cookies = [cookie for cookie in sensitive_cookies if 'sess' in cookie.lower()]
    if session_cookies:
        # Check if any of the session cookies are also in the insecure or httponly_missing lists
        session_insecure = [cookie for cookie in session_cookies if cookie in insecure_cookies]
        session_not_httponly = [cookie for cookie in session_cookies if cookie in httponly_missing]
        
        if session_insecure or session_not_httponly:
            Vulnerability.objects.create(
                scan=scan,
                name="Insecure Session Cookies",
                description="Session cookies do not have proper security flags. This can lead to session hijacking attacks.",
                severity="high",
                evidence=f"Session cookies without proper protection: {', '.join(set(session_insecure + session_not_httponly)[:5])}",
                remediation="Ensure all session cookies have both Secure and HttpOnly flags set.",
                confidence=0.9
            )
            logger.info(f"Found insecure session cookies: {', '.join(set(session_insecure + session_not_httponly))}")

def _analyze_cookies(self):
    """
    Analyze cookies for security issues
    """
    logger.info(f"Analyzing cookies for {self.target_url}")
    
    try:
        # Get cookies from previous response or make a new request
        if hasattr(self, 'response') and self.response:
            cookies = dict(self.response.cookies)
        else:
            response = requests.get(self.target_url, headers=self.headers, timeout=10)
            cookies = dict(response.cookies)
        
        # Store cookies in results
        self.results['cookies'] = {k: str(v) for k, v in cookies.items()}
        
        # Use cookie analyzer
        from scanning.passive.analyzers.cookie_analyzer import analyze_cookies
        if self.response:
            analyze_cookies(self.scan, cookies, dict(self.response.headers))
        else:
            analyze_cookies(self.scan, cookies)
        
        # Try to use ZAP if available for more comprehensive cookie analysis
        if self.available_tools.get('zap', {}).get('available', False):
            try:
                from scanning.integrations.zap_adapter import ZAPAdapter
                adapter = ZAPAdapter(config={
                    'zap_host': self.available_tools['zap']['host'],
                    'zap_port': self.available_tools['zap']['port'],
                    'zap_api_key': self.config.zap_config.get('api_key', '') if hasattr(self.config, 'zap_config') else ''
                })
                
                cookie_findings = adapter.check_cookies(self.target_url)
                if cookie_findings:
                    logger.info(f"ZAP found {len(cookie_findings)} cookie-related issues")
                    for finding in cookie_findings:
                        finding['source'] = 'zap'
                        self._add_finding(finding)
            except Exception as zap_err:
                logger.warning(f"Error using ZAP for cookie analysis: {str(zap_err)}")
        
        # Update progress
        self.update_progress(65, "Cookie analysis completed")
        
    except Exception as e:
        logger.error(f"Error in cookie analysis: {str(e)}")
        self._add_error_finding("Cookie Analysis Error", str(e))
        self.update_progress(65, "Cookie analysis failed")

def analyze_cookie_patterns(scan, cookies):
    """
    Analyze cookie patterns for potential issues
    
    Args:
        scan (Scan): Scan object
        cookies (dict): Cookies to analyze
    """
    # Check for predictable session IDs
    sequential_patterns = check_sequential_patterns(cookies)
    if sequential_patterns:
        Vulnerability.objects.create(
            scan=scan,
            name="Predictable Session IDs",
            description="Session IDs appear to follow a predictable pattern, which could potentially be exploited to hijack sessions.",
            severity="medium",
            evidence=f"The following cookies have predictable patterns: {', '.join(sequential_patterns)}",
            remediation="Ensure session IDs are generated using a secure random number generator.",
            confidence=0.7
        )
    
    # Check for weak cookie encryption/encoding
    weak_encoding = check_weak_encoding(cookies)
    if weak_encoding:
        Vulnerability.objects.create(
            scan=scan,
            name="Weakly Encoded Cookie Values",
            description="Some cookies appear to use weak encoding or encryption methods, which may be easily decoded or predicted.",
            severity="medium",
            evidence=f"The following cookies have potentially weak encoding: {', '.join(weak_encoding)}",
            remediation="Use strong encryption methods for sensitive cookie data and avoid easily decodable formats like Base64.",
            confidence=0.6
        )

def check_sequential_patterns(cookies):
    """
    Check for sequential patterns in cookie values (which might indicate predictable session IDs)
    
    Args:
        cookies (dict): Cookies to analyze
        
    Returns:
        list: Cookies with potentially predictable patterns
    """
    suspicious_cookies = []
    for name, value in cookies.items():
        if 'sess' in name.lower() or 'id' in name.lower():
            # Check if value is a number or contains only hex digits
            if value.isdigit() and len(value) < 10:  # Short numeric values are suspicious
                suspicious_cookies.append(name)
            # Check for incremental patterns in hex values
            elif all(c in '0123456789abcdefABCDEF' for c in value) and len(value) <= 16:
                suspicious_cookies.append(name)
    
    return suspicious_cookies

def check_weak_encoding(cookies):
    """
    Check for weakly encoded cookie values
    
    Args:
        cookies (dict): Cookies to analyze
        
    Returns:
        list: Cookies with potentially weak encoding
    """
    weak_encoding = []
    for name, value in cookies.items():
        # Check for Base64-encoded values
        if len(value) % 4 == 0 and re.match(r'^[A-Za-z0-9+/]+={0,2}$', value):
            weak_encoding.append(name)
        
        # Check for URL-encoded values that might be too simple
        if '%' in value and len(re.findall(r'%[0-9A-Fa-f]{2}', value)) > 2:
            weak_encoding.append(name)
    
    return weak_encoding