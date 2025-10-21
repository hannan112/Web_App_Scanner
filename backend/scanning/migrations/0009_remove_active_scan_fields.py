from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("scanning", "0008_alter_scanconfiguration_crawl_depth_and_more"),
    ]

    operations = [
        migrations.RemoveField(model_name="scanconfiguration", name="crawl_depth"),
        migrations.RemoveField(model_name="scanconfiguration", name="crawl_max_pages"),
        migrations.RemoveField(model_name="scanconfiguration", name="crawl_timeout"),
        migrations.RemoveField(model_name="scanconfiguration", name="respect_robots_txt"),
        migrations.RemoveField(model_name="scanconfiguration", name="use_zap_spider"),
        migrations.RemoveField(model_name="scanconfiguration", name="zap_spider_type"),
        migrations.RemoveField(model_name="scanconfiguration", name="scan_js_files"),
        migrations.RemoveField(model_name="scanconfiguration", name="scan_forms"),
    ]


