"""
Content analyzer for passive scanning to detect information disclosure issues
"""
import logging
import re
from bs4 import BeautifulSoup
from scanning.models.vulnerability import Vulnerability

logger = logging.getLogger(__name__)

def analyze_information_disclosure(scan, url, html_content, headers):
    """
    Analyze HTML content for information disclosure vulnerabilities.
    
    Args:
        scan (Scan): Scan object
        url (str): URL being analyzed
        html_content (str): HTML content to analyze
        headers (dict): HTTP response headers
    """
    try:
        # Create BeautifulSoup object
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for HTML comments that might contain sensitive information
        check_html_comments(scan, url, soup)
        
        # Check for exposed email addresses
        check_exposed_emails(scan, url, html_content)
        
        # Check for developer comments or TODO notes
        check_developer_notes(scan, url, html_content)
        
        # Check for version information disclosure
        check_version_disclosure(scan, url, html_content, headers)
        
        # Check for exposed internal paths
        check_internal_paths(scan, url, html_content)
        
        # Check for error messages that might reveal sensitive details
        check_error_messages(scan, url, html_content)
        
    except Exception as e:
        logger.error(f"Error analyzing content for {url}: {str(e)}")

def check_html_comments(scan, url, soup):
    """Check for HTML comments that might contain sensitive information."""
    comments = soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith('<!--'))
    
    sensitive_patterns = [
        r'password', r'user', r'todo', r'fix', r'key', r'api', 
        r'token', r'secret', r'config', r'db', r'database',
        r'todo:', r'fixme:', r'hack', r'workaround', r'bypass'
    ]
    
    sensitive_comments = []
    
    for comment in comments:
        comment_text = comment.strip()
        if any(re.search(pattern, comment_text, re.IGNORECASE) for pattern in sensitive_patterns):
            # Sanitize the comment for display (max 100 chars)
            sanitized = comment_text[:100] + '...' if len(comment_text) > 100 else comment_text
            sensitive_comments.append(sanitized)
    
    if sensitive_comments:
        # Create vulnerability record
        Vulnerability.objects.create(
            scan=scan,
            name="Sensitive Information in HTML Comments",
            description="HTML comments containing potentially sensitive information were found. These comments might reveal internal workings, credentials, or other sensitive details.",
            severity="low",
            url=url,
            evidence=f"Found {len(sensitive_comments)} potentially sensitive comments. First few examples: {'; '.join(sensitive_comments[:3])}",
            remediation="Remove comments containing sensitive information before deploying to production.",
            confidence=0.7
        )
        logger.info(f"Found {len(sensitive_comments)} potentially sensitive HTML comments on {url}")

def check_exposed_emails(scan, url, html_content):
    """Check for exposed email addresses."""
    # Simple regex for email detection
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, html_content)
    
    if emails:
        # Filter out common non-sensitive emails
        non_sensitive = ['example.com', 'test.com', 'domain.com']
        sensitive_emails = [email for email in emails if not any(ns in email for ns in non_sensitive)]
        
        if sensitive_emails:
            # Obfuscate emails for display
            obfuscated = []
            for email in sensitive_emails[:5]:
                parts = email.split('@')
                if len(parts) == 2:
                    username, domain = parts
                    obfuscated.append(f"{username[:3]}***@{domain}")
            
            Vulnerability.objects.create(
                scan=scan,
                name="Exposed Email Addresses",
                description=f"Found {len(sensitive_emails)} email addresses exposed in the HTML content. These can be harvested for spam or targeted phishing attacks.",
                severity="info",
                url=url,
                evidence=f"Examples (obfuscated): {', '.join(obfuscated)}",
                remediation="Consider obfuscating email addresses or using contact forms instead of plaintext emails.",
                confidence=0.8
            )
            logger.info(f"Found {len(sensitive_emails)} exposed email addresses on {url}")

def check_developer_notes(scan, url, html_content):
    """Check for developer comments or TODO notes."""
    dev_patterns = [
        r'todo:', r'fixme:', r'hack:', r'xxx:', r'note:', r'bug:',
        r'(?:^|\s)todo\b', r'(?:^|\s)fixme\b', r'(?:^|\s)hack\b', 
        r'(?:^|\s)xxx\b', r'(?:^|\s)debug\b', r'(?:^|\s)temp\b'
    ]
    
    matches = []
    for pattern in dev_patterns:
        found = re.findall(pattern, html_content, re.IGNORECASE)
        matches.extend(found)
    
    if matches:
        Vulnerability.objects.create(
            scan=scan,
            name="Developer Notes or TODOs Exposed",
            description="Developer notes, TODOs, or other debugging information found in the page source. These might reveal internal workings or security issues.",
            severity="info",
            url=url,
            evidence=f"Found developer notes including: {', '.join(matches[:5])}",
            remediation="Remove development notes and comments before deploying to production.",
            confidence=0.6
        )
        logger.info(f"Found {len(matches)} developer notes on {url}")

