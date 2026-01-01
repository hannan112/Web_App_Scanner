import uuid
from django.db import migrations, models

def populate_uuids(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    for project in Project.objects.all():
        project.uuid = uuid.uuid4()
        project.save()

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_project_uuid'),
    ]

    operations = [
        migrations.RunPython(populate_uuids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='project',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
