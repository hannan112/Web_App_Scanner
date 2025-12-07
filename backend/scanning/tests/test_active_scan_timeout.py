import unittest
from unittest.mock import MagicMock, patch
import time
from scanning.active.zap_active_adapter import ZAPActiveAdapter

class TestActiveScanTimeout(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock()
        self.mock_config.active_scan_timeout_minutes = 0.001  # Very short timeout (~0.06 seconds)
        self.adapter = ZAPActiveAdapter(config=self.mock_config)
        self.adapter.active_scan_id = "123"
        self.adapter.scan_logger = MagicMock()
        
    @patch('scanning.active.zap_active_adapter.time.sleep')
    @patch('scanning.active.zap_active_adapter.time.time')
    def test_monitor_active_scan_timeout(self, mock_time, mock_sleep):
        # Mock time to simulate timeout
        # First call: start time
        # Second call: check elapsed (should be > timeout)
        start_time = 1000.0
        mock_time.side_effect = [start_time, start_time + 10.0]  # 10 seconds elapsed > 0.06s timeout
        
        # Mock API request to return running status
        self.adapter._make_api_request = MagicMock(return_value={"status": "50"})
        self.adapter._make_api_post_request = MagicMock()
        
        # Run the monitor method
        self.adapter._monitor_active_scan_progress()
        
        # Verify stop was called
        self.adapter._make_api_post_request.assert_called_with("ascan/action/stop", {"scanId": "123"})
        
        # Verify logger was called
        self.adapter.scan_logger.log_error.assert_called()
        args, _ = self.adapter.scan_logger.log_error.call_args
        self.assertEqual(args[0], "Active Scan Timeout")

if __name__ == '__main__':
    unittest.main()
