from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
import json
from .models import (
    ScanConfiguration, Scan, PassiveReconResult, 
    CrawlResult, Vulnerability, ScanLog
)
from projects.models import Project

User = get_user_model()

class ScanningAPITestCase(APITestCase):
    """Test case for the scanning API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123!'
        )
        
        # Create test project
        self.project = Project.objects.create(
            name='Test Project',
            target_url='https://example.com',
            user=self.user
        )
        
        # Create test scan configuration
        self.scan_config = ScanConfiguration.objects.create(
            project=self.project,
            scan_type='passive',
            crawl_depth=2,
            respect_robots_txt=True,
            crawl_max_pages=50
        )
        
        # Create a test scan
        self.scan = Scan.objects.create(
            project=self.project,
            configuration=self.scan_config,
            status='completed',
            progress=100.0
        )
        
        # Create test passive recon result
        self.passive_result = PassiveReconResult.objects.create(
            scan=self.scan,
            dns_records={'A': ['93.184.216.34']},
            server_info={'server': 'nginx'},
            robots_txt='User-agent: *\nDisallow: /admin',
            sitemap_xml='<?xml version="1.0" encoding="UTF-8"?><urlset></urlset>'
        )
        
        # Create test vulnerability
        self.vulnerability = Vulnerability.objects.create(
            scan=self.scan,
            name='Missing Security Header',
            description='Content-Security-Policy header is missing',
            severity='medium',
            remediation='Add Content-Security-Policy header'
        )
        
        # Create test scan log
        self.log = ScanLog.objects.create(
            scan=self.scan,
            level='INFO',
            message='Scan completed successfully'
        )
        
        # Set up client with authentication
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # API endpoints
        self.config_list_url = reverse('scan-configuration-list')
        self.scan_list_url = reverse('scan-list')
        self.vulnerability_list_url = reverse('vulnerability-list')
    
    def test_scan_configuration_list(self):
        """Test retrieving scan configurations"""
        response = self.client.get(self.config_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['scan_type'], 'passive')
    
    def test_scan_configuration_create(self):
        """Test creating a new scan configuration"""
        data = {
            'project': self.project.id,
            'scan_type': 'active',
            'crawl_depth': 3,
            'respect_robots_txt': True,
            'crawl_max_pages': 100
        }
        response = self.client.post(self.config_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ScanConfiguration.objects.count(), 2)
        self.assertEqual(response.data['scan_type'], 'active')
    
    def test_scan_configuration_retrieve(self):
        """Test retrieving a specific scan configuration"""
        url = reverse('scan-configuration-detail', args=[self.scan_config.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.scan_config.id)
    
    def test_scan_configuration_update(self):
        """Test updating a scan configuration"""
        url = reverse('scan-configuration-detail', args=[self.scan_config.id])
        data = {
            'project': self.project.id,
            'scan_type': 'passive',
            'crawl_depth': 5,  # Changed from 2 to 5
            'respect_robots_txt': True,
            'crawl_max_pages': 50
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.scan_config.refresh_from_db()
        self.assertEqual(self.scan_config.crawl_depth, 5)
    
    def test_scan_list(self):
        """Test retrieving scans"""
        response = self.client.get(self.scan_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'completed')
    
    def test_scan_create(self):
        """Test creating a new scan"""
        data = {
            'project': self.project.id,
            'configuration': self.scan_config.id
        }
        response = self.client.post(self.scan_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Scan.objects.count(), 2)
        
        # Note: In a real test, we would mock the background scanning process
        # Since we're not actually running scans in tests
    
    def test_scan_retrieve(self):
        """Test retrieving a specific scan"""
        url = reverse('scan-detail', args=[self.scan.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.scan.id)
    
    def test_scan_results(self):
        """Test retrieving scan results"""
        url = reverse('scan-results', args=[self.scan.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.scan.id)
        # Check that we have passive data in the response
        self.assertIsNotNone(response.data.get('passive_data'))
    
    def test_scan_logs(self):
        """Test retrieving scan logs"""
        url = reverse('scan-logs', args=[self.scan.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['message'], 'Scan completed successfully')
    
    def test_scan_vulnerabilities(self):
        """Test retrieving scan vulnerabilities"""
        url = reverse('scan-vulnerabilities', args=[self.scan.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Missing Security Header')
    
    def test_scan_passive(self):
        """Test retrieving passive scan results"""
        url = reverse('scan-passive', args=[self.scan.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dns_records'], {'A': ['93.184.216.34']})
    
    def test_vulnerability_list(self):
        """Test retrieving vulnerabilities"""
        response = self.client.get(self.vulnerability_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['severity'], 'medium')
    
    def test_vulnerability_retrieve(self):
        """Test retrieving a specific vulnerability"""
        url = reverse('vulnerability-detail', args=[self.vulnerability.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.vulnerability.id)
    
    def test_unauthorized_access(self):
        """Test that unauthenticated users cannot access API"""
        # Create a client without authentication
        client = APIClient()
        
        response = client.get(self.scan_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_other_user_data_isolation(self):
        """Test that users cannot access other users' data"""
        # Create another user with their own project and scan
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpassword123!'
        )
        
        other_project = Project.objects.create(
            name='Other Project',
            target_url='https://example.org',
            user=other_user
        )
        
        other_config = ScanConfiguration.objects.create(
            project=other_project,
            scan_type='passive'
        )
        
        other_scan = Scan.objects.create(
            project=other_project,
            configuration=other_config,
            status='completed'
        )
        
        # Authenticate as the original test user
        self.client.force_authenticate(user=self.user)
        
        # Try to access the other user's scan
        url = reverse('scan-detail', args=[other_scan.id])
        response = self.client.get(url)
        
        # Should get 404 because the queryset is filtered by user
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MockScanningTestCase(APITestCase):
    """Test case with mocked scanning functionality"""
    
    def setUp(self):
        """Set up test data with mocks"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123!'
        )
        
        # Create test project
        self.project = Project.objects.create(
            name='Test Project',
            target_url='https://example.com',
            user=self.user
        )
        
        # Create test scan configuration
        self.scan_config = ScanConfiguration.objects.create(
            project=self.project,
            scan_type='passive',
            crawl_depth=2,
            respect_robots_txt=True,
            crawl_max_pages=50
        )
        
        # Set up client with authentication
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # API endpoints
        self.scan_list_url = reverse('scan-list')
    
    # This would require mocking the scanning functions
    # For a real implementation, use unittest.mock to patch the scanning functions
    
    def test_scan_stop(self):
        """Test stopping a scan"""
        # Create a scan that's in progress
        scan = Scan.objects.create(
            project=self.project,
            configuration=self.scan_config,
            status='in_progress',
            progress=50.0
        )
        
        # Try to stop it
        url = reverse('scan-stop', args=[scan.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the scan was stopped
        scan.refresh_from_db()
        self.assertEqual(scan.status, 'stopped')