def check_version_disclosure(scan, url, html_content, headers):
    """Check for version information disclosure in HTML or headers."""
    version_patterns = [
        r'version[:\s="\']+([\d\.]+)', 
        r'v([\d\.]+)', 
        r'(?:jquery|angular|react|vue|bootstrap)[:\s="\']+([\d\.]+)',
        r'(?:wordpress|drupal|joomla|django)[:\s="\']+([\d\.]+)'
    ]
    
    versions_found = []
    
    # Check HTML content
    for pattern in version_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            versions_found.extend(matches)
    
    # Check headers
    server_header = headers.get('Server', '')
    if server_header and any(tech in server_header.lower() for tech in ['apache', 'nginx', 'iis', 'php', 'tomcat']):
        versions_found.append(server_header)
    
    x_powered_by = headers.get('X-Powered-By', '')
    if x_powered_by:
        versions_found.append(x_powered_by)
    
    if versions_found:
        Vulnerability.objects.create(
            scan=scan,
            name="Version Information Disclosure",
            description="Software version information is disclosed through page content or HTTP headers. This may help attackers identify vulnerabilities in outdated software.",
            severity="low",
            url=url,
            evidence=f"Versions disclosed: {', '.join(versions_found[:5])}",
            remediation="Remove or obfuscate version information from HTTP headers and HTML content.",
            confidence=0.9
        )
        logger.info(f"Found version information disclosure on {url}")

def check_internal_paths(scan, url, html_content):
    """Check for exposed internal file paths."""
    # Common patterns for internal paths
    path_patterns = [
        r'[C-Z]:\\\\[A-Za-z0-9\\_.]+', # Windows paths
        r'/home/[A-Za-z0-9/_.]+',      # Linux paths
        r'/var/www/[A-Za-z0-9/_.]+',   # Common web server paths
        r'/usr/local/[A-Za-z0-9/_.]+', # Common Unix paths
        r'/tmp/[A-Za-z0-9/_.]+',       # Temp directories
        r'/app/[A-Za-z0-9/_.]+',       # Common app directories
        r'/srv/[A-Za-z0-9/_.]+',       # Service directories
    ]
    
    paths_found = []
    for pattern in path_patterns:
        matches = re.findall(pattern, html_content)
        paths_found.extend(matches)
    
    if paths_found:
        Vulnerability.objects.create(
            scan=scan,
            name="Internal Path Disclosure",
            description="Internal server file paths are exposed in the HTML content. This information can be valuable for attackers trying to understand the server environment.",
            severity="low",
            url=url,
            evidence=f"Internal paths found: {', '.join(paths_found[:3])}",
            remediation="Ensure internal file paths are not exposed in HTML content, error messages, or comments.",
            confidence=0.8
        )
        logger.info(f"Found {len(paths_found)} internal paths on {url}")

def check_error_messages(scan, url, html_content):
    """Check for detailed error messages that might reveal sensitive information."""
    error_patterns = [
        r'(?:sql|mysql|postgresql|oracle)\s+(?:error|exception)',
        r'(?:exception|error)(?:\s+at\s+|\:)[A-Za-z0-9_.]+',
        r'stack trace',
        r'syntax error',
        r'failed to load resource',
        r'uncaught (?:exception|error)',
        r'(?:warning|notice|deprecated)\:',
        r'call to undefined function',
        r'fatal error'
    ]
    
    errors_found = []
    for pattern in error_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        errors_found.extend(matches)
    
    if errors_found:
        Vulnerability.objects.create(
            scan=scan,
            name="Detailed Error Messages",
            description="Detailed error messages are exposed to users. These can reveal information about the internal workings, technologies, or structure of the application.",
            severity="low",
            url=url,
            evidence=f"Error messages found: {', '.join(errors_found[:3])}",
            remediation="Configure the application to display generic error messages to users while logging detailed errors server-side.",
            confidence=0.7
        )
        logger.info(f"Found {len(errors_found)} detailed error messages on {url}")