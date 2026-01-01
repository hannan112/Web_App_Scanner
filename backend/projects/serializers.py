import requests
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from rest_framework import serializers

from .models import Project


class ProjectListSerializer(serializers.ModelSerializer):
    """Serializer for listing projects"""

    scan_count = serializers.IntegerField(read_only=True, default=0)
    last_scan_date = serializers.DateTimeField(read_only=True, default=None)

    class Meta:
        model = Project
        fields = [
            "id",
            "uuid",
            "name",
            "target_url",
            "created_at",
            "scan_count",
            "last_scan_date",
        ]
        read_only_fields = ["id", "uuid", "created_at", "scan_count", "last_scan_date"]


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed project view"""

    class Meta:
        model = Project
        fields = ["id", "uuid", "name", "target_url", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "uuid", "created_at", "updated_at"]


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating projects"""

    class Meta:
        model = Project
        fields = ["id", "uuid", "name", "target_url", "description"]
        read_only_fields = ["id", "uuid"]

    def validate_target_url(self, value):
        """
        Validate target URL format
        URL reachability check is optional - we validate format only
        Scanning will handle actual connectivity issues
        """
        # Validate URL format using Django's URLValidator
        url_validator = URLValidator()
        try:
            url_validator(value)
        except ValidationError:
            raise serializers.ValidationError("Invalid URL format")
        
        # Optional: Try to verify URL is reachable (non-blocking)
        # If validation fails, we still allow the URL since scanning will handle it
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        try:
            # Try HEAD request first (more efficient)
            response = requests.head(
                value, 
                timeout=5,  # Shorter timeout to avoid blocking
                allow_redirects=True,
                headers=headers,
                verify=True  # Verify SSL certificates
            )
            
            # If HEAD returns 405 (Method Not Allowed), try GET instead
            if response.status_code == 405:
                response = requests.get(
                    value,
                    timeout=5,
                    allow_redirects=True,
                    headers=headers,
                    verify=True
                )
            
            # Accept any response as valid - even 4xx/5xx means the URL exists
            # The actual scanning will determine if it's accessible
            # We only reject if there's a connection error (URL doesn't exist)
            
        except requests.exceptions.Timeout:
            # Timeout is OK - URL might be slow, scanning will handle it
            pass
        except requests.exceptions.ConnectionError:
            # Connection error might mean URL doesn't exist, but we'll be permissive
            # Some URLs might require VPN or special network access
            pass
        except requests.exceptions.SSLError:
            # SSL errors are OK - scanning will handle certificate issues
            pass
        except requests.exceptions.RequestException:
            # Any other request exception - still allow the URL
            # URL format is valid, scanning will handle connectivity
            pass
        
        return value
