from django.core.management.base import BaseCommand
from scanning.models.scan import Scan
from scanning.unified_engine import UnifiedScanningEngine
import logging

class Command(BaseCommand):
    help = 'Manually run ML False Positive Reduction on a specific scan'

    def add_arguments(self, parser):
        parser.add_argument('scan_id', type=int, help='The ID of the scan to process')
        parser.add_argument('--force', action='store_true', help='Force run even if not comprehensive (use with caution)')

    def handle(self, *args, **options):
        scan_id = options['scan_id']
        force = options['force']
        
        try:
            scan = Scan.objects.get(id=scan_id)
        except Scan.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Scan "{scan_id}" does not exist'))
            return

        self.stdout.write(f"Found Scan: {scan} (Status: {scan.status}, Type: {scan.configuration.scan_type})")

        if scan.configuration.scan_type != 'comprehensive' and not force:
            self.stdout.write(self.style.ERROR('Scan is not comprehensive. ML reduction is restricted. Use --force to override.'))
            return

        engine = UnifiedScanningEngine(scan_id)
        # Manually inject configuration if needed, though engine init should load it via scan_id
        # The engine.__init__ loads self.scan and self.configuration in .start(), but we are calling a specific method.
        # We need to manually setup the engine state.
        engine.scan = scan
        engine.configuration = scan.configuration
        engine.target_url = scan.target_url

        self.stdout.write("Applying ML False Positive Reduction...")
        try:
            # We call the method directly. 
            # Note: We added a guard clause inside apply_ml_fp_reduction, so checking here is double safety.
            # If --force is used, we might need to temporarily mock/change the configuration type in memory 
            # if the strict guard check inside the method blocks us.
            
            if force and scan.configuration.scan_type != 'comprehensive':
                self.stdout.write(self.style.WARNING("Forcing execution on non-comprehensive scan..."))
                # Hack: Temporarily pretend it is comprehensive for the engine check
                original_type = engine.configuration.scan_type
                engine.configuration.scan_type = 'comprehensive'
                engine.apply_ml_fp_reduction()
                engine.configuration.scan_type = original_type
            else:
                 engine.apply_ml_fp_reduction()
                 
            self.stdout.write(self.style.SUCCESS('Successfully applied ML reduction.'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error applying ML reduction: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())
