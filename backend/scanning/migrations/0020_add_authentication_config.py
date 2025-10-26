# Generated manually for authentication configuration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scanning', '0019_add_parameter_fuzzing_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='scanconfiguration',
            name='enable_authentication',
            field=models.BooleanField(default=False, help_text='Enable authentication for authenticated applications'),
        ),
        migrations.AddField(
            model_name='scanconfiguration',
            name='auth_login_url',
            field=models.URLField(blank=True, null=True, help_text='Login page URL'),
        ),
        migrations.AddField(
            model_name='scanconfiguration',
            name='auth_username_field',
            field=models.CharField(default='username', help_text='Username field name', max_length=100),
        ),
        migrations.AddField(
            model_name='scanconfiguration',
            name='auth_password_field',
            field=models.CharField(default='password', help_text='Password field name', max_length=100),
        ),
        migrations.AddField(
            model_name='scanconfiguration',
            name='auth_username',
            field=models.CharField(blank=True, help_text='Username for authentication', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='scanconfiguration',
            name='auth_password',
            field=models.CharField(blank=True, help_text='Password for authentication', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='scanconfiguration',
            name='auth_success_indicators',
            field=models.JSONField(default=list, help_text='Indicators of successful authentication'),
        ),
    ]


