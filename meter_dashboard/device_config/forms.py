from django import forms
from django.contrib import admin
from .models import MeterDevice, RaspberryPi


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
        # Add help text
        self.fields['meter_model'].help_text = (
            "Select from the dropdown or type a new meter model. "
            "New models will be automatically saved."
        )


class RaspberryPiForm(forms.ModelForm):
    class Meta:
        model = RaspberryPi
        fields = '__all__'
        widgets = {
            'ssh_password': forms.PasswordInput(render_value=True, attrs={'class': 'vTextField', 'autocomplete': 'new-password', 'data-toggle': 'password'}),
        }

    class Media:
        js = ('admin/js/show_password_toggle.js',)
