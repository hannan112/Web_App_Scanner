"""
Web application security scanning module

This module provides functionality for scanning web applications for security issues.
"""

# Define module version
__version__ = '0.1.0'

# The functions below are for backward compatibility
# They're defined here to avoid circular imports

def start_scan(scan_id):
    """
    Start a scan with the given ID
    
    Args:
        scan_id: The ID of the scan to start
        
    Returns:
        bool: True if scan started successfully, False otherwise
    """
    # Delay import to avoid circular imports
    from scanning.engine import ScanningEngine
    
    engine = ScanningEngine(scan_id)
    return engine.start() is not None

def stop_scan(scan_id):
    """
    Stop a scan with the given ID
    
    Args:
        scan_id: The ID of the scan to stop
        
    Returns:
        bool: True if scan stopped successfully, False otherwise
    """
    # Delay import to avoid circular imports
    from scanning.engine import ScanningEngine
    
    engine = ScanningEngine(scan_id)
    return engine.stop()

# Export public API
__all__ = ['start_scan', 'stop_scan']