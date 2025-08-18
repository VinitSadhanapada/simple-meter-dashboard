from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('meter_readings.urls')),
    path('device-config/', include('device_config.urls')),
    
    # Old-style paths for backward compatibility
    path('device/', include('device_config.urls')),
    path('dashboard/', RedirectView.as_view(pattern_name='meter_readings:dashboard'), name='dashboard'),
]
