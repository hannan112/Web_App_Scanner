"""
Email service using Resend API
"""
import logging
import os
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("Resend package not installed. Email notifications will not work.")


class EmailService:
    """Service for sending emails via Resend"""
    
    def __init__(self):
        if not RESEND_AVAILABLE:
            raise ImportError("Resend package is not installed. Install it with: pip install resend")
        
        # Get API key from environment
        api_key = os.getenv('RESEND_API_KEY') or getattr(settings, 'RESEND_API_KEY', None)
        if not api_key:
            raise ValueError("RESEND_API_KEY not found in environment variables or settings")
        
        # Initialize Resend
        resend.api_key = api_key
        
        # Get email settings
        # For free Resend accounts, you can use their test domain: onboarding@resend.dev
        # Or verify your own domain in Resend dashboard
        raw_from_email = os.getenv('EMAIL_FROM_ADDRESS') or getattr(settings, 'EMAIL_FROM_ADDRESS', None)
        self.from_name = os.getenv('EMAIL_FROM_NAME') or getattr(settings, 'EMAIL_FROM_NAME', 'Security Scanner')
        
        # Resend doesn't allow sending from Gmail/Yahoo/Outlook directly
        # Use Resend's test domain for free accounts (works immediately)
        if raw_from_email and any(domain in raw_from_email.lower() for domain in ['@gmail.com', '@yahoo.com', '@outlook.com', '@hotmail.com']):
            logger.warning(f"Gmail/Yahoo/Outlook addresses require domain verification.")
            logger.warning(f"Using Resend test domain: onboarding@resend.dev")
            logger.warning(f"To use your own email, verify your domain at https://resend.com/domains")
            self.from_email = "onboarding@resend.dev"
        elif raw_from_email:
            self.from_email = raw_from_email
        else:
            # Default to Resend test domain if nothing is set
            self.from_email = "onboarding@resend.dev"
            logger.info("Using Resend test domain: onboarding@resend.dev")
        
        # Get base URL for links
        self.base_url = os.getenv('NEXT_PUBLIC_SITE_URL') or getattr(settings, 'SITE_URL', 'http://localhost:3000')
    
    def send_scan_completed_email(self, user_email: str, user_name: str, scan_id: int, 
                                  scan_type: str, project_name: str, target_url: str,
                                  duration: str, start_time: str, end_time: str,
                                  vulnerability_count: Optional[int] = None):
        """Send email when scan completes successfully"""
        try:
            subject = f"✅ Scan Completed: {project_name}"
            
            # Build email body
            html_body = self._build_completed_email_html(
                user_name=user_name,
                scan_id=scan_id,
                scan_type=scan_type,
                project_name=project_name,
                target_url=target_url,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
                vulnerability_count=vulnerability_count
            )
            
            text_body = self._build_completed_email_text(
                user_name=user_name,
                scan_id=scan_id,
                scan_type=scan_type,
                project_name=project_name,
                target_url=target_url,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
                vulnerability_count=vulnerability_count
            )
            
            # Send email
            params = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [user_email],
                "subject": subject,
                "html": html_body,
                "text": text_body,
            }
            
            logger.info(f"📧 Calling Resend API to send email to {user_email}...")
            logger.info(f"📧 Email params: from={self.from_name} <{self.from_email}>, to={user_email}, subject={subject}")
            
            email = resend.Emails.send(params)
            
            logger.info(f"📧 Resend API response: {email}")
            logger.info(f"✅ Scan completion email sent successfully to {user_email} for scan {scan_id}. Email ID: {email.get('id')}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send scan completion email: {e}", exc_info=True)
            raise
    
    def send_scan_failed_email(self, user_email: str, user_name: str, scan_id: int,
                               scan_type: str, project_name: str, target_url: str,
                               duration: str, start_time: str, end_time: str,
                               error_message: Optional[str] = None):
        """Send email when scan fails"""
        try:
            subject = f"❌ Scan Failed: {project_name}"
            
            # Build email body
            html_body = self._build_failed_email_html(
                user_name=user_name,
                scan_id=scan_id,
                scan_type=scan_type,
                project_name=project_name,
                target_url=target_url,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
                error_message=error_message
            )
            
            text_body = self._build_failed_email_text(
                user_name=user_name,
                scan_id=scan_id,
                scan_type=scan_type,
                project_name=project_name,
                target_url=target_url,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
                error_message=error_message
            )
            
            # Send email
            params = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [user_email],
                "subject": subject,
                "html": html_body,
                "text": text_body,
            }
            
            email = resend.Emails.send(params)
            logger.info(f"Scan failure email sent successfully to {user_email} for scan {scan_id}. Email ID: {email.get('id')}")
            
        except Exception as e:
            logger.error(f"Failed to send scan failure email: {e}", exc_info=True)
            raise
    
    def _build_completed_email_html(self, user_name: str, scan_id: int, scan_type: str,
                                    project_name: str, target_url: str, duration: str,
                                    start_time: str, end_time: str, vulnerability_count: Optional[int]):
        """Build HTML email body for completed scan"""
        results_url = f"{self.base_url}/scans/{scan_id}/results"
        
        vuln_text = f"<strong>{vulnerability_count}</strong> vulnerabilities" if vulnerability_count is not None else "Results available"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .info-box {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #667eea; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Scan Completed Successfully</h1>
                </div>
                <div class="content">
                    <p>Hi {user_name},</p>
                    <p>Your security scan has completed successfully!</p>
                    
                    <div class="info-box">
                        <strong>Project:</strong> {project_name}<br>
                        <strong>Target URL:</strong> {target_url}<br>
                        <strong>Scan Type:</strong> {scan_type}<br>
                        <strong>Duration:</strong> {duration}<br>
                        <strong>Started:</strong> {start_time}<br>
                        <strong>Completed:</strong> {end_time}<br>
                        <strong>Findings:</strong> {vuln_text}
                    </div>
                    
                    <a href="{results_url}" class="button">View Scan Results</a>
                    
                    <p>You can view detailed results, vulnerabilities, and download reports from the scan results page.</p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from Security Scanner.</p>
                    <p>If you did not initiate this scan, please contact support.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _build_completed_email_text(self, user_name: str, scan_id: int, scan_type: str,
                                     project_name: str, target_url: str, duration: str,
                                     start_time: str, end_time: str, vulnerability_count: Optional[int]):
        """Build plain text email body for completed scan"""
        results_url = f"{self.base_url}/scans/{scan_id}/results"
        vuln_text = f"{vulnerability_count} vulnerabilities" if vulnerability_count is not None else "Results available"
        
        return f"""
Hi {user_name},

Your security scan has completed successfully!

Project: {project_name}
Target URL: {target_url}
Scan Type: {scan_type}
Duration: {duration}
Started: {start_time}
Completed: {end_time}
Findings: {vuln_text}

View your scan results: {results_url}

You can view detailed results, vulnerabilities, and download reports from the scan results page.

---
This is an automated notification from Security Scanner.
If you did not initiate this scan, please contact support.
        """
    
    def _build_failed_email_html(self, user_name: str, scan_id: int, scan_type: str,
                                 project_name: str, target_url: str, duration: str,
                                 start_time: str, end_time: str, error_message: Optional[str]):
        """Build HTML email body for failed scan"""
        status_url = f"{self.base_url}/scans/{scan_id}/status"
        
        error_section = f"""
        <div class="info-box" style="border-left-color: #e74c3c;">
            <strong>Error Message:</strong><br>
            {error_message or 'Unknown error occurred'}
        </div>
        """ if error_message else ""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .info-box {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #e74c3c; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #e74c3c; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>❌ Scan Failed</h1>
                </div>
                <div class="content">
                    <p>Hi {user_name},</p>
                    <p>Unfortunately, your security scan has failed.</p>
                    
                    <div class="info-box">
                        <strong>Project:</strong> {project_name}<br>
                        <strong>Target URL:</strong> {target_url}<br>
                        <strong>Scan Type:</strong> {scan_type}<br>
                        <strong>Duration:</strong> {duration}<br>
                        <strong>Started:</strong> {start_time}<br>
                        <strong>Failed:</strong> {end_time}
                    </div>
                    
                    {error_section}
                    
                    <a href="{status_url}" class="button">View Scan Status</a>
                    
                    <p>Please check the scan status page for more details. You may want to try running the scan again.</p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from Security Scanner.</p>
                    <p>If you did not initiate this scan, please contact support.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _build_failed_email_text(self, user_name: str, scan_id: int, scan_type: str,
                                  project_name: str, target_url: str, duration: str,
                                  start_time: str, end_time: str, error_message: Optional[str]):
        """Build plain text email body for failed scan"""
        status_url = f"{self.base_url}/scans/{scan_id}/status"
        error_text = f"\nError Message: {error_message}" if error_message else ""
        
        return f"""
Hi {user_name},

Unfortunately, your security scan has failed.

Project: {project_name}
Target URL: {target_url}
Scan Type: {scan_type}
Duration: {duration}
Started: {start_time}
Failed: {end_time}
{error_text}

View scan status: {status_url}

Please check the scan status page for more details. You may want to try running the scan again.

---
This is an automated notification from Security Scanner.
If you did not initiate this scan, please contact support.
        """

