from backend import settings


def send_verification_email(email, token):
    """Send verification email to user"""
    verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"
    
    # For testing or development, print the URL
    print(f"Verification URL for {email}: {verification_url}")

def send_password_reset_email(email, token):
    """Send password reset email to user"""
    reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"
    
    # For testing, just print the reset URL
    print(f"Password reset URL for {email}: {reset_url}")
    
    # Comment out the email sending for now
    # send_mail(...)