"""
Active Security Scanner

Main coordinator for active security scanning operations.
Handles the orchestration of ZAP and other active scanning tools.
"""

import logging
from typing import Dict
from scanning.active.engines.active_engine import ActiveScanningEngine

logger = logging.getLogger(__name__)


class ActiveScanner:
    """
    Active security scanner for comprehensive vulnerability testing
    Coordinates ZAP and other active scanning tools
    """

    def __init__(self, scan_id: int):
        self.scan_id = scan_id
        self.engine = ActiveScanningEngine(scan_id)

    def run_scan(self) -> bool:
        """
        Run complete active security scan
        
        Returns:
            bool: True if scan completed successfully, False otherwise
        """
        try:
            logger.info(f"Starting active security scan for scan ID: {self.scan_id}")
            
            # Start the active scanning engine
            success = self.engine.start()
            
            if success:
                logger.info(f"Active security scan completed successfully for scan ID: {self.scan_id}")
            else:
                logger.error(f"Active security scan failed for scan ID: {self.scan_id}")
                
            return success
            
        except Exception as e:
            logger.exception(f"Active security scan error for scan ID {self.scan_id}: {e}")
            return False

    def stop_scan(self) -> bool:
        """
        Stop the active scan
        
        Returns:
            bool: True if scan stopped successfully, False otherwise
        """
        try:
            logger.info(f"Stopping active security scan for scan ID: {self.scan_id}")
            
            self.engine.stop_scan()
            
            logger.info(f"Active security scan stopped successfully for scan ID: {self.scan_id}")
            return True
            
        except Exception as e:
            logger.exception(f"Error stopping active security scan for scan ID {self.scan_id}: {e}")
            return False

    @staticmethod
    def validate_zap_connection() -> bool:
        """
        Validate ZAP connection without running a scan
        
        Returns:
            bool: True if ZAP is accessible, False otherwise
        """
        try:
            from scanning.active.zap_active_adapter import ZAPActiveAdapter
            
            adapter = ZAPActiveAdapter()
            return adapter.check_zap_connection()
            
        except Exception as e:
            logger.error(f"ZAP connection validation failed: {e}")
            return False

    @staticmethod
    def get_zap_status() -> Dict:
        """
        Get ZAP status and version information
        
        Returns:
            dict: ZAP status information
        """
        try:
            from scanning.active.zap_active_adapter import ZAPActiveAdapter
            
            adapter = ZAPActiveAdapter()
            
            if adapter.check_zap_connection():
                version = adapter._get_zap_version()
                return {
                    "status": "connected",
                    "version": version,
                    "url": adapter.base_url
                }
            else:
                return {
                    "status": "disconnected",
                    "error": "Cannot connect to ZAP",
                    "url": adapter.base_url
                }
                
        except Exception as e:
            logger.error(f"Error getting ZAP status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }