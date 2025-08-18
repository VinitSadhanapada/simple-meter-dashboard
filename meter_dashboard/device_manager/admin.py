
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect

from .models import RaspberryPi, MeterDevice, SystemConfiguration, ConfigurationDeployment
from .forms import RaspberryPiForm, MeterDeviceForm
# --- SystemConfiguration Admin ---
@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
	list_display = ['raspberry_pi', 'simulation_mode',
					'reading_interval', 'port', 'last_updated']
	list_filter = ['simulation_mode', 'enable_mqtt', 'enable_rtc']
	search_fields = ['raspberry_pi__pi_name', 'raspberry_pi__pi_ip']
	readonly_fields = ['last_updated']

	fieldsets = (
		('Raspberry Pi', {
			'fields': ('raspberry_pi',)
		}),
		('Reading Configuration', {
			'fields': ('simulation_mode', 'reading_interval', 'inter_device_delay', 'port')
		}),
		('Communication Settings', {
			'fields': ('enable_mqtt', 'enable_rtc')
		}),
		('Timestamps', {
			'fields': ('last_updated',),
			'classes': ('collapse',)
		}),
	)


# --- ConfigurationDeployment Admin ---
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
			return self.readonly_fields + ['raspberry_pi', 'deployment_type']
		return self.readonly_fields

	actions = ['retry_failed_deployments']

	def retry_failed_deployments(self, request, queryset):
		# This would need to be implemented with the deployment service
		failed_deployments = queryset.filter(status='FAILED')
		self.message_user(
			request, f'Retry functionality needs to be implemented for {failed_deployments.count()} deployments.')
	retry_failed_deployments.short_description = "Retry failed deployments"

class DashboardLinkAdminMixin:
	def changelist_view(self, request, extra_context=None):
		if extra_context is None:
			extra_context = {}
		extra_context['dashboard_link'] = True
		return super().changelist_view(request, extra_context=extra_context)

	def change_view(self, request, object_id, form_url='', extra_context=None):
		if extra_context is None:
			extra_context = {}
		extra_context['dashboard_link'] = True
		return super().change_view(request, object_id, form_url, extra_context=extra_context)


@admin.register(RaspberryPi)
class RaspberryPiAdmin(DashboardLinkAdminMixin, admin.ModelAdmin):
	form = RaspberryPiForm
	list_display = ['pi_name', 'pi_ip', 'location',
					'ssh_status_indicator', 'meter_count', 'last_updated']
	list_filter = ['location', 'created_at']
	search_fields = ['pi_name', 'pi_ip', 'location']
	readonly_fields = ['last_updated', 'created_at', 'is_active']

	fieldsets = (
		('Basic Information', {
			'fields': ('pi_name', 'pi_ip', 'location')
		}),
		('SSH Configuration', {
			'fields': ('ssh_username', 'ssh_password', 'ssh_key_path', 'ssh_port', 'config_path'),
			'description': 'Configure SSH access for this Raspberry Pi. Either provide password or SSH key path.'
		}),
		('Timestamps', {
			'fields': ('created_at', 'last_updated'),
			'classes': ('collapse',)
		}),
	)

	def meter_count(self, obj):
		return obj.meters.filter(is_active=True).count()
	meter_count.short_description = 'Active Meters'

	def ssh_status_indicator(self, obj):
		color = '#28a745' if obj.ssh_status else '#dc3545'
		title = 'SSH OK' if obj.ssh_status else 'SSH Failed'
		return format_html(
			'<div style="text-align:center;"><span title="{}" style="font-size:2em; text-decoration:none; display:inline-block; vertical-align:middle; color:{};">\u25cf</span></div>',
			title, color)
	ssh_status_indicator.short_description = 'SSH Status'
	ssh_status_indicator.allow_tags = True

	actions = []

	class Media:
		# Add datalist for locations
		js = ()
		css = {
			'all': ('admin/css/meter_device_admin.css',)
		}

	def render_change_form(self, request, context, *args, **kwargs):
		# Add datalist for locations
		locations = RaspberryPi.objects.exclude(location="").values_list('location', flat=True).distinct()
		context['location_datalist'] = mark_safe(
			'<datalist id="location_list">' +
			''.join([f'<option value="{loc}">{loc}</option>' for loc in locations]) +
			'</datalist>'
		)

		return super().render_change_form(request, context, *args, **kwargs)


# --- MeterDevice Admin ---
@admin.register(MeterDevice)
class MeterDeviceAdmin(DashboardLinkAdminMixin, admin.ModelAdmin):
	form = MeterDeviceForm

	list_display = ['meter_name', 'meter_model', 'meter_address',
					'raspberry_pi', 'location', 'active_toggle', 'last_updated', 'delete_meter']
	def delete_meter(self, obj):
		url = reverse('admin:device_manager_meterdevice_delete', args=[obj.pk])
		return format_html(
			'<a href="{}" title="Delete Meter" style="color:#dc3545; font-size:1.3em; text-decoration:none;" onclick="return confirm(\'Are you sure you want to delete this meter?\')">✖</a>', url)
	delete_meter.short_description = 'Delete Meter'
	delete_meter.allow_tags = True

	def active_toggle(self, obj):
		url = reverse('toggle_meter_active', args=[obj.pk])
		color = '#28a745' if obj.is_active else '#dc3545'
		title = 'Deactivate' if obj.is_active else 'Activate'
		return format_html(
			'<div style="text-align:center;"><a href="{}" title="{}" style="font-size:2em; text-decoration:none; display:inline-block; vertical-align:middle;"><span style="color:{};">●</span></a></div>',
			url, title, color)
	active_toggle.short_description = 'Active'
	active_toggle.allow_tags = True
	list_filter = ['meter_model', 'is_active',
				   'raspberry_pi__pi_name', 'created_at']
	search_fields = ['meter_name', 'meter_model',
					 'location', 'raspberry_pi__pi_name']
	readonly_fields = ['location', 'last_updated', 'created_at']

	fieldsets = (
		('Meter Information', {
			'fields': ('meter_name', 'meter_model', 'meter_address')
		}),
		('Location & Assignment', {
			'fields': ('location', 'raspberry_pi', 'is_active')
		}),
		('Timestamps', {
			'fields': ('created_at', 'last_updated'),
			'classes': ('collapse',)
		}),
	)

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

	actions = []

	def activate_meters(self, request, queryset):
		updated = queryset.update(is_active=True)
		self.message_user(request, f'{updated} meters were activated.')
	activate_meters.short_description = "Activate selected meters"

	def deactivate_meters(self, request, queryset):
		updated = queryset.update(is_active=False)
		self.message_user(request, f'{updated} meters were deactivated.')
	deactivate_meters.short_description = "Deactivate selected meters"
