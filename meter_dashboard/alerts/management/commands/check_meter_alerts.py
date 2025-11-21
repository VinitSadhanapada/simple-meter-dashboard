from django.core.management.base import BaseCommand
from django.utils import timezone

# Placeholder imports; adapt once Meter & Reading access patterns confirmed.
# from meters.models import Meter
# from meter_readings.models import Reading
from meter_dashboard.alerts.models import ActiveAlert

"""Management command: evaluate meter readings over the last window
and maintain ActiveAlert rows.

Execution Strategy (initial minimal version):
1. Iterate all meters.
2. Query readings in last WINDOW_MINUTES.
3. Compute aggregate(s): avg, min, max (extendable).
4. Compare with static thresholds (later: dynamic per meter).
5. Insert/update ActiveAlert when out of bounds; delete if back to normal.

Deferred Enhancements:
- ForeignKey relationships once models imported cleanly.
- Configurable thresholds (DB table or JSON per meter).
- Multi-rule support (voltage, current, power factor, etc.).
- Rate-of-change / sustained violation logic.
- AlertEvent historical logging.
- Notification hooks (email/WebSocket).

Run Frequency: every 1–2 minutes via cron/systemd initially.
Later: Celery beat.
"""

WINDOW_MINUTES = 10
# Simple static threshold example; refine later or load from env / DB.
THRESHOLDS = {
    # code: (low, high, source_field)
    'voltage_out_of_range': (210.0, 250.0, 'voltage'),
}

class Command(BaseCommand):
    help = "Evaluate meter readings over the last window and update ActiveAlert table"

    def handle(self, *args, **options):
        start = timezone.now()
        window_start = start - timezone.timedelta(minutes=WINDOW_MINUTES)

        # TODO: Replace placeholders with actual ORM queries once models known.
        # meters = Meter.objects.all()
        meters = []  # Placeholder list; integrate with real Meter model.

        evaluated = 0
        for meter in meters:
            evaluated += 1
            # readings = Reading.objects.filter(meter=meter, timestamp__gte=window_start)
            readings = []  # Placeholder
            if not readings:
                # If no data in window, optionally clear existing alerts.
                continue
            # Placeholder aggregate; replace with ORM aggregations.
            avg_voltage = 0.0
            low, high, field = THRESHOLDS['voltage_out_of_range']
            if avg_voltage < low or avg_voltage > high:
                ActiveAlert.objects.update_or_create(
                    meter_id=getattr(meter, 'id', 0),
                    code='voltage_out_of_range',
                    defaults={'value': avg_voltage}
                )
            else:
                ActiveAlert.objects.filter(meter_id=getattr(meter, 'id', 0), code='voltage_out_of_range').delete()

        self.stdout.write(self.style.SUCCESS(
            f"Alert evaluation complete. Meters evaluated={evaluated}. Window start={window_start.isoformat()}"
        ))
