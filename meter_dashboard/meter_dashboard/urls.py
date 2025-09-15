from django.contrib import admin
from django.urls import path, include

from django.views.generic import RedirectView
from .api_views import api_root

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='device_config:dashboard'), name='home'),
    path('device-config/', include('device_config.urls')),

    # Old-style paths for backward compatibility
    path('device/', include('device_config.urls')),
     # path('dashboard/', RedirectView.as_view(pattern_name='meter_readings:dashboard'), name='dashboard'),  # Meter readings tab removed

    # Include the meters app URLs
    path('meters/', include('meters.urls')),

    # Basic API root endpoint
    path('api/', api_root, name='api_root'),

    # Add meter_readings URLs
    path('meter_readings/', include('meter_readings.urls')),
]
