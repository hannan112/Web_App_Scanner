import os
import django
import json
import logging

import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()

from scanning.models.scan import Scan
from scanning.models.vulnerability import Vulnerability

def check_latest_scan():
    # Find latest comprehensive scan
    scan = Scan.objects.filter(configuration__scan_type='comprehensive').order_by('-id').first()
    if not scan:
        print("No comprehensive scan found.")
        return

    print(f"Checking Latest Comprehensive Scan: ID {scan.id} - Status: {scan.status}")

    vulns = Vulnerability.objects.filter(scan=scan)
    print(f"Total Vulnerabilities: {vulns.count()}")

    fp_count = 0
    ml_info_count = 0 
    
    for v in vulns:
        info = {}
        if v.other_info:
            if isinstance(v.other_info, str):
                try:
                    info = json.loads(v.other_info)
                except:
                    pass
            elif isinstance(v.other_info, dict):
                info = v.other_info
        
        if info:
            ml_info_count += 1
            if info.get('ml_is_fp'):
                fp_count += 1
                print(f"  - FP Found: {v.name} (Conf: {info.get('ml_fp_confidence')})")

    print(f"Vulnerabilities with ML Info: {ml_info_count}")
    print(f"False Positives Detected (DB Level): {fp_count}")

    # Verify Serializer Output
    print("\nVerifying Serializer Output...")
    from scanning.serializers import VulnerabilitySummarySerializer
    
    # Test on one FP vulnerability
    fp_vuln = None
    for v in vulns:
        if v.other_info and "ml_is_fp" in str(v.other_info):
            fp_vuln = v
            break
            
    if fp_vuln:
        serializer = VulnerabilitySummarySerializer(fp_vuln)
        data = serializer.data
        print(f"Sample Serialized Data for FP Vuln ({fp_vuln.id}):")
        print(json.dumps(data, indent=2))
        
        if 'is_fp' in data:
            print(f"FAILED?? is_fp present: {data['is_fp']}")
        else:
            print("CRITICAL: is_fp MISSING in serializer output")
    else:
        print("No FP vulnerability found to test serializer.")

if __name__ == '__main__':
    check_latest_scan()
