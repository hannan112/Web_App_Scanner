# authentication/backends.py
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend to allow login with email

    Since we're using email as the USERNAME_FIELD in our CustomUser model,
    we need a custom backend that can authenticate using either username or email.
    """

    def authenticate(self, request, username=None, email=None, password=None, **kwargs):
        try:
            # Try to find a user by matching either username or email
            # If email is provided, use it; otherwise, use username as either username or email
            user = User.objects.get(
                Q(username=username) | Q(email=email if email else username)
            )
        except User.DoesNotExist:
            return None

        # Check password and whether the user can be authenticated (is_active, etc.)
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
