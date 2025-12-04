
import threading
import time
import logging
import sys
import os

# Mock the UnifiedScanningEngine
class MockEngine:
    def __init__(self, scan_id, tracker):
        self.scan_id = scan_id
        self.tracker = tracker
        
    def stop_scan(self):
        print(f"Engine {self.scan_id}: Stopping scan...")
        time.sleep(1) # Simulate long running operation
        print(f"Engine {self.scan_id}: Calling unregister_scan...")
        self.tracker.unregister_scan(self.scan_id)
        print(f"Engine {self.scan_id}: Unregistered.")
        return True

    def cleanup_resources(self):
        pass

# Add backend to path to import ScanTracker
sys.path.append('/home/hannan/Web_App_Scanner/backend')

from scanning.scan_tracker import ScanTracker

def test_deadlock_fix():
    print("Starting deadlock verification test...")
    tracker = ScanTracker()
    scan_id = 1
    engine = MockEngine(scan_id, tracker)
    
    print("Registering scan...")
    tracker.register_scan(scan_id, engine)
    
    print("Stopping scan (this caused deadlock before)...")
    # This runs in the main thread
    success = tracker.stop_scan(scan_id)
    
    if success:
        print("SUCCESS: Scan stopped without deadlock!")
    else:
        print("FAILURE: Scan stop failed (or timed out/deadlocked if this doesn't print)")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_deadlock_fix()
