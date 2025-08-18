#!/usr/bin/env python3
"""
Quick check and fix for DCMS template issues
"""


def quick_fix():
    """Quick fix for immediate URL issues"""

    from pathlib import Path

    # 1. First, create a comprehensive URLs file
    urls_content = '''from django.urls import path
from . import views

app_name = 'device_config'

urlpatterns = [
    # Main views
    path('', views.DeviceConfigView.as_view(), name='device_list'),
    path('', views.DeviceConfigView.as_view(), name='device_config'),
    
    # All possible DCMS URL patterns
    path('meters/', views.DeviceConfigView.as_view(), name='meter_list'),
    path('raspberry-pi/', views.DeviceConfigView.as_view(), name='raspberry_pi_list'),
    path('system-config/', views.DeviceConfigView.as_view(), name='system_config'),
    path('deployment/', views.DeviceConfigView.as_view(), name='deployment_list'),
    path('config-deployment/', views.DeviceConfigView.as_view(), name='config_deployment_list'),
    
    # Device CRUD
    path('add/', views.AddPiView.as_view(), name='add_device'),
    path('edit/<int:pi_id>/', views.EditPiView.as_view(), name='edit_device'),
    path('delete/<int:pi_id>/', views.DeletePiView.as_view(), name='delete_device'),
    path('deploy/<int:pi_id>/', views.DeployConfigView.as_view(), name='deploy_config'),
    path('test/<int:pi_id>/', views.TestConnectionView.as_view(), name='test_connection'),
    
    # Backward compatibility
    path('add-pi/', views.AddPiView.as_view(), name='add_pi'),
    path('edit-pi/<int:pi_id>/', views.EditPiView.as_view(), name='edit_pi'),
    path('delete-pi/<int:pi_id>/', views.DeletePiView.as_view(), name='delete_pi'),
]
'''

    # 2. Write the URLs file
    urls_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/urls.py')

    with open(urls_file, 'w') as f:
        f.write(urls_content)

    print("✅ Updated URLs with all DCMS patterns")

    # 3. Also add the meter_list route to main project URLs
    main_urls = '''from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('meter_readings.urls')),
    path('device-config/', include('device_config.urls')),
    path('dashboard/', include('meter_readings.urls')),
    
    # Direct URL name for templates
    path('meter-list/', RedirectView.as_view(pattern_name='device_config:meter_list'), name='meter_list'),
]
'''

    main_urls_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/meter_dashboard/urls.py')

    with open(main_urls_file, 'w') as f:
        f.write(main_urls)

    print("✅ Added meter_list to main URLs")

    print("""
🎉 Quick fix applied!

✅ Added all possible DCMS URL patterns
✅ Added meter_list route to main project
✅ Backward compatibility maintained

🚀 Try Django server now:
   cd meter_dashboard
   python3 manage.py runserver 0.0.0.0:8000
    """)


if __name__ == "__main__":
    quick_fix()
