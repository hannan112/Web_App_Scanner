# Generated manually for parameter fuzzing configuration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scanning', '0018_alter_scanconfiguration_sqlmap_timeout_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='scanconfiguration',
            name='enable_parameter_fuzzing',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='scanconfiguration',
            name='max_parameter_combinations',
            field=models.IntegerField(default=50, help_text='Maximum parameter combinations to test per URL'),
        ),
        migrations.AddField(
            model_name='scanconfiguration',
            name='max_parameters_per_url',
            field=models.IntegerField(default=10, help_text='Maximum parameters to test per URL'),
        ),
        migrations.AddField(
            model_name='scanconfiguration',
            name='parameter_fuzzing_values',
            field=models.JSONField(default=dict, help_text='Custom parameter values to test'),
        ),
    ]
