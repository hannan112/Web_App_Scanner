from django.urls import include, path
from rest_framework.routers import DefaultRouter

from authentication import views

from .views import (ScanConfigurationViewSet, ScanViewSet,
                    VulnerabilityViewSet, check_tools_status)

router = DefaultRouter()
router.register(
    r"configurations", ScanConfigurationViewSet, basename="scan-configuration"
)
router.register(r"scans", ScanViewSet, basename="scan")
router.register(r"vulnerabilities", VulnerabilityViewSet, basename="vulnerability")

urlpatterns = [
    path("", include(router.urls)),
    # scanning/urls.py - Add to existing urlpatterns
    path("tools-status/", check_tools_status, name="tools-status"),
]
