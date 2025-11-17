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
        """Stop a running scan - does NOT remove from tracker until engine confirms"""
        with self._lock:
            engine = self._running_scans.get(scan_id)
            if engine:
                try:
                    # Stop the scan engine
                    # The engine's stop_scan() method will handle:
                    # 1. Setting stop event
                    # 2. Stopping ZAP processes
                    # 3. Updating database status
                    # 4. Unregistering from tracker (after verification)
                    success = engine.stop_scan()

                    # Clean up resources
                    try:
                        engine.cleanup_resources()
                    except Exception as cleanup_error:
                        logger.warning(f"Error cleaning up resources for scan {scan_id}: {cleanup_error}")

                    # NOTE: We no longer immediately delete from tracker here.
                    # The engine will call unregister_scan() after verifying stop.
                    # This allows retry if stop fails.
                    logger.info(f"Initiated stop for scan {scan_id}, engine will unregister after verification")
                    return success
                except Exception as e:
                    logger.error(f"Error stopping scan {scan_id}: {e}")
                    # On exception, remove from tracker to prevent memory leaks
                    if scan_id in self._running_scans:
                        del self._running_scans[scan_id]
                        logger.warning(f"Removed scan {scan_id} from tracker due to stop error")
                    return False
            else:
                logger.warning(f"Scan {scan_id} not found in tracker - may have already stopped")
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