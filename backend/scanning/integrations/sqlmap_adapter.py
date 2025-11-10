# scanning/integrations/sqlmap_adapter.py

import json
import logging
import os
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SQLMapAdapter:
    """Adapter for SQLMap SQL injection testing tool"""

    def __init__(self, config=None):
        self.config = config or {}
        # Try to get path from config, otherwise use default
        default_path = self.config.get("sqlmap_path")
        if not default_path:
            # Priority 1: Try global sqlmap installation
            if self._is_global_sqlmap_available():
                self.sqlmap_path = "sqlmap"
            # Priority 2: Try local project sqlmap
            else:
                import os
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                sqlmap_path = os.path.join(project_root, "tools", "sqlmap", "sqlmap.py")
                if os.path.exists(sqlmap_path):
                    self.sqlmap_path = f"python3 {sqlmap_path}"
                else:
                    self.sqlmap_path = "sqlmap"  # Fallback to system sqlmap
        else:
            self.sqlmap_path = default_path
        self.min_confidence = float(self.config.get("min_confidence", 0.5))  # Lower threshold for better detection
        self.timeout = int(self.config.get("timeout", 300))  # Use full 300 seconds (5 minutes) from config
        self.risk_level = int(self.config.get("risk_level", 2))  # Higher risk level for better detection
        self.level = int(self.config.get("level", 2))  # Higher level for more thorough testing
        
    def _is_global_sqlmap_available(self) -> bool:
        """Check if global sqlmap is available in PATH"""
        try:
            result = subprocess.run(
                ["which", "sqlmap"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
        
    def is_available(self) -> Dict[str, Any]:
        """
        Check if SQLMap is available for use
        
        Returns:
            Dict with availability status and error info
        """
        try:
            # Handle both command and script paths
            if self.sqlmap_path.startswith("python3"):
                # It's a Python script
                cmd = self.sqlmap_path.split() + ["--version"]
            else:
                # It's a command
                cmd = [self.sqlmap_path, "--version"]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.decode().strip()
                return {
                    "available": True,
                    "version": version,
                    "tool": "sqlmap"
                }
            else:
                return {
                    "available": False,
                    "error": f"SQLMap version check failed: {result.stderr.decode()}",
                    "tool": "sqlmap"
                }
        except subprocess.TimeoutExpired:
            return {
                "available": False,
                "error": "SQLMap version check timed out",
                "tool": "sqlmap"
            }
        except FileNotFoundError:
            return {
                "available": False,
                "error": "SQLMap not found in PATH. Install from: https://github.com/sqlmapproject/sqlmap",
                "tool": "sqlmap"
            }
        except Exception as e:
            return {
                "available": False,
                "error": f"Error checking SQLMap: {str(e)}",
                "tool": "sqlmap"
            }

    def scan_url(self, url: str, forms: List[Dict] = None) -> List[Dict[str, Any]]:
        """
        Scan a URL for SQL injection vulnerabilities using SQLMap
        
        Args:
            url (str): URL to scan
            forms (List[Dict], optional): Forms to test for SQL injection
            
        Returns:
            List[Dict]: List of SQL injection findings
        """
        findings = []
        
        # Check if SQLMap is available
        availability = self.is_available()
        if not availability["available"]:
            return [{
                "name": "SQLMap Not Available",
                "description": f"SQLMap is not available: {availability.get('error', 'Unknown error')}",
                "severity": "info",
                "url": url,
                "confidence": 1.0,
                "source": "sqlmap",
                "remediation": "Install SQLMap: pip install sqlmap or download from GitHub"
            }]
        
        try:
            # Test URL for SQL injection
            url_findings = self._test_url_sqli(url)
            findings.extend(url_findings)
            
            # Test forms for SQL injection
            if forms:
                for form in forms:
                    form_findings = self._test_form_sqli(url, form)
                    findings.extend(form_findings)
            
        except Exception as e:
            logger.error(f"Error in SQLMap scan: {str(e)}")
            findings.append({
                "name": "SQLMap Scan Error",
                "description": f"Error during SQLMap scan: {str(e)}",
                "severity": "info",
                "url": url,
                "confidence": 1.0,
                "source": "sqlmap"
            })
        
        return findings

    def scan_discovered_urls(self, discovered_data: Dict) -> List[Dict[str, Any]]:
        """
        Scan discovered URLs and forms for SQL injection vulnerabilities
        
        Args:
            discovered_data (Dict): Discovery results containing URLs, forms, and endpoints
            
        Returns:
            List[Dict]: List of SQL injection findings
        """
        all_findings = []
        
        # Check if SQLMap is available
        availability = self.is_available()
        if not availability["available"]:
            return [{
                "name": "SQLMap Not Available",
                "description": f"SQLMap is not available: {availability.get('error', 'Unknown error')}",
                "severity": "info",
                "url": "discovered_urls",
                "confidence": 1.0,
                "source": "sqlmap",
                "remediation": "Install SQLMap: pip install sqlmap or download from GitHub"
            }]
        
        try:
            # Extract URLs from discovery results
            urls_to_test = self._extract_urls_from_discovery(discovered_data)
            forms_to_test = self._extract_forms_from_discovery(discovered_data)
            
            logger.info(f"SQLMap will test {len(urls_to_test)} URLs and {len(forms_to_test)} forms")
            
            # Test each URL
            for i, url in enumerate(urls_to_test):
                logger.info(f"Testing URL {i+1}/{len(urls_to_test)}: {url}")
                
                # Find forms associated with this URL
                url_forms = [form for form in forms_to_test if form.get('url') == url]
                
                # Test the URL
                findings = self.scan_url(url, url_forms)
                all_findings.extend(findings)
                
                # Add a small delay to avoid overwhelming the target
                time.sleep(1)
            
            # Test standalone forms
            for form in forms_to_test:
                if not form.get('url'):
                    # Form without specific URL, test with base URL
                    base_url = discovered_data.get('target_url', '')
                    if base_url:
                        findings = self.scan_url(base_url, [form])
                        all_findings.extend(findings)
            
            logger.info(f"SQLMap testing completed. Found {len(all_findings)} total findings")
            
        except Exception as e:
            logger.error(f"Error in SQLMap discovered URLs scan: {str(e)}")
            all_findings.append({
                "name": "SQLMap Discovery Scan Error",
                "description": f"Error during SQLMap discovery scan: {str(e)}",
                "severity": "info",
                "url": "discovered_urls",
                "confidence": 1.0,
                "source": "sqlmap"
            })
        
        return all_findings

    def _extract_urls_from_discovery(self, discovered_data: Dict) -> List[str]:
        """Extract URLs from discovery results"""
        urls = []
        
        # Extract from various discovery sources
        url_sources = [
            'urls_discovered',
            'all_discovered_urls', 
            'endpoints_discovered',
            'api_endpoints',
            'js_endpoints',
            'directories',
            'wayback_urls'
        ]
        
        for source in url_sources:
            if source in discovered_data:
                data = discovered_data[source]
                if isinstance(data, list):
                    urls.extend(data)
                elif isinstance(data, dict):
                    # Handle nested structures
                    if 'urls' in data:
                        urls.extend(data['urls'])
                    elif 'endpoints' in data:
                        urls.extend(data['endpoints'])
                    elif 'directories' in data:
                        for item in data['directories']:
                            if isinstance(item, dict) and 'url' in item:
                                urls.append(item['url'])
                            elif isinstance(item, str):
                                urls.append(item)
        
        # Remove duplicates and filter valid URLs
        unique_urls = list(set(urls))
        valid_urls = [url for url in unique_urls if url and isinstance(url, str) and url.startswith(('http://', 'https://'))]
        
        # Filter out static resources and documentation pages
        filtered_urls = self._filter_sqlmap_urls(valid_urls)
        
        # Prioritize URLs with parameters (more likely to be vulnerable)
        urls_with_params = [url for url in filtered_urls if '?' in url]
        urls_without_params = [url for url in filtered_urls if '?' not in url]
        
        # Return prioritized list (URLs with parameters first)
        return urls_with_params + urls_without_params

    def _extract_forms_from_discovery(self, discovered_data: Dict) -> List[Dict]:
        """Extract forms from discovery results"""
        forms = []
        
        # Extract from forms_discovered
        if 'forms_discovered' in discovered_data:
            forms.extend(discovered_data['forms_discovered'])
        
        # Extract from enhanced discovery results
        if 'enhanced_discovery' in discovered_data:
            enhanced = discovered_data['enhanced_discovery']
            if 'forms_discovered' in enhanced:
                forms.extend(enhanced['forms_discovered'])
        
        # Filter valid forms
        valid_forms = []
        for form in forms:
            if isinstance(form, dict) and form.get('data'):
                valid_forms.append(form)
        
        return valid_forms

    def _filter_sqlmap_urls(self, urls: List[str]) -> List[str]:
        """Filter URLs to exclude static resources and documentation pages"""
        filtered_urls = []
        
        # Patterns to exclude (static resources, documentation, etc.)
        exclude_patterns = [
            '/static/', '/css/', '/js/', '/images/', '/img/', '/assets/',
            '/docs/', '/documentation/', '/api/docs/', '/swagger/',
            '/favicon.ico', '/robots.txt', '/sitemap.xml',
            '/admin/docs/', '/redoc/', '/openapi.json'
        ]
        
        # File extensions to exclude
        exclude_extensions = [
            '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
            '.pdf', '.txt', '.xml', '.json', '.woff', '.woff2', '.ttf'
        ]
        
        for url in urls:
            # Skip URLs with exclude patterns
            if any(pattern in url.lower() for pattern in exclude_patterns):
                continue
                
            # Skip URLs with static file extensions
            if any(url.lower().endswith(ext) for ext in exclude_extensions):
                continue
                
            # Skip URLs that are clearly static or documentation
            if any(keyword in url.lower() for keyword in ['/static', '/docs', '/api/docs', '/swagger']):
                continue
                
            filtered_urls.append(url)
        
        return filtered_urls

    def _test_url_sqli(self, url: str) -> List[Dict[str, Any]]:
        """Test URL parameters for SQL injection"""
        findings = []
        
        try:
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
                output_file = temp_file.name
            
            # Build SQLMap command for URL testing
            if self.sqlmap_path.startswith("python3"):
                # It's a Python script (local installation)
                cmd = self.sqlmap_path.split() + [
                    "-u", url,
                    "--batch",  # Non-interactive mode
                    "--risk", str(self.risk_level),
                    "--level", str(self.level),
                    "--timeout", "10",  # 10 seconds per HTTP request (allows time-based detection)
                    "--retries", "2",  # Retry twice on failure
                    "--threads", "1",
                    "--delay", "0",  # No delay for faster scanning
                    "--technique=BEUSTQ",  # All techniques for comprehensive testing
                    "--no-cast",  # Skip type casting for speed
                    "-v", "1",  # Verbose level 1 for better output parsing
                    "--output-dir", tempfile.gettempdir()
                ]
            else:
                # It's a global command (system installation)
                cmd = [
                    self.sqlmap_path,
                    "-u", url,
                    "--batch",  # Non-interactive mode
                    "--risk", str(self.risk_level),
                    "--level", str(self.level),
                    "--timeout", "10",  # 10 seconds per HTTP request (allows time-based detection)
                    "--retries", "2",  # Retry twice on failure
                    "--threads", "1",
                    "--delay", "0",  # No delay for faster scanning
                    "--technique=BEUSTQ",  # All techniques for comprehensive testing
                    "--no-cast",  # Skip type casting for speed
                    "-v", "1",  # Verbose level 1 for better output parsing
                    "--output-dir", tempfile.gettempdir()
                ]
            
            # Add JSON output if supported
            if self._supports_json_output():
                cmd.extend(["--output-format", "json"])
                cmd.extend(["--output-file", output_file])
            
            logger.info(f"Running SQLMap on URL: {url}")
            logger.debug(f"SQLMap command: {' '.join(cmd)}")
            
            # Run SQLMap with timeout
            start_time = time.time()
            try:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=self.timeout
                )
                elapsed_time = time.time() - start_time
                logger.info(f"SQLMap completed in {elapsed_time:.1f}s for {url}")
            except subprocess.TimeoutExpired:
                logger.warning(f"SQLMap scan timed out after {self.timeout}s for {url}")
                return [{
                    "name": "SQLMap Timeout",
                    "description": f"SQLMap scan timed out after {self.timeout} seconds. This may indicate a slow or unresponsive target.",
                    "severity": "info",
                    "url": url,
                    "confidence": 0.3,
                    "source": "sqlmap",
                    "remediation": "Consider increasing timeout or testing with a faster target"
                }]

            # Parse results - ALWAYS parse output regardless of return code
            output_text = result.stdout.decode()
            stderr_text = result.stderr.decode()
            combined_output = output_text + " " + stderr_text

            # Log full output for debugging
            logger.debug(f"SQLMap return code: {result.returncode}")
            logger.debug(f"SQLMap output (first 500 chars): {output_text[:500]}")

            # Check for SQL injection indicators in output
            output_lower = combined_output.lower()
            injection_indicators = [
                "sql injection", "vulnerable", "exploitable",
                "boolean-based blind", "time-based blind", "error-based",
                "union query", "stacked queries", "injectable"
            ]

            has_injection = any(indicator in output_lower for indicator in injection_indicators)

            # Always parse output - don't rely on return code
            parsed_findings = self._parse_sqlmap_output(output_text, url)
            findings.extend(parsed_findings)

            # Log if we found vulnerabilities
            if parsed_findings:
                logger.info(f"✓ SQLMap found {len(parsed_findings)} SQL injection vulnerabilities in {url}")
            elif has_injection:
                logger.warning(f"SQLMap output contains injection keywords but parser found nothing for {url}")
            else:
                logger.info(f"✗ SQLMap found no SQL injection vulnerabilities in {url}")
            
            # Clean up temp files
            if os.path.exists(output_file):
                os.unlink(output_file)
            if os.path.exists(output_file.replace('.json', '.log')):
                os.unlink(output_file.replace('.json', '.log'))
                
        except subprocess.TimeoutExpired:
            logger.warning(f"SQLMap scan timed out for {url}")
            findings.append({
                "name": "SQLMap Timeout",
                "description": f"SQLMap scan timed out after {self.timeout} seconds",
                "severity": "info",
                "url": url,
                "confidence": 0.5,
                "source": "sqlmap"
            })
        except Exception as e:
            logger.error(f"Error in SQLMap URL test: {str(e)}")
        
        return findings

    def _test_form_sqli(self, url: str, form: Dict) -> List[Dict[str, Any]]:
        """Test form for SQL injection"""
        findings = []
        
        try:
            form_data = form.get("data", {})
            if not form_data:
                return findings
            
            # Build form data string for SQLMap
            data_pairs = []
            for key, value in form_data.items():
                data_pairs.append(f"{key}={value}")
            data_string = "&".join(data_pairs)
            
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
                output_file = temp_file.name
            
            # Build SQLMap command for form testing
            if self.sqlmap_path.startswith("python3"):
                # It's a Python script (local installation)
                cmd = self.sqlmap_path.split() + [
                    "-u", url,
                    "--data", data_string,
                    "--batch",
                    "--risk", str(self.risk_level),
                    "--level", str(self.level),
                    "--timeout", "10",  # 10 seconds per HTTP request
                    "--retries", "2",  # Retry twice on failure
                    "--threads", "1",
                    "--delay", "0",  # No delay for faster scanning
                    "--technique=BEUSTQ",  # All techniques for comprehensive testing
                    "--no-cast",  # Skip type casting for speed
                    "-v", "1",  # Verbose level 1
                    "--output-dir", tempfile.gettempdir()
                ]
            else:
                # It's a global command (system installation)
                cmd = [
                    self.sqlmap_path,
                    "-u", url,
                    "--data", data_string,
                    "--batch",
                    "--risk", str(self.risk_level),
                    "--level", str(self.level),
                    "--timeout", "10",  # 10 seconds per HTTP request
                    "--retries", "2",  # Retry twice on failure
                    "--threads", "1",
                    "--delay", "0",  # No delay for faster scanning
                    "--technique=BEUSTQ",  # All techniques for comprehensive testing
                    "--no-cast",  # Skip type casting for speed
                    "-v", "1",  # Verbose level 1
                    "--output-dir", tempfile.gettempdir()
                ]
            
            if form.get("method", "GET").upper() == "POST":
                cmd.extend(["--method", "POST"])
            
            logger.info(f"Testing form for SQL injection: {url}")
            
            # Run SQLMap
            start_time = time.time()
            try:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=self.timeout
                )
                elapsed_time = time.time() - start_time
                logger.info(f"SQLMap form test completed in {elapsed_time:.1f}s for {url}")
            except subprocess.TimeoutExpired:
                logger.warning(f"SQLMap form test timed out after {self.timeout}s for {url}")
                return [{
                    "name": "SQLMap Form Timeout",
                    "description": f"SQLMap form test timed out after {self.timeout} seconds. This may indicate a slow or unresponsive target.",
                    "severity": "info",
                    "url": url,
                    "confidence": 0.3,
                    "source": "sqlmap",
                    "remediation": "Consider increasing timeout or testing with a faster target"
                }]

            # Parse results - ALWAYS parse output regardless of return code
            output_text = result.stdout.decode()
            stderr_text = result.stderr.decode()
            combined_output = output_text + " " + stderr_text

            # Log full output for debugging
            logger.debug(f"SQLMap form return code: {result.returncode}")
            logger.debug(f"SQLMap form output (first 500 chars): {output_text[:500]}")

            # Always parse output - don't rely on return code
            parsed_findings = self._parse_sqlmap_output(output_text, url)
            findings.extend(parsed_findings)

            # Log results
            if parsed_findings:
                logger.info(f"✓ SQLMap found {len(parsed_findings)} SQL injection vulnerabilities in form at {url}")
            else:
                logger.info(f"✗ SQLMap found no SQL injection vulnerabilities in form at {url}")
            
            # Clean up
            if os.path.exists(output_file):
                os.unlink(output_file)
                
        except Exception as e:
            logger.error(f"Error in SQLMap form test: {str(e)}")
        
        return findings

    def _parse_sqlmap_output(self, output: str, url: str) -> List[Dict[str, Any]]:
        """Parse SQLMap output for vulnerabilities - Enhanced detection"""
        findings = []

        output_lower = output.lower()

        # Enhanced detection - check for multiple indicators
        vulnerability_indicators = [
            "parameter appears to be",  # SQLMap uses this phrase when it finds vulnerability
            "payload:",  # SQLMap shows payload when injection works
            "is vulnerable",
            "might be injectable",
            "injectable",
            "sql injection",
            "injection"
        ]

        has_vulnerability = any(indicator in output_lower for indicator in vulnerability_indicators)

        # Additional check: SQLMap lists vulnerable parameters
        if "parameter:" in output_lower and ("vulnerable" in output_lower or "injectable" in output_lower):
            has_vulnerability = True

        if has_vulnerability:
            # Determine injection type (can be multiple)
            injection_types = []
            if "boolean-based blind" in output_lower:
                injection_types.append("Boolean-based Blind")
            if "time-based blind" in output_lower:
                injection_types.append("Time-based Blind")
            if "error-based" in output_lower:
                injection_types.append("Error-based")
            if "union query" in output_lower or "union-based" in output_lower:
                injection_types.append("Union Query")
            if "stacked queries" in output_lower:
                injection_types.append("Stacked Queries")

            # Default if no specific type detected
            if not injection_types:
                injection_types = ["SQL Injection"]

            # Extract parameter name if possible
            parameter = "unknown"
            if "parameter:" in output_lower:
                try:
                    param_line = [line for line in output.split('\n') if 'parameter:' in line.lower()]
                    if param_line:
                        parameter = param_line[0].split('parameter:')[1].strip().split()[0]
                except:
                    pass

            # Extract database information
            database = "Unknown"
            if "mysql" in output_lower:
                database = "MySQL"
            elif "postgresql" in output_lower or "postgres" in output_lower:
                database = "PostgreSQL"
            elif "sqlite" in output_lower:
                database = "SQLite"
            elif "mssql" in output_lower or "sql server" in output_lower or "microsoft" in output_lower:
                database = "Microsoft SQL Server"
            elif "oracle" in output_lower:
                database = "Oracle"

            # Create a finding for each injection type detected
            for injection_type in injection_types:
                # Determine severity based on injection type
                severity = "high"
                if "blind" in injection_type.lower():
                    severity = "high"  # Blind injections are still serious
                elif "error-based" in injection_type.lower() or "union" in injection_type.lower():
                    severity = "critical"  # Direct data extraction

                finding = {
                    "name": f"SQL Injection - {injection_type}",
                    "description": f"SQLMap detected {injection_type} SQL injection vulnerability in parameter '{parameter}'. Target database: {database}. This vulnerability allows an attacker to manipulate SQL queries and potentially read, modify, or delete database data.",
                    "severity": severity,
                    "url": url,
                    "parameter": parameter,
                    "confidence": 0.9,
                    "source": "sqlmap",
                    "evidence": f"SQLMap detected injectable parameter. Output excerpt: {output[:500]}...",
                    "remediation": "Use parameterized queries (prepared statements) to prevent SQL injection. Never concatenate user input directly into SQL queries. Implement input validation and use ORM frameworks where possible."
                }

                findings.append(finding)

        return findings

    def _supports_json_output(self) -> bool:
        """Check if SQLMap supports JSON output"""
        try:
            result = subprocess.run(
                [self.sqlmap_path, "--help"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            return "--output-format" in result.stdout.decode()
        except:
            return False

    def get_supported_databases(self) -> List[str]:
        """Get list of supported databases"""
        return [
            "MySQL", "PostgreSQL", "SQLite", "Microsoft SQL Server", 
            "Oracle", "IBM DB2", "Firebird", "Sybase", "SAP MaxDB"
        ]

    def get_injection_techniques(self) -> List[str]:
        """Get list of supported injection techniques"""
        return [
            "Boolean-based Blind",
            "Time-based Blind", 
            "Error-based",
            "Union Query",
            "Stacked Queries",
            "Inline Queries"
        ]
