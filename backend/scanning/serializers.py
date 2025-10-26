from rest_framework import serializers

from scanning.models.scan import (
    ActiveScanResult,
    PassiveReconResult,
    Scan,
    ScanConfiguration,
    ScanLog,
)
from scanning.models.vulnerability import Vulnerability


class ScanConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for comprehensive scan configurations (passive, active, comprehensive)"""
    
    class Meta:
        model = ScanConfiguration
        fields = [
            "id",
            "project",
            "scan_type",
            "min_confidence",
            "user_agent",
            "request_timeout",
            
            # Passive scan tools
            "use_sslyze",
            "use_nuclei",
            "use_wappalyzer",
            "use_zap_passive",
            
            # Active scan settings
            "use_zap_active",
            "enable_spider",
            "enable_ajax_spider",
            "max_spider_depth",
            "max_spider_duration",
            
            # ZAP Active Scan Configuration
            "zap_attack_strength",
            "zap_active_scan_policy",
            
            # Vulnerability testing categories
            "test_sql_injection",
            "test_xss",
            "test_csrf",
            "test_authentication",
            "test_authorization",
            "test_session_management",
            "test_file_inclusion",
            "test_path_traversal",
            "test_command_injection",
            "test_xxe",
            
            # SQL Injection testing tools
            "use_sqlmap",
            "use_nosqlmap",
            "sqlmap_risk_level",
            "sqlmap_level",
            "sqlmap_timeout",
            
            # Rate limiting and safety
            "max_concurrent_requests",
            "request_delay_ms",
            "scan_timeout_minutes",
            
            # Enhanced discovery settings
            "use_enhanced_discovery",
            "discovery_timeout",
            "max_subdomains",
            "max_wayback_urls",
            "max_directories",
            
            # Parameter fuzzing settings
            "enable_parameter_fuzzing",
            "max_parameter_combinations",
            "max_parameters_per_url",
            "parameter_fuzzing_values",
            
            # Authentication settings
            "enable_authentication",
            "auth_login_url",
            "auth_username_field",
            "auth_password_field",
            "auth_username",
            "auth_password",
            "auth_success_indicators",
        ]
        extra_kwargs = {
            "project": {"required": True},
            "scan_type": {"required": True},
            "min_confidence": {"required": False, "default": 0.7},
            "user_agent": {"required": False, "default": None},
            "request_timeout": {"required": False, "default": 30},
        }

    def validate_scan_type(self, value):
        valid_types = ["passive", "active", "comprehensive"]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"scan_type must be one of: {', '.join(valid_types)}"
            )
        return value

    def validate(self, data):
        """Validate scan configuration based on scan type"""
        scan_type = data.get('scan_type')
        
        # Validate active scan settings if needed
        if scan_type in ['active', 'comprehensive']:
            # Ensure at least one active tool is enabled
            active_tools = [
                data.get('use_zap_active', False),
                data.get('enable_spider', False),
                data.get('enable_ajax_spider', False),
            ]
            if not any(active_tools):
                raise serializers.ValidationError(
                    "At least one active scanning tool must be enabled for active/comprehensive scans"
                )
        
        # Auto-enable SQLMap when SQL injection testing is enabled
        if data.get('test_sql_injection', False):
            data['use_sqlmap'] = True
            # Set reasonable defaults if not provided
            if 'sqlmap_risk_level' not in data:
                data['sqlmap_risk_level'] = 2
            if 'sqlmap_level' not in data:
                data['sqlmap_level'] = 2
            if 'sqlmap_timeout' not in data:
                data['sqlmap_timeout'] = 300
        
        return data


class PassiveReconResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassiveReconResult
        fields = [
            "id",
            "scan",
            "dns_records",
            "server_info",
            "robots_txt",
            "sitemap_xml",
            "technologies",
            "response_headers",
            "enhanced_discovery",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class ActiveScanResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveScanResult
        fields = [
            "id",
            "scan",
            "spider_results",
            "ajax_spider_results",
            "urls_discovered",
            "forms_discovered",
            "attack_surface",
            "raw_findings",
            "authentication_tests",
            "session_analysis",
            "zap_scan_id",
            "zap_spider_id",
            "zap_ajax_spider_id",
            "zap_active_scan_id",
            "total_requests_made",
            "total_responses_received",
            "scan_duration_seconds",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class VulnerabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vulnerability
        fields = [
            "id",
            "scan",
            "name",
            "description",
            "severity",
            "url",
            "parameter",
            "evidence",
            "confidence",
            "remediation",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class ScanLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanLog
        fields = [
            "id",
            "scan",
            "level",
            "message",
            "timestamp",
        ]
        read_only_fields = ["timestamp"]


class ScanResultsSerializer(serializers.ModelSerializer):
    """Serializer for comprehensive scan results"""
    passive_data = serializers.SerializerMethodField()
    passive_reconnaissance = serializers.SerializerMethodField()
    active_data = serializers.SerializerMethodField()
    vulnerabilities = serializers.SerializerMethodField()
    logs = serializers.SerializerMethodField()
    project_info = serializers.SerializerMethodField()
    project_id = serializers.SerializerMethodField()
    configuration_name = serializers.SerializerMethodField()

    class Meta:
        model = Scan
        fields = [
            "id",
            "uuid",
            "target_url",
            "status",
            "progress",
            "start_time",
            "end_time",
            "error_message",
            "created_at",
            "updated_at",
            "project_info",
            "project_id",
            "configuration_name",
            "passive_data",
            "passive_reconnaissance",
            "active_data",
            "vulnerabilities",
            "logs",
        ]
        read_only_fields = [
            "uuid",
            "status",
            "progress",
            "start_time",
            "end_time",
            "error_message",
            "created_at",
            "updated_at",
        ]

    def get_passive_data(self, obj):
        """Return passive reconnaissance data"""
        try:
            return PassiveReconResultSerializer(obj.passive_recon_result).data
        except PassiveReconResult.DoesNotExist:
            return None

    def get_passive_reconnaissance(self, obj):
        """Return passive reconnaissance data in legacy format for frontend compatibility"""
        try:
            passive_data = PassiveReconResultSerializer(obj.passive_recon_result).data
            return {
                "dns_records": passive_data.get('dns_records', {}),
                "server_info": passive_data.get('server_info', {}),
                "technologies": passive_data.get('technologies', {}),
                "response_headers": passive_data.get('response_headers', {}),
                "enhanced_discovery": passive_data.get('enhanced_discovery', {}),
            }
        except PassiveReconResult.DoesNotExist:
            return None

    def get_active_data(self, obj):
        """Return active scan data including discovered URLs and forms"""
        try:
            from scanning.models.scan import ActiveScanResult
            print(f"DEBUG: Looking for ActiveScanResult for scan {obj.id}")
            active_result = ActiveScanResult.objects.get(scan=obj)
            print(f"DEBUG: Found ActiveScanResult {active_result.id}")
            print(f"DEBUG: urls_discovered type: {type(active_result.urls_discovered)}")
            print(f"DEBUG: urls_discovered value: {active_result.urls_discovered}")
            print(f"DEBUG: urls_discovered length: {len(active_result.urls_discovered or [])}")
            print(f"DEBUG: forms_discovered type: {type(active_result.forms_discovered)}")
            print(f"DEBUG: forms_discovered value: {active_result.forms_discovered}")
            print(f"DEBUG: forms_discovered length: {len(active_result.forms_discovered or [])}")
            
            # Extract enhanced discovery stats if available
            enhanced_stats = {}
            if active_result.attack_surface and isinstance(active_result.attack_surface, dict):
                enhanced_stats = active_result.attack_surface.get('enhanced_stats', {})
            
            urls = active_result.urls_discovered or []
            forms = active_result.forms_discovered or []
            
            return {
                "urls_discovered": urls,
                "forms_discovered": forms,
                "spider_results": active_result.spider_results or {},
                "ajax_spider_results": active_result.ajax_spider_results or {},
                "attack_surface": active_result.attack_surface or {},
                "raw_findings": active_result.raw_findings or {},
                "authentication_tests": active_result.authentication_tests or {},
                "session_analysis": active_result.session_analysis or {},
                "total_urls": len(urls),
                "total_forms": len(forms),
                "zap_scan_id": active_result.zap_scan_id,
                "zap_spider_id": active_result.zap_spider_id,
                "zap_ajax_spider_id": active_result.zap_ajax_spider_id,
                "zap_active_scan_id": active_result.zap_active_scan_id,
                "total_requests_made": active_result.total_requests_made,
                "total_responses_received": active_result.total_responses_received,
                "scan_duration_seconds": active_result.scan_duration_seconds,
            }
        except ActiveScanResult.DoesNotExist:
            print(f"DEBUG: ActiveScanResult.DoesNotExist for scan {obj.id}")
            return {
                "error": "Active scan results not found. The scan may still be running or failed to save results.",
                "urls_discovered": [],
                "forms_discovered": [],
                "spider_results": {},
                "ajax_spider_results": {},
                "attack_surface": {},
                "raw_findings": {},
                "authentication_tests": {},
                "session_analysis": {},
                "total_urls": 0,
                "total_forms": 0,
                "zap_scan_id": None,
                "zap_spider_id": None,
                "zap_ajax_spider_id": None,
                "zap_active_scan_id": None,
                "total_requests_made": 0,
                "total_responses_received": 0,
                "scan_duration_seconds": 0,
            }
        except Exception as e:
            print(f"DEBUG: Exception in get_active_data for scan {obj.id}: {e}")
            return {
                "error": f"Error retrieving active scan results: {str(e)}",
                "urls_discovered": [],
                "forms_discovered": [],
                "spider_results": {},
                "ajax_spider_results": {},
                "attack_surface": {},
                "raw_findings": {},
                "authentication_tests": {},
                "session_analysis": {},
                "total_urls": 0,
                "total_forms": 0,
                "zap_scan_id": None,
                "zap_spider_id": None,
                "zap_ajax_spider_id": None,
                "zap_active_scan_id": None,
                "total_requests_made": 0,
                "total_responses_received": 0,
                "scan_duration_seconds": 0,
            }
    
    def _extract_api_endpoints(self, active_result):
        """Extract API endpoints from discovered URLs"""
        api_endpoints = []
        urls = active_result.urls_discovered or []
        
        api_indicators = ['api', 'rest', 'graphql', 'json', 'xml', 'service', '/v1/', '/v2/', '/v3/']
        
        for url in urls:
            if any(indicator in url.lower() for indicator in api_indicators):
                api_endpoints.append(url)
                
        return api_endpoints
    
    def _extract_js_endpoints(self, active_result):
        """Extract JavaScript/AJAX endpoints"""
        js_endpoints = []
        urls = active_result.urls_discovered or []
        
        js_indicators = ['ajax', 'xhr', 'fetch', 'async', 'callback', '.js']
        
        for url in urls:
            if any(indicator in url.lower() for indicator in js_indicators):
                js_endpoints.append(url)
                
        return js_endpoints

    def get_vulnerabilities(self, obj):
        """Return vulnerabilities found in the scan"""
        vulnerabilities = Vulnerability.objects.filter(scan=obj)
        return VulnerabilitySerializer(vulnerabilities, many=True).data

    def get_logs(self, obj):
        """Return scan logs"""
        logs = ScanLog.objects.filter(scan=obj).order_by('-timestamp')
        return ScanLogSerializer(logs, many=True).data

    def get_project_info(self, obj):
        """Return lightweight project info for header display"""
        try:
            if obj.configuration and obj.configuration.project:
                project = obj.configuration.project
                return {
                    "id": project.id,
                    "name": project.name,
                    "target_url": project.target_url,
                }
        except Exception:
            pass
        return None

    def get_project_id(self, obj):
        try:
            if obj.configuration and obj.configuration.project:
                return obj.configuration.project.id
        except Exception:
            pass
        return None

    def get_configuration_name(self, obj):
        try:
            if obj.configuration and hasattr(obj.configuration, 'scan_type'):
                return obj.configuration.scan_type
        except Exception:
            pass
        return None


class ScanSerializer(serializers.ModelSerializer):
    scan_type = serializers.SerializerMethodField()
    project_id = serializers.SerializerMethodField()
    configuration_name = serializers.SerializerMethodField()
    config = serializers.SerializerMethodField()

    class Meta:
        model = Scan
        fields = [
            "id",
            "uuid",
            "target_url",
            "configuration",
            "config",
            "status",
            "progress",
            "start_time",
            "end_time",
            "error_message",
            "created_at",
            "updated_at",
            "scan_type",
            "project_id",
            "configuration_name",
        ]
        read_only_fields = [
            "uuid",
            "status",
            "progress",
            "start_time",
            "end_time",
            "error_message",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "configuration": {"required": True},
        }

    def get_scan_type(self, obj):
        try:
            if obj.configuration and hasattr(obj.configuration, 'scan_type'):
                return obj.configuration.scan_type
            return None
        except Exception:
            # If there's any issue accessing the configuration, return None
            return None

    def get_project_id(self, obj):
        try:
            if obj.configuration and obj.configuration.project:
                return obj.configuration.project.id
            return None
        except Exception:
            return None

    def get_configuration_name(self, obj):
        try:
            if obj.configuration:
                return obj.configuration.get_scan_type_display()
            return None
        except Exception:
            return None

    def get_config(self, obj):
        try:
            if obj.configuration:
                return {
                    "scan_type": obj.configuration.scan_type,
                    "name": obj.configuration.get_scan_type_display(),
                }
            return None
        except Exception:
            return None
