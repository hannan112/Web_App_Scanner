import os
import django
from urllib.parse import urlparse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from scanning.models import Vulnerability, Scan
from django.db.models import Count

print("=== SCAN ANALYSIS ===\n")

# Get unique target URLs
scans = Scan.objects.all()
print(f"Total scans: {scans.count()}")

target_urls = {}
for scan in scans:
    domain = urlparse(scan.target_url).netloc
    if domain not in target_urls:
        target_urls[domain] = []
    target_urls[domain].append(scan.id)

print(f"\n=== UNIQUE SITES SCANNED ===")
print(f"Total unique sites: {len(target_urls)}")
for domain, scan_ids in sorted(target_urls.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {domain}: {len(scan_ids)} scans")

print(f"\n=== VULNERABILITIES PER SITE ===")
for domain, scan_ids in sorted(target_urls.items(), key=lambda x: len(x[1]), reverse=True):
    vuln_count = Vulnerability.objects.filter(scan_id__in=scan_ids).count()
    avg_per_scan = vuln_count / len(scan_ids) if len(scan_ids) > 0 else 0
    print(f"  {domain}:")
    print(f"    Total vulnerabilities: {vuln_count}")
    print(f"    Avg per scan: {avg_per_scan:.1f}")
    print(f"    Scans: {len(scan_ids)}")

# Analyze vulnerability consistency across scans of same site
print(f"\n=== VULNERABILITY CONSISTENCY (Same vuln appearing in multiple scans) ===")
for domain, scan_ids in list(target_urls.items())[:5]:  # Top 5 sites
    if len(scan_ids) < 2:
        continue
    print(f"\n{domain} ({len(scan_ids)} scans):")

    # Get all unique vulnerability names for this site
    vulns = Vulnerability.objects.filter(scan_id__in=scan_ids).values('name').annotate(
        count=Count('name')
    ).order_by('-count')[:10]

    for vuln in vulns:
        consistency = (vuln['count'] / len(scan_ids)) * 100
        print(f"  {vuln['name'][:60]}: appears {vuln['count']} times ({consistency:.0f}% consistency)")

print(f"\n=== SCAN STATUS ===")
for status_info in Scan.objects.values('status').annotate(count=Count('status')):
    print(f"  {status_info['status']}: {status_info['count']}")

print(f"\n=== VULNERABILITY OVERLAP ANALYSIS ===")
# Find vulnerabilities that appear in ALL scans (likely false positives)
all_vuln_names = Vulnerability.objects.values('name').annotate(
    scan_count=Count('scan', distinct=True),
    total_count=Count('name')
).order_by('-scan_count')

print(f"\nVulnerabilities appearing in 50+ scans (likely FPs):")
for vuln in all_vuln_names[:15]:
    if vuln['scan_count'] >= 50:
        print(f"  {vuln['name'][:60]}")
        print(f"    Appears in {vuln['scan_count']} scans, {vuln['total_count']} total occurrences")
