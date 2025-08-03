"""
Security header analyzer for passive scanning
"""
import logging

import requests
from scanning.models.vulnerability import Vulnerability

logger = logging.getLogger(__name__)

def analyze_security_headers(scan, headers):
    """
    Check for missing or misconfigured security headers and create vulnerability records.
    
    Args:
        scan (Scan): Scan object
        headers (dict): HTTP response headers
    """
    # Normalize header names to case-insensitive dictionary
    normalized_headers = {k.lower(): v for k, v in headers.items()}
    
    # Check for required security headers
    check_hsts_header(scan, normalized_headers)
    check_content_security_policy(scan, normalized_headers)
    check_x_content_type_options(scan, normalized_headers)
    check_x_frame_options(scan, normalized_headers)
    check_x_xss_protection(scan, normalized_headers)
    check_referrer_policy(scan, normalized_headers)
    check_feature_policy(scan, normalized_headers)
    check_cors_headers(scan, normalized_headers)
    check_cache_control(scan, normalized_headers)
    
    # Check for information disclosure in headers
    check_header_information_disclosure(scan, headers)

def check_hsts_header(scan, headers):
    """
    Check for HTTP Strict Transport Security (HSTS) header
    
    Args:
        scan (Scan): Scan object
        headers (dict): Normalized HTTP response headers
    """
    hsts_header = headers.get('strict-transport-security')
    
    if not hsts_header:
        Vulnerability.objects.create(
            scan=scan,
            name="Missing HSTS Header",
            description="HTTP Strict Transport Security (HSTS) header is missing. This header helps protect websites against protocol downgrade attacks and cookie hijacking by telling browsers to only use HTTPS.",
            severity="medium",
            remediation="Add the Strict-Transport-Security header with appropriate values, e.g., 'max-age=31536000; includeSubDomains'",
            confidence=1.0
        )
        logger.info("Missing HSTS header detected")
        return
    
    # Check for proper max-age value (at least 6 months = 15768000 seconds)
    if 'max-age=' in hsts_header:
        try:
            max_age_part = [part.strip() for part in hsts_header.split(';') if 'max-age=' in part][0]
            max_age = int(max_age_part.split('=')[1])
            
            if max_age < 15768000:
                Vulnerability.objects.create(
                    scan=scan,
                    name="HSTS Max-Age Too Short",
                    description=f"The HSTS header's max-age is set to {max_age} seconds, which is less than the recommended 6 months (15768000 seconds).",
                    severity="low",
                    remediation="Increase the HSTS max-age to at least 6 months (15768000 seconds).",
                    confidence=0.9
                )
                logger.info(f"HSTS max-age too short: {max_age} seconds")
        except (IndexError, ValueError):
            Vulnerability.objects.create(
                scan=scan,
                name="Invalid HSTS Max-Age",
                description="The HSTS header contains an invalid max-age value.",
                severity="low",
                remediation="Ensure the max-age value is a valid integer representing seconds.",
                confidence=0.9
            )
    else:
        Vulnerability.objects.create(
            scan=scan,
            name="HSTS Missing Max-Age",
            description="The HSTS header is missing the required max-age directive.",
            severity="medium",
            remediation="Add a max-age directive to the HSTS header with a value of at least 15768000 (6 months).",
            confidence=0.9
        )
    
    # Check for includeSubDomains directive
    if 'includesubdomains' not in hsts_header.lower():
        Vulnerability.objects.create(
            scan=scan,
            name="HSTS Missing includeSubDomains",
            description="The HSTS header is missing the 'includeSubDomains' directive, which extends the policy to all subdomains.",
            severity="low",
            remediation="Add the 'includeSubDomains' directive to the HSTS header.",
            confidence=0.8
        )
        logger.info("HSTS missing includeSubDomains directive")

def check_content_security_policy(scan, headers):
    """
    Check for Content Security Policy (CSP) header
    
    Args:
        scan (Scan): Scan object
        headers (dict): Normalized HTTP response headers
    """
    csp_header = headers.get('content-security-policy')
    
    if not csp_header:
        Vulnerability.objects.create(
            scan=scan,
            name="Missing Content Security Policy",
            description="Content Security Policy (CSP) header is missing. This header helps prevent cross-site scripting (XSS) and data injection attacks by controlling which resources can be loaded.",
            severity="medium",
            remediation="Implement a Content Security Policy that restricts content sources to trusted domains.",
            confidence=0.9
        )
        logger.info("Missing Content Security Policy header detected")
        return
    
    # Check for unsafe CSP directives
    unsafe_directives = []
    
    if "unsafe-inline" in csp_header:
        unsafe_directives.append("unsafe-inline")
    
    if "unsafe-eval" in csp_header:
        unsafe_directives.append("unsafe-eval")
    
    if "*" in csp_header:
        unsafe_directives.append("wildcard (*)")
    
    if "data:" in csp_header:
        unsafe_directives.append("data: URI")
    
    if unsafe_directives:
        Vulnerability.objects.create(
            scan=scan,
            name="Weak Content Security Policy",
            description=f"The Content Security Policy contains potentially unsafe directives: {', '.join(unsafe_directives)}. These can weaken the protection provided by CSP.",
            severity="low",
            remediation="Remove unsafe directives like 'unsafe-inline', 'unsafe-eval', wildcards (*), and 'data:' URIs from your CSP. Use nonces or hashes instead.",
            confidence=0.8
        )
        logger.info(f"Weak CSP directives detected: {', '.join(unsafe_directives)}")

