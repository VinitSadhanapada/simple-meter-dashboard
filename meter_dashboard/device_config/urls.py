from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router
router = DefaultRouter()
router.register(r'raspberry-pis', views.RaspberryPiViewSet)
router.register(r'meter-devices', views.MeterDeviceViewSet)
router.register(r'system-configurations', views.SystemConfigurationViewSet)
router.register(r'deployments', views.ConfigurationDeploymentViewSet)

app_name = 'device_config'

urlpatterns = [
    # Web interface
    path('', views.dashboard, name='dashboard'),
    path('pi/<int:pi_id>/', views.pi_detail, name='pi_detail'),
    path('meters/', views.meter_list, name='meter_list'),

    # Export utilities
    path('export/device-config/<int:pi_id>/',
         views.export_device_config, name='export_device_config'),
    path('export/system-config/<int:pi_id>/',
         views.export_system_config, name='export_system_config'),

    # API endpoints
    path('api/', include(router.urls)),
]
