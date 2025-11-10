"""
Scan-Specific Logging Utility

Captures logs from multiple sources during a scan:
1. Backend application logs
2. Docker container logs (ZAP, DVWA, etc.)
3. API request/response logs
4. Error traces

All logs are organized per-scan in: backend/logs/scan_<id>/
"""

import os
import logging
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List


logger = logging.getLogger(__name__)


class ScanLogger:
    """
    Manages comprehensive logging for a specific scan

    Directory structure:
    backend/logs/scan_<id>/
        ├── backend.log           # Backend application logs for this scan
        ├── zap_container.log     # ZAP Docker container logs
        ├── dvwa_container.log    # DVWA container logs (if running)
        ├── api_requests.log      # ZAP API request/response logs
        ├── errors.log            # Error-only logs
        └── scan_metadata.json    # Scan info, timestamps, etc.
    """

    def __init__(self, scan_id: int, base_log_dir: str = None):
        self.scan_id = scan_id
        self.base_log_dir = base_log_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'logs'
        )

        # Create scan-specific directory
        self.scan_log_dir = os.path.join(self.base_log_dir, f"scan_{scan_id}")
        Path(self.scan_log_dir).mkdir(parents=True, exist_ok=True)

        # Log file paths
        self.backend_log = os.path.join(self.scan_log_dir, "backend.log")
        self.zap_log = os.path.join(self.scan_log_dir, "zap_container.log")
        self.dvwa_log = os.path.join(self.scan_log_dir, "dvwa_container.log")
        self.api_log = os.path.join(self.scan_log_dir, "api_requests.log")
        self.error_log = os.path.join(self.scan_log_dir, "errors.log")
        self.metadata_file = os.path.join(self.scan_log_dir, "scan_metadata.json")

        # Docker log capture threads
        self.docker_threads: List[threading.Thread] = []
        self.stop_logging = threading.Event()

        # Start time
        self.start_time = datetime.now()

        logger.info(f"Initialized scan logger for scan {scan_id} at {self.scan_log_dir}")

    def start_docker_log_capture(self):
        """Start capturing Docker container logs in background threads"""
        # Find running Docker containers
        containers_to_monitor = self._get_docker_containers()

        for container_name, log_file in containers_to_monitor.items():
            thread = threading.Thread(
                target=self._capture_docker_logs,
                args=(container_name, log_file),
                daemon=True,
                name=f"DockerLogger-{container_name}"
            )
            thread.start()
            self.docker_threads.append(thread)
            logger.info(f"Started Docker log capture for: {container_name}")

    def _get_docker_containers(self) -> Dict[str, str]:
        """Detect running Docker containers to monitor"""
        containers = {}

        try:
            # Get all running containers
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )

            running_containers = result.stdout.strip().split('\n')

            # Map containers to log files
            for container in running_containers:
                if not container:
                    continue

                # ZAP container
                if 'zap' in container.lower():
                    containers[container] = self.zap_log
                # DVWA container
                elif 'dvwa' in container.lower():
                    containers[container] = self.dvwa_log
                # Other containers (generic logging)
                else:
                    log_file = os.path.join(
                        self.scan_log_dir,
                        f"{container}_container.log"
                    )
                    containers[container] = log_file

            logger.info(f"Found {len(containers)} Docker containers to monitor: {list(containers.keys())}")

        except Exception as e:
            logger.warning(f"Failed to detect Docker containers: {e}")

        return containers

    def _capture_docker_logs(self, container_name: str, log_file: str):
        """
        Capture Docker container logs in real-time

        Uses 'docker logs --follow' to stream logs to file
        """
        try:
            with open(log_file, 'w') as f:
                # Write header
                f.write(f"="*80 + "\n")
                f.write(f"Docker Container: {container_name}\n")
                f.write(f"Scan ID: {self.scan_id}\n")
                f.write(f"Started: {datetime.now().isoformat()}\n")
                f.write(f"="*80 + "\n\n")
                f.flush()

                # Start streaming logs
                # Use --since to only capture logs from scan start time
                since_time = self.start_time.strftime('%Y-%m-%dT%H:%M:%S')

                process = subprocess.Popen(
                    [
                        "docker", "logs",
                        "--follow",
                        "--since", since_time,
                        container_name
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Combine stderr into stdout
                    text=True,
                    bufsize=1  # Line buffered
                )

                # Read logs line by line
                while not self.stop_logging.is_set():
                    line = process.stdout.readline()
                    if not line:
                        # Check if process ended
                        if process.poll() is not None:
                            break
                        time.sleep(0.1)
                        continue

                    # Write to file
                    f.write(line)
                    f.flush()

                # Cleanup
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()

                # Write footer
                f.write(f"\n" + "="*80 + "\n")
                f.write(f"Ended: {datetime.now().isoformat()}\n")
                f.write(f"="*80 + "\n")

        except Exception as e:
            logger.error(f"Error capturing Docker logs for {container_name}: {e}")
            # Write error to log file
            try:
                with open(log_file, 'a') as f:
                    f.write(f"\n\nERROR: Failed to capture logs: {e}\n")
            except:
                pass

    def log_api_request(self, method: str, url: str, params: dict = None, response: dict = None, error: str = None):
        """Log ZAP API request and response"""
        try:
            with open(self.api_log, 'a') as f:
                timestamp = datetime.now().isoformat()

                f.write(f"\n{'='*80}\n")
                f.write(f"[{timestamp}] {method} {url}\n")
                f.write(f"{'-'*80}\n")

                if params:
                    f.write(f"Parameters:\n")
                    for key, value in params.items():
                        # Mask API key
                        if key.lower() == 'apikey':
                            value = value[:10] + '...' if len(value) > 10 else '***'
                        f.write(f"  {key}: {value}\n")

                if response:
                    f.write(f"\nResponse:\n")
                    f.write(f"  {response}\n")

                if error:
                    f.write(f"\n❌ ERROR:\n")
                    f.write(f"  {error}\n")

                f.write(f"{'='*80}\n")
                f.flush()

        except Exception as e:
            logger.error(f"Failed to log API request: {e}")

    def log_error(self, error_type: str, message: str, traceback: str = None):
        """Log errors separately for easy debugging"""
        try:
            with open(self.error_log, 'a') as f:
                timestamp = datetime.now().isoformat()

                f.write(f"\n{'='*80}\n")
                f.write(f"[{timestamp}] {error_type}\n")
                f.write(f"{'-'*80}\n")
                f.write(f"{message}\n")

                if traceback:
                    f.write(f"\nTraceback:\n")
                    f.write(f"{traceback}\n")

                f.write(f"{'='*80}\n")
                f.flush()

        except Exception as e:
            logger.error(f"Failed to log error: {e}")

    def save_metadata(self, metadata: dict):
        """Save scan metadata (config, timestamps, results summary)"""
        try:
            import json

            metadata['scan_id'] = self.scan_id
            metadata['log_directory'] = self.scan_log_dir
            metadata['start_time'] = self.start_time.isoformat()
            metadata['end_time'] = datetime.now().isoformat()

            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Saved scan metadata to {self.metadata_file}")

        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def stop_docker_log_capture(self):
        """Stop all Docker log capture threads"""
        logger.info("Stopping Docker log capture...")

        # Signal threads to stop
        self.stop_logging.set()

        # Wait for threads to finish (with timeout)
        for thread in self.docker_threads:
            thread.join(timeout=3)

        logger.info(f"Docker log capture stopped for scan {self.scan_id}")

    def create_summary(self) -> str:
        """Create a summary of all logs"""
        summary_file = os.path.join(self.scan_log_dir, "LOG_SUMMARY.txt")

        try:
            with open(summary_file, 'w') as f:
                f.write("="*80 + "\n")
                f.write(f"SCAN LOG SUMMARY - Scan ID: {self.scan_id}\n")
                f.write("="*80 + "\n\n")

                f.write(f"Scan Duration: {self.start_time.isoformat()} to {datetime.now().isoformat()}\n")
                f.write(f"Log Directory: {self.scan_log_dir}\n\n")

                f.write("Available Logs:\n")
                f.write("-"*80 + "\n")

                # List all log files with sizes
                for log_file in Path(self.scan_log_dir).glob("*.log"):
                    size = log_file.stat().st_size
                    size_kb = size / 1024
                    f.write(f"  • {log_file.name:<30} ({size_kb:>8.2f} KB)\n")

                # Count errors
                if os.path.exists(self.error_log):
                    with open(self.error_log, 'r') as error_f:
                        error_count = error_f.read().count('='*80)
                    f.write(f"\n⚠️  Total Errors Logged: {error_count}\n")

                f.write("\n" + "="*80 + "\n")
                f.write("Quick Access Commands:\n")
                f.write("-"*80 + "\n")
                f.write(f"  View backend logs:    tail -f {self.backend_log}\n")
                f.write(f"  View ZAP logs:        tail -f {self.zap_log}\n")
                f.write(f"  View errors only:     cat {self.error_log}\n")
                f.write(f"  View API requests:    cat {self.api_log}\n")
                f.write("="*80 + "\n")

            logger.info(f"Created log summary: {summary_file}")
            return summary_file

        except Exception as e:
            logger.error(f"Failed to create summary: {e}")
            return None

    def __enter__(self):
        """Context manager entry"""
        self.start_docker_log_capture()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_docker_log_capture()
        self.create_summary()


# Convenience function for easy usage
def create_scan_logger(scan_id: int) -> ScanLogger:
    """Create a new scan logger instance"""
    return ScanLogger(scan_id)
