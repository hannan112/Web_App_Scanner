"""
CORS policy analyzer for passive scanning
"""
import logging
import requests
from urllib.parse import urlparse
from scanning.models.vulnerability import Vulnerability

logger = logging.getLogger(__name__)

def check_cors_policy(scan, url):
    """
    Check CORS policy configuration for potential issues
    
    Args:
        scan (Scan): Scan object
        url (str): URL to check
    """
    try:
        # Extract domain for the Origin header test
        parsed_url = urlparse(url)
        origin_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Prepare headers for CORS test
        headers = {
            'Origin': 'https://malicious-site.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make a request with a fake origin
        response = requests.get(url, headers=headers, timeout=10)
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin', None),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials', None),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods', None),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers', None),
            'Access-Control-Expose-Headers': response.headers.get('Access-Control-Expose-Headers', None)
        }
        
        # Check for permissive CORS policy
        check_permissive_cors(scan, url, cors_headers)
        
        # Make another request with the legitimate origin
        headers['Origin'] = origin_domain
        response = requests.get(url, headers=headers, timeout=10)
        legitimate_cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin', None),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials', None)
        }
        
        # Check for origin reflection issues
        check_origin_reflection(scan, url, cors_headers, legitimate_cors_headers)
        
    except Exception as e:
        logger.error(f"Error checking CORS policy for {url}: {str(e)}")

def _analyze_cors(self):
    """
    Analyze CORS policy for security issues
    """
    logger.info(f"Analyzing CORS policy for {self.target_url}")
    
    try:
        # Import and use CORS analyzer
        from scanning.passive.analyzers.cors_analyzer import check_cors_policy
        
        # Check CORS policy
        check_cors_policy(self.scan, self.target_url)
        
        # Update progress
        self.update_progress(85, "CORS analysis completed")
        
    except Exception as e:
        logger.error(f"Error in CORS analysis: {str(e)}")
        self._add_error_finding("CORS Analysis Error", str(e))
        self.update_progress(85, "CORS analysis failed")

def check_permissive_cors(scan, url, cors_headers):
    """
    Check for permissive CORS policy (e.g., Allow-Origin: *)
    
    Args:
        scan (Scan): Scan object
        url (str): URL being checked
        cors_headers (dict): CORS headers from the response
    """
    allow_origin = cors_headers.get('Access-Control-Allow-Origin')
    allow_credentials = cors_headers.get('Access-Control-Allow-Credentials')
    
    if allow_origin == '*':
        if allow_credentials == 'true':
            # Wildcard with credentials is a serious issue
            Vulnerability.objects.create(
                scan=scan,
                name="Improper CORS Configuration",
                description="The application has both 'Access-Control-Allow-Origin: *' and 'Access-Control-Allow-Credentials: true', which is an invalid combination according to the CORS specification. Browsers will ignore the Allow-Credentials header.",
                severity="high",
                url=url,
                evidence=f"Access-Control-Allow-Origin: {allow_origin}, Access-Control-Allow-Credentials: {allow_credentials}",
                remediation="Do not use a wildcard (*) with Access-Control-Allow-Credentials: true. Instead, specify allowed origins explicitly.",
                confidence=0.9
            )
            logger.info(f"Found wildcard CORS policy with credentials on {url}")
        else:
            # Wildcard without credentials is less severe but still notable
            Vulnerability.objects.create(
                scan=scan,
                name="Permissive CORS Policy",
                description="The application uses a wildcard (*) in Access-Control-Allow-Origin header, allowing any domain to make cross-origin requests. This can potentially lead to data theft if sensitive information is exposed.",
                severity="medium",
                url=url,
                evidence=f"Access-Control-Allow-Origin: {allow_origin}",
                remediation="Instead of using a wildcard, specify the allowed origins explicitly.",
                confidence=0.8
            )
            logger.info(f"Found wildcard CORS policy on {url}")

def check_origin_reflection(scan, url, cors_headers, legitimate_cors_headers):
    """
    Check if the server reflects any Origin header back in Access-Control-Allow-Origin
    
    Args:
        scan (Scan): Scan object
        url (str): URL being checked
        cors_headers (dict): CORS headers from malicious origin request
        legitimate_cors_headers (dict): CORS headers from legitimate origin request
    """
    malicious_allow_origin = cors_headers.get('Access-Control-Allow-Origin')
    legitimate_allow_origin = legitimate_cors_headers.get('Access-Control-Allow-Origin')
    allow_credentials = cors_headers.get('Access-Control-Allow-Credentials')
    
    if malicious_allow_origin == 'https://malicious-site.com':
        # Server is reflecting the Origin header back
        if allow_credentials == 'true':
            # Reflection with credentials is a serious issue
            Vulnerability.objects.create(
                scan=scan,
                name="CORS Origin Reflection with Credentials",
                description="The server reflects the Origin header back in the Access-Control-Allow-Origin header and allows credentials. This can lead to cross-site request forgery and data theft attacks.",
                severity="critical",
                url=url,
                evidence=f"Origin: https://malicious-site.com, Access-Control-Allow-Origin: {malicious_allow_origin}, Access-Control-Allow-Credentials: {allow_credentials}",
                remediation="Implement a whitelist of allowed origins instead of reflecting the Origin header. Only allow trusted domains.",
                confidence=0.9
            )
            logger.info(f"Found CORS origin reflection with credentials on {url}")
        else:
            # Reflection without credentials is less severe but still an issue
            Vulnerability.objects.create(
                scan=scan,
                name="CORS Origin Reflection",
                description="The server reflects the Origin header back in the Access-Control-Allow-Origin header. This may allow malicious sites to make cross-origin requests to the application.",
                severity="medium",
                url=url,
                evidence=f"Origin: https://malicious-site.com, Access-Control-Allow-Origin: {malicious_allow_origin}",
                remediation="Implement a whitelist of allowed origins instead of reflecting the Origin header.",
                confidence=0.8
            )
            logger.info(f"Found CORS origin reflection on {url}")
    
    # Check for subdomains in allow origins
    if legitimate_allow_origin and '.' in legitimate_allow_origin:
        parsed = urlparse(legitimate_allow_origin)
        if parsed.netloc and parsed.netloc.count('.') > 1:
            # Check if it might be using a pattern like *.example.com
            domain_parts = parsed.netloc.split('.')
            if len(domain_parts) >= 3 and domain_parts[0] != 'www':
                Vulnerability.objects.create(
                    scan=scan,
                    name="CORS Allows Subdomains",
                    description="The CORS policy appears to allow requests from subdomains. If any of these subdomains can be compromised or contain vulnerabilities, they could be used to access data from the main application.",
                    severity="low",
                    url=url,
                    evidence=f"Access-Control-Allow-Origin: {legitimate_allow_origin}",
                    remediation="If possible, specify exact origins rather than allowing all subdomains.",
                    confidence=0.7
                )
                logger.info(f"CORS policy may allow subdomains on {url}")