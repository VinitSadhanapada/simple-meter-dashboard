from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import path, include


from .views import main_dashboard, api_live_page
from .views import alerts_dashboard
from .api_views import api_root, set_failure_mode, api_alert_events
from .ssh_api import ssh_command_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main_dashboard, name='home'),
    path('dashboard/', main_dashboard, name='dashboard_page'),
    path('device-config/', include('device_config.urls')),
    path('meters/', include('meters.urls')),
    path('api/', api_root, name='api_root'),
    path('api/set_failure_mode/', set_failure_mode, name='set_failure_mode'),
    path('api-live/', api_live_page, name='api_live_page'),
    path('api/alerts/', api_alert_events, name='api_alert_events'),
    path('alerts/', alerts_dashboard, name='alerts_dashboard'),
    path('meter_readings/', include('meter_readings.urls')),
    path('ssh-command/', ssh_command_view, name='ssh_command'),
    path('accounts/', include('django.contrib.auth.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
