"""
Enhanced Models with Better Relationships and Features

1. Add Model Managers for Common Queries
2. Implement Model Validation
3. Add Audit Trail
4. Better String Representations
5. Model Properties for Calculated Fields
"""

from django.db import models
from django.utils import timezone
from django.core.validators import validate_ipv4_address
from datetime import timedelta


class ActiveManager(models.Manager):
    """Manager to get only active records"""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class RecentReadingsManager(models.Manager):
    """Manager for recent meter readings"""

    def recent(self, hours=24):
        cutoff = timezone.now() - timedelta(hours=hours)
        return self.get_queryset().filter(reading_time__gte=cutoff)

    def by_location(self, location):
        return self.get_queryset().filter(pi_setup__location=location)

    def latest_per_meter(self):
        return self.get_queryset().distinct('meter_name').order_by('meter_name', '-reading_time')

# Enhanced MeterReading model


class EnhancedMeterReading(models.Model):
    """Enhanced meter reading model with better features"""

    # Existing fields...
    meter_name = models.CharField(max_length=100, db_index=True)
    reading_time = models.DateTimeField(db_index=True)
    watts_total = models.FloatField()
    vln_average = models.FloatField()

    # New calculated fields
    power_factor_calculated = models.FloatField(null=True, blank=True)
    energy_consumed_kwh = models.FloatField(null=True, blank=True)
    cost_estimate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = models.Manager()  # Default manager
    recent = RecentReadingsManager()

    class Meta:
        indexes = [
            models.Index(fields=['reading_time', 'meter_name']),
            models.Index(fields=['pi_setup', 'reading_time']),
        ]
        ordering = ['-reading_time']

    def __str__(self):
        return f"{self.meter_name} - {self.reading_time.strftime('%Y-%m-%d %H:%M')} - {self.watts_total}W"

    @property
    def power_consumption_level(self):
        """Categorize power consumption"""
        if self.watts_total < 1000:
            return 'Low'
        elif self.watts_total < 5000:
            return 'Medium'
        else:
            return 'High'

    @property
    def voltage_status(self):
        """Check voltage status"""
        if 220 <= self.vln_average <= 240:
            return 'Normal'
        elif self.vln_average < 220:
            return 'Low'
        else:
            return 'High'

    def calculate_energy_cost(self, rate_per_kwh=7.5):
        """Calculate estimated cost"""
        if self.energy_consumed_kwh:
            return self.energy_consumed_kwh * rate_per_kwh
        return 0

# Enhanced Pi Setup model


class EnhancedDcmsPiSetup(models.Model):
    """Enhanced Pi setup with validation and features"""

    pi_name = models.CharField(max_length=100, unique=True)
    pi_ip = models.GenericIPAddressField(
        unique=True, validators=[validate_ipv4_address])
    location = models.CharField(max_length=100, db_index=True)

    # Connection status
    connection_status = models.CharField(
        max_length=20,
        choices=[
            ('online', 'Online'),
            ('offline', 'Offline'),
            ('error', 'Error'),
            ('maintenance', 'Maintenance'),
        ],
        default='offline'
    )

    # Performance metrics
    cpu_usage = models.FloatField(null=True, blank=True)
    memory_usage = models.FloatField(null=True, blank=True)
    disk_usage = models.FloatField(null=True, blank=True)
    uptime_hours = models.IntegerField(null=True, blank=True)

    # Managers
    objects = models.Manager()
    active = ActiveManager()

    @property
    def is_online(self):
        """Check if Pi is online based on last connection"""
        if self.last_connected:
            return timezone.now() - self.last_connected < timedelta(minutes=10)
        return False

    @property
    def meter_count(self):
        """Count associated meters"""
        return self.meterreading_set.values('meter_name').distinct().count()

    def ping_test(self):
        """Test Pi connectivity"""
        import subprocess
        try:
            result = subprocess.run(['ping', '-c', '1', str(self.pi_ip)],
                                    capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False

# Audit Trail Model


class AuditLog(models.Model):
    """Track changes to important models"""

    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('CONFIG_CHANGE', 'Configuration Changed'),
        ('SSH_ACCESS', 'SSH Access'),
    ]

    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField()
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    user = models.CharField(max_length=100, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['timestamp']),
        ]
