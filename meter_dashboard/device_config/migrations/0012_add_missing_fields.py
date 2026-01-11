"""Add missing SystemConfiguration fields that exist in models but are absent in DB.

This migration is intended to repair a schema mismatch where prior migrations
were recorded as applied but the database schema didn't receive all columns.
"""
from django.db import migrations, models
import device_config.models
import encrypted_model_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('device_config', '0011_systemconfiguration_cloud_sync_config_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemconfiguration',
            name='cloud_sync_config',
            field=models.JSONField(blank=True, default=device_config.models._default_cloud_sync, help_text='Cloud sync configuration block'),
        ),
        migrations.AddField(
            model_name='systemconfiguration',
            name='mqtt_password',
            field=encrypted_model_fields.fields.EncryptedCharField(blank=True, help_text='MQTT password (optional)', null=True),
        ),
        migrations.AddField(
            model_name='systemconfiguration',
            name='mqtt_port',
            field=models.PositiveIntegerField(default=1883, help_text='MQTT broker port'),
        ),
        migrations.AddField(
            model_name='systemconfiguration',
            name='mqtt_qos',
            field=models.PositiveSmallIntegerField(default=0, help_text='MQTT QoS level'),
        ),
        migrations.AddField(
            model_name='systemconfiguration',
            name='mqtt_tls',
            field=models.BooleanField(default=False, help_text='Use TLS for MQTT connection'),
        ),
        migrations.AddField(
            model_name='systemconfiguration',
            name='mqtt_topic',
            field=models.CharField(default='meter/readings', help_text='MQTT topic for meter readings', max_length=200),
        ),
        migrations.AddField(
            model_name='systemconfiguration',
            name='mqtt_username',
            field=encrypted_model_fields.fields.EncryptedCharField(blank=True, help_text='MQTT username (optional)', null=True),
        ),
        migrations.AddField(
            model_name='systemconfiguration',
            name='usb_copy_config',
            field=models.JSONField(blank=True, default=device_config.models._default_usb_copy, help_text='USB copy behavior configuration'),
        ),
    ]
