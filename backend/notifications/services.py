"""
Email notification service for scan completion
"""
import logging
import os
from typing import Optional
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_scan_completion_email(scan, user):
    """
    Send email notification when a scan completes or fails
    
    Args:
        scan: Scan model instance
        user: User model instance (owner of the scan)
    """
    try:
        # Import here to avoid circular dependencies
        from notifications.email_service import EmailService
        
        email_service = EmailService()
        
        # Get scan details
        scan_type = scan.configuration.get_scan_type_display() if scan.configuration else "Unknown"
        project_name = scan.configuration.project.name if scan.configuration and scan.configuration.project else "Unknown Project"
        target_url = scan.target_url or "N/A"
        
        # Calculate duration
        duration = None
        if scan.start_time and scan.end_time:
            duration = scan.end_time - scan.start_time
            duration_str = format_duration(duration)
        else:
            duration_str = "N/A"
        
        # Get vulnerability count if scan completed
        vulnerability_count = None
        if scan.status == 'completed':
            try:
                from scanning.models.vulnerability import Vulnerability
                vulnerability_count = Vulnerability.objects.filter(scan=scan).count()
            except Exception as e:
                logger.warning(f"Could not get vulnerability count: {e}")
        
        # Prepare common email data
        common_data = {
            'user_email': 'hannanhaxor686@gmail.com',  # Hardcoded for Resend free tier
            'user_name': user.username or user.email.split('@')[0],
            'scan_id': scan.id,
            'scan_type': scan_type,
            'project_name': project_name,
            'target_url': target_url,
            'duration': duration_str,
            'start_time': scan.start_time.strftime('%Y-%m-%d %H:%M:%S') if scan.start_time else 'N/A',
            'end_time': scan.end_time.strftime('%Y-%m-%d %H:%M:%S') if scan.end_time else 'N/A',
        }
        
        # Send email based on status
        if scan.status == 'completed':
            # Add vulnerability count for completed scans
            email_data = {**common_data, 'vulnerability_count': vulnerability_count}
            email_service.send_scan_completed_email(**email_data)
        elif scan.status == 'failed':
            # Add error message for failed scans
            email_data = {**common_data, 'error_message': scan.error_message}
            email_service.send_scan_failed_email(**email_data)
        else:
            logger.info(f"Scan {scan.id} status is {scan.status}, skipping email notification")
            
    except Exception as e:
        logger.error(f"Failed to send scan completion email for scan {scan.id}: {e}", exc_info=True)
        # Don't raise - we don't want email failures to break scan completion


def format_duration(duration):
    """Format timedelta as human-readable string"""
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

