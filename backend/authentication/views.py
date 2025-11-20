import logging
import uuid
from datetime import timedelta

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from django.contrib.auth import get_user_model  # Add this import
from django.forms import ValidationError
from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, EmailVerification, PasswordResetToken
from .serializers import (
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
)
from .utils import send_password_reset_email, send_verification_email

logger = logging.getLogger(__name__)


class UserRegistrationView(APIView):
    """View for user registration"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Create verification token
            token = str(uuid.uuid4())
            expiry = timezone.now() + timedelta(days=7)
            EmailVerification.objects.create(user=user, token=token, expires_at=expiry)

            # Send verification email
            send_verification_email(user.email, token)

            return Response(
                {
                    "message": "User registered successfully. Please check your email to verify your account."
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    """View for email verification"""

    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            verification = EmailVerification.objects.get(token=token)
            if verification.expires_at < timezone.now():
                return Response(
                    {"error": "Verification link has expired."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = verification.user
            user.is_email_verified = True
            user.save()
            verification.delete()

            return Response(
                {"message": "Email verified successfully. You can now log in."},
                status=status.HTTP_200_OK,
            )
        except EmailVerification.DoesNotExist:
            return Response(
                {"error": "Invalid verification token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserLoginView(APIView):
    """View for user login"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                    },
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """View for password reset request"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            # Add your password reset logic here
            email = serializer.validated_data["email"]
            # Send reset email
            return Response(
                {"message": "Password reset email has been sent."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """View for password reset confirmation"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data["token"]

            try:
                reset_token = PasswordResetToken.objects.get(token=token)

                if reset_token.is_used:
                    return Response(
                        {"error": "This token has already been used."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if reset_token.expires_at < timezone.now():
                    return Response(
                        {"error": "Reset token has expired."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                user = reset_token.user
                user.set_password(serializer.validated_data["password"])
                user.save()

                # Mark token as used
                reset_token.is_used = True
                reset_token.save()

                return Response(
                    {"message": "Password has been reset successfully."},
                    status=status.HTTP_200_OK,
                )

            except PasswordResetToken.DoesNotExist:
                return Response(
                    {"error": "Invalid reset token."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.FRONTEND_URL
    client_class = OAuth2Client

    def post(self, request, *args, **kwargs):
        try:
            # Log received data for debugging
            logger.info(f"Google login request received: {request.data}")

            # Ensure required fields are present
            if "access_token" not in request.data and "id_token" not in request.data:
                logger.error("Missing required tokens in request")
                return Response(
                    {"error": "Missing required tokens"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Pass to parent implementation
            response = super().post(request, *args, **kwargs)

            # If the response contains 'key', transform it to access/refresh format
            if response.status_code == 200 and "key" in response.data:
                # Get the user associated with this key
                from django.contrib.auth import get_user_model

                User = get_user_model()

                # This line assumes dj-rest-auth is using token authentication
                # You might need to adjust this if using a different auth method
                from rest_framework.authtoken.models import Token

                token = Token.objects.get(key=response.data["key"])
                user = token.user

                # Generate JWT tokens
                from rest_framework_simplejwt.tokens import RefreshToken

                refresh = RefreshToken.for_user(user)

                # Return the expected format
                return Response(
                    {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "user": {
                            "id": user.id,
                            "email": user.email,
                            "username": user.username,
                        },
                    }
                )

            # Log successful login
            if status.is_success(response.status_code):
                logger.info(
                    f"Google login successful for user ID: {response.data.get('user', {}).get('id')}"
                )

            return response

        except Exception as e:
            logger.exception(f"Google login error: {str(e)}")
            return Response(
                {"error": "Authentication failed", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class GoogleAuthCallbackView(APIView):
    """
    Callback endpoint for Google OAuth flow
    """

    authentication_classes = []  # No authentication for callback
    permission_classes = []  # No permissions for callback

    def get(self, request):
        """Handle OAuth callback from Google"""
        code = request.GET.get("code")
        state = request.GET.get("state")
        error = request.GET.get("error")

        if error:
            logger.error(f"Google OAuth error: {error}")
            return HttpResponse(f"Authentication error: {error}", status=400)

        if not code:
            logger.error("No authorization code in callback")
            return HttpResponse("No authorization code provided", status=400)

        # Log successful callback
        logger.info(
            f"Google OAuth callback received with code: {code[:5]}... and state: {state}"
        )

        # Redirect to frontend with a success message
        redirect_url = (
            f"{settings.FRONTEND_URL}/oauth-callback?success=true&provider=google"
        )

        return HttpResponse(
            f"<html><body>Authentication successful. <a href='{redirect_url}'>Click here</a> if not redirected automatically."
            f"<script>window.location.href='{redirect_url}';</script></body></html>"
        )


class UserProfileView(APIView):
    """
    Get current user profile
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user profile"""
        user = request.user
        return Response({
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "date_joined": user.date_joined,
        }, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    View for changing user password
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Change user password"""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Set the new password
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            logger.info(f"Password changed successfully for user: {user.email}")
            
            return Response(
                {"message": "Password changed successfully."},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
