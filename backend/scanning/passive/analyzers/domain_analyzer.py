"""
Domain analyzer for passive scanning
"""
import logging
import socket
import dns.resolver
from scanning.models.vulnerability import Vulnerability

logger = logging.getLogger(__name__)

def perform_dns_lookup(domain):
    """
    Perform DNS lookups for a domain to gather information
    
    Args:
        domain (str): Domain to lookup
        
    Returns:
        dict: Dictionary of DNS records
    """
    results = {}
    
    # Always try to get the A record first (most reliable)
    try:
        a_records = dns.resolver.resolve(domain, 'A')
        results['A'] = [str(answer) for answer in a_records]
        results['IP'] = results['A'][0] if results['A'] else None
    except dns.resolver.NoAnswer:
        logger.debug(f"No A records for {domain}")
        results['A'] = []
    except Exception as e:
        logger.debug(f"Error resolving A records for {domain}: {str(e)}")
        results['A'] = []
    
    # Other record types to query (non-critical)
    record_types = ['AAAA', 'MX', 'NS', 'TXT', 'SOA']
    
    for record_type in record_types:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            results[record_type] = [str(answer) for answer in answers]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            # No records of this type is normal and expected
            results[record_type] = []
        except Exception as e:
            # Log but continue, these are not critical
            logger.debug(f"Error resolving {record_type} records for {domain}: {str(e)}")
            results[record_type] = []
    
    # If we couldn't get any DNS records, try a simple socket resolution
    if not results.get('A') and not results.get('IP'):
        try:
            ip_address = socket.gethostbyname(domain)
            results['IP'] = ip_address
        except socket.gaierror:
            results['IP'] = None
    
    return results

def check_subdomains(scan, domain):
    """
    Check for common subdomains
    
    Args:
        scan (Scan): Scan object
        domain (str): Domain to check
        
    Returns:
        list: List of discovered subdomains
    """
    common_subdomains = [
        'www', 'mail', 'ftp', 'webmail', 'login', 'admin', 'test',
        'dev', 'staging', 'api', 'app', 'beta', 'secure', 'mobile',
        'portal', 'vpn', 'cdn', 'cloud', 'media', 'static', 'support',
        'docs', 'blog', 'forum', 'shop', 'store', 'git', 'gitlab',
        'jenkins', 'jira', 'confluence', 'wiki', 'status', 'demo',
        'internal', 'intranet', 'corp', 'remote', 'stage', 'auth',
        'sso', 'account', 'accounts', 'cms', 'mta', 'mx', 'ns1', 'ns2'
    ]
    
    discovered_subdomains = []
    
    # Test some common subdomains (limited so as not to trigger alerts)
    sample_subdomains = common_subdomains[:20]  # Take just a few to avoid excessive lookups
    
    for subdomain in sample_subdomains:
        full_domain = f"{subdomain}.{domain}"
        try:
            ip = socket.gethostbyname(full_domain)
            discovered_subdomains.append({
                'subdomain': full_domain,
                'ip': ip
            })
            logger.info(f"Discovered subdomain: {full_domain} ({ip})")
        except socket.gaierror:
            continue  # Subdomain doesn't resolve
    
    # If we find quite a few subdomains, report it
    if len(discovered_subdomains) > 5:
        Vulnerability.objects.create(
            scan=scan,
            name="Multiple Subdomains Discovered",
            description=f"Multiple subdomains were discovered for {domain}. While not a vulnerability by itself, this provides additional attack surface area that should be reviewed.",
            severity="info",
            evidence=f"Discovered subdomains include: {', '.join([s['subdomain'] for s in discovered_subdomains[:5]])}",
            remediation="Ensure all subdomains follow the same security standards as the main domain.",
            confidence=0.8
        )
    
    return discovered_subdomains

def check_zone_transfer(scan, domain):
    """
    Check if the DNS server allows zone transfers
    
    Args:
        scan (Scan): Scan object
        domain (str): Domain to check
        
    Returns:
        bool: True if zone transfer is allowed
    """
    try:
        # First get the name servers
        answers = dns.resolver.resolve(domain, 'NS')
        nameservers = [str(answer) for answer in answers]
        
        if not nameservers:
            return False
        
        # Try zone transfer with first nameserver
        nameserver = nameservers[0]
        
        # Remove trailing dot if present
        if nameserver.endswith('.'):
            nameserver = nameserver[:-1]
        
        try:
            zone = dns.zone.from_xfr(dns.query.xfr(nameserver, domain, timeout=5))
            
            # If we got here, zone transfer is allowed
            Vulnerability.objects.create(
                scan=scan,
                name="DNS Zone Transfer Allowed",
                description=f"The DNS server for {domain} allows zone transfers. This can reveal all DNS records for the domain, providing valuable information to attackers.",
                severity="medium",
                evidence=f"Zone transfer succeeded from nameserver {nameserver}",
                remediation="Configure your DNS server to disallow zone transfers except to authorized servers.",
                confidence=0.9
            )
            return True
        except Exception as e:
            logger.debug(f"Zone transfer attempt failed (which is good): {str(e)}")
            return False
    except Exception as e:
        logger.debug(f"Error checking zone transfer: {str(e)}")
        return False

