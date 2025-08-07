import logging

from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import CustomUser

logger = logging.getLogger(__name__)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""

    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ("email", "username", "password", "password_confirm")

    def validate(self, data):
        """Validate that the passwords match and meet complexity requirements"""
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords don't match."})

        # Check password complexity
        password = data["password"]
        if not any(char.isdigit() for char in password):
            raise serializers.ValidationError(
                {"password": "Password must contain at least one number."}
            )
        if not any(char in "!@#$%^&*()_+" for char in password):
            raise serializers.ValidationError(
                {"password": "Password must contain at least one special character."}
            )

        return data

    def create(self, validated_data):
        """Create a new user with encrypted password"""
        validated_data.pop("password_confirm")
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        """Validate user credentials"""
        user = authenticate(email=data["email"], password=data["password"])
        logger.debug(f"Authentication attempt for email: {data['email']}")
        if not user:
            logger.warning(f"Failed authentication attempt for email: {data['email']}")
            raise serializers.ValidationError("Invalid credentials. Please try again.")
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled.")
        # Temporarily comment out for testing
        # if not user.is_email_verified:
        #     raise serializers.ValidationError("Email is not verified. Please check your inbox.")

        data["user"] = user
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Validate that the email exists"""
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""

    token = serializers.CharField(required=True)
    password = serializers.CharField(required=True, min_length=8, write_only=True)
    password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        """Validate that the passwords match and meet complexity requirements"""
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords don't match."})

        # Check password complexity
        password = data["password"]
        if not any(char.isdigit() for char in password):
            raise serializers.ValidationError(
                {"password": "Password must contain at least one number."}
            )
        if not any(char in "!@#$%^&*()_+" for char in password):
            raise serializers.ValidationError(
                {"password": "Password must contain at least one special character."}
            )

        return data


AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    # Add any custom authentication backends here
]
