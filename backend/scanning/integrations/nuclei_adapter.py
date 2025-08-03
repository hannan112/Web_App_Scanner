# scanning/integrations/nuclei_adapter.py
import logging
import subprocess
import json
import tempfile
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class NucleiAdapter:
    """Adapter for Nuclei vulnerability scanner"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.nuclei_path = self.config.get('nuclei_path', 'nuclei')
        self.templates_path = self.config.get('nuclei_templates_path', '')
        self.severity = self.config.get('severity', 'critical,high,medium,low')
        self.min_confidence = float(self.config.get('min_confidence', 0.7))
    
    def scan_url(self, url: str) -> List[Dict[str, Any]]:
        """
        Scan a URL using Nuclei with passive templates
        
        Args:
            url (str): URL to scan
            
        Returns:
            List[Dict]: List of findings
        """
        findings = []
        
        try:
            # Check if nuclei is installed
            if not self._is_nuclei_installed():
                return [{
                    'name': 'Nuclei Not Installed',
                    'description': 'Could not run Nuclei scanner. Please install it from: https://github.com/projectdiscovery/nuclei',
                    'severity': 'info',
                    'url': url,
                    'confidence': 1.0
                }]
            
            # Create temp file for JSON output
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
                output_file = temp_file.name
            
            try:
                # Build command with passive templates only
                cmd = [
                    self.nuclei_path,
                    '-u', url,
                    '-s', self.severity,
                    '-j',  # JSON output
                    '-o', output_file,
                    '-timeout', '5',  # 5 second timeout for passive checks
                    '-no-interactsh',  # No OOB testing
                    '-passive',  # Only passive templates
                ]
                
                # Add templates path if specified
                if self.templates_path:
                    passive_templates = os.path.join(self.templates_path, 'ssl,technologies,misconfiguration')
                    cmd.extend(['-t', passive_templates])
                
                # Run Nuclei
                logger.info(f"Running Nuclei: {' '.join(cmd)}")
                subprocess.run(cmd, check=True, capture_output=True)
                
                # Read results
                with open(output_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            try:
                                result = json.loads(line)
                                finding = self._convert_result(result, url)
                                if finding and finding.get('confidence', 0) >= self.min_confidence:
                                    findings.append(finding)
                            except json.JSONDecodeError:
                                logger.warning(f"Invalid JSON in Nuclei output: {line}")
            
            finally:
                # Clean up temp file
                if os.path.exists(output_file):
                    os.unlink(output_file)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Nuclei execution error: {e.stderr.decode() if e.stderr else str(e)}")
            findings.append({
                'name': 'Nuclei Execution Error',
                'description': f'Error running Nuclei: {e.stderr.decode() if e.stderr else str(e)}',
                'severity': 'info',
                'url': url,
                'confidence': 1.0
            })
        except Exception as e:
            logger.error(f"Error using Nuclei: {str(e)}")
            findings.append({
                'name': 'Nuclei Error',
                'description': f'Error using Nuclei: {str(e)}',
                'severity': 'info',
                'url': url,
                'confidence': 1.0
            })
        
        return findings
    
    def _is_nuclei_installed(self) -> bool:
        """Check if Nuclei is installed"""
        try:
            result = subprocess.run(
                [self.nuclei_path, '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return result.returncode == 0
        except Exception:
            return False

    def _run_nuclei_passive(self):
        """
        Run Nuclei passive templates if available
        """
        logger.info(f"Checking for Nuclei passive templates for {self.target_url}")
    
        try:
            # Check if Nuclei is available
            nuclei_available = False
            
            # If self.available_tools is defined, use it
            if hasattr(self, 'available_tools') and isinstance(self.available_tools, dict):
                nuclei_available = self.available_tools.get('nuclei', {}).get('available', False)
            else:
                # Otherwise, check for nuclei directly
                try:
                    import subprocess
                    result = subprocess.run(['nuclei', '-version'], 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE,
                                          timeout=5)
                    nuclei_available = result.returncode == 0
                except (FileNotFoundError, subprocess.SubprocessError):
                    nuclei_available = False
            
            # Check if nuclei is required by config
            nuclei_required = False
            if hasattr(self.config, 'use_nuclei'):
                nuclei_required = self.config.use_nuclei
            
            if not nuclei_available:
                if nuclei_required:
                    logger.warning("Nuclei was requested but is not available")
                    self._add_finding({
                        'name': 'Nuclei Not Available',
                        'description': 'Nuclei scanner was requested in the configuration but is not available on the system.',
                        'severity': 'info',
                        'confidence': 1.0,
                        'remediation': 'Install Nuclei to use this feature: https://github.com/projectdiscovery/nuclei'
                    })
                self.update_progress(95, "Nuclei scan skipped - tool not available")
                return
    
            # Import and use Nuclei adapter
            from scanning.integrations.nuclei_adapter import NucleiAdapter
    
            # Get Nuclei configuration
            nuclei_config = {}
            if hasattr(self.config, 'nuclei_config'):
                nuclei_config = self.config.nuclei_config
    
            # Create adapter instance
            adapter = NucleiAdapter(config=nuclei_config)
    
            # Run passive scan
            findings = adapter.scan_url(self.target_url)
    
            if findings:
                logger.info(f"Nuclei found {len(findings)} issues")
                for finding in findings:
                    finding['source'] = 'nuclei'
                    self._add_finding(finding)
    
            # Update progress
            self.update_progress(95, "Nuclei scan completed")
    
        except Exception as e:
            logger.error(f"Error in Nuclei scan: {str(e)}")
            self._add_error_finding("Nuclei Scan Error", str(e))
            self.update_progress(95, "Nuclei scan failed")

    def _convert_result(self, result: Dict, url: str) -> Dict[str, Any]:
        """Convert Nuclei result to finding format"""
        # Skip if there's a matcher-status (means it requires active testing)
        if result.get('matcher-status'):
            return None
            
        # Get info from result
        info = result.get('info', {})
        
        # Map severities
        severity_map = {
            'critical': 'critical',
            'high': 'high',
            'medium': 'medium',
            'low': 'low',
            'info': 'info',
            'unknown': 'info'
        }
        
        # Compute confidence based on template metadata
        template_id = info.get('template-id', '')
        is_cve = template_id.startswith('CVE-')
        confidence = 0.9 if is_cve else 0.7  # Higher confidence for CVEs
        
        # Create finding
        finding = {
            'name': info.get('name', 'Unknown Issue'),
            'description': info.get('description', ''),
            'severity': severity_map.get(info.get('severity', 'unknown'), 'info'),
            'url': result.get('matched-at', url),
            'evidence': result.get('matcher-name', ''),
            'confidence': confidence,
            'remediation': info.get('remedy', '')
        }
        
        return finding