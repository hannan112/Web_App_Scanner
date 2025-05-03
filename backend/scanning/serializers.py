from rest_framework import serializers
from scanning.models.scan import (
    ScanConfiguration, Scan, 
    PassiveReconResult, CrawlResult, ScanLog
)
from scanning.models.vulnerability import Vulnerability

class ScanConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanConfiguration
        fields = ['id', 'project', 'scan_type', 'crawl_depth', 'respect_robots_txt', 'crawl_max_pages']
        extra_kwargs = {
            'project': {'required': True},
            'scan_type': {'required': True},
            'crawl_depth': {'required': False, 'default': 2},
            'respect_robots_txt': {'required': False, 'default': True},
            'crawl_max_pages': {'required': False, 'default': 50}
        }

    def validate_scan_type(self, value):
        valid_types = ['passive', 'active', 'full']
        if value not in valid_types:
            raise serializers.ValidationError(f"scan_type must be one of: {', '.join(valid_types)}")
        return value

class ScanSerializer(serializers.ModelSerializer):
    """Serializer for basic scan information"""
    project_id = serializers.PrimaryKeyRelatedField(source='project', read_only=True)
    configuration_name = serializers.StringRelatedField(source='configuration', read_only=True)
    
    class Meta:
        model = Scan
        fields = [
            'id', 'uuid', 'project', 'project_id', 'configuration', 'configuration_name',
            'status', 'progress', 'start_time', 'end_time', 
            'error_message', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'uuid', 'status', 'progress', 'start_time', 
            'end_time', 'error_message', 'created_at', 'updated_at', 
            'project_id', 'configuration_name'
        ]

class PassiveReconResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassiveReconResult
        fields = [
            'id', 'scan', 'dns_records', 'server_info', 
            'robots_txt', 'sitemap_xml', 'technologies', 
            'response_headers', 'created_at'
        ]
        read_only_fields = ['created_at']

class CrawlResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrawlResult
        fields = [
            'id', 'scan', 'urls_discovered', 'forms_discovered', 
            'cookies', 'pages_crawled', 'created_at'
        ]
        read_only_fields = ['created_at']

class VulnerabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vulnerability
        fields = [
            'id', 'scan', 'name', 'description', 'severity', 
            'url', 'parameter', 'evidence', 'confidence', 
            'remediation', 'created_at'
        ]
        read_only_fields = ['created_at']

class ScanLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanLog
        fields = ['id', 'scan', 'level', 'message', 'timestamp']
        read_only_fields = ['timestamp']

# Nested serializers for detailed views
class VulnerabilityDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vulnerability
        fields = [
            'id', 'name', 'description', 'severity', 
            'url', 'parameter', 'evidence', 'confidence', 
            'remediation', 'created_at'
        ]
        read_only_fields = ['created_at']

class ScanDetailSerializer(serializers.ModelSerializer):
    vulnerabilities = VulnerabilityDetailSerializer(many=True, read_only=True)
    configuration_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Scan
        fields = [
            'id', 'uuid', 'status', 'progress', 
            'start_time', 'end_time', 'error_message', 
            'created_at', 'updated_at', 'vulnerabilities',
            'configuration_details'
        ]
        read_only_fields = [
            'uuid', 'status', 'progress', 'start_time', 
            'end_time', 'error_message', 'created_at', 
            'updated_at', 'vulnerabilities', 'configuration_details'
        ]
    
    def get_configuration_details(self, obj):
        return ScanConfigurationSerializer(obj.configuration).data

class PassiveReconSummarySerializer(serializers.ModelSerializer):
    """Simplified serializer for including passive recon in scan results"""
    class Meta:
        model = PassiveReconResult
        fields = ['id', 'dns_records', 'server_info', 'technologies']

# Update this part in scanning/serializers.py

class ScanResultsSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for scan results page"""
    vulnerabilities = VulnerabilityDetailSerializer(many=True, read_only=True)
    configuration = ScanConfigurationSerializer(read_only=True)
    passive_data = serializers.SerializerMethodField()
    crawl_data = serializers.SerializerMethodField()
    project_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Scan
        fields = [
            'id', 'uuid', 'status', 'progress', 
            'start_time', 'end_time', 'error_message',
            'created_at', 'updated_at', 'configuration',
            'vulnerabilities', 'passive_data', 'crawl_data',
            'project_info'
        ]
    
    def get_project_info(self, obj):
        """Return basic project information"""
        if obj.project:
            return {
                'id': obj.project.id,
                'name': obj.project.name,
                'target_url': obj.project.target_url
            }
        return None
    
    def get_passive_data(self, obj):
        try:
            return PassiveReconResultSerializer(obj.passive_recon_result).data
        except PassiveReconResult.DoesNotExist:
            return None
    
    def get_crawl_data(self, obj):
        try:
            crawl = obj.crawl_result
            return {
                'pages_crawled': crawl.pages_crawled,
                'urls_count': len(crawl.urls_discovered) if crawl.urls_discovered else 0,
                'forms_count': len(crawl.forms_discovered) if crawl.forms_discovered else 0
            }
        except CrawlResult.DoesNotExist:
            return None