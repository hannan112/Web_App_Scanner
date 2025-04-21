from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings


from .models import CustomUser, EmailVerification, PasswordResetToken
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    PasswordResetRequestSerializer, 
    PasswordResetConfirmSerializer
)
from .utils import send_verification_email, send_password_reset_email


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
            EmailVerification.objects.create(
                user=user,
                token=token,
                expires_at=expiry
            )

            # Send verification email
            send_verification_email(user.email, token)
            
            return Response(
                {"message": "User registered successfully. Please check your email to verify your account."},
                status=status.HTTP_201_CREATED
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
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = verification.user
            user.is_email_verified = True
            user.save()
            verification.delete()

            return Response(
                {"message": "Email verified successfully. You can now log in."},
                status=status.HTTP_200_OK
            )
        except EmailVerification.DoesNotExist:
            return Response(
                {"error": "Invalid verification token."},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserLoginView(APIView):
    """View for user login"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """View for password reset request"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            # Add your password reset logic here
            email = serializer.validated_data['email']
            # Send reset email
            return Response(
                {"message": "Password reset email has been sent."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """View for password reset confirmation"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            
            try:
                reset_token = PasswordResetToken.objects.get(token=token)
                
                if reset_token.is_used:
                    return Response(
                        {"error": "This token has already been used."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if reset_token.expires_at < timezone.now():
                    return Response(
                        {"error": "Reset token has expired."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                user = reset_token.user
                user.set_password(serializer.validated_data['password'])
                user.save()
                
                # Mark token as used
                reset_token.is_used = True
                reset_token.save()
                
                return Response(
                    {"message": "Password has been reset successfully."},
                    status=status.HTTP_200_OK
                )
            
            except PasswordResetToken.DoesNotExist:
                return Response(
                    {"error": "Invalid reset token."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.FRONTEND_URL
    client_class = OAuth2Client