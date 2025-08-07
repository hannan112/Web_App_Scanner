from django.contrib import admin

from .models import (AjaxSpiderResult, CrawlResult, PassiveReconResult, Scan,
                     ScanConfiguration, ScanLog, Vulnerability)


class ScanConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "scan_type",
        "crawl_depth",
        "respect_robots_txt",
        "reduce_false_positives",
        "created_at",
    )
    list_filter = ("scan_type", "respect_robots_txt", "reduce_false_positives")
    search_fields = ("project__name",)
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Basic Settings",
            {
                "fields": (
                    "project",
                    "scan_type",
                    "crawl_depth",
                    "respect_robots_txt",
                    "crawl_max_pages",
                )
            },
        ),
        ("Enhanced Scanner", {"fields": ("reduce_false_positives", "min_confidence")}),
        (
            "Tool Selection",
            {"fields": ("use_sslyze", "use_zap", "use_nuclei", "use_wappalyzer")},
        ),
        (
            "Advanced Tool Configuration",
            {
                "classes": ("collapse",),
                "fields": (
                    "zap_config",
                    "sslyze_config",
                    "nuclei_config",
                    "wappalyzer_config",
                ),
            },
        ),
    )


class ScanAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "status",
        "progress",
        "start_time",
        "end_time",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("project__name",)
    date_hierarchy = "created_at"
    readonly_fields = ("uuid", "progress", "start_time", "end_time", "error_message")


class PassiveReconResultAdmin(admin.ModelAdmin):
    list_display = ("scan", "created_at")
    search_fields = ("scan__project__name",)
    date_hierarchy = "created_at"


class CrawlResultAdmin(admin.ModelAdmin):
    list_display = ("scan", "pages_crawled", "created_at")
    search_fields = ("scan__project__name",)
    date_hierarchy = "created_at"


class VulnerabilityAdmin(admin.ModelAdmin):
    list_display = ("name", "severity", "scan", "created_at")
    list_filter = ("severity",)
    search_fields = ("name", "description", "scan__project__name")
    date_hierarchy = "created_at"


class ScanLogAdmin(admin.ModelAdmin):
    list_display = ("scan", "level", "message", "timestamp")
    list_filter = ("level",)
    search_fields = ("message", "scan__project__name")
    date_hierarchy = "timestamp"


class AjaxSpiderResultAdmin(admin.ModelAdmin):
    list_display = ("scan", "pages_crawled", "start_time", "end_time", "duration")
    search_fields = ("scan__project__name",)
    date_hierarchy = "start_time"
    readonly_fields = ("start_time", "end_time", "duration", "pages_crawled")


# Register models with their admin classes
admin.site.register(ScanConfiguration, ScanConfigurationAdmin)
admin.site.register(Scan, ScanAdmin)
admin.site.register(PassiveReconResult, PassiveReconResultAdmin)
admin.site.register(CrawlResult, CrawlResultAdmin)
admin.site.register(Vulnerability, VulnerabilityAdmin)
admin.site.register(ScanLog, ScanLogAdmin)
admin.site.register(AjaxSpiderResult, AjaxSpiderResultAdmin)