def check_x_content_type_options(scan, headers):
    """
    Check for X-Content-Type-Options header
    
    Args:
        scan (Scan): Scan object
        headers (dict): Normalized HTTP response headers
    """
    x_content_type = headers.get('x-content-type-options')
    
    if not x_content_type:
        Vulnerability.objects.create(
            scan=scan,
            name="Missing X-Content-Type-Options Header",
            description="X-Content-Type-Options header is missing. This header prevents browsers from MIME-sniffing a response away from the declared content-type, which can help prevent XSS attacks.",
            severity="low",
            remediation="Add the X-Content-Type-Options header with the value 'nosniff'.",
            confidence=1.0
        )
        logger.info("Missing X-Content-Type-Options header detected")
    elif x_content_type.lower() != 'nosniff':
        Vulnerability.objects.create(
            scan=scan,
            name="Incorrect X-Content-Type-Options Value",
            description="The X-Content-Type-Options header has an incorrect value. The only valid value is 'nosniff'.",
            severity="low",
            remediation="Set the X-Content-Type-Options header to 'nosniff'.",
            confidence=0.9
        )
        logger.info(f"Incorrect X-Content-Type-Options value: {x_content_type}")

def check_x_frame_options(scan, headers):
    """
    Check for X-Frame-Options header
    
    Args:
        scan (Scan): Scan object
        headers (dict): Normalized HTTP response headers
    """
    x_frame = headers.get('x-frame-options')
    
    if not x_frame:
        Vulnerability.objects.create(
            scan=scan,
            name="Missing X-Frame-Options Header",
            description="X-Frame-Options header is missing. This header can be used to prevent clickjacking attacks by ensuring the site cannot be embedded in a frame.",
            severity="low",
            remediation="Add the X-Frame-Options header with the value 'DENY' or 'SAMEORIGIN'.",
            confidence=1.0
        )
        logger.info("Missing X-Frame-Options header detected")
    elif x_frame.upper() not in ['DENY', 'SAMEORIGIN']:
        # Note: ALLOW-FROM is deprecated but might still be used
        if not x_frame.upper().startswith('ALLOW-FROM'):
            Vulnerability.objects.create(
                scan=scan,
                name="Incorrect X-Frame-Options Value",
                description=f"The X-Frame-Options header has an incorrect value: {x_frame}. Valid values are 'DENY' or 'SAMEORIGIN'.",
                severity="low",
                remediation="Set the X-Frame-Options header to 'DENY' or 'SAMEORIGIN'.",
                confidence=0.9
            )
            logger.info(f"Incorrect X-Frame-Options value: {x_frame}")
        else:
            Vulnerability.objects.create(
                scan=scan,
                name="Deprecated X-Frame-Options Value",
                description="The X-Frame-Options header uses the deprecated 'ALLOW-FROM' directive, which is not supported by all browsers.",
                severity="low",
                remediation="Use 'DENY' or 'SAMEORIGIN' instead of 'ALLOW-FROM'. For more specific control, use the frame-ancestors directive in Content Security Policy.",
                confidence=0.9
            )
            logger.info(f"Deprecated X-Frame-Options value: {x_frame}")

