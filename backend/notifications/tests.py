import os
from unittest.mock import patch

from django.test import TestCase, override_settings

from notifications.email_service import EmailService


@override_settings(RESEND_API_KEY="test-key", EMAIL_FROM_ADDRESS="test@example.com")
class EmailServiceTests(TestCase):
    def _send_completed(self, service):
        service.send_scan_completed_email(
            user_email="user@example.com",
            user_name="Test User",
            scan_id=1,
            scan_type="Passive Scan",
            project_name="Test Project",
            target_url="https://example.com",
            duration="1m 0s",
            start_time="2026-01-01 00:00:00",
            end_time="2026-01-01 00:01:00",
            vulnerability_count=3,
        )

    @patch("notifications.email_service.resend")
    def test_send_scan_completed_email_calls_resend(self, mock_resend):
        mock_resend.Emails.send.return_value = {"id": "email-123"}

        service = EmailService()
        self._send_completed(service)

        mock_resend.Emails.send.assert_called_once()
        params = mock_resend.Emails.send.call_args[0][0]
        self.assertEqual(params["to"], ["user@example.com"])
        self.assertIn("Test Project", params["subject"])

    @override_settings(RESEND_API_KEY=None)
    def test_missing_api_key_raises(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RESEND_API_KEY", None)
            with self.assertRaises(ValueError):
                EmailService()