def check_dnssec(scan, domain):
    """
    Check if DNSSEC is enabled for the domain
    
    Args:
        scan (Scan): Scan object
        domain (str): Domain to check
        
    Returns:
        bool: True if DNSSEC is enabled
    """
    try:
        # Look for DNSKEY records (indicates DNSSEC is configured)
        answers = dns.resolver.resolve(domain, 'DNSKEY')
        if answers:
            return True
        return False
    except dns.resolver.NoAnswer:
        # No DNSKEY records found
        Vulnerability.objects.create(
            scan=scan,
            name="DNSSEC Not Enabled",
            description=f"DNSSEC is not enabled for {domain}. This means the domain is susceptible to DNS spoofing and cache poisoning attacks.",
            severity="low",
            evidence="No DNSKEY records found during DNS lookup",
            remediation="Enable DNSSEC for your domain by working with your DNS provider.",
            confidence=0.7
        )
        return False
    except Exception as e:
        logger.debug(f"Error checking DNSSEC: {str(e)}")
        return False

def check_caa_records(scan, domain):
    """
    Check if the domain has CAA (Certificate Authority Authorization) records
    
    Args:
        scan (Scan): Scan object
        domain (str): Domain to check
        
    Returns:
        bool: True if CAA records exist
    """
    try:
        answers = dns.resolver.resolve(domain, 'CAA')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        # No CAA records
        Vulnerability.objects.create(
            scan=scan,
            name="No CAA Records",
            description=f"The domain {domain} does not have CAA (Certificate Authority Authorization) records. CAA records specify which certificate authorities are allowed to issue certificates for your domain.",
            severity="info",
            evidence="No CAA records found during DNS lookup",
            remediation="Consider adding CAA records to restrict which CAs can issue certificates for your domain.",
            confidence=0.6
        )
        return False
    except Exception as e:
        logger.debug(f"Error checking CAA records: {str(e)}")
        return False

def analyze_domain(scan, domain):
    """
    Perform a comprehensive analysis of a domain's DNS setup
    
    Args:
        scan (Scan): Scan object
        domain (str): Domain to analyze
    """
    # Perform DNS lookups
    dns_records = perform_dns_lookup(domain)
    
    # Check for subdomains
    subdomains = check_subdomains(scan, domain)
    
    # Check zone transfer
    zone_transfer_allowed = check_zone_transfer(scan, domain)
    
    # Check DNSSEC
    dnssec_enabled = check_dnssec(scan, domain)
    
    # Check CAA records
    caa_records_exist = check_caa_records(scan, domain)
    
    # Return results
    return {
        'dns_records': dns_records,
        'subdomains': subdomains,
        'zone_transfer_allowed': zone_transfer_allowed,
        'dnssec_enabled': dnssec_enabled,
        'caa_records_exist': caa_records_exist
    }

def check_spf_dkim_dmarc(scan, domain):
    """
    Check if the domain has proper email authentication records (SPF, DKIM, DMARC)
    
    Args:
        scan (Scan): Scan object
        domain (str): Domain to check
    """
    # Check SPF record
    spf_found = False
    try:
        txt_records = dns.resolver.resolve(domain, 'TXT')
        for record in txt_records:
            record_text = str(record)
            if "v=spf1" in record_text:
                spf_found = True
                break
    except Exception:
        pass
    
    if not spf_found:
        Vulnerability.objects.create(
            scan=scan,
            name="Missing SPF Record",
            description=f"The domain {domain} does not have an SPF (Sender Policy Framework) record. This makes it easier for attackers to spoof emails from your domain.",
            severity="medium",
            evidence="No SPF record found in DNS TXT records",
            remediation="Add an SPF record to specify which servers are authorized to send email on behalf of your domain.",
            confidence=0.8
        )
    
    # Check DMARC record
    dmarc_found = False
    try:
        dmarc_records = dns.resolver.resolve(f"_dmarc.{domain}", 'TXT')
        for record in dmarc_records:
            record_text = str(record)
            if "v=DMARC1" in record_text:
                dmarc_found = True
                break
    except Exception:
        pass
    
    if not dmarc_found:
        Vulnerability.objects.create(
            scan=scan,
            name="Missing DMARC Record",
            description=f"The domain {domain} does not have a DMARC (Domain-based Message Authentication, Reporting, and Conformance) record. DMARC helps prevent email spoofing and phishing.",
            severity="medium",
            evidence="No DMARC record found at _dmarc.{domain}",
            remediation="Add a DMARC record to specify how receiving mail servers should handle emails that fail SPF or DKIM verification.",
            confidence=0.8
        )
    
    return {
        'spf_found': spf_found,
        'dmarc_found': dmarc_found
    }