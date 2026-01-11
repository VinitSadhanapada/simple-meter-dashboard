-- tools/clear_meterreadings_keep_drishti.sql
--
-- Safe script to backup and remove all meter readings EXCEPT those
-- belonging to the DrishtiStudio Raspberry Pi.
--
-- IMPORTANT: Review the SELECT preview section before running the DELETE.
-- Replace <DB_USER>, <DB_NAME> and <RPI_ID> as needed. If you don't know
-- the RPI id, run the provided SELECT to find it first.

-- 1) Recommended filesystem backup using pg_dump (run from shell):
-- pg_dump -U <DB_USER> -d <DB_NAME> -t public.meterreadings -Fc -f meterreadings_backup.dump

-- 2) Optional quick SQL backup (creates a copy table with timestamp):
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'meterreadings_backup') THEN
    CREATE TABLE public.meterreadings_backup AS TABLE public.meterreadings WITH NO DATA;
  END IF;
END$$;

INSERT INTO public.meterreadings_backup
SELECT * FROM public.meterreadings;

-- 3) Find RaspberryPi records that match the DrishtiStudio name/location
-- (adjust matching text as needed). This will show candidate RPI ids.
SELECT id, pi_name, location
FROM device_config_raspberrypi
WHERE lower(pi_name) LIKE '%drishti%'
   OR lower(location) LIKE '%drishti%';

-- If the previous query returns the correct RPI row, note its `id` value
-- and replace <RPI_ID> in the statements below. Example: set RPI_ID = 42

-- 4) Preview which meter_name values would be kept and which would be removed.
-- Replace <RPI_ID> with the chosen id from the previous query.
-- (This SELECT lists meter names that WOULD BE DELETED.)
SELECT DISTINCT mr.meter_name
FROM public.meterreadings mr
WHERE mr.meter_name NOT IN (
  SELECT md.meter_name
  FROM device_config_meterdevice md
  WHERE md.raspberry_pi = <RPI_ID>
);

-- Also preview the rows that would be deleted (LIMIT added for safety):
SELECT *
FROM public.meterreadings mr
WHERE mr.meter_name NOT IN (
  SELECT md.meter_name
  FROM device_config_meterdevice md
  WHERE md.raspberry_pi = <RPI_ID>
)
ORDER BY mr.time DESC
LIMIT 200;

-- 5) When you're ready: run the DELETE inside a transaction. Replace <RPI_ID>.
-- IMPORTANT: Do NOT run this until you have confirmed the preview above.
BEGIN;

DELETE FROM public.meterreadings
WHERE meter_name NOT IN (
  SELECT md.meter_name
  FROM device_config_meterdevice md
  WHERE md.raspberry_pi = <RPI_ID>
);

-- You can check how many rows will be removed using the preview queries earlier.
COMMIT;

-- 6) Reclaim space and update planner statistics:
VACUUM ANALYZE public.meterreadings;

-- 7) Verify remaining meters belong to the DrishtiStudio Raspberry Pi:
SELECT DISTINCT mr.meter_name
FROM public.meterreadings mr
LEFT JOIN device_config_meterdevice md ON md.meter_name = mr.meter_name
LEFT JOIN device_config_raspberrypi rp ON rp.id = md.raspberry_pi
WHERE rp.id = <RPI_ID>;

-- End of script. If you prefer I can produce a one-shot shell script that runs
-- the pg_dump and then launches psql to execute the DELETE (with prompts).
