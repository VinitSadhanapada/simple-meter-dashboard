"""
Quick Implementation: Database Indexes for Performance
Add these to your meters/migrations/ folder
"""

from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('meters', '0008_alter_dcmspisetup_ssh_key_path_and_more'),
    ]

    operations = [
        # Add indexes for frequently queried fields
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_meter_readings_time ON meter_readings(reading_time DESC);",
            "DROP INDEX IF EXISTS idx_meter_readings_time;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_meter_readings_location ON meter_readings(location);",
            "DROP INDEX IF EXISTS idx_meter_readings_location;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_meter_readings_device ON meter_readings(device_id);",
            "DROP INDEX IF EXISTS idx_meter_readings_device;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_meter_readings_time_location ON meter_readings(reading_time DESC, location);",
            "DROP INDEX IF EXISTS idx_meter_readings_time_location;"
        ),
    ]