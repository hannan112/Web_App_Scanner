"""
Test script to verify email notification setup
Run this to test if your Resend configuration is working
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from notifications.email_service import EmailService

def test_email():
    """Test sending an email"""
    try:
        print("Testing email configuration...")
        print(f"RESEND_API_KEY: {'Set' if os.getenv('RESEND_API_KEY') else 'NOT SET'}")
        print(f"EMAIL_FROM_ADDRESS: {os.getenv('EMAIL_FROM_ADDRESS', 'NOT SET')}")
        print(f"EMAIL_FROM_NAME: {os.getenv('EMAIL_FROM_NAME', 'NOT SET')}")
        print()
        
        # Initialize email service
        email_service = EmailService()
        print("✅ Email service initialized successfully!")
        print()
        
        # Test sending a simple email
        print("Sending test email...")
        email_service.send_scan_completed_email(
            user_email="hannanhaxor686@gmail.com",
            user_name="Test User",
            scan_id=999,
            scan_type="Test Scan",
            project_name="Test Project",
            target_url="https://example.com",
            duration="1m 30s",
            start_time="2024-01-01 10:00:00",
            end_time="2024-01-01 10:01:30",
            vulnerability_count=5
        )
        
        print("✅ Test email sent successfully!")
        print("Check your inbox at hannanhaxor686@gmail.com")
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\nPlease check your .env file has:")
        print("  RESEND_API_KEY=re_your_key")
        print("  EMAIL_FROM_ADDRESS=your_email@gmail.com")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email()

