import logging
from urllib.parse import urlparse
from scanning.passive.analyzers.base_analyzer import BaseAnalyzer
from scanning.passive.analyzers.domain_analyzer import perform_dns_lookup, check_subdomains

logger = logging.getLogger(__name__)

class DnsAnalyzer(BaseAnalyzer):
    """Analyzer for DNS records"""
    
    def __init__(self, scan, config, target_url):
        """
        Initialize the DNS analyzer
        
        Args:
            scan (Scan): The scan model object
            config (ScanConfiguration): The scan configuration
            target_url (str): The target URL
        """
        super().__init__(scan, config)
        self.target_url = target_url
        parsed_url = urlparse(target_url)
        self.domain = parsed_url.netloc
    
    def analyze(self):
        """
        Analyze DNS records
        
        Returns:
            dict: DNS analysis results
        """
        logger.info(f"Starting DNS analysis for {self.domain}")
        results = {'dns_records': {}, 'subdomains': []}
        
        try:
            # Perform DNS lookup
            dns_records = perform_dns_lookup(self.domain)
            results['dns_records'] = dns_records
            
            # Check for subdomains
            try:
                subdomains = check_subdomains(self.scan, self.domain)
                if subdomains:
                    results['subdomains'] = subdomains
            except Exception as subnet_err:
                logger.warning(f"Error checking subdomains: {str(subnet_err)}")
            
            logger.info(f"DNS analysis completed for {self.domain}")
            
        except Exception as e:
            logger.error(f"Error in DNS analysis: {str(e)}")
            self.add_error_finding("DNS Analysis Error", str(e))
        
        return results