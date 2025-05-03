"""
Form security analyzer for passive scanning
"""
import logging
import re
from urllib.parse import urlparse
from scanning.models.vulnerability import Vulnerability

logger = logging.getLogger(__name__)

def analyze_forms(scan, forms):
    """
    Analyze forms for security issues.
    
    Args:
        scan (Scan): Scan object
        forms (list): Forms discovered during scanning
    """
    csrf_missing = []
    autocomplete_enabled = []
    insecure_method = []
    sensitive_forms = []
    password_inputs = []
    
    https_url_pattern = re.compile(r'^https://')
    
    for form in forms:
        form_url = form.get('url', '')
        form_action = form.get('action', '')
        form_method = form.get('method', 'get').upper()
        
        # Check HTTP/HTTPS
        if form_url and form_action and not https_url_pattern.match(form_url):
            insecure_method.append(form_url)
        
        # Check for CSRF protection
        has_csrf = False
        # Check form inputs for CSRF token fields
        for input_field in form.get('inputs', []):
            field_name = input_field.get('name', '').lower()
            if any(csrf_term in field_name for csrf_term in ['csrf', 'token', 'nonce', 'xsrf']):
                has_csrf = True
                break
        
        # Check form attributes for CSRF token
        if not has_csrf and 'data-csrf' in form:
            has_csrf = True
        
        # If still no CSRF token found and it's a POST form, report it
        if not has_csrf and form_method == 'POST':
            csrf_missing.append(form_url or form_action or "Unknown form URL")
        
        # Check for sensitive fields with autocomplete enabled
        has_sensitive_field = False
        for input_field in form.get('inputs', []):
            field_type = input_field.get('type', '').lower()
            field_name = input_field.get('name', '').lower()
            field_autocomplete = input_field.get('autocomplete', '').lower()
            
            # Check for password fields
            if field_type == 'password':
                password_inputs.append(form_url or form_action or "Unknown form URL")
                has_sensitive_field = True
                
                # Check autocomplete on password field
                if field_autocomplete != 'off' and field_autocomplete != 'new-password':
                    autocomplete_enabled.append(form_url or form_action or "Unknown form URL")
            
            # Check for other sensitive fields
            sensitive_fields = ['credit', 'card', 'cvv', 'ssn', 'social', 'secret', 'passport', 'account']
            if any(sensitive in field_name for sensitive in sensitive_fields):
                has_sensitive_field = True
                
                # Check autocomplete on sensitive field
                if field_autocomplete != 'off':
                    autocomplete_enabled.append(form_url or form_action or "Unknown form URL")
        
        # Mark forms with sensitive fields
        if has_sensitive_field:
            sensitive_forms.append(form_url or form_action or "Unknown form URL")
    
    # Create vulnerability records
    if csrf_missing:
        Vulnerability.objects.create(
            scan=scan,
            name="Missing CSRF Protection",
            description=f"Found {len(csrf_missing)} forms without CSRF protection. These forms may be vulnerable to cross-site request forgery (CSRF) attacks, where attackers can make unauthorized requests on behalf of authenticated users.",
            severity="medium",
            evidence=f"Forms found at: {', '.join(csrf_missing[:5])}",
            remediation="Implement CSRF protection for all forms by including a CSRF token that is validated server-side.",
            confidence=0.8
        )
        logger.info(f"Found {len(csrf_missing)} forms without CSRF protection")
    
    if autocomplete_enabled:
        Vulnerability.objects.create(
            scan=scan,
            name="Autocomplete Enabled on Sensitive Fields",
            description=f"Found {len(autocomplete_enabled)} forms with autocomplete enabled on sensitive fields. This may allow browsers to store sensitive information, potentially exposing it to anyone with access to the user's device.",
            severity="low",
            evidence=f"Forms found at: {', '.join(autocomplete_enabled[:5])}",
            remediation="Disable autocomplete for sensitive fields by adding autocomplete='off' to the input fields or form element.",
            confidence=0.7
        )
        logger.info(f"Found {len(autocomplete_enabled)} forms with autocomplete enabled on sensitive fields")
    
    if insecure_method:
        Vulnerability.objects.create(
            scan=scan,
            name="Insecure Form Submission",
            description=f"Found {len(insecure_method)} forms submitted over HTTP rather than HTTPS. This can lead to sensitive information being transmitted in cleartext, making it vulnerable to interception.",
            severity="high",
            evidence=f"Forms found at: {', '.join(insecure_method[:5])}",
            remediation="Ensure all forms, especially those containing sensitive information, are submitted over HTTPS. Update form action URLs to use https:// protocol.",
            confidence=0.9
        )
        logger.info(f"Found {len(insecure_method)} forms submitted over HTTP")
    
    # Additional check for password forms that don't use POST
    password_with_get = []
    for form_url in password_inputs:
        for form in forms:
            if (form.get('url') == form_url or form.get('action') == form_url) and form.get('method', '').upper() != 'POST':
                password_with_get.append(form_url)
    
    if password_with_get:
        Vulnerability.objects.create(
            scan=scan,
            name="Password Submitted with GET Method",
            description=f"Found {len(password_with_get)} forms containing password fields that use the GET method instead of POST. This can result in passwords being visible in the URL, server logs, browser history, and referer headers.",
            severity="high",
            evidence=f"Forms found at: {', '.join(password_with_get[:5])}",
            remediation="Ensure all forms that contain password fields use the POST method.",
            confidence=0.9
        )
        logger.info(f"Found {len(password_with_get)} password forms using GET method")

