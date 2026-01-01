from django.test import TestCase
from unittest.mock import patch, MagicMock
from scanning.models.vulnerability import Vulnerability
from scanning.models.scan import Scan, ScanConfiguration
from scanning.unified_engine import UnifiedScanningEngine, HEADER_VULNS
from projects.models import Project
from authentication.models import CustomUser
import pandas as pd
import json

class TestMLIntegration(TestCase):
    def setUp(self):
        # Create dependencies
        self.user = CustomUser.objects.create(username="testuser", email="test@example.com")
        self.project = Project.objects.create(name="Test Project", target_url="http://example.com", owner=self.user)
        self.config = ScanConfiguration.objects.create(project=self.project, scan_type="comprehensive")
        self.scan = Scan.objects.create(configuration=self.config)
        self.engine = UnifiedScanningEngine(self.scan.id)
        self.engine.configuration = self.config
        
    @patch('scanning.unified_engine.joblib.load')

    @patch('os.path.exists')
    def test_apply_ml_fp_reduction(self, mock_exists, mock_load):
        # value setup
        mock_exists.return_value = True
        
        # Mock model
        mock_model = MagicMock()
        # predict_proba returns [prob_0, prob_1] (prob_1 is FP confidence)
        # We will pass 2 items. 
        # Item 1: Real header issue (Likely FP) -> Should be high FP confidence
        # Item 2: SQL Injection (Likely TP) -> Should be low FP confidence
        mock_model.predict_proba.return_value = pd.DataFrame([[0.2, 0.8], [0.9, 0.1]]).to_numpy()
        mock_load.return_value = mock_model
        
        # Create vulnerabilities
        # Vuln 1: Header issue, no evidence (Should be Likely FP via Pseudo-label)
        v1 = Vulnerability.objects.create(
            scan=self.scan,
            name="Missing X-Frame-Options Header", # In HEADER_VULNS
            severity="low",
            evidence="", # No evidence
            url="http://example.com"
        )
        
        # Vuln 2: SQL Injection (Likely TP)
        v2 = Vulnerability.objects.create(
            scan=self.scan,
            name="SQL Injection", # In INJECTION_VULNS
            severity="high",
            evidence="payload",
            url="http://example.com/sqli"
        )
        
        # Run ML reduction
        self.engine.apply_ml_fp_reduction()
        
        # Reload vulns
        v1.refresh_from_db()
        v2.refresh_from_db()
        
        v1.refresh_from_db()
        v2.refresh_from_db()
        
        # Verify V1 (Header issue)
        # Model returned 0.8 conf
        self.assertIsNotNone(v1.other_info)
        info1 = v1.other_info if isinstance(v1.other_info, dict) else json.loads(v1.other_info)
        self.assertTrue(info1.get('ml_is_fp'))
        self.assertAlmostEqual(info1.get('ml_fp_confidence'), 0.8)
        
        # Verify V2 (Injection)
        # Model returned 0.1 conf
        self.assertIsNotNone(v2.other_info)
        info2 = v2.other_info if isinstance(v2.other_info, dict) else json.loads(v2.other_info)
        self.assertFalse(info2.get('ml_is_fp'))
        self.assertAlmostEqual(info2.get('ml_fp_confidence'), 0.1)



    def test_skipped_for_active_scan(self):
        # Create an active scan configuration
        active_config = ScanConfiguration.objects.create(project=self.project, scan_type="active")
        active_scan = Scan.objects.create(configuration=active_config)
        active_engine = UnifiedScanningEngine(active_scan.id)
        active_engine.configuration = active_config
        
        # Create a vulnerability that WOULD be flagged if ML ran
        v4 = Vulnerability.objects.create(
            scan=active_scan,
            name="Missing X-Frame-Options Header",
            severity="low",
            evidence="",
            url="http://example.com/4"
        )
        
        # Run ML reduction
        active_engine.apply_ml_fp_reduction()
        
        # Verify ML did NOT run
        v4.refresh_from_db()
        # other_info should be None or empty or at least NOT contain ml_is_fp
        if v4.other_info:
             if isinstance(v4.other_info, str):
                 info = json.loads(v4.other_info)
             else:
                 info = v4.other_info
             self.assertIsNone(info.get('ml_is_fp'))
        else:
             self.assertIsNone(v4.other_info)


    def test_informational_severity_exclusion(self):
        # Create a vulnerability with "informational" severity
        v5 = Vulnerability.objects.create(
            scan=self.scan,
            name="Info Vuln",
            severity="informational",
            evidence="",
            url="http://example.com/info"
        )
        
        # Run ML reduction
        self.engine.apply_ml_fp_reduction()
        
        # Verify V5 was skipped (other_info should be None or not contain ML data)
        v5.refresh_from_db()
        self.assertIsNone(v5.other_info)



