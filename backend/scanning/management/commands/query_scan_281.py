from django.core.management.base import BaseCommand
from scanning.models.scan import Scan, ActiveScanResult, PassiveReconResult
import json

class Command(BaseCommand):
    help = 'Query scan 281 discovered URLs from database'

    def handle(self, *args, **options):
        try:
            # Get scan 281
            scan = Scan.objects.get(id=281)
            self.stdout.write(f"✅ Found Scan 281:")
            self.stdout.write(f"   UUID: {scan.uuid}")
            self.stdout.write(f"   Target URL: {scan.target_url}")
            self.stdout.write(f"   Scan Type: {scan.scan_type}")
            self.stdout.write(f"   Status: {scan.status}")
            self.stdout.write("=" * 60)
            
            # Check for active scan results
            self.stdout.write("\n🔍 CHECKING ACTIVE SCAN RESULTS...")
            try:
                active_result = ActiveScanResult.objects.get(scan=scan)
                self.stdout.write("✅ Active scan results found")
                
                # URLs discovered
                urls_discovered = active_result.urls_discovered or []
                self.stdout.write(f"\n📋 DISCOVERED URLs ({len(urls_discovered)}):")
                if urls_discovered:
                    for i, url in enumerate(urls_discovered, 1):
                        self.stdout.write(f"   {i:3d}. {url}")
                else:
                    self.stdout.write("   No URLs discovered in active scan")
                
                # Forms discovered
                forms_discovered = active_result.forms_discovered or []
                self.stdout.write(f"\n📋 DISCOVERED FORMS ({len(forms_discovered)}):")
                if forms_discovered:
                    for i, form in enumerate(forms_discovered, 1):
                        if isinstance(form, dict):
                            form_info = f"Method: {form.get('method', 'GET')}, Action: {form.get('action', 'N/A')}"
                            if 'data' in form:
                                form_info += f", Fields: {len(form['data'])}"
                            self.stdout.write(f"   {i:3d}. {form_info}")
                        else:
                            self.stdout.write(f"   {i:3d}. {form}")
                else:
                    self.stdout.write("   No forms discovered in active scan")
                    
            except ActiveScanResult.DoesNotExist:
                self.stdout.write("❌ No active scan results found")
            
            # Check for passive scan results
            self.stdout.write("\n🔍 CHECKING PASSIVE SCAN RESULTS...")
            try:
                passive_result = PassiveReconResult.objects.get(scan=scan)
                self.stdout.write("✅ Passive scan results found")
                
                if passive_result.enhanced_discovery:
                    enhanced = passive_result.enhanced_discovery
                    self.stdout.write("\n📋 ENHANCED DISCOVERY DATA:")
                    
                    # URLs from enhanced discovery
                    if 'urls' in enhanced and enhanced['urls']:
                        urls = enhanced['urls']
                        self.stdout.write(f"\n🌐 Enhanced Discovery URLs ({len(urls)}):")
                        for i, url in enumerate(urls, 1):
                            self.stdout.write(f"   {i:3d}. {url}")
                    
                    # Subdomains
                    if 'subdomains' in enhanced and enhanced['subdomains']:
                        subdomains = enhanced['subdomains']
                        self.stdout.write(f"\n🌐 Subdomains ({len(subdomains)}):")
                        for i, subdomain in enumerate(subdomains, 1):
                            self.stdout.write(f"   {i:3d}. {subdomain}")
                    
                    # API Endpoints
                    if 'api_endpoints' in enhanced and enhanced['api_endpoints']:
                        endpoints = enhanced['api_endpoints']
                        self.stdout.write(f"\n🔌 API Endpoints ({len(endpoints)}):")
                        for i, endpoint in enumerate(endpoints, 1):
                            self.stdout.write(f"   {i:3d}. {endpoint}")
                    
                    # Directories
                    if 'directories' in enhanced and enhanced['directories']:
                        directories = enhanced['directories']
                        self.stdout.write(f"\n📁 Directories ({len(directories)}):")
                        for i, directory in enumerate(directories, 1):
                            self.stdout.write(f"   {i:3d}. {directory}")
                else:
                    self.stdout.write("❌ No enhanced discovery data found")
                    
            except PassiveReconResult.DoesNotExist:
                self.stdout.write("❌ No passive scan results found")
            
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("✅ Query completed successfully")
            
        except Scan.DoesNotExist:
            self.stdout.write("❌ Scan 281 not found in database")
        except Exception as e:
            self.stdout.write(f"❌ Error: {e}")
            import traceback
            self.stdout.write(traceback.format_exc())