def check_login_form_security(scan, forms):
    """
    Perform specific security checks on login forms
    
    Args:
        scan (Scan): Scan object
        forms (list): Forms discovered during scanning
    """
    login_forms = []
    insecure_login_forms = []
    
    # Identify login forms
    for form in forms:
        form_url = form.get('url', '')
        form_action = form.get('action', '')
        inputs = form.get('inputs', [])
        
        # Check if it's a login form
        has_password = any(input_field.get('type') == 'password' for input_field in inputs)
        has_username = any(any(user_field in input_field.get('name', '').lower() for user_field in ['user', 'email', 'login', 'name'])
                           for input_field in inputs)
        
        login_keywords = ['login', 'signin', 'sign-in', 'auth', 'account']
        url_suggests_login = any(keyword in (form_url.lower() + form_action.lower()) for keyword in login_keywords)
        
        if (has_password and has_username) or (has_password and url_suggests_login):
            login_forms.append(form)
            
            # Check if login form is submitted securely
            if form_url and not form_url.startswith('https://'):
                insecure_login_forms.append(form_url or form_action or "Unknown form URL")
    
    # Report insecure login forms
    if insecure_login_forms:
        Vulnerability.objects.create(
            scan=scan,
            name="Insecure Login Form",
            description=f"Found {len(insecure_login_forms)} login forms that are not served over HTTPS. This can lead to credentials being transmitted in cleartext and intercepted by attackers.",
            severity="critical",
            evidence=f"Login forms found at: {', '.join(insecure_login_forms[:5])}",
            remediation="Ensure all login forms are served over HTTPS and submitted to HTTPS endpoints.",
            confidence=0.9
        )
        logger.info(f"Found {len(insecure_login_forms)} insecure login forms")
    
    # Check for other login form issues
    check_brute_force_protection(scan, login_forms)

def check_brute_force_protection(scan, login_forms):
    """
    Check for potential lack of brute force protection in login forms
    
    Args:
        scan (Scan): Scan object
        login_forms (list): Login forms to analyze
    """
    # This is a basic passive check - we're looking for CAPTCHA or similar protections
    forms_without_protection = []
    
    for form in login_forms:
        form_url = form.get('url', '')
        form_action = form.get('action', '')
        form_html = form.get('html', '')  # If we have the raw HTML
        
        has_protection = False
        
        # Check for captcha inputs
        if form_html and any(captcha_term in form_html.lower() for captcha_term in ['captcha', 'recaptcha', 'g-recaptcha', 'cf-turnstile']):
            has_protection = True
        
        # Check form inputs for captcha fields
        for input_field in form.get('inputs', []):
            field_name = input_field.get('name', '').lower()
            field_id = input_field.get('id', '').lower()
            if 'captcha' in field_name or 'captcha' in field_id:
                has_protection = True
                break
        
        if not has_protection:
            forms_without_protection.append(form_url or form_action or "Unknown form URL")
    
    # Only report if we found login forms without protection
    if forms_without_protection and len(forms_without_protection) == len(login_forms):
        Vulnerability.objects.create(
            scan=scan,
            name="Potential Lack of Brute Force Protection",
            description="The login form(s) may not have adequate protection against brute force attacks. No CAPTCHA or similar protection mechanism was detected.",
            severity="medium",
            evidence=f"Login forms without apparent protection: {', '.join(forms_without_protection[:5])}",
            remediation="Implement protection mechanisms such as CAPTCHA, rate limiting, account lockout, or 2FA to prevent brute force attacks.",
            confidence=0.6  # Lower confidence as this is a passive detection
        )
        logger.info(f"Found {len(forms_without_protection)} login forms without apparent brute force protection")