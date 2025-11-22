# Email Notifications Setup Guide

This app handles email notifications when scans complete or fail.

## Setup Instructions

### 1. Install Dependencies

```bash
pip install resend
```

Or if using requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Get Resend API Key

1. Go to [https://resend.com](https://resend.com)
2. Sign up for a free account (3,000 emails/month free)
3. Verify your email address
4. Go to API Keys section
5. Create a new API key
6. Copy the API key (starts with `re_`)

### 3. Configure Environment Variables

Add these to your `.env` file in the `backend/` directory:

```env
# Resend API Configuration
RESEND_API_KEY=re_your_api_key_here

# Email From Address
# IMPORTANT: Resend doesn't allow Gmail/Yahoo/Outlook addresses directly
# Option 1: Use Resend's test domain (works immediately, no setup needed)
EMAIL_FROM_ADDRESS=onboarding@resend.dev

# Option 2: Verify your own domain in Resend dashboard, then use:
# EMAIL_FROM_ADDRESS=noreply@yourdomain.com

# Email From Name (optional, defaults to "Security Scanner")
EMAIL_FROM_NAME=Security Scanner

# Site URL for email links (optional, defaults to localhost:3000)
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

**Important Note about Gmail/Yahoo/Outlook:**
- Resend **does not allow** sending from Gmail, Yahoo, or Outlook addresses directly
- The code will automatically use `onboarding@resend.dev` if it detects a Gmail/Yahoo/Outlook address
- For production, you need to verify your own domain in Resend dashboard

### 4. Using Resend's Test Domain (Recommended for Testing)

- **Test Domain**: `onboarding@resend.dev` (works immediately, no verification needed)
- This is perfect for development and testing
- Emails will show as coming from "Security Scanner <onboarding@resend.dev>"
- Recipients will still receive emails normally

### 5. Verify Your Own Domain (For Production)

If you want to use your own email address:
1. Go to https://resend.com/domains
2. Add your domain (e.g., `yourdomain.com`)
3. Add the DNS records Resend provides
4. Wait for verification (usually a few minutes)
5. Then use: `EMAIL_FROM_ADDRESS=noreply@yourdomain.com`

### 5. Test the Setup

1. Start a scan in your application
2. Wait for it to complete
3. Check your email inbox for the notification

## How It Works

- When a scan completes successfully → Sends "Scan Completed" email
- When a scan fails → Sends "Scan Failed" email
- Emails include:
  - Project name
  - Target URL
  - Scan type
  - Duration
  - Results summary (for completed scans)
  - Link to view results

## Troubleshooting

### Email not sending?

1. Check that `RESEND_API_KEY` is set correctly
2. Verify your email address in Resend dashboard
3. Check backend logs for error messages
4. Make sure `EMAIL_FROM_ADDRESS` matches your verified email

### Getting API errors?

- Check Resend dashboard for API usage limits
- Free tier: 3,000 emails/month
- Verify your email address is confirmed in Resend

## Alternative Email Services

If you want to use a different service, you can modify `email_service.py`:

- **SendGrid**: Replace Resend code with SendGrid SDK
- **Mailgun**: Replace Resend code with Mailgun SDK
- **Amazon SES**: Replace Resend code with boto3

The interface in `services.py` remains the same.

