"""
Management command to test enhanced scanning with authentication and wordlist discovery
"""

from django.core.management.base import BaseCommand
from scanning.models import Scan, ScanConfiguration, Project
from scanning.integrations.enhanced_scan_manager import EnhancedScanManager
from scanning.active.zap_active_adapter import ZAPActiveAdapter
from authentication.models import CustomUser


class Command(BaseCommand):
    help = 'Test enhanced scanning with authentication and wordlist discovery'

    def add_arguments(self, parser):
        parser.add_argument('target_url', type=str, help='Target URL to scan')
        parser.add_argument('--auth-profile', type=str, help='Authentication profile (dvwa, testfire, etc.)')
        parser.add_argument(
            '--username',
            type=str,
            help='Username for authentication (overrides default)'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for authentication (overrides default)'
        )
        parser.add_argument(
            '--no-wordlist',
            action='store_true',
            help='Disable wordlist discovery'
        )
        parser.add_argument(
            '--no-sqli-tests',
            action='store_true',
            help='Disable SQL injection test URL generation'
        )
        parser.add_argument(
            '--custom-wordlist',
            type=str,
            help='Path to custom wordlist file'
        )

    def handle(self, *args, **options):
        target_url = options['target_url']
        auth_profile = options.get('auth_profile')
        custom_username = options.get('username')
        custom_password = options.get('password')
        use_wordlist = not options.get('no_wordlist', False)
        include_sqli = not options.get('no_sqli_tests', False)
        custom_wordlist = options.get('custom_wordlist')

        self.stdout.write(self.style.SUCCESS(f'\n🎯 Enhanced Scan Test for: {target_url}\n'))

        # Create or get test user
        user, _ = CustomUser.objects.get_or_create(
            email='test@scanner.local',
            defaults={'username': 'test_scanner'}
        )

        # Create or get test project
        project, _ = Project.objects.get_or_create(
            owner=user,
            name='Enhanced Scan Test',
            defaults={'target_url': target_url}
        )

        # Create scan configuration
        config, _ = ScanConfiguration.objects.get_or_create(
            project=project,
            defaults={
                'scan_type': 'active',
                'use_zap_active': True,
                'enable_spider': True,
                'enable_ajax_spider': True,
                'max_spider_depth': 5,
                'test_sql_injection': True,
                'test_xss': True,
                'zap_attack_strength': 'MEDIUM',
            }
        )

        # Create scan instance
        scan = Scan.objects.create(
            configuration=config,
            project=project,
            target_url=target_url,
            status='pending'
        )

        self.stdout.write(f'📋 Created scan #{scan.id}\n')

        try:
            # Initialize ZAP adapter
            self.stdout.write('🔧 Initializing ZAP adapter...')
            zap_adapter = ZAPActiveAdapter(config=config.__dict__, scan_id=scan.id)

            if not zap_adapter.check_zap_connection():
                self.stdout.write(self.style.ERROR('❌ Cannot connect to ZAP. Ensure ZAP is running on port 8080.'))
                return

            self.stdout.write(self.style.SUCCESS('✅ ZAP connected\n'))

            # Initialize enhanced scan manager
            self.stdout.write('🚀 Initializing enhanced scan manager...')
            enhanced_manager = EnhancedScanManager(zap_adapter, target_url, config)

            # Step 1: Setup authentication
            self.stdout.write('\n' + '='*60)
            self.stdout.write('STEP 1: Authentication Setup')
            self.stdout.write('='*60)

            custom_creds = None
            if custom_username and custom_password:
                # Determine credential field names based on profile
                if auth_profile == 'testfire':
                    custom_creds = {'uid': custom_username, 'passw': custom_password}
                else:
                    custom_creds = {'username': custom_username, 'password': custom_password}

            auth_success = enhanced_manager.setup_authentication(
                profile_name=auth_profile,
                custom_credentials=custom_creds
            )

            if auth_success:
                self.stdout.write(self.style.SUCCESS('✅ Authentication setup complete'))
                if enhanced_manager.authenticated:
                    self.stdout.write(f'   Profile: {enhanced_manager.auth_manager.profile["name"]}')
            else:
                self.stdout.write(self.style.WARNING('⚠️  Authentication setup failed (continuing without auth)'))

            # Step 2: Discover scan targets
            self.stdout.write('\n' + '='*60)
            self.stdout.write('STEP 2: Target Discovery')
            self.stdout.write('='*60)

            discovery_results = enhanced_manager.discover_scan_targets(
                use_wordlists=use_wordlist,
                custom_wordlist_path=custom_wordlist,
                include_sqli_tests=include_sqli
            )

            self.stdout.write(self.style.SUCCESS('\n✅ Target discovery complete:'))
            self.stdout.write(f'   Total targets: {discovery_results["total_targets"]}')
            self.stdout.write(f'   Base URLs: {len(discovery_results["base_urls"])}')
            self.stdout.write(f'   Discovered URLs: {len(discovery_results["discovered_urls"])}')
            self.stdout.write(f'   SQLi test URLs: {len(discovery_results["sqli_test_urls"])}')
            self.stdout.write(f'   Priority URLs: {len(discovery_results["priority_urls"])}')

            # Show some example discovered URLs
            if discovery_results['discovered_urls']:
                self.stdout.write('\n📍 Sample discovered URLs:')
                for url in discovery_results['discovered_urls'][:10]:
                    self.stdout.write(f'   {url}')
                if len(discovery_results['discovered_urls']) > 10:
                    self.stdout.write(f'   ... and {len(discovery_results["discovered_urls"]) - 10} more')

            # Show priority URLs
            if discovery_results['priority_urls']:
                self.stdout.write('\n⭐ Priority URLs (will scan first):')
                for url in discovery_results['priority_urls'][:10]:
                    self.stdout.write(f'   {url}')

            # Step 3: Configure scan scope
            self.stdout.write('\n' + '='*60)
            self.stdout.write('STEP 3: Scan Scope Configuration')
            self.stdout.write('='*60)

            scope_success = enhanced_manager.configure_scan_scope()
            if scope_success:
                self.stdout.write(self.style.SUCCESS('✅ Scan scope configured'))
            else:
                self.stdout.write(self.style.WARNING('⚠️  Scan scope configuration had issues'))

            # Step 4: Run targeted active scan
            self.stdout.write('\n' + '='*60)
            self.stdout.write('STEP 4: Targeted Active Scanning')
            self.stdout.write('='*60)
            self.stdout.write('🔍 Starting targeted active scan (this may take several minutes)...\n')

            def progress_callback(progress, message):
                self.stdout.write(f'[{progress:.1f}%] {message}')

            scan_results = enhanced_manager.run_targeted_active_scan(progress_callback=progress_callback)

            self.stdout.write(self.style.SUCCESS('\n✅ Targeted active scan complete:'))
            self.stdout.write(f'   URLs scanned: {scan_results["urls_scanned"]}')
            self.stdout.write(f'   Errors: {len(scan_results["errors"])}')

            if scan_results['errors']:
                self.stdout.write('\n⚠️  Errors encountered:')
                for error in scan_results['errors'][:5]:
                    self.stdout.write(f'   {error}')

            # Step 5: Get results
            self.stdout.write('\n' + '='*60)
            self.stdout.write('STEP 5: Results Retrieval')
            self.stdout.write('='*60)

            results = enhanced_manager.get_enhanced_results()

            self.stdout.write(self.style.SUCCESS('\n✅ Results retrieved:'))
            self.stdout.write(f'   Total vulnerabilities: {results["total_alerts"]}')

            # Group vulnerabilities by severity
            if results['vulnerabilities']:
                from collections import Counter
                severity_counts = Counter()

                for vuln in results['vulnerabilities']:
                    risk = vuln.get('risk', 'Unknown')
                    severity_counts[risk] += 1

                self.stdout.write('\n📊 Vulnerabilities by severity:')
                for severity, count in severity_counts.most_common():
                    self.stdout.write(f'   {severity}: {count}')

                # Show sample vulnerabilities
                self.stdout.write('\n🔍 Sample vulnerabilities:')
                for vuln in results['vulnerabilities'][:10]:
                    name = vuln.get('name', 'Unknown')
                    risk = vuln.get('risk', 'Unknown')
                    url = vuln.get('url', 'Unknown')
                    self.stdout.write(f'   [{risk}] {name}')
                    self.stdout.write(f'        URL: {url[:80]}')

                if len(results['vulnerabilities']) > 10:
                    self.stdout.write(f'   ... and {len(results["vulnerabilities"]) - 10} more')

            # Final summary
            self.stdout.write('\n' + '='*60)
            self.stdout.write('📈 SCAN SUMMARY')
            self.stdout.write('='*60)

            summary = enhanced_manager.get_scan_summary()
            self.stdout.write(f'Target: {summary["target_url"]}')
            self.stdout.write(f'Authenticated: {"✅ Yes" if summary["authenticated"] else "❌ No"}')
            if summary['auth_profile']:
                self.stdout.write(f'Auth Profile: {summary["auth_profile"]}')
            self.stdout.write(f'Total Targets Discovered: {summary["total_targets"]}')
            self.stdout.write(f'Priority Targets: {summary["priority_targets"]}')
            self.stdout.write(f'SQLi Test URLs: {summary["sqli_test_urls"]}')
            self.stdout.write(f'URLs Scanned: {scan_results["urls_scanned"]}')
            self.stdout.write(f'Vulnerabilities Found: {results["total_alerts"]}')

            self.stdout.write('\n' + self.style.SUCCESS('✅ Enhanced scan test complete!\n'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Enhanced scan test failed: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
