from django.contrib import admin

from .models import (PassiveReconResult, Scan,
                     ScanConfiguration, ScanLog, Vulnerability)


class ScanConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "scan_type",
        "min_confidence",
        "created_at",
    )
    list_filter = ("scan_type",)
    search_fields = ("project__name",)
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Basic Settings",
            {
                "fields": (
                    "project",
                    "scan_type",
                    "min_confidence",
                    "user_agent",
                    "request_timeout",
                )
            },
        ),
        (
            "Tool Selection",
            {"fields": ("use_sslyze", "use_nuclei", "use_wappalyzer", "use_zap_passive")},
        ),
    )


class ScanAdmin(admin.ModelAdmin):
    list_display = (
        "target_url",
        "status",
        "progress",
        "start_time",
        "end_time",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("target_url",)
    date_hierarchy = "created_at"
    readonly_fields = ("uuid", "progress", "start_time", "end_time", "error_message")


class PassiveReconResultAdmin(admin.ModelAdmin):
    list_display = ("scan", "created_at")
    search_fields = ("scan__target_url",)
    date_hierarchy = "created_at"


class VulnerabilityAdmin(admin.ModelAdmin):
    list_display = ("name", "severity", "scan", "created_at")
    list_filter = ("severity",)
    search_fields = ("name", "description", "scan__target_url")
    date_hierarchy = "created_at"


class ScanLogAdmin(admin.ModelAdmin):
    list_display = ("scan", "level", "message", "timestamp")
    list_filter = ("level",)
    search_fields = ("message", "scan__target_url")
    date_hierarchy = "timestamp"


# Register models
admin.site.register(ScanConfiguration, ScanConfigurationAdmin)
admin.site.register(Scan, ScanAdmin)
admin.site.register(PassiveReconResult, PassiveReconResultAdmin)
admin.site.register(Vulnerability, VulnerabilityAdmin)
admin.site.register(ScanLog, ScanLogAdmin)
