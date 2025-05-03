"""
Models for storing scan data
"""
from django.db import models
from django.utils import timezone
import uuid
from projects.models import Project

# Move ScanConfiguration, Scan, PassiveReconResult, CrawlResult, ScanLog from scanning/models.py
class ScanConfiguration(models.Model):
    """Model for storing scan configurations"""
    SCAN_TYPE_CHOICES = [
        ('passive', 'Passive Scan'),
        ('active', 'Active Scan'),
        ('full', 'Full Scan')
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='scan_configurations')
    scan_type = models.CharField(max_length=20, choices=SCAN_TYPE_CHOICES)
    
    # Crawler configuration
    crawl_depth = models.IntegerField(default=2)
    respect_robots_txt = models.BooleanField(default=True)
    crawl_max_pages = models.IntegerField(default=100)
    crawl_timeout = models.IntegerField(default=30)  # in seconds
    
    # Scan scope
    scan_js_files = models.BooleanField(default=True)
    scan_forms = models.BooleanField(default=True)
    
    # Advanced options
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    request_delay = models.FloatField(default=0.5)  # in seconds
    custom_headers = models.JSONField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.scan_type} Configuration"

class Scan(models.Model):
    """Model for storing scan sessions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('stopped', 'Stopped by User')
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='scans')
    configuration = models.ForeignKey(ScanConfiguration, on_delete=models.CASCADE, related_name='scans')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.FloatField(default=0.0)  # 0 to 100
    
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    error_message = models.TextField(blank=True, null=True)
    
    # For tracking Celery tasks
    task_id = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} Scan - {self.uuid}"
    
    def start(self):
        """Mark scan as started"""
        self.status = 'in_progress'
        self.start_time = timezone.now()
        self.save()
    
    def complete(self):
        """Mark scan as completed"""
        self.status = 'completed'
        self.progress = 100.0
        self.end_time = timezone.now()
        self.save()
    
    def fail(self, error_message):
        """Mark scan as failed with error message"""
        self.status = 'failed'
        self.error_message = error_message
        self.end_time = timezone.now()
        self.save()
    
    def stop(self):
        """Mark scan as stopped by user"""
        self.status = 'stopped'
        self.end_time = timezone.now()
        self.save()

class PassiveReconResult(models.Model):
    """Model for storing passive reconnaissance results"""
    scan = models.OneToOneField(Scan, on_delete=models.CASCADE, related_name='passive_recon_result')
    
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
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Passive Recon for {self.scan.project.name}"


class CrawlResult(models.Model):
    """Model for storing crawl results"""
    scan = models.OneToOneField(Scan, on_delete=models.CASCADE, related_name='crawl_result')
    
    # Discovered URLs
    urls_discovered = models.JSONField(blank=True, null=True)
    
    # Forms discovered
    forms_discovered = models.JSONField(blank=True, null=True)
    
    # Cookies
    cookies = models.JSONField(blank=True, null=True)
    
    # Pages visited count
    pages_crawled = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Crawl Results for {self.scan.project.name}"



class ScanLog(models.Model):
    """Model for storing scan logs"""
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name='logs')
    
    level = models.CharField(max_length=20)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.scan.project.name} Log - {self.timestamp}"