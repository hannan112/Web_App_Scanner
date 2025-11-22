#!/usr/bin/env python
"""Simple test to verify Resend email works"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

print("=" * 50)
print("Testing Email Configuration")
print("=" * 50)

# Check environment variables
api_key = os.getenv('RESEND_API_KEY')
from_email = os.getenv('EMAIL_FROM_ADDRESS')

print(f"\nRESEND_API_KEY: {'✅ Set' if api_key else '❌ NOT SET'}")
if api_key:
    print(f"  Key starts with: {api_key[:10]}...")

print(f"\nEMAIL_FROM_ADDRESS: {from_email or '❌ NOT SET'}")

# Try to import and initialize
try:
    import resend
    print("\n✅ Resend package imported successfully")
    
    if api_key:
        resend.api_key = api_key
        print("✅ Resend API key configured")
        
        # Use test domain if Gmail detected
        if from_email and '@gmail.com' in from_email.lower():
            print(f"\n⚠️  Gmail detected, switching to Resend test domain")
            from_email = "onboarding@resend.dev"
        
        if not from_email:
            from_email = "onboarding@resend.dev"
            print(f"\n⚠️  No email set, using Resend test domain")
        
        print(f"\n📧 Will send from: {from_email}")
        
        # Try to send a test email
        print("\n" + "=" * 50)
        print("Attempting to send test email...")
        print("=" * 50)
        
        params = {
            "from": f"Security Scanner <{from_email}>",
            "to": ["hannanhaxor686@gmail.com"],
            "subject": "✅ Test Email - Email Notifications Working!",
            "html": """
            <h2>🎉 Email Notifications Are Working!</h2>
            <p>This is a test email from your Security Scanner application.</p>
            <p>When scans complete or fail, you'll receive similar notifications.</p>
            """,
            "text": "Email Notifications Are Working! This is a test email.",
        }
        
        email = resend.Emails.send(params)
        print(f"\n✅ Email sent successfully!")
        print(f"   Email ID: {email.get('id')}")
        print(f"   Check your inbox: hannanhaxor686@gmail.com")
        
    else:
        print("\n❌ RESEND_API_KEY not found in environment")
        print("   Add it to your .env file")
        
except ImportError:
    print("\n❌ Resend package not installed")
    print("   Run: pip install resend")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)

