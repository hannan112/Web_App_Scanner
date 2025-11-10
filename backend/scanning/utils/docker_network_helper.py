"""
Docker Network Helper

Handles URL translation when ZAP is running in Docker but target is on host.
ZAP container can't reach localhost - needs host.docker.internal or host IP.
"""

import logging
import socket
import os

logger = logging.getLogger(__name__)


def is_zap_in_docker(zap_host: str) -> bool:
    """
    Check if ZAP is running in Docker

    Args:
        zap_host: ZAP host address

    Returns:
        bool: True if ZAP appears to be in Docker
    """
    # If ZAP host is 'zap' or a Docker network name, it's in Docker
    if zap_host in ['zap', 'zap-container']:
        return True

    # If using localhost/127.0.0.1, check if ZAP_HOST env var suggests Docker
    zap_host_env = os.getenv('ZAP_HOST', '')
    if zap_host_env in ['zap', 'zap-container']:
        return True

    # If we can detect Docker environment
    if os.path.exists('/.dockerenv'):
        return True

    return False


def translate_url_for_docker(url: str, zap_host: str = None) -> str:
    """
    Translate localhost URLs to be accessible from Docker container

    When ZAP is in Docker and target is on host:
    - localhost:8005 → host.docker.internal:8005
    - 127.0.0.1:8005 → host.docker.internal:8005

    Args:
        url: Target URL to scan
        zap_host: ZAP host address (to detect if in Docker)

    Returns:
        str: Translated URL that ZAP container can access
    """
    if not url:
        return url

    # Check if ZAP is in Docker
    if zap_host and not is_zap_in_docker(zap_host):
        logger.debug(f"ZAP not in Docker, no URL translation needed: {url}")
        return url

    # Check if URL uses localhost or 127.0.0.1
    if 'localhost' in url or '127.0.0.1' in url:
        # Try host.docker.internal first (works on Docker Desktop)
        translated = url.replace('localhost', 'host.docker.internal')
        translated = translated.replace('127.0.0.1', 'host.docker.internal')

        logger.info(f"Translated URL for Docker: {url} → {translated}")
        return translated

    # URL doesn't need translation
    return url


def get_host_ip() -> str:
    """
    Get host machine IP address (fallback for Linux without host.docker.internal)

    Returns:
        str: Host IP address or None
    """
    try:
        # Get default gateway (Docker host) IP
        # This works on Linux where host.docker.internal might not be available
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        host_ip = s.getsockname()[0]
        s.close()

        # On Docker, the host is usually at the gateway IP
        # Typically 172.17.0.1 or 172.18.0.1
        parts = host_ip.split('.')
        if len(parts) == 4 and parts[0] == '172':
            # Replace last octet with 1 to get gateway
            gateway_ip = f"{parts[0]}.{parts[1]}.{parts[2]}.1"
            logger.debug(f"Detected Docker host IP: {gateway_ip}")
            return gateway_ip

        return host_ip

    except Exception as e:
        logger.warning(f"Could not detect host IP: {e}")
        return None


def translate_url_with_host_ip(url: str) -> str:
    """
    Translate localhost URLs using detected host IP (Linux fallback)

    Args:
        url: Target URL

    Returns:
        str: Translated URL using host IP
    """
    if not url or ('localhost' not in url and '127.0.0.1' not in url):
        return url

    host_ip = get_host_ip()
    if not host_ip:
        logger.warning("Could not detect host IP for URL translation")
        return url

    translated = url.replace('localhost', host_ip)
    translated = translated.replace('127.0.0.1', host_ip)

    logger.info(f"Translated URL using host IP: {url} → {translated}")
    return translated


def ensure_target_accessible(url: str, zap_host: str = None) -> str:
    """
    Ensure target URL is accessible from ZAP container

    Tries multiple strategies:
    1. Docker container name (if target is in Docker)
    2. host.docker.internal (works on Docker Desktop)
    3. Detected host IP (works on Linux)
    4. Original URL (if not localhost)

    Args:
        url: Target URL
        zap_host: ZAP host address

    Returns:
        str: Best URL for ZAP to access target
    """
    import subprocess

    # If not localhost, return as-is
    if 'localhost' not in url and '127.0.0.1' not in url:
        return url

    # If ZAP not in Docker, return as-is
    if zap_host and not is_zap_in_docker(zap_host):
        return url

    logger.info(f"Translating localhost URL for Docker environment: {url}")

    # Strategy 1: Check if target is DVWA in Docker (localhost:8005)
    if ':8005' in url:
        try:
            # Check if DVWA container exists
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=dvwa", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            dvwa_containers = [name for name in result.stdout.strip().split('\n') if 'dvwa' in name.lower()]

            if dvwa_containers:
                dvwa_container = dvwa_containers[0]
                # DVWA runs on port 80 inside container
                translated = url.replace('localhost:8005', f'{dvwa_container}:80')
                translated = translated.replace('127.0.0.1:8005', f'{dvwa_container}:80')
                logger.info(f"✅ Found DVWA container '{dvwa_container}', using direct connection: {translated}")
                return translated
        except Exception as e:
            logger.warning(f"Could not detect DVWA container: {e}")

    # Strategy 2: Try host.docker.internal (Docker Desktop - Mac/Windows)
    translated = translate_url_for_docker(url, zap_host)
    logger.info(f"Using host.docker.internal translation: {translated}")

    # Note: On Linux, host.docker.internal may not work
    # User may need to connect containers to same network manually

    return translated


# Convenience function
def get_docker_accessible_url(url: str, zap_host: str = None) -> str:
    """
    Get Docker-accessible version of URL (main entry point)

    Args:
        url: Target URL to scan
        zap_host: ZAP host address

    Returns:
        str: URL that ZAP container can access
    """
    return ensure_target_accessible(url, zap_host)
