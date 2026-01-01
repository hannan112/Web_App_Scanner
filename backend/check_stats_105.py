import os
import django
import sys
import json

# Setup Django environment
sys.path.append('/home/hannan-ali/Web_App_Scanner/backend')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from scanning.models.scan import Scan
from scanning.models.vulnerability import Vulnerability

def check_105():
    try:
        scan = Scan.objects.get(id=105)
        print(f"Checking Scan {scan.id} (Type: {scan.configuration.scan_type})")
        
        vulns = Vulnerability.objects.filter(scan=scan)
        total = vulns.count()
        fps = 0
        
        for v in vulns:
            if v.other_info:
                try:
                    info = json.loads(v.other_info) if isinstance(v.other_info, str) else v.other_info
                    if isinstance(info, dict) and info.get('ml_is_fp'):
                        fps += 1
                except:
                    pass
        
        print(f"Total Findings: {total}")
        print(f"Ml Identified FPs: {fps}")
        if total > 0:
            print(f"Reduction: {fps/total*100:.2f}%")
            
    except Scan.DoesNotExist:
        print("Scan 105 not found")

if __name__ == "__main__":
    check_105()
