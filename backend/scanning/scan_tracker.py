"""
Scan Tracker

Global registry for tracking running scans and their engines
to enable proper stopping and management.
"""

import logging
from threading import Lock
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ScanTracker:
    """Thread-safe tracker for running scan engines"""
    
    def __init__(self):
        self._running_scans: Dict[int, 'UnifiedScanningEngine'] = {}
        self._lock = Lock()
    
    def register_scan(self, scan_id: int, engine: 'UnifiedScanningEngine'):
        """Register a running scan engine"""
        with self._lock:
            self._running_scans[scan_id] = engine
            logger.info(f"Registered scan {scan_id} in tracker")
    
    def unregister_scan(self, scan_id: int):
        """Remove a scan from the tracker (when completed or failed)"""
        with self._lock:
            if scan_id in self._running_scans:
                del self._running_scans[scan_id]
                logger.info(f"Unregistered scan {scan_id} from tracker")
    
    def get_scan_engine(self, scan_id: int) -> Optional['UnifiedScanningEngine']:
        """Get the engine for a running scan"""
        with self._lock:
            return self._running_scans.get(scan_id)
    
    def is_scan_running(self, scan_id: int) -> bool:
        """Check if a scan is currently running"""
        with self._lock:
            return scan_id in self._running_scans
    
    def stop_scan(self, scan_id: int) -> bool:
        """Stop a running scan"""
        with self._lock:
            engine = self._running_scans.get(scan_id)
            if engine:
                try:
                    # Stop the scan engine
                    success = engine.stop_scan()
                    
                    # Clean up resources
                    try:
                        engine.cleanup_resources()
                    except Exception as cleanup_error:
                        logger.warning(f"Error cleaning up resources for scan {scan_id}: {cleanup_error}")
                    
                    # Remove from tracker
                    del self._running_scans[scan_id]
                    logger.info(f"Successfully stopped scan {scan_id}")
                    return success
                except Exception as e:
                    logger.error(f"Error stopping scan {scan_id}: {e}")
                    # Still remove from tracker to prevent memory leaks
                    if scan_id in self._running_scans:
                        del self._running_scans[scan_id]
                    return False
            else:
                logger.warning(f"Scan {scan_id} not found in tracker")
                return False
    
    def get_running_scan_ids(self) -> list:
        """Get list of currently running scan IDs"""
        with self._lock:
            return list(self._running_scans.keys())


# Global instance
_scan_tracker = ScanTracker()


def get_scan_tracker() -> ScanTracker:
    """Get the global scan tracker instance"""
    return _scan_tracker