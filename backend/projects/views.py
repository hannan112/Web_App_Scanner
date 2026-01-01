import logging
from django.db.models import Count, Max, Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Project
from .serializers import (ProjectCreateUpdateSerializer,
                          ProjectDetailSerializer, ProjectListSerializer)

logger = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on Project model"""

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "uuid"

    def get_object(self):
        """
        Override get_object to allow lookup by either UUID or integer ID.
        This ensures backward compatibility for simplified navigation and cached frontend links.
        """
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs.get(lookup_url_kwarg)

        # Check if the lookup value is an integer (legacy ID)
        if lookup_value is not None and str(lookup_value).isdigit():
            filter_kwargs = {"id": lookup_value}
        else:
            # Assume it's a UUID
            filter_kwargs = {self.lookup_field: lookup_value}

        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_serializer_class(self):
        if self.action == "list":
            return ProjectListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ProjectCreateUpdateSerializer
        return ProjectDetailSerializer

    def get_queryset(self):
        """Return only projects owned by the authenticated user, annotated with scan stats"""
        user = self.request.user

        # Annotate with scan_count and last_scan_date via scan configurations relationship
        # Scan is linked as Scan.configuration -> ScanConfiguration.project
        queryset = (
            Project.objects
            .filter(owner=user)
            .annotate(
                scan_count=Count("scan_configurations__scans", distinct=True),
                last_scan_date=Max("scan_configurations__scans__end_time"),
            )
        )

        return queryset

    def perform_create(self, serializer):
        """Set the owner to the authenticated user when creating a project"""
        serializer.save(owner=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Override create to log validation errors"""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Project creation validation failed: {serializer.errors}")
            logger.error(f"Request data: {request.data}")
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        """Project dashboard statistics"""
        # Get total projects
        total_projects = self.get_queryset().count()

        # Get projects created in the last month
        month_ago = timezone.now() - timezone.timedelta(days=30)
        new_projects = self.get_queryset().filter(created_at__gte=month_ago).count()

        # Get recently updated projects
        recent_projects = self.get_queryset().order_by("-updated_at")[:5]

        # Return dashboard data
        return Response(
            {
                "total_projects": total_projects,
                "new_projects_last_month": new_projects,
                "recent_projects": ProjectListSerializer(
                    recent_projects, many=True
                ).data,
            }
        )

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None, uuid=None, **kwargs):
        """Get detailed project statistics"""
        project = self.get_object()

        # Try to get scan stats if scanning app is installed
        try:
            from scanning.models import Scan, Vulnerability
            from scanning.serializers import ScanSerializer

            # Get scan counts by type - scans are now linked via configuration->project
            scan_counts = (
                Scan.objects.filter(configuration__project=project)
                .values("configuration__scan_type")
                .annotate(count=Count("id"))
            )

            # Get recent scans
            recent_scans = Scan.objects.filter(configuration__project=project).order_by("-start_time")[
                :5
            ]
            recent_scans_serialized = ScanSerializer(recent_scans, many=True).data

            # Get vulnerability counts if available
            try:
                vuln_counts = (
                    Vulnerability.objects.filter(scan__configuration__project=project)
                    .values("severity")
                    .annotate(count=Count("id"))
                )
                vuln_data = {item["severity"]: item["count"] for item in vuln_counts}
            except Exception:
                vuln_data = {}

            # Ensure all severities are present for frontend display
            severities = ["critical", "high", "medium", "low", "info"]
            vulnerabilities_summary = {s: int(vuln_data.get(s, 0)) for s in severities}

            total_scans = Scan.objects.filter(configuration__project=project).count()
            last_scan_date = (
                Scan.objects.filter(configuration__project=project).aggregate(
                    last=Max("end_time")
                )["last"]
            )
            latest_scan = (
                Scan.objects.filter(configuration__project=project)
                .order_by("-start_time")
                .first()
            )
            latest_status = latest_scan.status if latest_scan else None

            scan_data = {
                "total_scans": total_scans,
                "scan_counts_by_type": {
                    item["configuration__scan_type"]: item["count"]
                    for item in scan_counts
                },
                "recent_scans": recent_scans_serialized,
                "vulnerability_counts": vuln_data,
            }
        except ImportError:
            # If scanning app not installed yet
            scan_data = {
                "total_scans": 0,
                "scan_counts_by_type": {},
                "recent_scans": [],
                "vulnerability_counts": {},
            }
            vulnerabilities_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
            total_scans = 0
            last_scan_date = None
            latest_status = None

        # Combine project data with scan stats
        project_data = ProjectDetailSerializer(project).data
        response_data = {
            "project": project_data,
            "scan_stats": scan_data,
            "vulnerabilities": vulnerabilities_summary,
            "total_scans": total_scans,
            "last_scan_date": last_scan_date,
            "scan_status": latest_status,
        }

        return Response(response_data)
    
    @action(detail=True, methods=["post"])
    def start_scan(self, request, pk=None):
        """Start a new scan for this project using the same logic as /scans endpoint"""
        try:
            project = self.get_object()
            
            # Get configuration ID from request data
            config_id_raw = request.data.get("configuration")
            if not config_id_raw:
                return Response(
                    {"error": "Configuration ID is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Convert to integer if it's a string
            try:
                config_id = int(config_id_raw)
            except (ValueError, TypeError):
                return Response(
                    {"error": "Invalid configuration ID"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Import here to avoid circular imports
            from scanning.models import ScanConfiguration, Scan
            from scanning.unified_engine import UnifiedScanningEngine
            import threading
            
            # Get the configuration and verify it belongs to this project
            configuration = ScanConfiguration.objects.filter(
                id=config_id, 
                project=project
            ).first()
            
            if not configuration:
                return Response(
                    {"error": "Configuration not found or doesn't belong to this project"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Enforce one running/pending scan per project
            try:
                from scanning.models import Scan as ScanModel
                existing_active_qs = ScanModel.objects.filter(
                    configuration__project=project,
                    status__in=["pending", "running", "in_progress"],
                ).order_by("-start_time", "-created_at")

                # Reconcile stale statuses with tracker
                if existing_active_qs.exists():
                    try:
                        from scanning.scan_tracker import get_scan_tracker
                        tracker = get_scan_tracker()
                        for candidate in list(existing_active_qs):
                            if not tracker.is_scan_running(candidate.id):
                                candidate.status = "failed"
                                candidate.error_message = (candidate.error_message or "") + "\nAuto-corrected stale running status"
                                candidate.end_time = timezone.now()
                                candidate.save(update_fields=["status", "error_message", "end_time", "updated_at"])
                        # Refresh queryset after corrections
                        existing_active_qs = ScanModel.objects.filter(
                            configuration__project=project,
                            status__in=["pending", "running", "in_progress"],
                        ).order_by("-start_time", "-created_at")
                    except Exception as reconcile_error:
                        logger.warning(f"Could not reconcile stale scans: {reconcile_error}")

                if existing_active_qs.exists():
                    active_scan = existing_active_qs.first()
                    return Response(
                        {
                            "error": "Another scan is already pending or running for this project.",
                            "active_scan_id": active_scan.id,
                            "active_scan_status": active_scan.status,
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

            # Start the scan using our unified engine
            engine = UnifiedScanningEngine(scan.id)
            
            try:
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

                logger.info(f"Scan {scan.id} started asynchronously from project endpoint")
                
            except Exception as e:
                logger.exception(f"Error during scan execution: {e}")
                scan.fail(f"Scan execution error: {str(e)}")
                return Response(
                    {"error": f"Scan execution error: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Return the scan data
            from scanning.serializers import ScanSerializer
            serializer = ScanSerializer(scan)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error starting scan from project endpoint: {e}")
            return Response(
                {"error": f"Error starting scan: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=True, methods=["get"])
    def scan_status(self, request, pk=None):
        """Get the status of the latest scan for this project"""
        try:
            project = self.get_object()
            
            # Import here to avoid circular imports
            from scanning.models import Scan
            
            # Get the latest scan for this project
            latest_scan = Scan.objects.filter(
                configuration__project=project
            ).order_by('-start_time').first()
            
            if not latest_scan:
                return Response({
                    "status": "no_scans",
                    "message": "No scans found for this project"
                })
            
            # Get project information
            project_info = {
                "id": project.id,
                "name": project.name,
                "target_url": project.target_url,
            }
            
            data = {
                "id": latest_scan.id,
                "status": latest_scan.status,
                "progress": latest_scan.progress,
                "started_at": latest_scan.start_time,
                "completed_at": latest_scan.end_time,
                "created_at": latest_scan.created_at,
                "error": latest_scan.error_message,
                "project_id": project.id,
                "project_info": project_info,
                "configuration_name": latest_scan.configuration.scan_type if latest_scan.configuration else "Standard",
                "scan_type": latest_scan.configuration.scan_type if latest_scan.configuration else None,
            }

            return Response(data)
            
        except Exception as e:
            logger.error(f"Error getting scan status from project endpoint: {e}")
            return Response(
                {"error": f"Error getting scan status: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )