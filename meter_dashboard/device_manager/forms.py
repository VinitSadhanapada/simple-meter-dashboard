

from django import forms
from .models import RaspberryPi, MeterDevice

class MeterModelWidget(forms.TextInput):
	"""Custom widget that provides a datalist with predefined options"""
	def __init__(self, attrs=None):
		default_attrs = {
			'list': 'meter_models_list',
			'placeholder': 'Select or type meter model'
		}
		if attrs:
			default_attrs.update(attrs)
		super().__init__(default_attrs)

class MeterDeviceForm(forms.ModelForm):
	"""Custom form for MeterDevice with enhanced meter_model field"""
	class Meta:
		model = MeterDevice
		fields = '__all__'
		widgets = {
			'meter_model': MeterModelWidget(),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['meter_model'].help_text = (
			"Select from the dropdown or type a new meter model. "
			"New models will be automatically saved."
		)

	def clean(self):
		cleaned_data = super().clean()
		# Set instance fields from cleaned_data for validation
		for field, value in cleaned_data.items():
			setattr(self.instance, field, value)
		# Always set location to RPI location in the form as well (even if editing)
		if self.instance.raspberry_pi:
			self.instance.location = self.instance.raspberry_pi.location
			cleaned_data['location'] = self.instance.raspberry_pi.location
		# Call model's clean method to enforce model-level validation (including location rule)
		try:
			self.instance.clean()
		except Exception as e:
			from django.core.exceptions import ValidationError
			raise ValidationError(e)
		return cleaned_data

class LocationWidget(forms.TextInput):
	def __init__(self, attrs=None):
		default_attrs = {
			'list': 'location_list',
			'placeholder': 'Select or type location'
		}
		if attrs:
			default_attrs.update(attrs)
		super().__init__(default_attrs)

class RaspberryPiForm(forms.ModelForm):
	class Meta:
		model = RaspberryPi
		fields = '__all__'
		widgets = {
			'location': LocationWidget(),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['location'].help_text = (
			"Select from the dropdown or type a new location. "
			"New locations will be automatically saved."
		)
