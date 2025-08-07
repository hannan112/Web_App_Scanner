"""
URL parsing utilities for the scanning module
"""

from urllib.parse import parse_qs, urljoin, urlparse


def extract_domain(url):
    """
    Extract the domain from a URL

    Args:
        url (str): URL to parse

    Returns:
        str: Domain name
    """
    parsed = urlparse(url)
    return parsed.netloc


def is_same_domain(url1, url2):
    """
    Check if two URLs belong to the same domain

    Args:
        url1 (str): First URL
        url2 (str): Second URL

    Returns:
        bool: True if both URLs belong to the same domain
    """
    domain1 = extract_domain(url1)
    domain2 = extract_domain(url2)

    # Handle subdomains
    if domain1 and domain2:
        # Extract main domain parts
        parts1 = domain1.split(".")
        parts2 = domain2.split(".")

        # Take the last two parts for comparison (e.g., example.com)
        if len(parts1) >= 2 and len(parts2) >= 2:
            main_domain1 = ".".join(parts1[-2:])
            main_domain2 = ".".join(parts2[-2:])
            return main_domain1 == main_domain2

    # Default exact match
    return domain1 == domain2


def extract_query_params(url):
    """
    Extract and parse query parameters from a URL

    Args:
        url (str): URL to parse

    Returns:
        dict: Dictionary of query parameters
    """
    parsed = urlparse(url)
    return parse_qs(parsed.query)


def normalize_url(url, base_url=None):
    """
    Normalize a URL by resolving relative paths and removing fragments

    Args:
        url (str): URL to normalize
        base_url (str, optional): Base URL for resolving relative URLs

    Returns:
        str: Normalized URL
    """
    # Resolve relative URLs
    if base_url and not url.startswith(("http://", "https://")):
        url = urljoin(base_url, url)

    # Parse URL
    parsed = urlparse(url)

    # Remove fragments
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    # Add query parameters if present
    if parsed.query:
        normalized += f"?{parsed.query}"

    return normalized


def is_valid_url(url):
    """
    Check if a URL is valid

    Args:
        url (str): URL to check

    Returns:
        bool: True if URL is valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def get_base_url(url):
    """
    Get the base URL (scheme + domain) from a full URL

    Args:
        url (str): URL to parse

    Returns:
        str: Base URL (e.g., https://example.com)
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def get_path_from_url(url):
    """
    Extract the path component from a URL

    Args:
        url (str): URL to parse

    Returns:
        str: Path component of the URL
    """
    parsed = urlparse(url)
    return parsed.path


def join_url_path(base_url, path):
    """
    Join a base URL with a path, handling slash properly

    Args:
        base_url (str): Base URL
        path (str): Path to join

    Returns:
        str: Joined URL
    """
    return urljoin(base_url, path)
