

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.http import HttpResponse

# API Router
router = DefaultRouter()
router.register(r'pis', views.RaspberryPiViewSet)
router.register(r'meters', views.MeterDeviceViewSet)
router.register(r'system-configs', views.SystemConfigurationViewSet)
router.register(r'deployments', views.ConfigurationDeploymentViewSet)


# URL patterns
urlpatterns = [
    # Test URL to check if this file is loaded
    path('api/test/', lambda request: HttpResponse('ok')),  # <-- TEST URL

    # Homepage
    path('', views.home, name='home'),

    # Web Interface URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('pi/<int:pi_id>/', views.pi_detail, name='pi_detail'),
    path('meters/', views.meter_list, name='meter_list'),
    path('pi/<int:pi_id>/deploy/', views.deploy_config, name='deploy_config'),

    # Export URLs
    path('pi/<int:pi_id>/export/device-config/',
        views.export_device_config, name='export_device_config'),
    path('pi/<int:pi_id>/export/system-config/',
        views.export_system_config, name='export_system_config'),

    # Admin toggle meter active
    path('meter/<int:pk>/toggle_active/', views.toggle_meter_active, name='toggle_meter_active'),

    # API URLs
    path('api/', include(router.urls)),

    # AJAX URLs
    path('pi/test_connection/', views.test_pi_connection_ajax, name='test_pi_connection_ajax'),
]
