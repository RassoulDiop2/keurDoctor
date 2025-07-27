# Generated migration pour corriger session_id NULL

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0010_add_access_direct_field'),  # Dernière migration existante
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='session_id',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
    ]
