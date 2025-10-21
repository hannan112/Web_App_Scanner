#!/usr/bin/env python3
"""
Test script for improved discovery system for local applications
"""

import os
import sys
import django

# Add the backend directory to Python path
sys.path.append('/home/hannan/prototype-2/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from scanning.active.enhanced_discovery import EnhancedDiscoveryEngine
from scanning.integrations.sqlmap_adapter import SQLMapAdapter

def test_improved_discovery():
    """Test the improved discovery system"""
    
    print("🔍 Testing Improved Discovery for Local Applications")
    print("=" * 60)
    
    target_url = "http://172.20.0.2:5000"
    
    # Test discovery
    print("\n1️⃣ Running Enhanced Discovery...")
    discovery_engine = EnhancedDiscoveryEngine(target_url)
    discovery_results = discovery_engine.run_comprehensive_discovery()
    
    print(f"   ✅ Discovery completed!")
    print(f"   📊 Found {len(discovery_results.get('urls_discovered', []))} URLs")
    print(f"   📝 Found {len(discovery_results.get('forms_discovered', []))} forms")
    print(f"   🎯 Found {len(discovery_results.get('endpoints_discovered', []))} endpoints")
    
    # Show discovered URLs
    urls = discovery_results.get('urls_discovered', [])
    if urls:
        print(f"\n   🔗 Discovered URLs:")
        for i, url in enumerate(urls[:10], 1):  # Show first 10
            print(f"      {i}. {url}")
        if len(urls) > 10:
            print(f"      ... and {len(urls) - 10} more")
    
    # Show discovered forms
    forms = discovery_results.get('forms_discovered', [])
    if forms:
        print(f"\n   📝 Discovered Forms:")
        for i, form in enumerate(forms[:5], 1):  # Show first 5
            print(f"      {i}. {form.get('url', 'Unknown')} ({form.get('method', 'GET')})")
            print(f"         Data: {list(form.get('data', {}).keys())}")
        if len(forms) > 5:
            print(f"      ... and {len(forms) - 5} more")
    
    # Test SQLMap integration
    print(f"\n2️⃣ Testing SQLMap Integration...")
    sqlmap_config = {
        "risk_level": 2,
        "level": 3,
        "timeout": 60,
        "min_confidence": 0.6
    }
    
    sqlmap_adapter = SQLMapAdapter(sqlmap_config)
    
    # Check availability
    availability = sqlmap_adapter.is_available()
    if not availability["available"]:
        print(f"   ❌ SQLMap not available: {availability.get('error')}")
        return
    
    print(f"   ✅ SQLMap available: {availability.get('version', 'Unknown version')}")
    
    # Test SQLMap on discovered URLs
    print(f"\n3️⃣ Running SQLMap on Discovered URLs...")
    try:
        findings = sqlmap_adapter.scan_discovered_urls(discovery_results)
        
        print(f"   ✅ SQLMap testing completed!")
        print(f"   📊 Found {len(findings)} total findings")
        
        # Categorize findings
        vulnerabilities = [f for f in findings if f.get('severity') in ['critical', 'high', 'medium']]
        info_findings = [f for f in findings if f.get('severity') == 'info']
        
        print(f"   🚨 Vulnerabilities: {len(vulnerabilities)}")
        print(f"   ℹ️  Info findings: {len(info_findings)}")
        
        # Display vulnerabilities
        if vulnerabilities:
            print(f"\n   🔍 Vulnerabilities Found:")
            for i, vuln in enumerate(vulnerabilities, 1):
                print(f"      {i}. {vuln.get('name', 'Unknown')}")
                print(f"         Severity: {vuln.get('severity', 'Unknown')}")
                print(f"         URL: {vuln.get('url', 'Unknown')}")
                print(f"         Confidence: {vuln.get('confidence', 'Unknown')}")
                if vuln.get('description'):
                    desc = vuln.get('description', '')[:100]
                    print(f"         Description: {desc}...")
                print()
        
        if info_findings:
            print(f"   ℹ️  Info findings: {len(info_findings)} (check logs for details)")
        
    except Exception as e:
        print(f"   ❌ Error during SQLMap testing: {str(e)}")
        return
    
    print("\n✅ Improved discovery test completed successfully!")
    
    # Show statistics
    stats = discovery_results.get('discovery_stats', {})
    print(f"\n📊 Discovery Statistics:")
    print(f"   Total URLs: {stats.get('total_urls', 0)}")
    print(f"   Total Forms: {stats.get('total_forms', 0)}")
    print(f"   Total Endpoints: {stats.get('total_endpoints', 0)}")
    print(f"   URLs with Parameters: {stats.get('urls_with_params', 0)}")
    print(f"   POST Forms: {stats.get('post_forms', 0)}")
    print(f"   GET Forms: {stats.get('get_forms', 0)}")

def main():
    """Main test function"""
    print("🧪 Improved Discovery Test Suite")
    print("=" * 60)
    
    test_improved_discovery()
    
    print("\n💡 Improvements Made:")
    print("   • Specialized discovery for local applications")
    print("   • Common endpoint discovery")
    print("   • Form discovery and analysis")
    print("   • Parameter discovery")
    print("   • API endpoint discovery")
    print("   • Better integration with SQLMap")
    print("   • Comprehensive URL and form testing")

if __name__ == "__main__":
    main()

