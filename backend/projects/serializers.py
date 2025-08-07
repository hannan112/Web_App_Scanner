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
            "name",
            "target_url",
            "created_at",
            "scan_count",
            "last_scan_date",
        ]
        read_only_fields = ["id", "created_at", "scan_count", "last_scan_date"]


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed project view"""

    class Meta:
        model = Project
        fields = ["id", "name", "target_url", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating projects"""

    class Meta:
        model = Project
        fields = ["id", "name", "target_url", "description"]
        read_only_fields = ["id"]

    def validate_target_url(self, value):
        """
        Validate target URL is reachable
        """
        try:
            response = requests.head(value, timeout=5)
            if response.status_code >= 400:
                raise serializers.ValidationError(
                    f"URL returned status code {response.status_code}"
                )
        except requests.RequestException:
            raise serializers.ValidationError("URL is not reachable")
        return value
