from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('device_config', '0014_optional_section_excludes'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE device_config_systemconfiguration "
                "DROP COLUMN IF EXISTS enable_mqtt;"
            ),
            reverse_sql=(
                "ALTER TABLE device_config_systemconfiguration "
                "ADD COLUMN IF NOT EXISTS enable_mqtt boolean NOT NULL DEFAULT false;"
            ),
        )
    ]
