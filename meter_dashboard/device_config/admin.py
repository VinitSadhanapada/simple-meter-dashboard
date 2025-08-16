from django.contrib import admin
from .models import RaspberryPi, MeterDevice, SystemConfiguration, ConfigurationDeployment


@admin.register(RaspberryPi)
class RaspberryPiAdmin(admin.ModelAdmin):
    list_display = ['pi_name', 'pi_ip', 'location',
                    'is_active', 'ssh_key_configured', 'last_updated']
    list_filter = ['is_active', 'ssh_key_configured', 'created_at']
    search_fields = ['pi_name', 'pi_ip', 'location']
    readonly_fields = ['last_updated', 'created_at', 'ssh_setup_error']

    fieldsets = (
        ('Basic Information', {
            'fields': ('pi_name', 'pi_ip', 'location', 'is_active')
        }),
        ('SSH Configuration', {
            'fields': ('ssh_username', 'ssh_password', 'ssh_key_path', 'ssh_port', 'config_path')
        }),
        ('SSH Status', {
            'fields': ('ssh_key_configured', 'ssh_setup_error'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MeterDevice)
class MeterDeviceAdmin(admin.ModelAdmin):
    list_display = ['meter_name', 'meter_model',
                    'meter_address', 'raspberry_pi', 'location', 'is_active']
    list_filter = ['meter_model', 'is_active', 'raspberry_pi']
    search_fields = ['meter_name', 'meter_model',
                     'location', 'raspberry_pi__pi_name']
    readonly_fields = ['last_updated', 'created_at']

    fieldsets = (
        ('Device Information', {
            'fields': ('meter_name', 'meter_model', 'meter_address', 'location')
        }),
        ('Configuration', {
            'fields': ('raspberry_pi', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ['raspberry_pi', 'simulation_mode',
                    'reading_interval', 'enable_mqtt', 'enable_rtc']
    list_filter = ['simulation_mode', 'enable_mqtt', 'enable_rtc', 'log_level']
    search_fields = ['raspberry_pi__pi_name', 'raspberry_pi__pi_ip']
    readonly_fields = ['last_updated']

    fieldsets = (
        ('Pi Configuration', {
            'fields': ('raspberry_pi',)
        }),
        ('Reading Settings', {
            'fields': ('simulation_mode', 'reading_interval', 'inter_device_delay', 'port')
        }),
        ('Features', {
            'fields': ('enable_mqtt', 'enable_rtc', 'log_level')
        }),
        ('Timestamps', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ConfigurationDeployment)
class ConfigurationDeploymentAdmin(admin.ModelAdmin):
    list_display = ['raspberry_pi', 'deployment_type',
                    'status', 'deployed_at', 'completed_at']
    list_filter = ['deployment_type', 'status', 'deployed_at']
    search_fields = ['raspberry_pi__pi_name', 'raspberry_pi__pi_ip']
    readonly_fields = ['deployed_at', 'completed_at']

    fieldsets = (
        ('Deployment Info', {
            'fields': ('raspberry_pi', 'deployment_type', 'status')
        }),
        ('Error Details', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('deployed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
