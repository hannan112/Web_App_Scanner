# authentication/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # If user exists, connect the account to the existing account
        if sociallogin.is_existing:
            return

        # Check if the email exists
        if sociallogin.account.provider and not sociallogin.is_existing:
            # If it has an email and user with this email exists
            if sociallogin.email_addresses:
                email = sociallogin.email_addresses[0]
                User = get_user_model()  # Use Django's get_user_model() function directly
                try:
                    existing_user = User.objects.get(email=email.email)
                    # Connect this social account to the existing user
                    sociallogin.connect(request, existing_user)
                except User.DoesNotExist:
                    pass