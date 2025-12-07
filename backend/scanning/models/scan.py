"""
Models for storing passive scan data
"""

import uuid

from django.db import models
from django.utils import timezone

from projects.models import Project


class ScanConfiguration(models.Model):
    """Enhanced scan configuration for passive, active, and comprehensive scans"""

    SCAN_TYPE_CHOICES = [
        ("passive", "Passive Scan"),
        ("active", "Active Scan"),
        ("comprehensive", "Comprehensive Scan (Passive + Active)"),
    ]

    ATTACK_STRENGTH_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("INSANE", "Insane"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="scan_configurations")
    scan_type = models.CharField(max_length=20, choices=SCAN_TYPE_CHOICES, default="passive")

    # Passive scan settings
    min_confidence = models.FloatField(default=0.7)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    request_timeout = models.IntegerField(default=30)

    # Tool configuration
    use_sslyze = models.BooleanField(default=True)
    use_nuclei = models.BooleanField(default=True)
    use_wappalyzer = models.BooleanField(default=True)
    use_zap_passive = models.BooleanField(default=True)
    
    # SQL Injection testing tools
    use_sqlmap = models.BooleanField(default=True)
    use_nosqlmap = models.BooleanField(default=False)
    sqlmap_risk_level = models.IntegerField(default=1, help_text="SQLMap risk level (1-3)")
    sqlmap_level = models.IntegerField(default=1, help_text="SQLMap level (1-5)")
    sqlmap_timeout = models.IntegerField(default=60, help_text="SQLMap timeout in seconds")

    # Active scan settings
    use_zap_active = models.BooleanField(default=True)
    enable_spider = models.BooleanField(default=True)
    enable_ajax_spider = models.BooleanField(default=True)
    max_spider_depth = models.IntegerField(default=3)
    max_spider_duration = models.IntegerField(default=300)  # 5 minutes in seconds
    
    # ZAP Active Scan Configuration
    zap_attack_strength = models.CharField(max_length=20, choices=ATTACK_STRENGTH_CHOICES, default="MEDIUM")
    zap_active_scan_policy = models.CharField(max_length=100, default="Default Policy")
    active_scan_timeout_minutes = models.IntegerField(default=30, help_text="Timeout for active scan phase in minutes")
    
    # Vulnerability testing categories
    test_sql_injection = models.BooleanField(default=True)
    test_xss = models.BooleanField(default=True)
    test_csrf = models.BooleanField(default=True)
    test_authentication = models.BooleanField(default=True)
    test_authorization = models.BooleanField(default=True)
    test_session_management = models.BooleanField(default=True)
    test_file_inclusion = models.BooleanField(default=True)
    test_path_traversal = models.BooleanField(default=True)
    test_command_injection = models.BooleanField(default=True)
    test_xxe = models.BooleanField(default=True)
    
    # Rate limiting and safety
    max_concurrent_requests = models.IntegerField(default=5)
    request_delay_ms = models.IntegerField(default=100)
    scan_timeout_minutes = models.IntegerField(default=60)
    
    # Enhanced discovery settings
    use_enhanced_discovery = models.BooleanField(default=True)
    discovery_timeout = models.IntegerField(default=30)
    max_subdomains = models.IntegerField(default=100)
    max_wayback_urls = models.IntegerField(default=200)
    max_directories = models.IntegerField(default=50)
    
    # Parameter fuzzing settings
    enable_parameter_fuzzing = models.BooleanField(default=True)
    max_parameter_combinations = models.IntegerField(default=50, help_text="Maximum parameter combinations to test per URL")
    max_parameters_per_url = models.IntegerField(default=10, help_text="Maximum parameters to test per URL")
    parameter_fuzzing_values = models.JSONField(default=list, help_text="Custom parameter values to test")
    
    # Authentication settings for authenticated applications
    enable_authentication = models.BooleanField(default=False, help_text="Enable authentication for authenticated applications")
    auth_login_url = models.URLField(blank=True, null=True, help_text="Login page URL")
    auth_username_field = models.CharField(max_length=100, default="username", help_text="Username field name")
    auth_password_field = models.CharField(max_length=100, default="password", help_text="Password field name")
    auth_username = models.CharField(max_length=255, blank=True, null=True, help_text="Username for authentication")
    auth_password = models.CharField(max_length=255, blank=True, null=True, help_text="Password for authentication")
    auth_success_indicators = models.JSONField(default=list, help_text="Indicators of successful authentication")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.get_scan_type_display()} Configuration"


