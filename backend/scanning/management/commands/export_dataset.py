import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from scanning.models.vulnerability import Vulnerability
from scanning.models.scan import Scan

class Command(BaseCommand):
    help = 'Export vulnerabilities and scans to CSV in the dataset directory'

    def handle(self, *args, **options):
        dataset_dir = os.path.join(settings.BASE_DIR, 'dataset')
        os.makedirs(dataset_dir, exist_ok=True)

        # Export Vulnerabilities
        vulnerability_file = os.path.join(dataset_dir, 'vulnerabilities.csv')
        self.stdout.write(f'Exporting vulnerabilities to {vulnerability_file}...')
        
        with open(vulnerability_file, 'w', newline='') as csvfile:
            fieldnames = ['id', 'scan_id', 'name', 'severity', 'confidence', 'url', 'parameter', 'description', 'is_false_positive', 'ml_confidence', 'created_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            vulnerabilities = Vulnerability.objects.all()
            count = 0
            for v in vulnerabilities:
                writer.writerow({
                    'id': v.id,
                    'scan_id': v.scan.id,
                    'name': v.name,
                    'severity': v.severity,
                    'confidence': v.confidence,
                    'url': v.url,
                    'parameter': v.parameter,
                    'description': v.description.replace('\n', ' ').replace('\r', ''),
                    'is_false_positive': getattr(v, 'is_false_positive', ''),
                    'ml_confidence': getattr(v, 'ml_confidence', ''),
                    'created_at': v.created_at.isoformat(),
                })
                count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Successfully exported {count} vulnerabilities.'))

        # Export Scans
        scan_file = os.path.join(dataset_dir, 'scans.csv')
        self.stdout.write(f'Exporting scans to {scan_file}...')

        with open(scan_file, 'w', newline='') as csvfile:
            fieldnames = ['id', 'uuid', 'target_url', 'status', 'scan_type', 'is_baseline', 'created_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            scans = Scan.objects.all()
            count = 0
            for s in scans:
                writer.writerow({
                    'id': s.id,
                    'uuid': s.uuid,
                    'target_url': s.target_url,
                    'status': s.status,
                    'scan_type': s.configuration.scan_type,
                    'is_baseline': getattr(s, 'is_baseline', False),
                    'created_at': s.created_at.isoformat(),
                })
                count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Successfully exported {count} scans.'))
