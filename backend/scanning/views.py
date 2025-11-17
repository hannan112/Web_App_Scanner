# backend/scanning/views.py
import logging
import threading
import os
import shutil
import subprocess
from django.utils import timezone
from django.http import HttpResponse, JsonResponse

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .data_optimizer import ScanDataOptimizer

logger = logging.getLogger(__name__)

from projects.models import Project
# Import the unified scanning engine
from scanning.unified_engine import UnifiedScanningEngine
# Use the modular model structure imports
from scanning.models import (ActiveScanResult, PassiveReconResult, Scan,
                             ScanConfiguration, ScanLog, Vulnerability)

from .serializers import (ActiveScanResultSerializer, PassiveReconResultSerializer,
                          ScanConfigurationSerializer, ScanLogSerializer,
                          ScanResultsSerializer, ScanSerializer,
                          VulnerabilitySerializer)


class ScanConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing scan configurations"""

    serializer_class = ScanConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return scan configurations for projects owned by the current user"""
        return ScanConfiguration.objects.filter(project__owner=self.request.user)

    def perform_create(self, serializer):
        """Validate the user has access to the project"""
        project_id = self.request.data.get("project")
        project = get_object_or_404(Project, id=project_id, owner=self.request.user)
        
        # Debug logging
        logger.info(f"Creating scan configuration with data: {self.request.data}")
        
        try:
            serializer.save(project=project)
            logger.info(f"Scan configuration created successfully: {serializer.instance.id}")
        except Exception as e:
            logger.error(f"Error creating scan configuration: {str(e)}")
            logger.error(f"Serializer errors: {serializer.errors}")
            logger.error(f"Request data keys: {list(self.request.data.keys())}")
            raise
    
    def create(self, request, *args, **kwargs):
        """Override create to add validation error logging"""
        logger.info(f"ScanConfiguration create called with data: {request.data}")
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"ScanConfiguration create failed: {str(e)}")
            # Check if it's a validation error
            if hasattr(e, 'detail'):
                logger.error(f"Validation error details: {e.detail}")
            raise


