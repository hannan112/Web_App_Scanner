from django.core.management.base import BaseCommand
from scanning.models.scan import Scan, ScanConfiguration
from scanning.models.vulnerability import Vulnerability
from projects.models import Project
from authentication.models import CustomUser
from scanning.unified_engine import HEADER_VULNS, INJECTION_VULNS
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seeds database with a dummy Comprehensive Scan and Vulnerabilities for ML Testing'

    def handle(self, *args, **options):
        # 1. Create User & Project
        user, _ = CustomUser.objects.get_or_create(username="ml_tester", defaults={"email": "ml@test.com"})
        project, _ = Project.objects.get_or_create(name="ML Test Project", defaults={
            "target_url": "http://test-ml.com",
            "owner": user
        })
        
        # 2. Create Scan Configuration (Comprehensive)
        config = ScanConfiguration.objects.create(
            project=project,
            scan_type="comprehensive"
        )
        
        # 3. Create Scan (Completed)
        scan = Scan.objects.create(
            configuration=config,
            status="completed",
            target_url="http://test-ml.com",
            start_time=timezone.now(),
            end_time=timezone.now()
        )
        
        self.stdout.write(f"Created Scan ID: {scan.id}")

        # 4. Create Vulnerabilities
        
        # Case A: Likely FP (Header issue, No evidence, Low severity)
        v1 = Vulnerability.objects.create(
            scan=scan,
            name="Missing X-Frame-Options Header",
            severity="low",
            evidence="", 
            parameter="Not Applicable",
            url="http://test-ml.com",
            description="Header missing"
        )
        
        # Case B: Likely TP (SQL Injection, High severity, Evidence)
        v2 = Vulnerability.objects.create(
            scan=scan,
            name="SQL Injection",
            severity="high",
            evidence="' OR '1'='1",
            parameter="id",
            url="http://test-ml.com/product?id=1",
            description="SQLi detected"
        )
        
        self.stdout.write(f"Created 2 Vulnerabilities for Scan {scan.id}")
        self.stdout.write(f"V1: {v1.name} (Should be flagged FP)")
        self.stdout.write(f"V2: {v2.name} (Should NOT be flagged FP)")
