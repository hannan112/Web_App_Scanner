from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ScanConfigurationViewSet,
    ScanViewSet,
    VulnerabilityViewSet
)

router = DefaultRouter()
router.register(r'configurations', ScanConfigurationViewSet, basename='scan-configuration')
router.register(r'scans', ScanViewSet, basename='scan')
router.register(r'vulnerabilities', VulnerabilityViewSet, basename='vulnerability')

urlpatterns = [
    path('', include(router.urls)),
]
