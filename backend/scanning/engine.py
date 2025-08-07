"""
Main scanning engine that orchestrates the entire scanning process
"""

import logging
import threading
from urllib.parse import urlparse

from django.utils import timezone

from scanning.models.scan import Scan, ScanLog
from scanning.passive.unified_scanner import UnifiedPassiveScanner

# Import active and ML engines later as they're implemented

logger = logging.getLogger(__name__)


class ScanningEngine:
    """
    Core scanning engine that orchestrates the scanning process
    """

    def __init__(self, scan_id):
        """
        Initialize the scanning engine with a scan ID.

        Args:
            scan_id (int): ID of the scan to perform
        """
        self.scan_id = scan_id
        self.scan = None
        self.configuration = None
        self.target_url = None
        self.domain = None
        self._stop_requested = False
        self._progress_lock = threading.Lock()

    def start(self):
        """
        Start the scanning process in a new thread.

        Returns:
            threading.Thread or None: The thread object if successfully started, None otherwise
        """
        try:
            self.scan = Scan.objects.get(id=self.scan_id)
            self.configuration = self.scan.configuration
            self.target_url = self.scan.project.target_url

            # Extract domain from URL
            self.domain = urlparse(self.target_url).netloc

            # Mark scan as started
            self.scan.status = "in_progress"
            self.scan.start_time = timezone.now()
            self.scan.save()

            # Log the start of the scan
            ScanLog.objects.create(
                scan=self.scan,
                level="INFO",
                message=f"Starting {self.configuration.scan_type} scan for {self.target_url}",
            )

            # Start the scan in a background thread
            scan_type = self.configuration.scan_type

            if scan_type == "passive":
                thread = threading.Thread(target=self._run_passive_scan)
            elif scan_type == "active":
                thread = threading.Thread(target=self._run_active_scan)
            elif scan_type == "full":
                thread = threading.Thread(target=self._run_comprehensive_scan)
            else:
                self._fail_scan("Invalid scan type")
                return None

            thread.daemon = True
            thread.start()

            return thread

        except Exception as e:
            logger.exception(f"Error starting scan: {str(e)}")
            if self.scan:
                self._fail_scan(str(e))
            return None

    def stop(self):
        """
        Stop a running scan

        Returns:
            bool: True if stop was successful, False otherwise
        """
        try:
            if not self.scan:
                self.scan = Scan.objects.get(id=self.scan_id)

            if self.scan.status == "in_progress":
                self._stop_requested = True
                self.scan.status = "stopped"
                self.scan.end_time = timezone.now()
                self.scan.save()

                ScanLog.objects.create(
                    scan=self.scan,
                    level="INFO",
                    message="Scan was stopped by user request",
                )

                return True
            else:
                logger.warning(
                    f"Cannot stop scan {self.scan_id} as it is not in progress"
                )
                return False

        except Exception as e:
            logger.exception(f"Error stopping scan: {str(e)}")
            return False

    # In scanning/engine.py, improve the _run_passive_scan method:

    def _run_passive_scan(self):
        """
        Run a passive scan using the unified scanner.

        This method coordinates passive scanning of the target URL using the
        UnifiedPassiveScanner, which intelligently combines built-in analyzers
        and mature security tools.
        """
        try:
            self._log_info("Starting passive reconnaissance")

            # Check if scan should be stopped
            if self._stop_requested:
                return

            self._log_info("Using Unified Passive Scanner")

            # Create the scanner instance
            scanner = UnifiedPassiveScanner(
                self.scan_id, self.scan, self.target_url, self.configuration
            )

            # Check which tools are available
            tool_status = []
            for tool, status in scanner.available_tools.items():
                tool_status.append(
                    f"{tool}: {'Available' if status.get('available') else 'Not available'}"
                )
            self._log_info(f"Tool availability: {', '.join(tool_status)}")

            # Run the scan
            try:
                scanner.run_scan()
                self._log_info("Passive scan completed successfully")
            except Exception as scan_error:
                self._log_error(f"Error during passive scan: {str(scan_error)}")
                raise

            # Complete the scan if not stopped
            if not self._stop_requested:
                self._complete_scan()

        except Exception as e:
            logger.exception(f"Error in passive scan: {str(e)}")
            self._fail_scan(str(e))

    def _fail_scan(self, error_message):
        """Mark scan as failed with error message"""
        if not self.scan:
            try:
                self.scan = Scan.objects.get(id=self.scan_id)
            except Scan.DoesNotExist:
                logger.error(f"Could not find scan with ID {self.scan_id}")
                return

        self.scan.status = "failed"
        self.scan.error_message = error_message
        self.scan.end_time = timezone.now()
        self.scan.save()

        self._log_error(f"Scan failed with error: {error_message}")

    def _run_active_scan(self):
        """
        Run an active scan (includes crawling and vulnerability testing).
        """
        try:
            # Check if scan should be stopped
            if self._stop_requested:
                return

            self._log_info("Starting active scan")

            # Run passive scan first using the unified scanner
            passive_scanner = UnifiedPassiveScanner(
                self.scan_id, self.scan, self.target_url, self.configuration
            )

            # Run the passive scan
            passive_scanner.run_scan()

            # Check if scan should be stopped
            if self._stop_requested:
                return

            # Active scanning implementation
            self._log_info("Starting active vulnerability testing")

            # TODO: Implement active scanning components
            # For now, provide a clearer placeholder implementation
            from scanning.models import Vulnerability

            # Record that active scanning is not yet implemented
            Vulnerability.objects.create(
                scan=self.scan,
                name="Active Scanning Not Implemented",
                description="Active scanning functionality is still under development. Only passive findings are reported.",
                severity="info",
                confidence=1.0,
                remediation="Check for updates to enable active scanning features.",
            )

            # Complete the scan if not stopped
            if not self._stop_requested:
                self._complete_scan()

        except Exception as e:
            logger.exception(f"Error in active scan: {str(e)}")
            self._fail_scan(str(e))

    def _run_comprehensive_scan(self):
        """
        Run a comprehensive scan (passive, active, and ML).
        """
        try:
            # Similar to active scan for now
            self._run_active_scan()

        except Exception as e:
            logger.exception(f"Error in comprehensive scan: {str(e)}")
            self._fail_scan(str(e))

    def _complete_scan(self):
        """Mark scan as completed"""
        self.scan.status = "completed"
        self.scan.progress = 100.0
        self.scan.end_time = timezone.now()
        self.scan.save()

        self._log_info("Scan completed successfully")

    def _fail_scan(self, error_message):
        """Mark scan as failed with error message"""
        if not self.scan:
            try:
                self.scan = Scan.objects.get(id=self.scan_id)
            except Scan.DoesNotExist:
                logger.error(f"Could not find scan with ID {self.scan_id}")
                return

        self.scan.status = "failed"
        self.scan.error_message = error_message
        self.scan.end_time = timezone.now()
        self.scan.save()

        self._log_error(f"Scan failed with error: {error_message}")

    def _log_info(self, message):
        """Log info message"""
        if not self.scan:
            return

        ScanLog.objects.create(scan=self.scan, level="INFO", message=message)

    def _log_error(self, message):
        """Log error message"""
        if not self.scan:
            return

        ScanLog.objects.create(scan=self.scan, level="ERROR", message=message)

    def update_progress(self, progress, message=None):
        """Update scan progress with thread safety"""
        with self._progress_lock:
            self.progress = progress
            self.scan.progress = progress
            self.scan.save()

        if message:
            logger.info(f"Scan {self.scan_id}: {message} - {progress}%")

            # Log to database (this might also need locking if sharing the scan object)
            ScanLog.objects.create(
                scan=self.scan, level="INFO", message=f"{message} - {progress}%"
            )


# Helper functions for backward compatibility
def start_scan(scan_id):
    """Start a scan with the given ID"""
    engine = ScanningEngine(scan_id)
    thread = engine.start()
    return thread is not None


def stop_scan(scan_id):
    """Stop a scan with the given ID"""
    engine = ScanningEngine(scan_id)
    return engine.stop()
