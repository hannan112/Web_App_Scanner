"""
Management command to test SQLMap integration with discovery workflow
"""

from django.core.management.base import BaseCommand
from scanning.integrations.sqlmap_adapter import SQLMapAdapter
from scanning.active.enhanced_discovery import EnhancedDiscoveryEngine


class Command(BaseCommand):
    help = 'Test SQLMap integration with discovery workflow'

    def add_arguments(self, parser):
        parser.add_argument(
            '--target',
            type=str,
            default='http://172.20.0.2:5000',
            help='Target URL to test (default: http://172.20.0.2:5000)'
        )
        parser.add_argument(
            '--risk-level',
            type=int,
            default=2,
            help='SQLMap risk level (1-3, default: 2)'
        )
        parser.add_argument(
            '--level',
            type=int,
            default=3,
            help='SQLMap level (1-5, default: 3)'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=60,
            help='SQLMap timeout in seconds (default: 60)'
        )

    def handle(self, *args, **options):
        target_url = options['target']
        risk_level = options['risk_level']
        level = options['level']
        timeout = options['timeout']

        self.stdout.write(
            self.style.SUCCESS(f"🚀 Testing SQLMap Integration with {target_url}")
        )
        self.stdout.write("=" * 60)

        # Step 1: Run discovery
        self.stdout.write("\n1️⃣ Running Enhanced Discovery...")
        try:
            discovery_engine = EnhancedDiscoveryEngine(target_url)
            discovery_results = discovery_engine.run_comprehensive_discovery()
            
            urls_count = len(discovery_results.get('urls_discovered', []))
            forms_count = len(discovery_results.get('forms_discovered', []))
            
            self.stdout.write(
                self.style.SUCCESS(f"   ✅ Discovery completed!")
            )
            self.stdout.write(f"   📊 Found {urls_count} URLs")
            self.stdout.write(f"   📝 Found {forms_count} forms")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Discovery failed: {str(e)}")
            )
            return

        # Step 2: Configure SQLMap
        self.stdout.write("\n2️⃣ Configuring SQLMap...")
        sqlmap_config = {
            "risk_level": risk_level,
            "level": level,
            "timeout": timeout,
            "min_confidence": 0.6
        }
        
        sqlmap_adapter = SQLMapAdapter(sqlmap_config)
        
        # Check availability
        availability = sqlmap_adapter.is_available()
        if not availability["available"]:
            self.stdout.write(
                self.style.ERROR(f"   ❌ SQLMap not available: {availability.get('error')}")
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f"   ✅ SQLMap available: {availability.get('version', 'Unknown version')}")
        )

        # Step 3: Run SQLMap on discovered URLs
        self.stdout.write("\n3️⃣ Running SQLMap on Discovered URLs...")
        
        try:
            findings = sqlmap_adapter.scan_discovered_urls(discovery_results)
            
            self.stdout.write(
                self.style.SUCCESS(f"   ✅ SQLMap testing completed!")
            )
            self.stdout.write(f"   📊 Found {len(findings)} total findings")
            
            # Categorize findings
            vulnerabilities = [f for f in findings if f.get('severity') in ['critical', 'high', 'medium']]
            info_findings = [f for f in findings if f.get('severity') == 'info']
            
            self.stdout.write(f"   🚨 Vulnerabilities: {len(vulnerabilities)}")
            self.stdout.write(f"   ℹ️  Info findings: {len(info_findings)}")
            
            # Display vulnerabilities
            if vulnerabilities:
                self.stdout.write("\n   🔍 Vulnerabilities Found:")
                for i, vuln in enumerate(vulnerabilities, 1):
                    self.stdout.write(f"      {i}. {vuln.get('name', 'Unknown')}")
                    self.stdout.write(f"         Severity: {vuln.get('severity', 'Unknown')}")
                    self.stdout.write(f"         URL: {vuln.get('url', 'Unknown')}")
                    self.stdout.write(f"         Confidence: {vuln.get('confidence', 'Unknown')}")
                    if vuln.get('description'):
                        desc = vuln.get('description', '')[:100]
                        self.stdout.write(f"         Description: {desc}...")
                    self.stdout.write()
            
            if info_findings:
                self.stdout.write(f"   ℹ️  Info findings: {len(info_findings)} (check logs for details)")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Error during SQLMap testing: {str(e)}")
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS("\n✅ Integration test completed successfully!")
        )
        
        # Show integration features
        self.stdout.write("\n💡 Integration Features:")
        self.stdout.write("   • Automatically extracts URLs from discovery results")
        self.stdout.write("   • Prioritizes URLs with parameters (more likely vulnerable)")
        self.stdout.write("   • Tests both URLs and forms")
        self.stdout.write("   • Handles various discovery data formats")
        self.stdout.write("   • Provides detailed logging and progress tracking")
        self.stdout.write("   • Categorizes findings by severity")


