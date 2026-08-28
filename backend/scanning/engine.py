"""
Passive Scanning Engine

Orchestrates passive security scanning operations.
"""

import logging
from django.utils import timezone
from scanning.passive.scanner import PassiveScanner

logger = logging.getLogger(__name__)


class PassiveScanningEngine:
    """Passive scanning engine - no active testing"""

    def __init__(self, scan_id: int):
        self.scan_id = scan_id
        self.scan = None
        self.target_url = None
        self.configuration = None

    def start(self):
        """Start passive scanning"""
        try:
            # Lazy import to avoid circular dependencies
            from scanning.models.scan import Scan
            
            # Load scan details
            self.scan = Scan.objects.get(id=self.scan_id)
            self.target_url = self.scan.target_url
            self.configuration = self.scan.configuration

            # Validate scan type
            if self.configuration.scan_type != 'passive':
                raise ValueError(f"Engine only supports passive scans, got: {self.configuration.scan_type}")

            # Run passive scan
            self._run_passive_scan()
            
            # Return True to indicate success
            return True

        except Exception as e:
            logger.exception(f"Passive scan engine failed: {e}")
            self._fail_scan(str(e))
            # Return False to indicate failure
            return False

    def _run_passive_scan(self):
        """Execute passive scanning"""
        try:
            self.scan.status = 'running'
            self.scan.start_time = timezone.now()
            self.scan.progress = 0.0
            self.scan.save()

            # Create and run passive scanner with progress callback
            scanner = PassiveScanner(
                self.scan_id,
                self.target_url,
                self.configuration
            )
            
            # Set progress callback for real-time updates
            scanner.set_progress_callback(self._update_progress)

            results = scanner.run_scan()

            # Save results and complete scan
            self._complete_scan(results)

        except Exception as e:
            logger.exception(f"Passive scan failed: {e}")
            self._fail_scan(str(e))

    def _update_progress(self, percent: float, message: str):
        """Update scan progress and log message"""
        try:
            # Lazy import to avoid circular dependencies
            from scanning.models.scan import ScanLog
            
            # Refresh scan object to avoid stale data
            self.scan.refresh_from_db()
            
            # Ensure progress only moves forward (never decreases)
            current_progress = self.scan.progress
            if percent < current_progress:
                logger.warning(f"Progress would decrease from {current_progress}% to {percent}%, keeping current progress")
                percent = current_progress
            
            # Update progress
            self.scan.progress = percent
            self.scan.save(update_fields=['progress', 'updated_at'])
            
            # Create log entry
            ScanLog.objects.create(
                scan=self.scan,
                level='INFO',
                message=f"{percent:.1f}% - {message}"
            )
            
            logger.info(f"Scan {self.scan_id}: {percent:.1f}% - {message}")
            
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")
            # Don't fail the entire scan if progress update fails
            # Just log the error and continue

    def _complete_scan(self, results):
        try:
            # Lazy import to avoid circular dependencies
            from scanning.models.scan import PassiveReconResult, ScanLog
            from scanning.models.vulnerability import Vulnerability
            
            # Reload the scan object to ensure we have the latest data
            self.scan.refresh_from_db()
            
            # Save comprehensive results to PassiveReconResult
            recon_result, created = PassiveReconResult.objects.get_or_create(
                scan=self.scan,
                defaults={
                    'dns_records': results.get('dns_analysis', {}),
                    'server_info': results.get('target_info', {}),
                    'technologies': results.get('technology_detection', {}),
                    'response_headers': results.get('security_headers', {}),
                    'enhanced_discovery': results.get('enhanced_discovery', {}),
                }
            )
            
            if not created:
                # Update existing result with all comprehensive data
                recon_result.dns_records = results.get('dns_analysis', {})
                recon_result.server_info = results.get('target_info', {})
                recon_result.technologies = results.get('technology_detection', {})
                recon_result.response_headers = results.get('security_headers', {})
                recon_result.enhanced_discovery = results.get('enhanced_discovery', {})
                recon_result.save()
            
            # Save vulnerabilities to the Vulnerability model with deduplication
            vulnerabilities = results.get('vulnerabilities', [])
            for vuln_data in vulnerabilities:
                try:
                    vuln, created = Vulnerability.objects.get_or_create(
                        scan=self.scan,
                        name=vuln_data.get('type', 'Unknown Vulnerability'),
                        url=self.target_url,  # Use target URL as default
                        defaults={
                            'description': vuln_data.get('description', 'No description available'),
                            'severity': vuln_data.get('severity', 'low'),
                            'parameter': vuln_data.get('parameter', ''),
                            'evidence': str(vuln_data.get('details', '')),
                            'confidence': vuln_data.get('confidence', 1.0),
                            'remediation': vuln_data.get('remediation', '')
                        }
                    )
                    if not created:
                        logger.debug(f"Vulnerability already exists: {vuln.name} for {vuln.url}")
                except Exception as e:
                    logger.error(f"Failed to save vulnerability: {e}")
                    # Continue with other vulnerabilities
            
            # Update scan status and completion time
            self.scan.status = 'completed'
            self.scan.end_time = timezone.now()
            self.scan.progress = 100.0
            self.scan.save()
            
            # Log completion with results summary
            results_summary = {
                'dns_records': bool(results.get('dns_analysis')),
                'ssl_analysis': bool(results.get('ssl_analysis')),
                'technologies': bool(results.get('technology_detection')),
                'security_headers': bool(results.get('security_headers')),
                'content_analysis': bool(results.get('content_analysis')),
                'cookie_analysis': bool(results.get('cookie_analysis')),
                'vulnerabilities': len(vulnerabilities),
                'total_findings': len(vulnerabilities)
            }
            
            ScanLog.objects.create(
                scan=self.scan,
                level='INFO',
                message=f"Scan completed successfully with results saved: {results_summary}"
            )
            
            logger.info(f"Scan {self.scan_id} completed successfully with comprehensive results saved")
            logger.info(f"Results summary: {results_summary}")

        except Exception as e:
            logger.exception(f"Failed saving results: {e}")
            self._fail_scan(str(e))

    def _fail_scan(self, error_message: str):
        if not self.scan:
            return
        self.scan.status = 'failed'
        self.scan.error_message = error_message
        self.scan.end_time = timezone.now()
        self.scan.save()
        
        # Log the error
        try:
            from scanning.models.scan import ScanLog
            ScanLog.objects.create(
                scan=self.scan,
                level='ERROR',
                message=f"Scan failed: {error_message}"
            )
        except Exception as e:
            logger.error(f"Failed to create error log: {e}")
