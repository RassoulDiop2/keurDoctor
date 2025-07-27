# Generated manually to add missing access_direct field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0009_add_medical_models_clean'),
    ]

    operations = [
        migrations.AddField(
            model_name='rfidcard',
            name='access_direct',
            field=models.BooleanField(default=False, help_text="Permet l'accès direct au dashboard sans OTP"),
        ),
    ]
