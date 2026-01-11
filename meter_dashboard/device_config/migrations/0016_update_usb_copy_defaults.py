from django.db import migrations

NEW_USB_COPY_DEFAULTS = {
    "enabled": True,
    "dest_root_name": "COPIED_DATA",
    "subfolder": "data/csv",
    "poll_interval_sec": 5,
    "cooldown_seconds": 600,
    "min_free_mb": 50,
    "mount_settle_seconds": 2,
    "sync_after_copy": True,
    "eject_after_copy": True,
    "write_done_marker": True,
    "always_copy_on_insert": True,
    "min_rw_seconds": 30,
    "quiesce_wait_seconds": 120,
}

def forwards(apps, schema_editor):
    SystemConfiguration = apps.get_model('device_config', 'SystemConfiguration')
    for cfg in SystemConfiguration.objects.all():
        data = cfg.usb_copy_config or {}
        changed = False
        # Update dest_root_name if legacy value
        if data.get('dest_root_name') in ('OfflineDashboard', 'OFFLINEDASHBOARD'):
            data['dest_root_name'] = NEW_USB_COPY_DEFAULTS['dest_root_name']
            changed = True
        # Ensure all new keys present
        for k, v in NEW_USB_COPY_DEFAULTS.items():
            if k not in data:
                data[k] = v
                changed = True
        if changed:
            cfg.usb_copy_config = data
            cfg.save(update_fields=['usb_copy_config'])

def backwards(apps, schema_editor):
    # No rollback performed (keys can remain); leaving data intact.
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('device_config', '0015_cleanup_enable_mqtt_column'),
    ]
    operations = [
        migrations.RunPython(forwards, backwards),
    ]
