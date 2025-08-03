# backend/scanning/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import subprocess
import shutil
import os
from django.shortcuts import get_object_or_404
import logging
from scanning.passive.unified_scanner import UnifiedPassiveScanner

logger = logging.getLogger(__name__)

# Use the modular model structure imports
from scanning.models import (
    ScanConfiguration, Scan, PassiveReconResult, 
    CrawlResult, ScanLog, Vulnerability
)

from .serializers import (
    ScanConfigurationSerializer, ScanSerializer,
    PassiveReconResultSerializer, CrawlResultSerializer, 
    ScanLogSerializer, ScanResultsSerializer,
    VulnerabilitySerializer
)
from projects.models import Project

# Import the new scanner engine
from scanning.engine import ScanningEngine

from scanning.engine import ScanningEngine, start_scan, stop_scan 

class ScanConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing scan configurations"""
    serializer_class = ScanConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return scan configurations for projects owned by the current user"""
        return ScanConfiguration.objects.filter(project__owner=self.request.user)
    
    def perform_create(self, serializer):
        """Validate the user has access to the project"""
        project_id = self.request.data.get('project')
        project = get_object_or_404(Project, id=project_id, owner=self.request.user)
        serializer.save(project=project)


class ScanViewSet(viewsets.ModelViewSet):
    """ViewSet for managing scans"""
    serializer_class = ScanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return scans for projects owned by the current user"""
        return Scan.objects.filter(project__owner=self.request.user)
    
    def get_serializer_class(self):
        """Return different serializer for detailed view"""
        if self.action == 'retrieve' or self.action == 'results':
            return ScanResultsSerializer
        return ScanSerializer
    
    def create(self, request):
        """Create a new scan with configuration"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get project and configuration
        project_id = serializer.validated_data.get('project').id
        config_id = serializer.validated_data.get('configuration').id
        
        # Verify user owns the project
        project = get_object_or_404(Project, id=project_id, owner=request.user)
        configuration = get_object_or_404(ScanConfiguration, id=config_id, project=project)
        
        # Create scan
        scan = Scan.objects.create(
            project=project,
            configuration=configuration,
            status='pending'
        )
        
        # Start the scan using our new engine
        engine = ScanningEngine(scan.id)
        success = engine.start() is not None
        
        if not success:
            scan.fail("Failed to start scan")
            return Response(
                {"error": "Failed to start scan"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return the scan data
        serializer = self.get_serializer(scan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop a running scan"""
        scan = self.get_object()
        
        if scan.status != 'in_progress':
            return Response(
                {"error": "Can only stop scans that are in progress"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success = stop_scan(scan.id)
        
        if not success:
            return Response(
                {"error": "Failed to stop scan"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        scan.refresh_from_db()  # Refresh to get updated status
        serializer = self.get_serializer(scan)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get comprehensive scan results"""
        try:
            scan = self.get_object()
            
            # Add project information to response
            if hasattr(scan, 'project') and scan.project is not None:
                project_data = {
                    'id': scan.project.id,
                    'name': scan.project.name,
                    'target_url': scan.project.target_url
                }
            else:
                project_data = None
            
            # Get results using the results serializer
            serializer = ScanResultsSerializer(scan)
            data = serializer.data
            data['project'] = project_data
            
            return Response(data)
        except Exception as e:
            logger.error(f"Error retrieving scan results: {str(e)}")
            return Response(
                {"error": f"Error retrieving scan results: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get current scan status and progress"""
        try:
            scan = self.get_object()
            
            data = {
                'id': scan.id,
                'status': scan.status,
                'progress': scan.progress,
                'started_at': scan.start_time,
                'completed_at': scan.end_time,
                'error': scan.error_message,
                'project_id': scan.project.id if scan.project else None
            }
            
            return Response(data)
        except Exception as e:
            logger.error(f"Error retrieving scan status: {str(e)}")
            return Response(
                {"error": f"Error retrieving scan status: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get logs for a scan"""
        try:
            scan = self.get_object()
            logs = ScanLog.objects.filter(scan=scan).order_by('-timestamp')
            serializer = ScanLogSerializer(logs, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving scan logs: {str(e)}")
            return Response(
                {"error": f"Error retrieving scan logs: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def vulnerabilities(self, request, pk=None):
        """Get vulnerabilities discovered in a scan"""
        try:
            scan = self.get_object()
            vulnerabilities = Vulnerability.objects.filter(scan=scan)
            
            # Filter by severity if specified
            severity = request.query_params.get('severity')
            if severity:
                vulnerabilities = vulnerabilities.filter(severity=severity)
            
            serializer = VulnerabilitySerializer(vulnerabilities, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving vulnerabilities: {str(e)}")
            return Response(
                {"error": f"Error retrieving vulnerabilities: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
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
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            logger.error(f"Error retrieving passive recon results: {str(e)}")
            return Response(
                {"error": f"Error retrieving passive recon results: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def crawl(self, request, pk=None):
        """Get crawl results"""
        try:
            scan = self.get_object()
            try:
                results = CrawlResult.objects.get(scan=scan)
                serializer = CrawlResultSerializer(results)
                return Response(serializer.data)
            except CrawlResult.DoesNotExist:
                return Response(
                    {"error": "Crawl results not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            logger.error(f"Error retrieving crawl results: {str(e)}")
            return Response(
                {"error": f"Error retrieving crawl results: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        """Generate a PDF report for the scan"""
        try:
            scan = self.get_object()
            
            # For completed scans only
            if scan.status != 'completed':
                return Response(
                    {"error": "Reports are only available for completed scans"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # TODO: Implement report generation
            # For now, return a mock response
            return Response(
                {"message": "Report generation initiated"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return Response(
                {"error": f"Error generating report: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VulnerabilityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing vulnerabilities (read-only)"""
    serializer_class = VulnerabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return vulnerabilities for scans of projects owned by the current user"""
        return Vulnerability.objects.filter(scan__project__owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get vulnerability summary statistics"""
        user = request.user
        
        # Get counts by severity
        vulns = Vulnerability.objects.filter(scan__project__owner=user)
        counts_by_severity = {
            severity: vulns.filter(severity=severity).count()
            for severity in ['critical', 'high', 'medium', 'low', 'info']
        }
        
        # Get recent vulnerabilities
        recent = vulns.order_by('-created_at')[:10]
        recent_serialized = self.get_serializer(recent, many=True).data
        
        # Get counts by type (using the name field to group)
        counts_by_type = {}
        for vuln in vulns:
            vuln_type = vuln.name
            if vuln_type in counts_by_type:
                counts_by_type[vuln_type] += 1
            else:
                counts_by_type[vuln_type] = 1
        
        return Response({
            'by_severity': counts_by_severity,
            'by_type': counts_by_type,
            'recent': recent_serialized,
            'total': vulns.count()
        })
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_tools_status(request):
    """Check if external scanning tools are installed and available"""
    tools_status = {
        'sslyze': _check_sslyze(),
        'zap': _check_zap(),
        'nuclei': _check_nuclei(),
        'wappalyzer': _check_wappalyzer()
    }
    
    return Response(tools_status)

def _check_sslyze():
    """Check if SSLyze is installed"""
    try:
        # Try to import SSLyze
        import sslyze
        return {
            'installed': True,
            'version': sslyze.__version__,
            'status': 'available'
        }
    except ImportError:
        return {
            'installed': False,
            'status': 'not_installed',
            'message': 'SSLyze is not installed. Run: pip install sslyze'
        }

def _check_zap():
    """Check if ZAP is available"""
    try:
        # Check if ZAP is configured in environment
        zap_host = os.environ.get('ZAP_HOST', 'localhost')
        zap_port = os.environ.get('ZAP_PORT', '8080')
        
        # Try to import ZAP
        import zapv2
        
        # Try basic connection
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((zap_host, int(zap_port)))
        sock.close()
        
        if result == 0:
            return {
                'installed': True,
                'status': 'available',
                'host': zap_host,
                'port': zap_port
            }
        else:
            return {
                'installed': True,
                'status': 'not_running',
                'message': f'ZAP is not running at {zap_host}:{zap_port}'
            }
    except ImportError:
        return {
            'installed': False,
            'status': 'not_installed',
            'message': 'ZAP Python API is not installed. Run: pip install python-owasp-zap-v2.4'
        }
    except Exception as e:
        return {
            'installed': False,
            'status': 'error',
            'message': str(e)
        }

def _check_nuclei():
    """Check if Nuclei is installed"""
    try:
        # Check if nuclei is in PATH
        nuclei_path = shutil.which('nuclei')
        if not nuclei_path:
            return {
                'installed': False,
                'status': 'not_found',
                'message': 'Nuclei not found in PATH'
            }
        
        # Check version
        result = subprocess.run(['nuclei', '-version'], 
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)
        
        if result.returncode == 0:
            version = result.stdout.strip()
            
            # Check templates
            templates_result = subprocess.run(['nuclei', '-templates-version'], 
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             text=True)
            
            templates_info = templates_result.stdout.strip() if templates_result.returncode == 0 else 'No templates found'
            
            return {
                'installed': True,
                'version': version,
                'templates': templates_info,
                'status': 'available'
            }
        
        return {
            'installed': True,
            'status': 'error',
            'message': result.stderr or 'Unknown error running nuclei'
        }
        
    except Exception as e:
        return {
            'installed': False,
            'status': 'error',
            'message': str(e)
        }

def _check_wappalyzer():
    """Check if Wappalyzer is installed"""
    try:
        # Try to import Wappalyzer
        from Wappalyzer import Wappalyzer
        
        # Get version (if available)
        version = getattr(Wappalyzer, '__version__', 'Unknown')
        
        return {
            'installed': True,
            'version': version,
            'status': 'available'
        }
    except ImportError:
        return {
            'installed': False,
            'status': 'not_installed',
            'message': 'Python Wappalyzer is not installed. Run: pip install python-Wappalyzer'
        }
    except Exception as e:
        return {
            'installed': False,
            'status': 'error',
            'message': str(e)
        }