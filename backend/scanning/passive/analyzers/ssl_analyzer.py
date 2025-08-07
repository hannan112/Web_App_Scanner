"""
SSL/TLS certificate and configuration analyzer
"""

import datetime
import logging
import socket
import ssl
from urllib.parse import urlparse

from scanning.models.vulnerability import Vulnerability

logger = logging.getLogger(__name__)


def analyze_ssl_certificate(scan, target_url):
    """
    Analyze SSL/TLS certificate for security issues

    Args:
        scan (Scan): The scan object
        target_url (str): The target URL

    Returns:
        dict: SSL certificate information
    """
    result = {"certificate": None, "protocol": None, "cipher": None, "issues": []}

    try:
        # Parse the URL to get hostname and port
        parsed_url = urlparse(target_url)
        hostname = parsed_url.netloc.split(":")[0]
        port = parsed_url.port or 443

        # Only analyze HTTPS URLs
        if parsed_url.scheme != "https":
            result["issues"].append("Not using HTTPS")

            # Create vulnerability record for non-HTTPS site
            Vulnerability.objects.create(
                scan=scan,
                name="HTTPS Not Implemented",
                description="The website is not using HTTPS. This means that all data transmitted between the user and the website can be intercepted and read by attackers.",
                severity="high",
                url=target_url,
                remediation="Implement HTTPS by obtaining an SSL/TLS certificate and configuring your web server to use it.",
                confidence=1.0,
            )
            return result

        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = (
            ssl.CERT_NONE
        )  # For analysis, we want to check invalid certs too

        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = (
            ssl.CERT_NONE
        )  # For analysis, we want to check invalid certs too

        # Connect to the server
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Get certificate
                cert = ssock.getpeercert(binary_form=False)
                cipher = ssock.cipher()
                protocol = ssock.version()

                # Store certificate info
                if cert:
                    # Safely extract certificate information with error handling
                    try:
                        subject_entries = cert.get("subject", [])
                        issuer_entries = cert.get("issuer", [])

                        formatted_subject = {}
                        for entry in subject_entries:
                            if entry and len(entry) > 0 and len(entry[0]) >= 2:
                                formatted_subject[entry[0][0]] = entry[0][1]

                        formatted_issuer = {}
                        for entry in issuer_entries:
                            if entry and len(entry) > 0 and len(entry[0]) >= 2:
                                formatted_issuer[entry[0][0]] = entry[0][1]

                        result["certificate"] = {
                            "subject": formatted_subject,
                            "issuer": formatted_issuer,
                            "version": cert.get("version", ""),
                            "notBefore": cert.get("notBefore", ""),
                            "notAfter": cert.get("notAfter", ""),
                            "serialNumber": cert.get("serialNumber", ""),
                            "subjectAltName": cert.get("subjectAltName", []),
                        }
                    except Exception as cert_error:
                        logger.error(
                            f"Error processing certificate data: {str(cert_error)}"
                        )
                        result["certificate"] = {
                            "error": f"Certificate data processing error: {str(cert_error)}"
                        }
                        # Still continue with protocol and cipher info

                # Store protocol and cipher info
                if cipher:
                    result["protocol"] = protocol
                    result["cipher"] = {
                        "name": cipher[0],
                        "version": cipher[1],
                        "bits": cipher[2],
                    }

    except Exception as e:
        logger.error(f"SSL Error: {str(e)}")
        result["issues"].append(f"SSL Error: {str(e)}")

        # Create vulnerability record
        Vulnerability.objects.create(
            scan=scan,
            name="SSL/TLS Error",
            description=f"SSL connection error: {str(e)}",
            severity="high",
            url=target_url,
            remediation="Check your SSL/TLS configuration and certificates.",
            confidence=0.9,
        )
    except (socket.gaierror, socket.timeout, ConnectionRefusedError) as e:
        logger.error(f"Connection Error: {str(e)}")
        result["issues"].append(f"Connection Error: {str(e)}")
    except Exception as e:
        logger.error(f"Error analyzing SSL certificate: {str(e)}")
        result["issues"].append(f"Error: {str(e)}")

    return result


