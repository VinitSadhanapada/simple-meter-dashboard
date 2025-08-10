from django.urls import path
from .views import meter_data, live_dashboard, dashboard_charts, get_device_config, update_device_status, device_management, push_config_view

urlpatterns = [
    path('api/meter/', meter_data),
    path('api/dashboard/', live_dashboard),
    path('charts/', dashboard_charts, name='dashboard_charts'),
    path('api/config/<str:pi_device_id>/',
         get_device_config, name='get_device_config'),
    path('api/status/<str:pi_device_id>/',
         update_device_status, name='update_device_status'),
    path('devices/', device_management, name='device_management'),
    path('devices/<int:device_id>/push-config/', push_config_view),
]
