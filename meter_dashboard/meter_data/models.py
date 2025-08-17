from django.db import models

class MeterReading(models.Model):
    location = models.TextField()
    device_id = models.CharField(max_length=100)
    meter_name = models.TextField(null=True, blank=True)
    time = models.DateTimeField()
    model = models.TextField(null=True, blank=True)
    watts_total = models.FloatField(null=True, blank=True)
    watts_r_ph = models.FloatField(null=True, blank=True)
    watts_y_ph = models.FloatField(null=True, blank=True)
    watts_b_ph = models.FloatField(null=True, blank=True)
    pf_ave = models.FloatField(null=True, blank=True)
    pf_r_ph = models.FloatField(null=True, blank=True)
    pf_y_ph = models.FloatField(null=True, blank=True)
    pf_b_ph = models.FloatField(null=True, blank=True)
    vln_average = models.FloatField(null=True, blank=True)
    v_r_ph = models.FloatField(null=True, blank=True)
    v_y_ph = models.FloatField(null=True, blank=True)
    v_b_ph = models.FloatField(null=True, blank=True)
    a_average = models.FloatField(null=True, blank=True)
    a_r_ph = models.FloatField(null=True, blank=True)
    a_y_ph = models.FloatField(null=True, blank=True)
    a_b_ph = models.FloatField(null=True, blank=True)
    frequency = models.FloatField(null=True, blank=True)
    wh_received = models.FloatField(null=True, blank=True)
    load_hours_delivered = models.FloatField(null=True, blank=True)
    no_of_interruption = models.FloatField(null=True, blank=True)
    on_hours = models.TextField(null=True, blank=True)
    v_r_harmonics = models.FloatField(null=True, blank=True)
    v_y_harmonics = models.FloatField(null=True, blank=True)
    v_b_harmonics = models.FloatField(null=True, blank=True)
    a_r_harmonics = models.FloatField(null=True, blank=True)
    a_y_harmonics = models.FloatField(null=True, blank=True)
    a_b_harmonics = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'meter_readings'
        ordering = ['-time']

    def __str__(self):
        return f"{self.time} - {self.device_id} - {self.meter_name}"
