from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('device_config', '0013_fix_missing_otadeployment_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='configurationdeployment',
            name='exclude_reading',
            field=models.BooleanField(default=False, help_text="Skip 'Reading Configuration' section (simulation_mode, intervals, port, enable_rtc, enable_csv_write)"),
        ),
        migrations.AddField(
            model_name='configurationdeployment',
            name='exclude_mqtt',
            field=models.BooleanField(default=False, help_text="Skip 'MQTT Settings' section (ENABLE_MQTT, MQTT block)"),
        ),
        migrations.AddField(
            model_name='configurationdeployment',
            name='exclude_usb_copy',
            field=models.BooleanField(default=False, help_text="Skip 'USB Copy' section"),
        ),
        migrations.AddField(
            model_name='configurationdeployment',
            name='exclude_cloud_sync',
            field=models.BooleanField(default=False, help_text="Skip 'Cloud Sync' section"),
        ),
        migrations.AddField(
            model_name='configurationdeployment',
            name='exclude_logging',
            field=models.BooleanField(default=False, help_text="Skip 'Logging' section (LOG_LEVEL)"),
        ),
        migrations.AddField(
            model_name='configurationdeployment',
            name='exclude_legacy_network',
            field=models.BooleanField(default=False, help_text="Skip 'Legacy / Network' section (DB_SERVER_IP, SERVER_API_IP)"),
        ),
    ]
