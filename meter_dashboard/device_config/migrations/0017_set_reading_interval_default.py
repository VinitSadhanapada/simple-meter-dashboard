from django.db import migrations, models


def forwards(apps, schema_editor):
    SystemConfiguration = apps.get_model('device_config', 'SystemConfiguration')
    # Set reading_interval to 5 for all existing configurations
    SystemConfiguration.objects.all().update(reading_interval=5)


def backwards(apps, schema_editor):
    # Do not attempt to restore previous values
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('device_config', '0016_update_usb_copy_defaults'),
    ]

    operations = [
        migrations.AlterField(
            model_name='systemconfiguration',
            name='reading_interval',
            field=models.PositiveIntegerField(default=5, help_text='Seconds between reading cycles'),
        ),
        migrations.RunPython(forwards, backwards),
    ]
