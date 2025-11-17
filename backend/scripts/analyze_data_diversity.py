import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from scanning.models import Vulnerability, Scan
from django.db.models import Count, Avg
from collections import defaultdict

print("=== DATA DIVERSITY ANALYSIS ===\n")

# Analyze vulnerability type diversity
vuln_types = Vulnerability.objects.values('name').annotate(count=Count('name')).order_by('-count')

print(f"Total unique vulnerability types: {vuln_types.count()}\n")

# Categorize vulnerability types
categories = {
    'Missing Headers': 0,
    'Information Disclosure': 0,
    'Authentication/Session': 0,
    'Injection': 0,
    'XSS': 0,
    'CSRF': 0,
    'Configuration': 0,
    'Cryptography/SSL': 0,
    'Other': 0
}

for vuln in vuln_types:
    name = vuln['name'].lower()
    if any(x in name for x in ['header', 'csp', 'hsts', 'x-content', 'x-frame']):
        categories['Missing Headers'] += vuln['count']
    elif any(x in name for x in ['information', 'disclosure', 'leaks', 'timestamp', 'version']):
        categories['Information Disclosure'] += vuln['count']
    elif any(x in name for x in ['session', 'cookie', 'authentication', 'login']):
        categories['Authentication/Session'] += vuln['count']
    elif any(x in name for x in ['injection', 'sql', 'command', 'ldap']):
        categories['Injection'] += vuln['count']
    elif any(x in name for x in ['xss', 'cross-site scripting', 'script']):
        categories['XSS'] += vuln['count']
    elif any(x in name for x in ['csrf', 'cross-site request']):
        categories['CSRF'] += vuln['count']
    elif any(x in name for x in ['configuration', 'misconfiguration', 'cors', 'cache']):
        categories['Configuration'] += vuln['count']
    elif any(x in name for x in ['ssl', 'tls', 'certificate', 'crypto']):
        categories['Cryptography/SSL'] += vuln['count']
    else:
        categories['Other'] += vuln['count']

print("=== VULNERABILITY CATEGORY DISTRIBUTION ===")
total = sum(categories.values())
for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
    percentage = (count / total * 100) if total > 0 else 0
    print(f"  {cat}: {count} ({percentage:.1f}%)")

print("\n=== SITE TYPE DIVERSITY ===")
sites = {
    'www.infinitywaveinc.com': 'Production (Real)',
    'localhost:8005': 'Development (Local)',
    'juice-shop.herokuapp.com': 'Vulnerable App (Training)',
    'demo.testfire.net': 'Vulnerable App (Training)',
    'localhost:5001': 'Development (Local)',
    'www.pmtrainingschool.com': 'Production (Real)',
    'mujtaba123.pythonanywhere.com': 'Production (Cloud)',
    'example.com': 'Demo',
    'oliamist.com': 'Production (Real)'
}

site_types = defaultdict(int)
for site, stype in sites.items():
    site_type = stype.split('(')[1].split(')')[0]
    site_types[site_type] += 1

print("Current site type distribution:")
for stype, count in site_types.items():
    print(f"  {stype}: {count} sites")

print("\n=== CRITICAL/HIGH SEVERITY VULNERABILITIES ===")
critical_high = Vulnerability.objects.filter(severity__in=['critical', 'high']).values('name').annotate(
    count=Count('name')
).order_by('-count')

print(f"Total critical/high severity findings: {Vulnerability.objects.filter(severity__in=['critical', 'high']).count()}")
print("\nTop critical/high vulnerabilities:")
for vuln in critical_high[:10]:
    print(f"  {vuln['name']}: {vuln['count']}")

print("\n=== SEVERITY IMBALANCE ===")
severity_dist = Vulnerability.objects.values('severity').annotate(count=Count('severity'))
for s in severity_dist:
    percentage = (s['count'] / 23517 * 100)
    print(f"  {s['severity']}: {s['count']} ({percentage:.1f}%)")

print("\n=== GAPS IN CURRENT DATA ===")
print("1. Critical/High severity: Only 6 findings (0.03%)")
print("2. Dominated by: Missing Headers (38.4%)")
print("3. Missing: Real injection vulnerabilities")
print("4. Missing: Real XSS vulnerabilities")
print("5. Missing: Authentication bypass examples")
print("6. Limited: E-commerce applications")
print("7. Limited: API endpoints (REST/GraphQL)")
print("8. Limited: Modern frameworks (React, Vue, Angular)")
