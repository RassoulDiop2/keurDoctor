# Generated manually to remove IoT models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0007_auditlog'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AuthentificationIoT',
        ),
        migrations.DeleteModel(
            name='DispositifIoT',
        ),
        migrations.DeleteModel(
            name='TentativeAuthentificationIoT',
        ),
    ] 