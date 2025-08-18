from django.urls import path
from . import views

app_name = 'device_config'

urlpatterns = [
    # Main device list view
    path('', views.DeviceConfigView.as_view(), name='device_list'),
    path('', views.DeviceConfigView.as_view(), name='device_config'),

    # Old-style dashboard paths for compatibility
    path('dashboard/', views.DeviceConfigView.as_view(), name='dashboard'),
    path('device/dashboard/', views.DeviceConfigView.as_view(),
         name='device_dashboard'),

    # DCMS compatibility URLs
    path('meters/', views.DeviceConfigView.as_view(), name='meter_list'),
    path('raspberry-pi/', views.DeviceConfigView.as_view(),
         name='raspberry_pi_list'),
    path('system-config/', views.DeviceConfigView.as_view(), name='system_config'),
    path('deployment/', views.DeviceConfigView.as_view(), name='deployment_list'),

    # Pi detail views (for URLs like /device-config/pi/2/)
    path('pi/<int:pi_id>/', views.PiDetailView.as_view(), name='pi_detail'),
    path('device/<int:device_id>/',
         views.PiDetailView.as_view(), name='device_detail'),

    # Device CRUD operations
    path('add/', views.AddPiView.as_view(), name='add_device'),
    path('edit/<int:pi_id>/', views.EditPiView.as_view(), name='edit_device'),
    path('delete/<int:pi_id>/', views.DeletePiView.as_view(), name='delete_device'),

    # SSH operations
    path('deploy/<int:pi_id>/',
         views.DeployConfigView.as_view(), name='deploy_config'),
    path('test/<int:pi_id>/', views.TestConnectionView.as_view(),
         name='test_connection'),

    # Backward compatibility
    path('add-pi/', views.AddPiView.as_view(), name='add_pi'),
    path('edit-pi/<int:pi_id>/', views.EditPiView.as_view(), name='edit_pi'),
    path('delete-pi/<int:pi_id>/', views.DeletePiView.as_view(), name='delete_pi'),
]
