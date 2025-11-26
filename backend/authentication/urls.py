from django.urls import path
from django.contrib.auth.views import LogoutView
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    EmailVerificationView,
    GoogleAuthCallbackView,
    GoogleLoginView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    UserLoginView,
    UserProfileView,
    UserRegistrationView,
    PasswordChangeView,
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path(
        "verify-email/<str:token>/",
        EmailVerificationView.as_view(),
        name="verify-email",
    ),
    path("login/", UserLoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path(
        "request-password-reset/",
        PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path("google/", GoogleLoginView.as_view(), name="google_login"),
    path("google/callback/", GoogleAuthCallbackView.as_view(), name="google_callback"),
    path("user/", UserProfileView.as_view(), name="user_profile"),
    path("password/change/", PasswordChangeView.as_view(), name="password_change"),
    path("logout/", LogoutView.as_view(next_page='/api/auth/login/'), name="logout"),
]
