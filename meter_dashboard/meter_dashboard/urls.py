from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from django.views.generic import RedirectView
from .api_views import api_root

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', RedirectView.as_view(pattern_name='meter_readings.urls'), name='home'),
    # path('dashboard/', RedirectView.as_view(pattern_name='meter_readings:dashboard'), name='dashboard'),  # Meter readings tab removed

    path('', include('meter_readings.urls')),
    path('device-config/', include('device_config.urls')),
    # path('device/', include('device_config.urls')),
    path('meters/', include('meters.urls')),
    path('api/', api_root, name='api_root'),
    path('meter_readings/', include('meter_readings.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
