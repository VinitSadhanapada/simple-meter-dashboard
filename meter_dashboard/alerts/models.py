from django.db import models
from django.utils import timezone

# NOTE: Model is intentionally minimal; will evolve after review of plan.
# ActiveAlert tracks alerts currently considered active based on the latest
# evaluation window (e.g., last 10 minutes). Clearing removes the row.
# For historical audit you may later add an AlertEvent table.
class ActiveAlert(models.Model):
    meter_id = models.IntegerField(db_index=True)  # Replace with ForeignKey to Meter when referencing existing app
    code = models.CharField(max_length=64, db_index=True)  # e.g. 'voltage_out_of_range'
    value = models.FloatField(null=True, blank=True)  # Representative metric (avg voltage, etc.)
    first_seen = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('meter_id', 'code')
        indexes = [
            models.Index(fields=['meter_id', 'code']),
        ]

    def __str__(self):
        return f"ActiveAlert(meter={self.meter_id}, code={self.code})"