class ScanViewSet(viewsets.ModelViewSet):
    """ViewSet for managing scans"""

    serializer_class = ScanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return scans for projects owned by the current user"""
        return Scan.objects.filter(configuration__project__owner=self.request.user)

    def get_serializer_class(self):
        """Return different serializer for detailed view"""
        if self.action == "retrieve" or self.action == "results":
            return ScanResultsSerializer
        return ScanSerializer

    def create(self, request):
        """Create a new scan with configuration"""
        # Debug logging
        logger.info(f"Creating scan with data: {request.data}")
        
        # Get configuration ID directly from request data
        config_id_raw = request.data.get("configuration")
        if not config_id_raw:
            return Response(
                {"error": "Configuration ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        logger.info(f"Config ID from request: {config_id_raw} (type: {type(config_id_raw)})")
        
        # Convert to integer if it's a string
        try:
            config_id = int(config_id_raw)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid configuration ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        logger.info(f"Converted config ID: {config_id}")
        
        # Get the configuration and verify user owns the project
        configuration = get_object_or_404(ScanConfiguration, id=config_id)
        project = configuration.project
        
        # Verify user owns the project
        if project.owner != request.user:
            return Response(
                {"error": "You don't have permission to access this project"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Enforce one running/pending scan per USER (not just per project)
        # This prevents CPU overload from multiple simultaneous scans
        try:
            # Check for ANY running scan for this user across ALL projects
            user_active_scans = Scan.objects.filter(
                configuration__project__owner=request.user,
                status__in=["pending", "running", "in_progress"],
            ).order_by("-start_time", "-created_at")

            # Reconcile stale statuses against the in-memory tracker
            if user_active_scans.exists():
                try:
                    from scanning.scan_tracker import get_scan_tracker
                    tracker = get_scan_tracker()
                    for candidate in list(user_active_scans):
                        if not tracker.is_scan_running(candidate.id):
                            # Auto-correct stale running/pending scan
                            candidate.status = "failed"
                            candidate.error_message = (candidate.error_message or "") + "\nAuto-corrected stale running status"
                            candidate.end_time = timezone.now()
                            candidate.save(update_fields=["status", "error_message", "end_time", "updated_at"])
                    # Refresh queryset after corrections
                    user_active_scans = Scan.objects.filter(
                        configuration__project__owner=request.user,
                        status__in=["pending", "running", "in_progress"],
                    ).order_by("-start_time", "-created_at")
                except Exception as reconcile_error:
                    logger.warning(f"Could not reconcile stale scans: {reconcile_error}")

            if user_active_scans.exists():
                active_scan = user_active_scans.first()
                active_project = active_scan.configuration.project if active_scan.configuration else None
                return Response(
                    {
                        "error": "You already have a scan running. Please wait for it to complete or stop it before starting a new scan.",
                        "active_scan_id": active_scan.id,
                        "active_scan_status": active_scan.status,
                        "active_project_id": active_project.id if active_project else None,
                        "active_project_name": active_project.name if active_project else "Unknown",
                        "active_target_url": active_scan.target_url or (active_project.target_url if active_project else None),
                    },
                    status=status.HTTP_409_CONFLICT,
                )
        except Exception as e:
            logger.warning(f"Could not check existing active scans: {e}")

        # Create scan with configuration and target_url from project
        scan = Scan.objects.create(
            configuration=configuration, 
            target_url=project.target_url,
            status="pending"
        )

        # Start the scan using our unified engine (supports passive, active, and comprehensive)
        engine = UnifiedScanningEngine(scan.id)
        
        try:
            logger.info(f"Starting scan engine for scan {scan.id}")
            # Optimistically mark as running so the UI begins polling immediately
            try:
                scan.status = "running"
                scan.start_time = timezone.now()
                scan.progress = 0.0
                scan.save(update_fields=["status", "start_time", "progress", "updated_at"])
            except Exception as e:
                logger.warning(f"Could not pre-mark scan {scan.id} as running: {e}")

            # Run engine in a background thread to allow real-time polling
            thread = threading.Thread(target=engine.start, daemon=True, name=f"scan-{scan.id}")
            engine.register_thread(thread)
            thread.start()

            logger.info(f"Scan {scan.id} started asynchronously")
            
        except Exception as e:
            logger.exception(f"Error during scan execution: {e}")
            scan.fail(f"Scan execution error: {str(e)}")
            return Response(
                {"error": f"Scan execution error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Return the scan data
        try:
            logger.info(f"Attempting to return scan data for scan {scan.id}")
            
            # Use the existing scan object instead of querying the database again
            logger.info(f"Using existing scan object, status: {scan.status}")
            
            # Return the full scan object using the proper serializer
            logger.info(f"Preparing full scan response for scan {scan.id}")
            serializer = self.get_serializer(scan)
            response_data = serializer.data
            logger.info(f"Full scan response prepared for scan {scan.id}")
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.exception(f"Error returning scan response: {e}")
            return Response(
                {"error": f"Error returning scan response: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def stop(self, request, pk=None):
        """Stop a running scan"""
        scan = self.get_object()

        # Accept legacy 'in_progress' as running
        if scan.status not in ["running", "in_progress"]:
            return Response(
                {"error": "Can only stop scans that are in progress"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Use the scan tracker to stop the scan
        try:
            from scanning.scan_tracker import get_scan_tracker
            tracker = get_scan_tracker()
            
            success = tracker.stop_scan(scan.id)
            
            if success:
                # Refresh scan object to get updated status
                scan.refresh_from_db()
                return Response({
                    "message": "Scan stopped successfully",
                    "status": scan.status,
                    "end_time": scan.end_time
                })
            else:
                # Try to update scan status directly if tracker fails
                scan.status = "stopped"
                scan.end_time = timezone.now()
                scan.save()
                
                return Response({
                    "message": "Scan stop initiated (may take a few moments to complete)",
                    "status": scan.status,
                    "end_time": scan.end_time
                })
                
        except Exception as e:
            logger.error(f"Error stopping scan {scan.id}: {e}")
            return Response(
                {"error": f"Error stopping scan: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def force_stop(self, request, pk=None):
        """Force stop a scan using Docker-level termination (emergency stop)"""
        scan = self.get_object()

        try:
            import subprocess

            logger.warning(f"⚠️ FORCE STOP requested for scan {scan.id}")

            # Step 1: Try normal stop first
            from scanning.scan_tracker import get_scan_tracker
            tracker = get_scan_tracker()
            tracker.stop_scan(scan.id)

            # Step 2: Force kill ZAP browser processes
            logger.info("🔴 Force killing AJAX spider browser processes...")
            try:
                subprocess.run(
                    ["docker", "exec", "zap", "pkill", "-9", "-f", "firefox"],
                    capture_output=True,
                    timeout=5
                )
                logger.info("Sent SIGKILL to firefox processes")
            except Exception as e:
                logger.warning(f"Firefox force kill failed: {e}")

            try:
                subprocess.run(
                    ["docker", "exec", "zap", "pkill", "-9", "-f", "chrome"],
                    capture_output=True,
                    timeout=5
                )
                logger.info("Sent SIGKILL to chrome processes")
            except Exception as e:
                logger.warning(f"Chrome force kill failed: {e}")

            # Step 3: Kill all Java processes in ZAP (nuclear option)
            # logger.warning("🔴🔴🔴 NUCLEAR: Killing all ZAP Java processes...")
            # try:
            #     subprocess.run(
            #         ["docker", "exec", "zap", "pkill", "-9", "-f", "java"],
            #         capture_output=True,
            #         timeout=5
            #     )
            #     logger.info("Sent SIGKILL to Java processes (ZAP will restart)")
            # except Exception as e:
            #     logger.warning(f"Java process kill failed: {e}")

            # Step 4: Update scan status
            scan.refresh_from_db()
            scan.status = 'stopped'
            scan.end_time = timezone.now()
            scan.save()

            from scanning.models.scan import ScanLog
            ScanLog.objects.create(
                scan=scan,
                level='WARNING',
                message="Scan FORCE STOPPED by user (Docker-level termination)"
            )

            logger.warning(f"✅ Scan {scan.id} FORCE STOPPED")

            return Response({
                "message": "Scan force stopped (Docker-level termination)",
                "status": scan.status,
                "warning": "ZAP browser processes were forcibly killed",
                "end_time": scan.end_time
            })

        except Exception as e:
            logger.error(f"Error force stopping scan {scan.id}: {e}")
            return Response(
                {"error": f"Error force stopping scan: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def download_raw_data(self, request, pk=None):
        """Download complete raw scan data for manual analysis"""
        try:
            scan = self.get_object()

            # Get data type requested
            data_type = request.GET.get('type', 'all')  # all, vulnerabilities, ajax_spider, raw_findings

            if data_type == 'vulnerabilities':
                data = list(Vulnerability.objects.filter(scan=scan).values())
                filename = f'scan_{scan.id}_vulnerabilities.json'
            elif data_type == 'ajax_spider':
                try:
                    active_results = ActiveScanResult.objects.get(scan=scan)
                    data = active_results.ajax_spider_results
                    filename = f'scan_{scan.id}_ajax_spider.json'
                except ActiveScanResult.DoesNotExist:
                    data = {"error": "No AJAX spider data found"}
                    filename = f'scan_{scan.id}_ajax_spider_empty.json'
            elif data_type == 'raw_findings':
                try:
                    active_results = ActiveScanResult.objects.get(scan=scan)
                    data = active_results.raw_findings
                    filename = f'scan_{scan.id}_raw_findings.json'
                except ActiveScanResult.DoesNotExist:
                    data = {"error": "No raw findings data found"}
                    filename = f'scan_{scan.id}_raw_findings_empty.json'
            else:  # data_type == 'all'
                # Complete scan export
                data = {
                    'scan_info': {
                        'id': scan.id,
                        'uuid': scan.uuid,
                        'target_url': scan.target_url,
                        'status': scan.status,
                        'start_time': scan.start_time,
                        'end_time': scan.end_time,
                        'created_at': scan.created_at,
                        'updated_at': scan.updated_at
                    },
                    'vulnerabilities': list(Vulnerability.objects.filter(scan=scan).values()),
                    'scan_logs': list(ScanLog.objects.filter(scan=scan).values()),
                }

                # Add active scan data if available
                try:
                    active_results = ActiveScanResult.objects.get(scan=scan)
                    data['active_scan_results'] = {
                        'ajax_spider_results': active_results.ajax_spider_results,
                        'raw_findings': active_results.raw_findings,
                        'spider_results': active_results.spider_results,
                        'urls_discovered': active_results.urls_discovered,
                        'forms_discovered': active_results.forms_discovered,
                        'attack_surface': active_results.attack_surface,
                        'authentication_tests': active_results.authentication_tests,
                        'session_analysis': active_results.session_analysis
                    }
                except ActiveScanResult.DoesNotExist:
                    data['active_scan_results'] = None

                # Add passive scan data if available
                try:
                    passive_results = PassiveReconResult.objects.get(scan=scan)
                    data['passive_scan_results'] = {
                        'dns_records': passive_results.dns_records,
                        'server_info': passive_results.server_info,
                        'robots_txt': passive_results.robots_txt,
                        'sitemap_xml': passive_results.sitemap_xml,
                        'technologies': passive_results.technologies,
                        'response_headers': passive_results.response_headers
                    }
                except PassiveReconResult.DoesNotExist:
                    data['passive_scan_results'] = None

                filename = f'scan_{scan.id}_complete_data.json'

            # Return JSON download response
            from django.http import JsonResponse, HttpResponse
            import json

            response = HttpResponse(
                json.dumps(data, indent=2, default=str),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(response.content)

            return response

        except Exception as e:
            logger.error(f"Error downloading raw data: {str(e)}")
            return Response(
                {"error": f"Error downloading raw data: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def results(self, request, pk=None):
        """Get comprehensive scan results with optimized data size"""
        try:
            scan = self.get_object()

            # Add pagination parameters
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 50))
            limit_vulnerabilities = request.GET.get('limit_vulnerabilities', 'true').lower() == 'true'

            # Add project information to response via configuration
            if hasattr(scan, "configuration") and scan.configuration and scan.configuration.project:
                project_data = {
                    "id": scan.configuration.project.id,
                    "name": scan.configuration.project.name,
                    "target_url": scan.configuration.project.target_url,
                }
            else:
                project_data = None

            # Get basic scan data
            scan_data = {
                "id": scan.id,
                "uuid": scan.uuid,
                "target_url": scan.target_url,
                "status": scan.status,
                "progress": scan.progress,
                "start_time": scan.start_time,
                "end_time": scan.end_time,
                "error_message": scan.error_message,
                "created_at": scan.created_at,
                "updated_at": scan.updated_at,
                "project": project_data,
                "project_info": project_data,  # Add project_info for frontend compatibility
                "project_id": scan.configuration.project.id if scan.configuration and scan.configuration.project else None,
                # Add missing scanType field that frontend expects
                "scanType": scan.configuration.scan_type if scan.configuration else "unknown",
                "scan_type": scan.configuration.scan_type if scan.configuration else "unknown",  # Alternative field name
                "configuration_name": scan.configuration.get_scan_type_display() if scan.configuration else "Unknown",
            }

            # Get passive reconnaissance results if available
            try:
                passive_results = PassiveReconResult.objects.get(scan=scan)
                passive_data = PassiveReconResultSerializer(passive_results).data
                
                # Transform database fields to match scanner output format
                # The scanner generates comprehensive results that need to be properly mapped
                comprehensive_data = {
                    "dns_analysis": passive_data.get('dns_records', {}),
                    "target_info": passive_data.get('server_info', {}),
                    "technology_detection": passive_data.get('technologies', {}),
                    "security_headers": passive_data.get('response_headers', {}),
                    "ssl_analysis": {},  # Will be populated from scan logs if available
                    "content_analysis": {},  # Will be populated from scan logs if available
                    "cookie_analysis": {},  # Will be populated from scan logs if available
                    "vulnerabilities": [],
                    "vulnerability_summary": {}
                }
                
                # Try to extract additional information from scan logs
                scan_logs = ScanLog.objects.filter(scan=scan).order_by('timestamp')
                for log in scan_logs:
                    if 'SSL analysis completed' in log.message:
                        comprehensive_data["ssl_analysis"] = {"status": "completed"}
                    elif 'Content analysis completed' in log.message:
                        comprehensive_data["content_analysis"] = {"status": "completed"}
                    elif 'Cookie analysis completed' in log.message:
                        comprehensive_data["cookie_analysis"] = {"status": "completed"}
                    elif 'Vulnerability aggregation completed' in log.message:
                        # Extract vulnerability count from log message
                        if 'findings' in log.message:
                            try:
                                import re
                                match = re.search(r'(\d+) findings', log.message)
                                if match:
                                    comprehensive_data["vulnerability_summary"]["total_count"] = int(match.group(1))
                            except:
                                pass
                
                # Add the comprehensive data to scan_data with the key that frontend expects
                scan_data["passive_data"] = comprehensive_data
                # Also provide legacy shape used by the frontend component props fallback
                scan_data["passive_reconnaissance"] = {
                    "dns_records": passive_data.get('dns_records', {}),
                    "server_info": passive_data.get('server_info', {}),
                    "technologies": passive_data.get('technologies', {}),  # This contains the full technology_detection object
                    "response_headers": passive_data.get('response_headers', {}),
                    "enhanced_discovery": passive_data.get('enhanced_discovery', {}),  # ADD ENHANCED DISCOVERY
                }
                
            except PassiveReconResult.DoesNotExist:
                scan_data["passive_data"] = {
                    "error": "Passive reconnaissance results not found. The scan may still be running or failed to save results."
                }

            # Get active scan results if available (OPTIMIZED)
            try:
                active_results = ActiveScanResult.objects.get(scan=scan)
                active_data = ActiveScanResultSerializer(active_results).data

                # Initialize the data optimizer
                try:
                    optimizer = ScanDataOptimizer()
                except ImportError as e:
                    logger.error(f"Could not import ScanDataOptimizer: {e}")
                    optimizer = None

                # Check if this is a request for optimized data
                # Allow disabling optimization with ?optimize=false for debugging
                optimize_data = request.GET.get('optimize', 'false').lower() == 'true' and optimizer is not None
                spider_page = int(request.GET.get('spider_page', 1))
                ajax_page = int(request.GET.get('ajax_page', 1))

                if optimize_data and optimizer:
                    try:
                        # Optimize spider results
                        spider_data = active_data.get("spider_results") or {}
                        optimized_spider = optimizer.optimize_spider_results(
                            spider_data, page=spider_page, page_size=50
                        )

                        # Optimize AJAX spider results
                        ajax_data = active_data.get("ajax_spider_results") or {}
                        optimized_ajax = optimizer.optimize_ajax_spider_results(
                            ajax_data, page=ajax_page, page_size=30
                        )

                        # Create optimized active data with clean, displayable information
                        active_recon_data = {
                            # Spider results - filtered and paginated URLs
                            "urls_discovered": optimized_spider["urls"]["data"],
                            "urls_pagination": optimized_spider["urls"]["pagination"],
                            "urls_stats": optimized_spider["statistics"],
                            "forms_discovered": optimized_spider["forms"]["data"],

                            # AJAX results - only security-relevant information
                            "ajax_security_endpoints": optimized_ajax.get("security_relevant_endpoints", {}).get("data", []),
                            "ajax_api_endpoints": optimized_ajax.get("api_endpoints", []),
                            "ajax_dynamic_forms": optimized_ajax.get("dynamic_forms", []),
                            "ajax_auth_endpoints": optimized_ajax.get("authentication_endpoints", []),
                            "ajax_sensitive_data": optimized_ajax.get("sensitive_data_findings", []),
                            "ajax_summary": optimized_ajax.get("summary", {}),

                            # Keep original structures for compatibility but mark as legacy
                            "spider_results": optimized_spider,
                            "ajax_spider_results": {
                                "security_summary": optimized_ajax.get("summary", {}),
                                "displayable_data": {
                                    "security_endpoints": optimized_ajax.get("security_relevant_endpoints", {}).get("data", []),
                                    "api_endpoints": optimized_ajax.get("api_endpoints", [])[:10],  # Top 10 for display
                                    "auth_endpoints": optimized_ajax.get("authentication_endpoints", [])[:5],  # Top 5 for display
                                },
                                "optimization_applied": True,
                                "note": "Raw AJAX data has been processed to show only security-relevant information"
                            },

                            # Other scan data
                            "attack_surface": active_data.get("attack_surface") or {},
                            "raw_findings": active_data.get("raw_findings") or {},
                            "authentication_tests": active_data.get("authentication_tests") or {},
                            "session_analysis": active_data.get("session_analysis") or {},

                            # Optimization metadata
                            "optimization_info": {
                                "optimized": True,
                                "spider_data_size_mb": optimized_spider.get("data_size_mb", 0),
                                "ajax_data_processed": True,
                                "ajax_endpoints_analyzed": optimized_ajax.get("summary", {}).get("total_endpoints_analyzed", 0),
                                "security_relevant_found": {
                                    "api_endpoints": len(optimized_ajax.get("api_endpoints", [])),
                                    "auth_endpoints": len(optimized_ajax.get("authentication_endpoints", [])),
                                    "sensitive_data_issues": len(optimized_ajax.get("sensitive_data_findings", []))
                                }
                            }
                        }
                    except Exception as opt_error:
                        logger.error(f"Error during data optimization: {opt_error}")
                        # Fall back to unoptimized data
                        active_recon_data = {
                            "urls_discovered": active_data.get("urls_discovered") or [],
                            "forms_discovered": active_data.get("forms_discovered") or [],
                            "spider_results": active_data.get("spider_results") or {},
                            "ajax_spider_results": active_data.get("ajax_spider_results") or {},
                            "attack_surface": active_data.get("attack_surface") or {},
                            "raw_findings": active_data.get("raw_findings") or {},
                            "authentication_tests": active_data.get("authentication_tests") or {},
                            "session_analysis": active_data.get("session_analysis") or {}
                        }
                else:
                    # Legacy unoptimized data (use with caution for large datasets)
                    active_recon_data = {
                        "urls_discovered": active_data.get("urls_discovered") or [],
                        "forms_discovered": active_data.get("forms_discovered") or [],
                        "spider_results": active_data.get("spider_results") or {},
                        "ajax_spider_results": active_data.get("ajax_spider_results") or {},
                        "attack_surface": active_data.get("attack_surface") or {},
                        "raw_findings": active_data.get("raw_findings") or {},
                        "authentication_tests": active_data.get("authentication_tests") or {},
                        "session_analysis": active_data.get("session_analysis") or {}
                    }

                # Ensure proper data format for frontend
                if not isinstance(active_recon_data.get("urls_discovered"), list):
                    active_recon_data["urls_discovered"] = []
                if not isinstance(active_recon_data.get("forms_discovered"), list):
                    active_recon_data["forms_discovered"] = []

                # Add the missing fields that frontend expects
                active_recon_data["api_endpoints"] = active_recon_data.get("api_endpoints", [])
                active_recon_data["js_endpoints"] = active_recon_data.get("js_endpoints", [])
                active_recon_data["total_urls"] = len(active_recon_data.get("urls_discovered", []))
                active_recon_data["total_forms"] = len(active_recon_data.get("forms_discovered", []))
                
                scan_data["active_data"] = active_recon_data
                
            except ActiveScanResult.DoesNotExist:
                scan_data["active_data"] = {
                    "error": "Active scan results not found. The scan may still be running or failed to save results.",
                    "urls_discovered": [],
                    "forms_discovered": [],
                    "spider_results": {},
                    "ajax_spider_results": {},
                    "attack_surface": {},
                    "raw_findings": {},
                    "authentication_tests": {},
                    "session_analysis": {}
                }

            # Get vulnerabilities if any (with pagination and size optimization)
            try:
                vulnerabilities = Vulnerability.objects.filter(scan=scan)
                if vulnerabilities.exists():
                    if limit_vulnerabilities:
                        # Limit vulnerabilities to prevent massive responses
                        limited_vulnerabilities = vulnerabilities[:100]  # Limit to first 100
                        vuln_data = VulnerabilitySerializer(limited_vulnerabilities, many=True).data

                        # Truncate evidence fields to prevent huge responses
                        for vuln in vuln_data:
                            if vuln.get('evidence') and len(str(vuln['evidence'])) > 10000:
                                vuln['evidence'] = str(vuln['evidence'])[:10000] + "... [truncated]"

                        scan_data["vulnerabilities"] = vuln_data
                        scan_data["vulnerability_summary"] = {
                            "total_count": vulnerabilities.count(),
                            "showing_count": len(vuln_data),
                            "truncated": vulnerabilities.count() > 100
                        }
                    else:
                        # Full vulnerabilities (use with caution)
                        scan_data["vulnerabilities"] = VulnerabilitySerializer(vulnerabilities, many=True).data
                else:
                    scan_data["vulnerabilities"] = []
            except Exception as e:
                scan_data["vulnerabilities"] = {"error": f"Failed to retrieve vulnerabilities: {str(e)}"}

            # Get scan logs
            try:
                logs = ScanLog.objects.filter(scan=scan).order_by("-timestamp")
                scan_data["logs"] = ScanLogSerializer(logs, many=True).data
            except Exception as e:
                scan_data["logs"] = {"error": f"Failed to retrieve logs: {str(e)}"}

            # Add summary statistics (calculate from database, not from serialized data)
            try:
                vuln_queryset = Vulnerability.objects.filter(scan=scan)
                scan_data["summary"] = {
                    "total_vulnerabilities": vuln_queryset.count(),
                    "critical_count": vuln_queryset.filter(severity="critical").count(),
                    "high_count": vuln_queryset.filter(severity="high").count(),
                    "medium_count": vuln_queryset.filter(severity="medium").count(),
                    "low_count": vuln_queryset.filter(severity="low").count(),
                    "info_count": vuln_queryset.filter(severity="info").count(),
                }
            except Exception as e:
                logger.error(f"Error calculating vulnerability statistics: {str(e)}")
                scan_data["summary"] = {
                    "total_vulnerabilities": 0,
                    "critical_count": 0,
                    "high_count": 0,
                    "medium_count": 0,
                    "low_count": 0,
                    "info_count": 0,
                }

            return Response(scan_data)
        except Exception as e:
            import traceback
            logger.error(f"Error retrieving scan results: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response(
                {"error": f"Error retrieving scan results: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        """Get current scan status and progress"""
        try:
            scan = self.get_object()

            project_info = None
            if scan.configuration and scan.configuration.project:
                project_info = {
                    "id": scan.configuration.project.id,
                    "name": scan.configuration.project.name,
                    "target_url": scan.configuration.project.target_url,
                }

            data = {
                "id": scan.id,
                "status": scan.status,
                "progress": scan.progress,
                "started_at": scan.start_time,
                "completed_at": scan.end_time,
                "created_at": scan.created_at,
                "error": scan.error_message,
                "project_id": scan.configuration.project.id if scan.configuration and scan.configuration.project else None,
                "project_info": project_info,
                "configuration_name": scan.configuration.scan_type if scan.configuration else "Standard",
                "scan_type": scan.configuration.scan_type if scan.configuration else None,
            }

            return Response(data)
        except Exception as e:
            logger.error(f"Error retrieving scan status: {str(e)}")
            return Response(
                {"error": f"Error retrieving scan status: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def logs(self, request, pk=None):
        """Get logs for a scan"""
        try:
            scan = self.get_object()
            logs = ScanLog.objects.filter(scan=scan).order_by("-timestamp")
            serializer = ScanLogSerializer(logs, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving scan logs: {str(e)}")
            return Response(
                {"error": f"Error retrieving scan logs: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def vulnerabilities(self, request, pk=None):
        """Get vulnerabilities discovered in a scan"""
        try:
            scan = self.get_object()
            vulnerabilities = Vulnerability.objects.filter(scan=scan)

            # Filter by severity if specified
            severity = request.query_params.get("severity")
            if severity:
                vulnerabilities = vulnerabilities.filter(severity=severity)

            serializer = VulnerabilitySerializer(vulnerabilities, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving vulnerabilities: {str(e)}")
            return Response(
                {"error": f"Error retrieving vulnerabilities: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def passive(self, request, pk=None):
        """Get passive reconnaissance results"""
        try:
            scan = self.get_object()
            try:
                results = PassiveReconResult.objects.get(scan=scan)
                serializer = PassiveReconResultSerializer(results)
                return Response(serializer.data)
            except PassiveReconResult.DoesNotExist:
                return Response(
                    {"error": "Passive reconnaissance results not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except Exception as e:
            logger.error(f"Error retrieving passive recon results: {str(e)}")
            return Response(
                {"error": f"Error retrieving passive recon results: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def crawl(self, request, pk=None):
        """Get crawl results"""
        # The CrawlResult model was removed, so this will cause an error.
        # Assuming the intent was to remove this action or update it.
        # For now, keeping it as is, but it will fail.
        # try:
        #     scan = self.get_object()
        #     try:
        #         results = CrawlResult.objects.get(scan=scan)
        #         serializer = CrawlResultSerializer(results)
        #         return Response(serializer.data)
        #     except CrawlResult.DoesNotExist:
        #         return Response(
        #             {"error": "Crawl results not found"},
        #             status=status.HTTP_404_NOT_FOUND,
        #         )
        # except Exception as e:
        #     logger.error(f"Error retrieving crawl results: {str(e)}")
        #     return Response(
        #         {"error": f"Error retrieving crawl results: {str(e)}"},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     )
        return Response(
            {"error": "Crawl functionality is currently unavailable."},
            status=status.HTTP_501_NOT_IMPLEMENTED, # 501 Not Implemented
        )

    @action(detail=True, methods=["post"])
    def report(self, request, pk=None):
        """Generate a PDF report for the scan"""
        try:
            scan = self.get_object()

            # For completed scans only
            if scan.status != "completed":
                return Response(
                    {"error": "Reports are only available for completed scans"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # TODO: Implement report generation
            # For now, return a mock response
            return Response(
                {"message": "Report generation initiated"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return Response(
                {"error": f"Error generating report: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def progress(self, request, pk=None):
        """Get real-time scan progress and recent logs"""
        try:
            # Debug logging for authentication issues
            logger.debug(f"Progress request for scan {pk} by user {request.user}")
            scan = self.get_object()
            
            # Get recent logs for progress tracking
            recent_logs = ScanLog.objects.filter(scan=scan).order_by("-timestamp")[:10]
            
            # Get project information
            project_info = None
            if scan.configuration and scan.configuration.project:
                project_info = {
                    "id": scan.configuration.project.id,
                    "name": scan.configuration.project.name,
                    "target_url": scan.configuration.project.target_url,
                }
            
            progress_data = {
                "id": scan.id,
                "status": scan.status,
                "progress": scan.progress,
                "start_time": scan.start_time,
                "end_time": scan.end_time,
                "error_message": scan.error_message,
                "recent_logs": ScanLogSerializer(recent_logs, many=True).data,
                "is_complete": scan.status in ['completed', 'failed'],
                "estimated_time_remaining": None,
                "project_info": project_info,
                "project_id": scan.configuration.project.id if scan.configuration and scan.configuration.project else None,
                "configuration_name": scan.configuration.scan_type if scan.configuration else "Standard",
                "scan_type": scan.configuration.scan_type if scan.configuration else None,
            }
            
            # Calculate estimated time remaining if scan is running
            if scan.status in ['running', 'in_progress'] and scan.start_time:
                elapsed = timezone.now() - scan.start_time
                if scan.progress > 0:
                    total_estimated = elapsed.total_seconds() * (100 / scan.progress)
                    remaining_seconds = total_estimated - elapsed.total_seconds()
                    if remaining_seconds > 0:
                        progress_data["estimated_time_remaining"] = int(remaining_seconds)
            
            return Response(progress_data)
            
        except Exception as e:
            logger.error(f"Error retrieving scan progress: {str(e)}")
            return Response(
                {"error": f"Error retrieving scan progress: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def statistics(self, request, pk=None):
        """Get active scan statistics"""
        try:
            scan = self.get_object()
            
            # Check if it's an active scan
            if not scan.configuration or scan.configuration.scan_type not in ['active', 'comprehensive']:
                return Response(
                    {"error": "Statistics are only available for active and comprehensive scans"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Get active scan results if available
            stats = {
                "spider_urls_found": 0,
                "ajax_spider_urls_found": 0,
                "total_vulnerabilities": 0,
                "vulnerability_severity_breakdown": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "info": 0,
                },
                "scan_duration": "0:00:00",
                "zap_version": "Unknown",
            }
            
            # Try to get active scan results
            try:
                active_results = ActiveScanResult.objects.get(scan=scan)
                if active_results.spider_results:
                    stats["spider_urls_found"] = len(active_results.spider_results.get("urls", []))
                if active_results.ajax_spider_results:
                    stats["ajax_spider_urls_found"] = len(active_results.ajax_spider_results.get("urls", []))
            except ActiveScanResult.DoesNotExist:
                pass
            
            # Get vulnerability stats
            vulnerabilities = Vulnerability.objects.filter(scan=scan)
            stats["total_vulnerabilities"] = vulnerabilities.count()
            
            for severity in ["critical", "high", "medium", "low", "info"]:
                stats["vulnerability_severity_breakdown"][severity] = vulnerabilities.filter(severity=severity).count()
            
            # Calculate scan duration
            if scan.start_time:
                end_time = scan.end_time or timezone.now()
                duration = end_time - scan.start_time
                hours, remainder = divmod(duration.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                stats["scan_duration"] = f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
            
            # Try to get ZAP version
            try:
                zap_status = _check_zap_detailed()
                if zap_status.get("version"):
                    stats["zap_version"] = zap_status["version"]
            except:
                pass
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"Error retrieving scan statistics: {str(e)}")
            return Response(
                {"error": f"Error retrieving scan statistics: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def spider_data(self, request, pk=None):
        """Get optimized spider data with pagination"""
        try:
            scan = self.get_object()

            # Check if it's an active or comprehensive scan
            if not scan.configuration or scan.configuration.scan_type not in ['active', 'comprehensive']:
                return Response(
                    {"error": "Spider data is only available for active and comprehensive scans"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get pagination parameters
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 50)), 200)  # Max 200 per page

            try:
                active_results = ActiveScanResult.objects.get(scan=scan)
                spider_data = active_results.spider_results or {}

                # Initialize optimizer and optimize spider data
                optimizer = ScanDataOptimizer()
                optimized_data = optimizer.optimize_spider_results(
                    spider_data, page=page, page_size=page_size
                )

                return Response(optimized_data)

            except ActiveScanResult.DoesNotExist:
                return Response(
                    {"error": "Active scan results not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        except Exception as e:
            logger.error(f"Error retrieving spider data: {str(e)}")
            return Response(
                {"error": f"Error retrieving spider data: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def ajax_spider_data(self, request, pk=None):
        """Get optimized AJAX spider data with pagination"""
        try:
            scan = self.get_object()

            # Check if it's an active or comprehensive scan
            if not scan.configuration or scan.configuration.scan_type not in ['active', 'comprehensive']:
                return Response(
                    {"error": "AJAX spider data is only available for active and comprehensive scans"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get pagination parameters
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 30)), 100)  # Max 100 per page

            try:
                active_results = ActiveScanResult.objects.get(scan=scan)
                ajax_data = active_results.ajax_spider_results or {}

                # Initialize optimizer and optimize AJAX data
                optimizer = ScanDataOptimizer()
                optimized_data = optimizer.optimize_ajax_spider_results(
                    ajax_data, page=page, page_size=page_size
                )

                return Response(optimized_data)

            except ActiveScanResult.DoesNotExist:
                return Response(
                    {"error": "Active scan results not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        except Exception as e:
            logger.error(f"Error retrieving AJAX spider data: {str(e)}")
            return Response(
                {"error": f"Error retrieving AJAX spider data: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def chunked_results(self, request, pk=None):
        """Get scan results in chunks to prevent frontend crashes"""
        try:
            scan = self.get_object()

            chunk_number = int(request.GET.get('chunk', 1))
            chunk_size_mb = float(request.GET.get('chunk_size', 2.0))  # Default 2MB chunks
            data_type = request.GET.get('type', 'all')  # all, spider, ajax, vulnerabilities

            # Get the requested data type
            if data_type == 'spider':
                try:
                    active_results = ActiveScanResult.objects.get(scan=scan)
                    data = {"spider_results": active_results.spider_results or {}}
                except ActiveScanResult.DoesNotExist:
                    return Response({"error": "Active scan results not found"},
                                  status=status.HTTP_404_NOT_FOUND)

            elif data_type == 'ajax':
                try:
                    active_results = ActiveScanResult.objects.get(scan=scan)
                    data = {"ajax_spider_results": active_results.ajax_spider_results or {}}
                except ActiveScanResult.DoesNotExist:
                    return Response({"error": "Active scan results not found"},
                                  status=status.HTTP_404_NOT_FOUND)

            elif data_type == 'vulnerabilities':
                vulnerabilities = Vulnerability.objects.filter(scan=scan)
                vuln_data = VulnerabilitySerializer(vulnerabilities, many=True).data
                data = {"vulnerabilities": vuln_data}

            else:  # 'all'
                # Get complete scan data (this might still be large)
                return self.results(request, pk)

            # Create chunks
            optimizer = ScanDataOptimizer()
            chunks = optimizer.create_chunked_response(data, chunk_size_mb)

            # Return the requested chunk
            if chunk_number <= len(chunks):
                chunk_data = chunks[chunk_number - 1]
                chunk_data["chunk_info"] = {
                    "current_chunk": chunk_number,
                    "total_chunks": len(chunks),
                    "chunk_size_mb": chunk_size_mb,
                    "data_type": data_type
                }
                return Response(chunk_data)
            else:
                return Response(
                    {"error": f"Chunk {chunk_number} not found. Available chunks: 1-{len(chunks)}"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        except Exception as e:
            logger.error(f"Error retrieving chunked results: {str(e)}")
            return Response(
                {"error": f"Error retrieving chunked results: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def compressed_results(self, request, pk=None):
        """Get compressed scan results to reduce transfer size"""
        try:
            scan = self.get_object()

            data_type = request.GET.get('type', 'spider')  # spider, ajax, vulnerabilities

            # Get the requested data
            if data_type == 'spider':
                try:
                    active_results = ActiveScanResult.objects.get(scan=scan)
                    data = active_results.spider_results or {}
                except ActiveScanResult.DoesNotExist:
                    return Response({"error": "Active scan results not found"},
                                  status=status.HTTP_404_NOT_FOUND)

            elif data_type == 'ajax':
                try:
                    active_results = ActiveScanResult.objects.get(scan=scan)
                    data = active_results.ajax_spider_results or {}
                except ActiveScanResult.DoesNotExist:
                    return Response({"error": "Active scan results not found"},
                                  status=status.HTTP_404_NOT_FOUND)

            elif data_type == 'vulnerabilities':
                vulnerabilities = Vulnerability.objects.filter(scan=scan)
                data = VulnerabilitySerializer(vulnerabilities, many=True).data
            else:
                return Response({"error": "Invalid data type"}, status=status.HTTP_400_BAD_REQUEST)

            # Compress the data
            optimizer = ScanDataOptimizer()
            compressed_data = optimizer.compress_json_response(data)

            # Return compressed response
            response = HttpResponse(compressed_data, content_type='application/gzip')
            response['Content-Encoding'] = 'gzip'
            response['Content-Disposition'] = f'attachment; filename="scan_{scan.id}_{data_type}_compressed.json.gz"'
            response['Content-Length'] = len(compressed_data)

            return response

        except Exception as e:
            logger.error(f"Error creating compressed results: {str(e)}")
            return Response(
                {"error": f"Error creating compressed results: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def test_fix(self, request, pk=None):
        """Test endpoint to verify the scanType fix"""
        try:
            scan = self.get_object()

            # Test basic scan data structure
            test_data = {
                "scan_id": scan.id,
                "scanType": scan.configuration.scan_type if scan.configuration else "unknown",
                "scan_type": scan.configuration.scan_type if scan.configuration else "unknown",
                "status": scan.status,
                "has_active_data": hasattr(scan, 'active_scan_result'),
                "has_passive_data": hasattr(scan, 'passive_recon_result'),
                "vulnerability_count": scan.vulnerabilities.count() if hasattr(scan, 'vulnerabilities') else 0
            }

            # Test if we can get forms data structure
            try:
                from scanning.models import ActiveScanResult
                active_results = ActiveScanResult.objects.get(scan=scan)
                forms_data = active_results.forms_discovered or []

                test_data["forms_test"] = {
                    "forms_count": len(forms_data) if isinstance(forms_data, list) else 0,
                    "forms_sample": forms_data[0] if forms_data else None,
                    "forms_type": type(forms_data).__name__
                }
            except:
                test_data["forms_test"] = {"error": "No active scan results"}

            return Response({
                "status": "success",
                "test_results": test_data,
                "message": "Fix test completed successfully"
            })

        except Exception as e:
            import traceback
            return Response({
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            })

    @action(detail=True, methods=["get"])
    def debug_optimizer(self, request, pk=None):
        """Debug endpoint to test data optimizer"""
        try:
            # Test if we can import and instantiate the optimizer
            from .data_optimizer import ScanDataOptimizer
            optimizer = ScanDataOptimizer()

            # Test basic functionality
            test_data = {"urls": ["http://example.com", "http://test.com"], "forms": []}
            result = optimizer.optimize_spider_results(test_data)

            return Response({
                "status": "success",
                "optimizer_working": True,
                "test_result": result
            })
        except Exception as e:
            import traceback
            return Response({
                "status": "error",
                "optimizer_working": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            })

    @action(detail=False, methods=["get"])
    def running_scan(self, request):
        """Get the currently running scan for this user (if any)"""
        try:
            # Get any running scan for this user
            running_scans = Scan.objects.filter(
                configuration__project__owner=request.user,
                status__in=["pending", "running", "in_progress"],
            ).order_by("-start_time", "-created_at")

            # Reconcile stale scans
            try:
                from scanning.scan_tracker import get_scan_tracker
                tracker = get_scan_tracker()
                for candidate in list(running_scans):
                    if not tracker.is_scan_running(candidate.id):
                        candidate.status = "failed"
                        candidate.error_message = (candidate.error_message or "") + "\nAuto-corrected stale running status"
                        candidate.end_time = timezone.now()
                        candidate.save(update_fields=["status", "error_message", "end_time", "updated_at"])

                # Refresh after corrections
                running_scans = Scan.objects.filter(
                    configuration__project__owner=request.user,
                    status__in=["pending", "running", "in_progress"],
                ).order_by("-start_time", "-created_at")
            except Exception as reconcile_error:
                logger.warning(f"Could not reconcile stale scans: {reconcile_error}")

            if running_scans.exists():
                scan = running_scans.first()
                project = scan.configuration.project if scan.configuration else None

                # Get recent logs
                recent_logs = ScanLog.objects.filter(scan=scan).order_by("-timestamp")[:5]

                return Response({
                    "has_running_scan": True,
                    "scan": {
                        "id": scan.id,
                        "status": scan.status,
                        "progress": scan.progress,
                        "target_url": scan.target_url,
                        "start_time": scan.start_time,
                        "project_id": project.id if project else None,
                        "project_name": project.name if project else "Unknown",
                        "scan_type": scan.configuration.scan_type if scan.configuration else "unknown",
                        "recent_logs": ScanLogSerializer(recent_logs, many=True).data,
                    }
                })
            else:
                return Response({
                    "has_running_scan": False,
                    "scan": None
                })

        except Exception as e:
            logger.error(f"Error checking running scan: {str(e)}")
            return Response(
                {"error": f"Error checking running scan: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def data_summary(self, request, pk=None):
        """Get a summary of data sizes and optimization recommendations"""
        try:
            scan = self.get_object()

            summary = {
                "scan_id": scan.id,
                "scan_status": scan.status,
                "data_analysis": {},
                "recommendations": []
            }

            # Analyze active scan data
            try:
                active_results = ActiveScanResult.objects.get(scan=scan)
                optimizer = ScanDataOptimizer()

                # Calculate sizes
                spider_size = optimizer._calculate_size_mb(active_results.spider_results or {})
                ajax_size = optimizer._calculate_size_mb(active_results.ajax_spider_results or {})

                summary["data_analysis"]["spider_data_size_mb"] = round(spider_size, 2)
                summary["data_analysis"]["ajax_data_size_mb"] = round(ajax_size, 2)
                summary["data_analysis"]["total_active_data_mb"] = round(spider_size + ajax_size, 2)

                # Count items
                spider_data = active_results.spider_results or {}
                if "urls" in spider_data:
                    urls = spider_data["urls"]
                    if isinstance(urls, list):
                        summary["data_analysis"]["total_urls"] = len(urls)
                    elif isinstance(urls, dict) and "data" in urls:
                        summary["data_analysis"]["total_urls"] = len(urls["data"])

                # Generate recommendations
                if spider_size > 10:  # > 10MB
                    summary["recommendations"].append(
                        "Spider data is very large (>10MB). Use pagination with /spider_data endpoint."
                    )

                if ajax_size > 5:  # > 5MB
                    summary["recommendations"].append(
                        "AJAX data is large (>5MB). Use chunked loading with /ajax_spider_data endpoint."
                    )

                total_size = spider_size + ajax_size
                if total_size > 15:  # > 15MB
                    summary["recommendations"].append(
                        "Total active data is very large. Consider using /compressed_results or /chunked_results endpoints."
                    )

            except ActiveScanResult.DoesNotExist:
                summary["data_analysis"]["active_data_available"] = False

            # Count vulnerabilities
            vuln_count = Vulnerability.objects.filter(scan=scan).count()
            summary["data_analysis"]["total_vulnerabilities"] = vuln_count

            if vuln_count > 1000:
                summary["recommendations"].append(
                    f"High number of vulnerabilities ({vuln_count}). Use pagination on /vulnerabilities endpoint."
                )

            return Response(summary)

        except Exception as e:
            logger.error(f"Error generating data summary: {str(e)}")
            return Response(
                {"error": f"Error generating data summary: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VulnerabilityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing vulnerabilities (read-only)"""

    serializer_class = VulnerabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return vulnerabilities for scans of projects owned by the current user"""
        return Vulnerability.objects.filter(scan__project__owner=self.request.user)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get vulnerability summary statistics"""
        user = request.user

        # Get counts by severity
        vulns = Vulnerability.objects.filter(scan__project__owner=user)
        counts_by_severity = {
            severity: vulns.filter(severity=severity).count()
            for severity in ["critical", "high", "medium", "low", "info"]
        }

        # Get recent vulnerabilities
        recent = vulns.order_by("-created_at")[:10]
        recent_serialized = self.get_serializer(recent, many=True).data

        # Get counts by type (using the name field to group)
        counts_by_type = {}
        for vuln in vulns:
            vuln_type = vuln.name
            if vuln_type in counts_by_type:
                counts_by_type[vuln_type] += 1
            else:
                counts_by_type[vuln_type] = 1

        return Response(
            {
                "by_severity": counts_by_severity,
                "by_type": counts_by_type,
                "recent": recent_serialized,
                "total": vulns.count(),
            }
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_tools_status(request):
    """Check if external scanning tools are installed and available"""
    tools_status = {
        "sslyze": _check_sslyze(),
        "zap": _check_zap(),
        "nuclei": _check_nuclei(),
        "wappalyzer": _check_wappalyzer(),
    }

    return Response(tools_status)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_zap_status(request):
    """Check ZAP service status specifically"""
    try:
        zap_status = _check_zap_detailed()
        return Response(zap_status)
    except Exception as e:
        logger.error(f"Error checking ZAP status: {str(e)}")
        return Response(
            {
                "status": "error",
                "error": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _check_sslyze():
    """Check if SSLyze is installed"""
    try:
        # Try to import SSLyze
        import sslyze

        return {"installed": True, "version": sslyze.__version__, "status": "available"}
    except ImportError:
        return {
            "installed": False,
            "status": "not_installed",
            "message": "SSLyze is not installed. Run: pip install sslyze",
        }


def _check_zap():
    """Check if ZAP is available"""
    try:
        # Check if ZAP is configured in environment
        zap_host = os.environ.get("ZAP_HOST", "localhost")
        zap_port = os.environ.get("ZAP_PORT", "8080")

        # Try to import ZAP
        # Try basic connection
        import socket

        import zapv2

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((zap_host, int(zap_port)))
        sock.close()

        if result == 0:
            return {
                "installed": True,
                "status": "available",
                "host": zap_host,
                "port": zap_port,
            }
        else:
            return {
                "installed": True,
                "status": "not_running",
                "message": f"ZAP is not running at {zap_host}:{zap_port}",
            }
    except ImportError:
        return {
            "installed": False,
            "status": "not_installed",
            "message": "ZAP Python API is not installed. Run: pip install python-owasp-zap-v2.4",
        }
    except Exception as e:
        return {"installed": False, "status": "error", "message": str(e)}


def _check_zap_detailed():
    """Check ZAP status with detailed information for frontend"""
    try:
        # Check if ZAP is configured in environment
        # Try multiple possible ZAP hosts (Docker service name vs localhost)
        possible_hosts = [
            os.environ.get("ZAP_HOST"),
            "localhost", 
            "127.0.0.1",
            "zap"  # Docker service name as fallback
        ]
        
        # Filter out None values and use first available
        zap_hosts = [h for h in possible_hosts if h is not None]
        if not zap_hosts:
            zap_hosts = ["localhost"]
        
        zap_port = os.environ.get("ZAP_PORT", "8080")
        zap_api_key = os.environ.get("ZAP_API_KEY", "changeme123")

        # Try to import ZAP
        import socket
        import zapv2

        # Try connecting to each possible host
        connected_host = None
        for zap_host in zap_hosts:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((zap_host, int(zap_port)))
                sock.close()
                
                if result == 0:
                    connected_host = zap_host
                    break
            except Exception as host_error:
                logger.debug(f"Failed to connect to {zap_host}:{zap_port} - {str(host_error)}")
                continue

        if not connected_host:
            return {
                "status": "disconnected",
                "error": f"Cannot connect to ZAP. Tried hosts: {', '.join(zap_hosts)} on port {zap_port}",
            }

        # Try to get ZAP version via API
        try:
            zap = zapv2.ZAPv2(
                proxies={'http': f'http://{connected_host}:{zap_port}',
                         'https': f'https://{connected_host}:{zap_port}'},
                apikey=zap_api_key
            )
            
            # Get ZAP version
            version_info = zap.core.version
            
            return {
                "status": "connected",
                "version": version_info,
                "url": f"http://{connected_host}:{zap_port}",
            }
        except Exception as api_error:
            logger.warning(f"ZAP API error: {str(api_error)}")
            # Connection works but API might have issues
            return {
                "status": "connected",
                "url": f"http://{connected_host}:{zap_port}",
                "version": "Unknown (API access limited)",
                "warning": "API access limited, but ZAP is running"
            }

    except ImportError:
        return {
            "status": "error",
            "error": "ZAP Python API is not installed. Run: pip install python-owasp-zap-v2.4",
        }
    except Exception as e:
        logger.error(f"ZAP detailed check error: {str(e)}")
        return {
            "status": "error", 
            "error": str(e)
        }


def _check_nuclei():
    """Check if Nuclei is installed"""
    try:
        # Check if nuclei is in PATH
        nuclei_path = shutil.which("nuclei")
        if not nuclei_path:
            return {
                "installed": False,
                "status": "not_found",
                "message": "Nuclei not found in PATH",
            }

        # Check version
        result = subprocess.run(
            ["nuclei", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode == 0:
            version = result.stdout.strip()

            # Check templates
            templates_result = subprocess.run(
                ["nuclei", "-templates-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            templates_info = (
                templates_result.stdout.strip()
                if templates_result.returncode == 0
                else "No templates found"
            )

            return {
                "installed": True,
                "version": version,
                "templates": templates_info,
                "status": "available",
            }

        return {
            "installed": True,
            "status": "error",
            "message": result.stderr or "Unknown error running nuclei",
        }

    except Exception as e:
        return {"installed": False, "status": "error", "message": str(e)}


def _check_wappalyzer():
    """Check if Wappalyzer is installed"""
    try:
        # Try to import Wappalyzer
        from Wappalyzer import Wappalyzer

        # Get version (if available)
        version = getattr(Wappalyzer, "__version__", "Unknown")

        return {"installed": True, "version": version, "status": "available"}
    except ImportError:
        return {
            "installed": False,
            "status": "not_installed",
            "message": "Python Wappalyzer is not installed. Run: pip install python-Wappalyzer",
        }
    except Exception as e:
        return {"installed": False, "status": "error", "message": str(e)}
