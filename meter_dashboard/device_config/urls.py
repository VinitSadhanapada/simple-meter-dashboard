from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router
router = DefaultRouter()
router.register(r'pis', views.RaspberryPiViewSet)
router.register(r'meters', views.MeterDeviceViewSet)
router.register(r'system-configs', views.SystemConfigurationViewSet)
router.register(r'deployments', views.ConfigurationDeploymentViewSet)

# URL patterns
urlpatterns = [
    # Web Interface URLs
    path('', views.dashboard, name='dashboard'),
    path('pi/<int:pi_id>/', views.pi_detail, name='pi_detail'),
    path('meters/', views.meter_list, name='meter_list'),
    path('pi/<int:pi_id>/deploy/', views.deploy_config, name='deploy_config'),

    # Export URLs
    path('pi/<int:pi_id>/export/device-config/',
         views.export_device_config, name='export_device_config'),
    path('pi/<int:pi_id>/export/system-config/',
         views.export_system_config, name='export_system_config'),

    # API URLs
    path('api/', include(router.urls)),
]