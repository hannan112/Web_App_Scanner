import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from scanning.models import Vulnerability, Scan
from django.db.models import Count, Avg

print(f'Total vulnerabilities: {Vulnerability.objects.count()}')
print(f'Total scans: {Scan.objects.count()}')

print(f'\n=== Vulnerability Severity Distribution ===')
for item in Vulnerability.objects.values('severity').annotate(count=Count('severity')).order_by('-count'):
    print(f"  {item['severity']}: {item['count']}")

print(f'\n=== Confidence Score Distribution ===')
for item in Vulnerability.objects.values('confidence').annotate(count=Count('confidence')).order_by('-confidence')[:15]:
    print(f"  {item['confidence']:.2f}: {item['count']}")

print(f'\n=== Top 10 Vulnerability Types ===')
for item in Vulnerability.objects.values('name').annotate(count=Count('name')).order_by('-count')[:10]:
    print(f"  {item['name']}: {item['count']}")

print(f'\n=== Average Confidence by Severity ===')
for item in Vulnerability.objects.values('severity').annotate(avg_conf=Avg('confidence')).order_by('-avg_conf'):
    print(f"  {item['severity']}: {item['avg_conf']:.3f}")

print(f'\n=== Low Confidence Vulnerabilities (< 0.7) ===')
low_conf = Vulnerability.objects.filter(confidence__lt=0.7).count()
print(f"  Count: {low_conf} ({low_conf/Vulnerability.objects.count()*100:.1f}%)")

print(f'\n=== Informational Severity Count ===')
info_count = Vulnerability.objects.filter(severity='info').count()
print(f"  Count: {info_count} ({info_count/Vulnerability.objects.count()*100:.1f}%)")
