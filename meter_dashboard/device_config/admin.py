from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import RaspberryPi, MeterDevice, SystemConfiguration, ConfigurationDeployment, OTADeployment
from .forms import MeterDeviceForm, RaspberryPiForm
import os
from device_config.tasks import run_ota_deployment


@admin.register(RaspberryPi)
class RaspberryPiAdmin(admin.ModelAdmin):
    form = RaspberryPiForm
    list_display = ['pi_name', 'pi_ip', 'mac_address', 'location', 'is_active',
                    'ssh_key_status', 'meter_count', 'last_updated']
    list_filter = ['is_active', 'ssh_key_configured', 'location', 'created_at']
    search_fields = ['pi_name', 'pi_ip', 'mac_address', 'location']
    readonly_fields = ['ssh_key_configured',
                       'ssh_setup_error', 'last_updated', 'created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('pi_name', 'pi_ip', 'mac_address', 'location', 'is_active')
        }),
        ('SSH Configuration', {
            'fields': ('ssh_username', 'ssh_password', 'ssh_key_path', 'ssh_port', 'config_path'),
            'description': 'SSH password is only needed for initial key setup. It can be cleared after setup.'
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

    def ssh_key_status(self, obj):
        if obj.ssh_key_configured:
            return format_html('<span style="color: green;">✓ Configured</span>')
        else:
            return format_html('<span style="color: red;">✗ Not Configured</span>')
    ssh_key_status.short_description = 'SSH Key Status'

    def meter_count(self, obj):
        return obj.meters.filter(is_active=True).count()
    meter_count.short_description = 'Active Meters'

    actions = ['activate_pis', 'deactivate_pis', 'setup_ssh_keys',
               'test_ssh_connections', 'regenerate_ssh_keys']

    def activate_pis(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} Raspberry Pis were activated.')
    activate_pis.short_description = "Activate selected Raspberry Pis"

    def deactivate_pis(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request, f'{updated} Raspberry Pis were deactivated.')
    deactivate_pis.short_description = "Deactivate selected Raspberry Pis"

    def setup_ssh_keys(self, request, queryset):
        """Admin action to set up SSH keys for selected Pis"""
        success_count = 0
        error_count = 0

        for pi in queryset:
            if not pi.ssh_password:
                messages.error(request, f'{pi.pi_name}: No SSH password set')
                error_count += 1
                continue

            success, message = pi.setup_ssh_key()
            if success:
                messages.success(request, f'{pi.pi_name}: {message}')
                success_count += 1
            else:
                messages.error(request, f'{pi.pi_name}: {message}')
                error_count += 1

        if success_count > 0:
            messages.info(
                request, f'SSH keys set up for {success_count} Pi(s)')
        if error_count > 0:
            messages.warning(
                request, f'Failed to set up SSH keys for {error_count} Pi(s)')

    setup_ssh_keys.short_description = "Set up SSH keys for selected Pis"

    def test_ssh_connections(self, request, queryset):
        """Admin action to test SSH connections for selected Pis"""
        for pi in queryset:
            success, message = pi.test_ssh_connection()
            if success:
                messages.success(request, f'{pi.pi_name}: {message}')
            else:
                messages.error(request, f'{pi.pi_name}: {message}')

    test_ssh_connections.short_description = "Test SSH connections for selected Pis"

    def regenerate_ssh_keys(self, request, queryset):
        """Admin action to regenerate SSH keys for selected Pis"""
        success_count = 0
        error_count = 0

        for pi in queryset:
            if not pi.ssh_password:
                messages.error(request, f'{pi.pi_name}: No SSH password set')
                error_count += 1
                continue

            success, message = pi.setup_ssh_key(force_regenerate=True)
            if success:
                messages.success(
                    request, f'{pi.pi_name}: SSH key regenerated - {message}')
                success_count += 1
            else:
                messages.error(request, f'{pi.pi_name}: {message}')
                error_count += 1

        if success_count > 0:
            messages.info(
                request, f'SSH keys regenerated for {success_count} Pi(s)')
        if error_count > 0:
            messages.warning(
                request, f'Failed to regenerate SSH keys for {error_count} Pi(s)')

    regenerate_ssh_keys.short_description = "Regenerate SSH keys for selected Pis"


@admin.register(MeterDevice)
class MeterDeviceAdmin(admin.ModelAdmin):
    form = MeterDeviceForm
    list_display = ['meter_name', 'meter_model', 'meter_address',
                    'raspberry_pi', 'get_location', 'is_active', 'last_updated']
    list_filter = ['meter_model', 'is_active',
                   'raspberry_pi__pi_name', 'created_at']
    search_fields = ['meter_name', 'meter_model', 'raspberry_pi__pi_name']
    readonly_fields = ['last_updated', 'created_at']

    fieldsets = (
        ('Meter Information', {
            'fields': ('meter_name', 'meter_model', 'meter_address')
        }),
        ('Assignment', {
            'fields': ('raspberry_pi', 'is_active')
        }),
        
        ('Timestamps', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    def get_location(self, obj):
        return obj.location
    get_location.short_description = 'Location'

    class Media:
        css = {
            'all': ('admin/css/meter_device_admin.css',)
        }
        js = ('admin/js/meter_device_admin.js',)

    def render_change_form(self, request, context, *args, **kwargs):
        """Add datalist options to the form"""
        # Get all available meter models
        available_models = MeterDevice.get_available_meter_models()
        predefined_models = MeterDevice.get_predefined_choices()

        context['available_models'] = available_models
        context['predefined_models'] = predefined_models

        # Add datalist HTML to the form
        extra_context = {
            'meter_models_datalist': mark_safe(
                '<datalist id="meter_models_list">' +
                ''.join([f'<option value="{model[0]}">{model[1]}</option>'
                        for model in available_models]) +
                '</datalist>'
            )
        }
        context.update(extra_context)

        return super().render_change_form(request, context, *args, **kwargs)

    actions = ['activate_meters', 'deactivate_meters']

    def activate_meters(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} meters were activated.')
    activate_meters.short_description = "Activate selected meters"

    def deactivate_meters(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} meters were deactivated.')
    deactivate_meters.short_description = "Deactivate selected meters"


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'raspberry_pi', 'simulation_mode', 'reading_interval', 'inter_device_delay', 'port',
        'enable_rtc', 'enable_csv_write', 'mqtt_broker_ip', 'mqtt_port', 'mqtt_topic', 'mqtt_tls',
        'log_level', 'last_updated'
    ]
    list_filter = ['simulation_mode', 'log_level', 'enable_csv_write', 'mqtt_tls']
    search_fields = ['raspberry_pi__pi_name', 'raspberry_pi__pi_ip', 'mqtt_topic']
    readonly_fields = ['last_updated']

    fieldsets = (
        ('Raspberry Pi', {
            'fields': ('raspberry_pi',)
        }),
        ('Reading Configuration', {
            'fields': ('simulation_mode', 'reading_interval', 'inter_device_delay', 'port', 'enable_rtc', 'enable_csv_write')
        }),
        ('MQTT Settings', {
            'fields': ('mqtt_broker_ip', 'mqtt_port', 'mqtt_username', 'mqtt_password', 'mqtt_topic', 'mqtt_tls', 'mqtt_qos')
        }),
        ('USB Copy', {
            'fields': ('usb_copy_config',),
            'classes': ('collapse',)
        }),
        ('Cloud Sync', {
            'fields': ('cloud_sync_config',),
            'classes': ('collapse',)
        }),
        ('Logging', {
            'fields': ('log_level',)
        }),
        ('Legacy / Network', {
            'fields': ('db_server_ip', 'server_api_ip'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


@admin.register(ConfigurationDeployment)
class ConfigurationDeploymentAdmin(admin.ModelAdmin):
    list_display = ['raspberry_pi', 'deployment_type',
                    'status', 'deployed_at', 'completed_at', 'duration']
    list_filter = ['deployment_type', 'status', 'deployed_at']
    search_fields = ['raspberry_pi__pi_name', 'raspberry_pi__pi_ip']
    readonly_fields = ['deployed_at', 'completed_at', 'duration']

    fieldsets = (
        ('Deployment Information', {
            'fields': ('raspberry_pi', 'deployment_type', 'status')
        }),
        ('Timing', {
            'fields': ('deployed_at', 'completed_at', 'duration')
        }),
        ('Error Details', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )

    def duration(self, obj):
        if obj.completed_at and obj.deployed_at:
            duration = obj.completed_at - obj.deployed_at
            return f"{duration.total_seconds():.2f}s"
        return "N/A"
    duration.short_description = 'Duration'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('raspberry_pi', 'deployment_type')
        return self.readonly_fields

    actions = ['retry_failed_deployments']

    def retry_failed_deployments(self, request, queryset):
        # This would need to be implemented with the deployment service
        failed_deployments = queryset.filter(status='FAILED')
        self.message_user(
            request, f'Retry functionality needs to be implemented for {failed_deployments.count()} deployments.')
    retry_failed_deployments.short_description = "Retry failed deployments"


@admin.register(OTADeployment)
class OTADeploymentAdmin(admin.ModelAdmin):
    list_display = ['raspberry_pi', 'source_dir',
                    'exclude_file', 'status', 'deployed_at', 'completed_at']
    list_filter = ['status', 'deployed_at']
    search_fields = ['raspberry_pi__pi_name',
                     'raspberry_pi__pi_ip', 'source_dir']
    readonly_fields = ['deployed_at', 'completed_at', 'result_message']

    fieldsets = (
        ('Deployment Information', {
            'fields': ('raspberry_pi', 'source_dir', 'exclude_file', 'status')
        }),
        ('Timing', {
            'fields': ('deployed_at', 'completed_at')
        }),
        ('Result', {
            'fields': ('result_message',),
            'classes': ('collapse',)
        }),
    )

    actions = ['deploy_ota']

    def deploy_ota(self, request, queryset):
        for ota in queryset:
            pi = ota.raspberry_pi
            ota.status = 'IN_PROGRESS'
            ota.result_message = 'Deployment started...'
            ota.save()
            run_ota_deployment.delay(ota.id)  # Run in background
            messages.info(
                request, f"Deployment to {pi.pi_name} started in background. Status will update on refresh.")
    deploy_ota.short_description = "Deploy selected OTA scripts to Raspberry Pi"


# Customize admin site headers
admin.site.site_header = "Device Configuration Management System"
admin.site.site_title = "DCMS Admin"
admin.site.index_title = "Welcome to Device Configuration Management System"
