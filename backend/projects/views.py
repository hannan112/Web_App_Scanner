from django.db.models import Count, Max, Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Project
from .serializers import (ProjectCreateUpdateSerializer,
                          ProjectDetailSerializer, ProjectListSerializer)


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on Project model"""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return ProjectListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ProjectCreateUpdateSerializer
        return ProjectDetailSerializer

    def get_queryset(self):
        """Return only projects owned by the authenticated user"""
        user = self.request.user

        # Annotate with scan count and last scan date if scanning app is installed
        try:
            from scanning.models import Scan

            queryset = Project.objects.filter(owner=user).annotate(
                scan_count=Count("scans"), last_scan_date=Max("scans__start_time")
            )
        except ImportError:
            # If scanning app is not yet installed, return without annotations
            queryset = Project.objects.filter(owner=user)

        return queryset

    def perform_create(self, serializer):
        """Set the owner to the authenticated user when creating a project"""
        serializer.save(owner=self.request.user)

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
    def stats(self, request, pk=None):
        """Get detailed project statistics"""
        project = self.get_object()

        # Try to get scan stats if scanning app is installed
        try:
            from scanning.models import Scan, Vulnerability
            from scanning.serializers import ScanSerializer

            # Get scan counts by type
            scan_counts = (
                Scan.objects.filter(project=project)
                .values("configuration__scan_type")
                .annotate(count=Count("id"))
            )

            # Get recent scans
            recent_scans = Scan.objects.filter(project=project).order_by("-start_time")[
                :5
            ]
            recent_scans_serialized = ScanSerializer(recent_scans, many=True).data

            # Get vulnerability counts if available
            try:
                vuln_counts = (
                    Vulnerability.objects.filter(scan__project=project)
                    .values("severity")
                    .annotate(count=Count("id"))
                )
                vuln_data = {item["severity"]: item["count"] for item in vuln_counts}
            except Exception:
                vuln_data = {}

            scan_data = {
                "total_scans": Scan.objects.filter(project=project).count(),
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

        # Combine project data with scan stats
        project_data = ProjectDetailSerializer(project).data
        response_data = {"project": project_data, "scan_stats": scan_data}

        return Response(response_data)