def check_x_xss_protection(scan, headers):
    """
    Check for X-XSS-Protection header
    
    Args:
        scan (Scan): Scan object
        headers (dict): Normalized HTTP response headers
    """
    x_xss = headers.get('x-xss-protection')
    
    if not x_xss:
        Vulnerability.objects.create(
            scan=scan,
            name="Missing X-XSS-Protection Header",
            description="X-XSS-Protection header is missing. While modern browsers rely more on Content Security Policy, this header still provides an additional layer of protection against cross-site scripting in older browsers.",
            severity="low",
            remediation="Add the X-XSS-Protection header with the value '1; mode=block'.",
            confidence=0.8
        )
        logger.info("Missing X-XSS-Protection header detected")
    elif x_xss == '0':
        Vulnerability.objects.create(
            scan=scan,
            name="X-XSS-Protection Disabled",
            description="The X-XSS-Protection header is set to '0', which disables XSS filtering in browsers that support it.",
            severity="low",
            remediation="Set the X-XSS-Protection header to '1; mode=block' to enable XSS filtering.",
            confidence=0.9
        )
        logger.info("X-XSS-Protection disabled")
    elif '1; mode=block' not in x_xss.lower():
        Vulnerability.objects.create(
            scan=scan,
            name="Suboptimal X-XSS-Protection Configuration",
            description="The X-XSS-Protection header is present but not configured optimally. The recommended value is '1; mode=block'.",
            severity="info",
            remediation="Set the X-XSS-Protection header to '1; mode=block'.",
            confidence=0.7
        )
        logger.info(f"Suboptimal X-XSS-Protection configuration: {x_xss}")

def check_referrer_policy(scan, headers):
    """
    Check for Referrer-Policy header
    
    Args:
        scan (Scan): Scan object
        headers (dict): Normalized HTTP response headers
    """
    referrer = headers.get('referrer-policy')
    
    if not referrer:
        Vulnerability.objects.create(
            scan=scan,
            name="Missing Referrer-Policy Header",
            description="Referrer-Policy header is missing. This header controls how much referrer information should be included with requests, which can help protect user privacy.",
            severity="low", 
            remediation="Add the Referrer-Policy header with an appropriate value such as 'no-referrer', 'no-referrer-when-downgrade', or 'same-origin'.",
            confidence=0.8
        )
        logger.info("Missing Referrer-Policy header detected")
    elif referrer.lower() == 'unsafe-url':
        Vulnerability.objects.create(
            scan=scan,
            name="Insecure Referrer-Policy",
            description="The Referrer-Policy is set to 'unsafe-url', which sends the full URL (including path and query parameters) to any origin. This can leak sensitive information in URLs.",
            severity="medium",
            remediation="Change the Referrer-Policy to a more restrictive value like 'no-referrer', 'no-referrer-when-downgrade', or 'same-origin'.",
            confidence=0.9
        )
        logger.info("Insecure Referrer-Policy detected")

def check_feature_policy(scan, headers):
    """
    Check for Feature-Policy/Permissions-Policy header
    
    Args:
        scan (Scan): Scan object
        headers (dict): Normalized HTTP response headers
    """
    # Check for both Feature-Policy (older) and Permissions-Policy (newer)
    feature_policy = headers.get('feature-policy')
    permissions_policy = headers.get('permissions-policy')
    
    if not feature_policy and not permissions_policy:
        Vulnerability.objects.create(
            scan=scan,
            name="Missing Permissions-Policy Header",
            description="Permissions-Policy (formerly Feature-Policy) header is missing. This header allows control over browser features and APIs, helping to prevent abuse.",
            severity="info",
            remediation="Consider adding the Permissions-Policy header to control which browser features and APIs can be used.",
            confidence=0.7
        )
        logger.info("Missing Permissions-Policy/Feature-Policy header detected")

def check_cors_headers(scan, headers):
    """
    Check CORS headers for security issues
    
    Args:
        scan (Scan): Scan object
        headers (dict): Normalized HTTP response headers
    """
    allow_origin = headers.get('access-control-allow-origin')
    allow_credentials = headers.get('access-control-allow-credentials')
    
    if allow_origin == '*' and allow_credentials == 'true':
        Vulnerability.objects.create(
            scan=scan,
            name="Incompatible CORS Configuration",
            description="The server has both 'Access-Control-Allow-Origin: *' and 'Access-Control-Allow-Credentials: true', which is an invalid combination according to the CORS specification. Browsers will ignore the Allow-Credentials header.",
            severity="high",
            remediation="Do not use a wildcard (*) with Access-Control-Allow-Credentials. Instead, specify allowed origins explicitly.",
            confidence=0.9
        )
        logger.info("Incompatible CORS configuration detected")
    elif allow_origin == '*':
        Vulnerability.objects.create(
            scan=scan,
            name="Permissive CORS Policy",
            description="The server uses a wildcard (*) in Access-Control-Allow-Origin header, allowing any domain to make cross-origin requests. This is generally not recommended for APIs that serve non-public data.",
            severity="medium",
            remediation="Instead of using a wildcard, specify the allowed origins explicitly.",
            confidence=0.8
        )
        logger.info("Permissive CORS Policy detected")