def check_certificate_issues(scan, ssl_result, url):
    """
    Check for common certificate issues and create vulnerability records

    Args:
        scan (Scan): The scan object
        ssl_result (dict): SSL analysis results
        url (str): The target URL
    """
    cert = ssl_result.get("certificate")
    if not cert:
        return

    # Check for expired or soon-to-expire certificate
    if "notAfter" in cert:
        try:
            # Parse certificate expiration date
            expires = datetime.datetime.strptime(
                cert["notAfter"], "%b %d %H:%M:%S %Y GMT"
            )
            now = datetime.datetime.now()
            days_remaining = (expires - now).days

            if days_remaining < 0:
                Vulnerability.objects.create(
                    scan=scan,
                    name="Expired SSL Certificate",
                    description=f"The SSL certificate expired on {cert['notAfter']}.",
                    severity="critical",
                    url=url,
                    remediation="Renew the SSL certificate immediately.",
                    confidence=1.0,
                )
            elif days_remaining < 30:
                Vulnerability.objects.create(
                    scan=scan,
                    name="SSL Certificate Expiring Soon",
                    description=f"The SSL certificate will expire in {days_remaining} days ({cert['notAfter']}).",
                    severity="medium",
                    url=url,
                    remediation="Plan to renew the SSL certificate soon.",
                    confidence=1.0,
                )
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing certificate date: {str(e)}")

    # Check for self-signed certificates
    issuer = cert.get("issuer", {})
    subject = cert.get("subject", {})

    # More robust self-signed certificate check
    if issuer and subject:
        # Compare the common name fields
        issuer_cn = issuer.get("commonName")
        subject_cn = subject.get("commonName")

        if issuer_cn == subject_cn:
            Vulnerability.objects.create(
                scan=scan,
                name="Self-Signed Certificate",
                description="The server is using a self-signed certificate. Self-signed certificates aren't trusted by browsers and can lead to security warnings.",
                severity="medium",
                url=url,
                remediation="Replace the self-signed certificate with one issued by a trusted Certificate Authority.",
                confidence=0.9,
            )

    # Check subject alternative names
    if "subjectAltName" in cert:
        hostname = urlparse(url).netloc.split(":")[0]
        valid_for_domain = False

        for name_type, value in cert["subjectAltName"]:
            if name_type.lower() == "dns":
                # Check exact match
                if value == hostname:
                    valid_for_domain = True
                    break

                # Check wildcard match
                if value.startswith("*.") and hostname.endswith(value[2:]):
                    valid_for_domain = True
                    break

        if not valid_for_domain:
            Vulnerability.objects.create(
                scan=scan,
                name="Certificate Hostname Mismatch",
                description=f"The SSL certificate is not valid for the domain {hostname}. This can cause security warnings in browsers.",
                severity="medium",
                url=url,
                remediation="Obtain a certificate that is valid for this specific domain.",
                confidence=0.9,
            )


def check_ssl_configuration(scan, ssl_result, url):
    """
    Check for weak SSL/TLS configurations

    Args:
        scan (Scan): The scan object
        ssl_result (dict): SSL analysis results
        url (str): The target URL
    """
    # Check for weak protocols
    protocol = ssl_result.get("protocol")
    if protocol:
        weak_protocols = ["SSLv2", "SSLv3", "TLSv1", "TLSv1.1"]

        if protocol in weak_protocols:
            Vulnerability.objects.create(
                scan=scan,
                name="Weak SSL/TLS Protocol",
                description=f"The server is using {protocol}, which is considered insecure and has known vulnerabilities.",
                severity="high",
                url=url,
                remediation="Configure the server to use TLSv1.2 or TLSv1.3 only.",
                confidence=0.9,
            )

    # Check for weak ciphers
    cipher = ssl_result.get("cipher")
    if cipher:
        weak_ciphers = [
            "RC4",
            "DES",
            "3DES",
            "MD5",
            "NULL",
            "EXPORT",
            "anon",
            "CBC",
            "ADH",
            "IDEA",
        ]

        if any(weak in cipher.upper() for weak in weak_ciphers):
            Vulnerability.objects.create(
                scan=scan,
                name="Weak SSL/TLS Cipher",
                description=f"The server is using a weak cipher: {cipher}. This can make encrypted connections vulnerable to attacks.",
                severity="high",
                url=url,
                remediation="Configure the server to use strong ciphers only (e.g., AES-GCM with forward secrecy).",
                confidence=0.9,
            )


def check_hsts(scan, headers, url):
    """
    Check for HTTP Strict Transport Security (HSTS) header

    Args:
        scan (Scan): The scan object
        headers (dict): HTTP response headers
        url (str): The target URL
    """
    hsts_header = headers.get("Strict-Transport-Security")

    if not hsts_header:
        Vulnerability.objects.create(
            scan=scan,
            name="Missing HSTS Header",
            description="The website does not use HTTP Strict Transport Security (HSTS). HSTS protects against downgrade attacks and cookie hijacking by telling browsers to always use secure connections.",
            severity="medium",
            url=url,
            remediation="Implement HSTS by adding the Strict-Transport-Security header with appropriate values, e.g., 'max-age=31536000; includeSubDomains'.",
            confidence=0.9,
        )
        return False

    # Check if max-age is sufficient (at least 6 months = 15768000 seconds)
    parts = hsts_header.split(";")
    for part in parts:
        if part.strip().startswith("max-age="):
            try:
                max_age = int(part.strip().split("=")[1])
                if max_age < 15768000:
                    Vulnerability.objects.create(
                        scan=scan,
                        name="Short HSTS Max-Age",
                        description=f"The HSTS max-age is set to {max_age} seconds, which is less than the recommended 6 months (15768000 seconds).",
                        severity="low",
                        url=url,
                        remediation="Increase the HSTS max-age to at least 6 months (15768000 seconds).",
                        confidence=0.8,
                    )
            except ValueError:
                pass

    # Check for includeSubDomains directive
    if "includeSubDomains" not in hsts_header:
        Vulnerability.objects.create(
            scan=scan,
            name="HSTS Missing includeSubDomains",
            description="The HSTS header is missing the 'includeSubDomains' directive. This could leave subdomains vulnerable to attacks.",
            severity="low",
            url=url,
            remediation="Add the 'includeSubDomains' directive to your HSTS header.",
            confidence=0.7,
        )

    return True
