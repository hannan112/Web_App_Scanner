from rest_framework import serializers
from scanning.models.scan import (
    AjaxSpiderResult, ScanConfiguration, Scan, 
    PassiveReconResult, CrawlResult, ScanLog
)
from scanning.models.vulnerability import Vulnerability

class ScanConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanConfiguration
        fields = ['id', 'project', 'scan_type', 'crawl_depth', 'respect_robots_txt', 'crawl_max_pages', 'reduce_false_positives',
            'use_sslyze',
            'use_zap',
            'use_nuclei',
            'use_wappalyzer',
            'min_confidence',
            'zap_config',
            'sslyze_config',
            'nuclei_config',
            'wappalyzer_config'] 
        extra_kwargs = {
            'project': {'required': True},
            'scan_type': {'required': True},
            'crawl_depth': {'required': False, 'default': 2},
            'respect_robots_txt': {'required': False, 'default': True},
            'crawl_max_pages': {'required': False, 'default': 50},
        }

    def validate_scan_type(self, value):
        valid_types = ['passive', 'active', 'full']
        if value not in valid_types:
            raise serializers.ValidationError(f"scan_type must be one of: {', '.join(valid_types)}")
        return value

class ScanConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanConfiguration
        fields = [
            'id', 'project', 'scan_type', 'crawl_depth', 'respect_robots_txt', 
            'crawl_max_pages', 'reduce_false_positives', 'min_confidence',
            'use_sslyze', 'use_zap', 'use_nuclei', 'use_wappalyzer',
            'zap_config', 'sslyze_config', 'nuclei_config', 'wappalyzer_config',
            'tool_preferences','allow_analyzer_fallbacks' 
        ] 
        extra_kwargs = {
            'project': {'required': True},
            'scan_type': {'required': True},
            'crawl_depth': {'required': False, 'default': 2},
            'respect_robots_txt': {'required': False, 'default': True},
            'crawl_max_pages': {'required': False, 'default': 50},
            'min_confidence': {'required': False, 'default': 0.7},
            'tool_preferences': {'required': False}
        }

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
    ajax_spider_data = serializers.SerializerMethodField()
    
    class Meta:
        model = Scan
        fields = [
            'id', 'uuid', 'status', 'progress', 
            'start_time', 'end_time', 'error_message',
            'created_at', 'updated_at', 'configuration',
            'vulnerabilities', 'passive_data', 'crawl_data',
            'project_info', 'ajax_spider_data'
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
        
    def get_ajax_spider_data(self, obj):
        try:
            result = obj.ajax_spider_result
            return AjaxSpiderResultSerializer(result).data
        except AjaxSpiderResult.DoesNotExist:
            return None
        

class AjaxSpiderResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AjaxSpiderResult
        fields = [
            'id', 'scan', 'urls_discovered', 'forms_discovered', 
            'ajax_requests', 'javascript_objects', 'start_time', 
            'end_time', 'duration', 'pages_crawled', 'created_at'
        ]
        read_only_fields = ['created_at']


class ScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = [
            'id', 'uuid', 'project', 'configuration', 'status', 
            'progress', 'start_time', 'end_time', 'error_message', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'uuid', 'status', 'progress', 'start_time', 
            'end_time', 'error_message', 'created_at', 'updated_at'
        ]