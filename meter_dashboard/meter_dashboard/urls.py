from django.contrib import admin
from django.urls import path, include
<<<<<<< HEAD

from django.views.generic import RedirectView
from .api_views import api_root
=======
from django.views.generic import RedirectView
>>>>>>> clubbed_mfm_dcms_16-aug

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('meter_readings.urls')),
<<<<<<< HEAD
    path('device-config/', include('device_config.urls')),
=======
    path('device-config/', include('device_config.urls', namespace='device_config')),
>>>>>>> clubbed_mfm_dcms_16-aug

    # Old-style paths for backward compatibility
    path('device/', include('device_config.urls')),
    path('dashboard/', RedirectView.as_view(pattern_name='meter_readings:dashboard'), name='dashboard'),

    # Include the meters app URLs
    path('meters/', include('meters.urls')),
<<<<<<< HEAD

    # Basic API root endpoint
    path('api/', api_root, name='api_root'),
=======
>>>>>>> clubbed_mfm_dcms_16-aug
]