class Scan(models.Model):
    """Enhanced scan model supporting passive, active, and comprehensive scans"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("stopping", "Stopping"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("stopped", "Stopped"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    configuration = models.ForeignKey(ScanConfiguration, on_delete=models.CASCADE, related_name="scans")
    target_url = models.URLField(blank=True, null=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    progress = models.FloatField(default=0.0)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    task_id = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.configuration.get_scan_type_display()} Scan - {self.uuid}"

    def fail(self, error_message: str):
        """Mark scan as failed with error message"""
        from django.utils import timezone
        self.status = "failed"
        self.error_message = error_message
        self.end_time = timezone.now()
        self.save()

    def complete(self):
        """Mark scan as completed"""
        from django.utils import timezone
        self.status = "completed"
        self.end_time = timezone.now()
        self.progress = 100.0
        self.save()


class PassiveReconResult(models.Model):
    """Model for storing passive reconnaissance results"""

    scan = models.OneToOneField(
        Scan, on_delete=models.CASCADE, related_name="passive_recon_result"
    )

    # DNS information
    dns_records = models.JSONField(blank=True, null=True)

    # Web server information
    server_info = models.JSONField(blank=True, null=True)

    # Robots.txt and sitemap
    robots_txt = models.TextField(blank=True, null=True)
    sitemap_xml = models.TextField(blank=True, null=True)

    # Technologies detected
    technologies = models.JSONField(blank=True, null=True)

    # Headers
    response_headers = models.JSONField(blank=True, null=True)

    # Enhanced discovery results
    enhanced_discovery = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Passive Recon for Scan {self.scan_id}"


class ScanLog(models.Model):
    """Model for storing scan logs"""

    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="logs")

    level = models.CharField(max_length=20)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan {self.scan_id} Log - {self.timestamp}"


class ActiveScanResult(models.Model):
    """Model for storing active scan results from ZAP and other active tools"""

    scan = models.OneToOneField(
        Scan, on_delete=models.CASCADE, related_name="active_scan_result"
    )

    # Spider results
    spider_results = models.JSONField(blank=True, null=True)
    ajax_spider_results = models.JSONField(blank=True, null=True)
    
    # URLs discovered during scanning
    urls_discovered = models.JSONField(blank=True, null=True)
    forms_discovered = models.JSONField(blank=True, null=True)
    
    # Attack surface mapping
    attack_surface = models.JSONField(blank=True, null=True)
    
    # Active vulnerability findings (raw from tools before processing)
    raw_findings = models.JSONField(blank=True, null=True)
    
    # Authentication test results
    authentication_tests = models.JSONField(blank=True, null=True)
    
    # Session management analysis
    session_analysis = models.JSONField(blank=True, null=True)
    
    # ZAP specific data
    zap_scan_id = models.CharField(max_length=100, blank=True, null=True)
    zap_spider_id = models.CharField(max_length=100, blank=True, null=True)
    zap_ajax_spider_id = models.CharField(max_length=100, blank=True, null=True)
    zap_active_scan_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Scan statistics
    total_requests_made = models.IntegerField(default=0)
    total_responses_received = models.IntegerField(default=0)
    scan_duration_seconds = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Active Scan Result for Scan {self.scan.uuid}"

    class Meta:
        verbose_name = "Active Scan Result"
        verbose_name_plural = "Active Scan Results"


    
