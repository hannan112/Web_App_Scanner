import logging

logger = logging.getLogger(__name__)

class BaseAnalyzer:
    """Base class for all passive analyzers"""
    
    def __init__(self, scan, config):
        """
        Initialize the analyzer
        
        Args:
            scan (Scan): The scan model object
            config (ScanConfiguration): The scan configuration
        """
        self.scan = scan
        self.config = config
        self.name = self.__class__.__name__
        self.findings = []
    
    def analyze(self):
        """
        Run the analysis
        
        This method should be implemented by subclasses
        
        Returns:
            dict: Analysis results
        """
        raise NotImplementedError("Subclasses must implement analyze()")
    
    def add_finding(self, finding):
        """
        Add a finding
        
        Args:
            finding (dict): Finding information
        """
        # Ensure required fields are present
        required_fields = ['name', 'description', 'severity']
        for field in required_fields:
            if field not in finding:
                logger.warning(f"Finding missing required field: {field}")
                return

        # Validate severity
        valid_severities = ['critical', 'high', 'medium', 'low', 'info']
        if finding['severity'] not in valid_severities:
            logger.warning(f"Finding has invalid severity: {finding['severity']}")
            finding['severity'] = 'info'  # Default to info

        # Set default values for optional fields
        if 'confidence' not in finding:
            finding['confidence'] = 0.8  # Default confidence
        if 'source' not in finding:
            finding['source'] = self.name

        # Add to findings list
        self.findings.append(finding)
        logger.info(f"Added finding: {finding['name']} ({finding['severity']}, confidence: {finding['confidence']})")
    
    def add_error_finding(self, name, error_message):
        """
        Add an error finding
        
        Args:
            name (str): Finding name
            error_message (str): Error message
        """
        self.add_finding({
            'name': name,
            'description': f"Error during analysis: {error_message}",
            'severity': 'info',
            'confidence': 1.0,
            'source': f"{self.name}_error"
        })
        logger.error(f"{name}: {error_message}")
    
    def get_findings(self):
        """
        Get all findings from this analyzer
        
        Returns:
            list: List of findings
        """
        return self.findings