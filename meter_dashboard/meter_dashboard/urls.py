from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from .views import main_dashboard
from .api_views import api_root

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main_dashboard, name='home'),
    path('device-config/', include('device_config.urls')),
    path('meters/', include('meters.urls')),
    path('api/', api_root, name='api_root'),
    path('meter_readings/', include('meter_readings.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