def _analyze_headers(self):
    """
    Analyze HTTP security headers
    """
    logger.info(f"Analyzing security headers for {self.target_url}")
    
    try:
        # Check if we have a response object from basic HTTP analysis
        if not hasattr(self, 'response') or not self.response:
            # Make a new request if needed
            response = requests.get(self.target_url, headers=self.headers, timeout=10)
            headers = dict(response.headers)
        else:
            # Use existing response
            headers = dict(self.response.headers)
        
        # Store headers in results if not already stored
        if not self.results.get('response_headers'):
            self.results['response_headers'] = headers
        
        # Import and use header analyzer
        from scanning.passive.analyzers.header_analyzer import analyze_security_headers
        analyze_security_headers(self.scan, headers)
        
        # Try to use ZAP if available for more comprehensive header analysis
        if self.available_tools.get('zap', {}).get('available', False):
            try:
                from scanning.integrations.zap_adapter import ZAPAdapter
                adapter = ZAPAdapter(config={
                    'zap_host': self.available_tools['zap']['host'],
                    'zap_port': self.available_tools['zap']['port'],
                    'zap_api_key': self.config.zap_config.get('api_key', '') if hasattr(self.config, 'zap_config') else ''
                })
                
                header_findings = adapter.check_headers(self.target_url)
                if header_findings:
                    logger.info(f"ZAP found {len(header_findings)} header-related issues")
                    for finding in header_findings:
                        finding['source'] = 'zap'
                        self._add_finding(finding)
            except Exception as zap_err:
                logger.warning(f"Error using ZAP for header analysis: {str(zap_err)}")
        
        # Update progress
        self.update_progress(60, "Security headers analysis completed")
        
    except Exception as e:
        logger.error(f"Error in security headers analysis: {str(e)}")
        self._add_error_finding("Security Headers Analysis Error", str(e))
        self.update_progress(60, "Security headers analysis failed")

def check_cache_control(scan, headers):
    """
    Check for proper Cache-Control header for sensitive content
    
    Args:
        scan (Scan): Scan object
        headers (dict): Normalized HTTP response headers
    """
    cache_control = headers.get('cache-control')
    pragma = headers.get('pragma')
    
    # Check for sensitive URLs - this is a basic check
    # In a real implementation, you'd check the current URL against a list of sensitive paths
    sensitive_path = False  # Placeholder for actual logic
    
    if sensitive_path and not cache_control:
        Vulnerability.objects.create(
            scan=scan,
            name="Missing Cache-Control Header on Sensitive Page",
            description="The page does not have a Cache-Control header set, which could result in sensitive information being cached by browsers or intermediaries.",
            severity="medium",
            remediation="Add the Cache-Control header with appropriate directives like 'no-store, no-cache, must-revalidate, private'.",
            confidence=0.8
        )
        logger.info("Missing Cache-Control header on potentially sensitive page")
    elif sensitive_path and cache_control:
        if 'no-store' not in cache_control.lower():
            Vulnerability.objects.create(
                scan=scan,
                name="Insufficient Cache-Control for Sensitive Content",
                description="The Cache-Control header does not include the 'no-store' directive, which is recommended for sensitive pages to prevent storing any part of the response.",
                severity="low",
                remediation="Add the 'no-store' directive to the Cache-Control header.",
                confidence=0.7
            )
            logger.info("Insufficient Cache-Control for potentially sensitive content")

def check_header_information_disclosure(scan, headers):
    """
    Check for information disclosure in HTTP headers
    
    Args:
        scan (Scan): Scan object
        headers (dict): Original HTTP response headers (case preserved)
    """
    sensitive_info = []
    
    # Check Server header for detailed version information
    if 'Server' in headers:
        server = headers['Server']
        if re.search(r'[a-zA-Z]+/[0-9\.]+', server):
            sensitive_info.append(f"Server: {server}")
    
    # Check X-Powered-By header
    if 'X-Powered-By' in headers:
        x_powered_by = headers['X-Powered-By']
        sensitive_info.append(f"X-Powered-By: {x_powered_by}")
    
    # Check for other potentially sensitive headers
    for header, value in headers.items():
        if header.lower().startswith(('x-aspnet', 'x-iis', 'x-weblogic', 'x-websphere', 'x-oracle')):
            sensitive_info.append(f"{header}: {value}")
    
    if sensitive_info:
        Vulnerability.objects.create(
            scan=scan,
            name="Header Information Disclosure",
            description="HTTP headers are revealing potentially sensitive information about the server technology stack. This information can be used by attackers to target known vulnerabilities.",
            severity="low",
            evidence="; ".join(sensitive_info),
            remediation="Configure your web server or application to suppress or modify headers that reveal implementation details like software names and versions.",
            confidence=0.9
        )
        logger.info(f"Header information disclosure detected: {'; '.join(sensitive_info)}")

# Import needed at the end to avoid circular imports
import re