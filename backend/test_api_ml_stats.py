import os
import django
import sys
import json
from django.conf import settings
# Setup Django environment BEFORE other imports
sys.path.append('/home/hannan-ali/Web_App_Scanner/backend')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

django.setup()

from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from scanning.views import ScanViewSet
from scanning.models.scan import Scan, ScanConfiguration
from authentication.models import CustomUser


def test_api_ml_stats():
    # 1. Get our test scan (ID 106)
    try:
        scan = Scan.objects.get(id=106)
        print(f"Testing Scan ID: {scan.id} (Status: {scan.status})")
    except Scan.DoesNotExist:
        print("Scan 106 not found. Seeding new data needed?")
        return

    # 2. Get User (owner)
    user = scan.configuration.project.owner
    print(f"User: {user.username}")

    # 3. Simulate API Request
    factory = APIRequestFactory()
    view = ScanViewSet.as_view({'get': 'results'})
    
    request = factory.get(f'/api/scans/{scan.id}/results/')
    force_authenticate(request, user=user)
    
    response = view(request, pk=scan.id)
    
    print(f"Response Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.data
        summary = data.get('summary', {})
        print("\n--- Summary Data ---")
        print(json.dumps(summary, indent=2))
        
        ml_stats = summary.get('ml_stats')
        if ml_stats:
            print("\n✅ ml_stats found!")
            print(f"Before ML Total: {ml_stats.get('before_ml_total')}")
            print(f"False Positives: {ml_stats.get('false_positives_detected')}")
            print(f"After ML Total:  {ml_stats.get('after_ml_total')}")
            
            # Verify against known constraints (Scan 106 had 2 vulns, 1 FP)
            if ml_stats['before_ml_total'] == 2 and ml_stats['false_positives_detected'] == 1:
                 print("\n✅ Verification PASSED: Correct stats for Scan 106")
            else:
                 print("\n❌ Verification FAILED: Stats do not match expected (2 total, 1 FP)")
        else:
            print("\n❌ ml_stats MISSING in response")
    else:
        print(f"API Request Failed: {response.data}")

if __name__ == "__main__":
    test_api_ml_stats()
