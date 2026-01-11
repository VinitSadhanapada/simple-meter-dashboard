from django.db import migrations


OTADEPLOYMENT_CREATE_SQL = r"""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'device_config_otadeployment'
    ) THEN
        CREATE TABLE public.device_config_otadeployment (
            id BIGSERIAL PRIMARY KEY,
            raspberry_pi_id BIGINT NOT NULL,
            source_dir VARCHAR(500) NOT NULL,
            exclude_file VARCHAR(500) NOT NULL DEFAULT '/home/isha/deepak/MFM_offline_setup/legacy/scp/dont_scp',
            status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            result_message TEXT NOT NULL DEFAULT '',
            deployed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMPTZ NULL,
            CONSTRAINT device_config_otadeployment_raspberry_pi_id_fk
                FOREIGN KEY (raspberry_pi_id)
                REFERENCES public.device_config_raspberrypi (id)
                ON DELETE CASCADE
        );
        CREATE INDEX device_config_otadeployment_raspberry_pi_id_idx
            ON public.device_config_otadeployment (raspberry_pi_id);
    END IF;
END$$;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("device_config", "0012_add_missing_fields"),
    ]

    operations = [
        migrations.RunSQL(sql=OTADEPLOYMENT_CREATE_SQL, reverse_sql=migrations.RunSQL.noop),
    ]
