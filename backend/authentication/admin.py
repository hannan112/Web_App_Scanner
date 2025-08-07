# authentication/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, EmailVerification, PasswordResetToken

admin.site.register(CustomUser, UserAdmin)
admin.site.register(EmailVerification)
admin.site.register(PasswordResetToken)
