import os
import django
import sys
import logging

# Setup Django environment
sys.path.append('/home/hannan-ali/Web_App_Scanner/backend')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from scanning.models.scan import Scan
from scanning.unified_engine import UnifiedScanningEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_ml_to_all():
    scans = Scan.objects.filter(status='completed').order_by('-id')
    total = scans.count()
    logger.info(f"rFound {total} completed scans. Starting batch processing...")
    
    success_count = 0
    error_count = 0
    
    for index, scan in enumerate(scans):
        try:
            logger.info(f"[{index+1}/{total}] Processing Scan {scan.id} (Type: {scan.configuration.scan_type})...")
            engine = UnifiedScanningEngine(scan.id)
            # The restriction inside unified_engine is already removed (commented out) 
            # so calling this will run ML regardless of type.
            engine.apply_ml_fp_reduction()
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to process Scan {scan.id}: {e}")
            error_count += 1
            
    logger.info(f"Batch processing complete. Success: {success_count}, Errors: {error_count}")

if __name__ == "__main__":
    apply_ml_to_all()
