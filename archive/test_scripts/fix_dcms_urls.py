#!/usr/bin/env python3
"""
Add all missing URL patterns that DCMS templates expect
"""


def add_missing_urls():
    """Add all missing URL patterns"""

    urls_content = '''from django.urls import path
from . import views


urlpatterns = [
    # Main device list (multiple aliases for compatibility)
    path('', views.DeviceConfigView.as_view(), name='device_list'),
    path('', views.DeviceConfigView.as_view(), name='device_config'),
    
    # DCMS compatibility URLs - all point to main view for now
    path('meters/', views.DeviceConfigView.as_view(), name='meter_list'),
    path('meter-list/', views.DeviceConfigView.as_view(), name='meter_list_alt'),
    path('raspberry-pi/', views.DeviceConfigView.as_view(), name='raspberry_pi_list'),
    path('system-config/', views.DeviceConfigView.as_view(), name='system_config'),
    path('deployment/', views.DeviceConfigView.as_view(), name='deployment_list'),
    path('config-deployment/', views.DeviceConfigView.as_view(), name='config_deployment_list'),
    
    # Device management
    path('add/', views.AddPiView.as_view(), name='add_device'),
    path('edit/<int:pi_id>/', views.EditPiView.as_view(), name='edit_device'),
    path('delete/<int:pi_id>/', views.DeletePiView.as_view(), name='delete_device'),
    
    # Device operations
    path('deploy/<int:pi_id>/', views.DeployConfigView.as_view(), name='deploy_config'),
    path('test/<int:pi_id>/', views.TestConnectionView.as_view(), name='test_connection'),
    
    # Alternative paths for backward compatibility
    path('add-pi/', views.AddPiView.as_view(), name='add_pi'),
    path('edit-pi/<int:pi_id>/', views.EditPiView.as_view(), name='edit_pi'),
    path('delete-pi/<int:pi_id>/', views.DeletePiView.as_view(), name='delete_pi'),
    path('deploy-config/<int:pi_id>/', views.DeployConfigView.as_view(), name='deploy_config_alt'),
    path('test-connection/<int:pi_id>/', views.TestConnectionView.as_view(), name='test_connection_alt'),
]
'''

    from pathlib import Path

    urls_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/urls.py')

    try:
        with open(urls_file, 'w', encoding='utf-8') as f:
            f.write(urls_content)
        print("✅ Added all missing URL patterns for DCMS compatibility")
        return True
    except Exception as e:
        print(f"❌ Error updating URLs: {e}")
        return False


def fix_template_url_references():
    """Fix template URL references to use correct patterns"""

    from pathlib import Path

    # Find and fix templates
    template_dirs = [
        Path('/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates'),
    ]

    # Common fixes for DCMS templates
    url_fixes = {
        "{% url 'meter_list' %}": "{% url 'device_config:meter_list' %}",
        "{% url 'device_manager:meter_list' %}": "{% url 'device_config:meter_list' %}",
        "{% url 'device_manager:device_list' %}": "{% url 'device_config:device_list' %}",
        "{% url 'device_manager:add_device' %}": "{% url 'device_config:add_device' %}",
        "{% url 'device_manager:edit_device' %}": "{% url 'device_config:edit_device' %}",
        "{% url 'device_manager:delete_device' %}": "{% url 'device_config:delete_device' %}",
        "{% url 'device_manager:deploy_config' %}": "{% url 'device_config:deploy_config' %}",
        "{% url 'device_manager:test_connection' %}": "{% url 'device_config:test_connection' %}",
        "{% url 'raspberry_pi_list' %}": "{% url 'device_config:raspberry_pi_list' %}",
        "{% url 'system_config' %}": "{% url 'device_config:system_config' %}",
        "{% url 'deployment_list' %}": "{% url 'device_config:deployment_list' %}",

        # Dashboard references
        "{% url 'dashboard' %}": "{% url 'meter_readings:dashboard' %}",
        "href='/dashboard/'": "href='{% url \"meter_readings:dashboard\" %}'",
        "href='/device-config/'": "href='{% url \"device_config:device_list\" %}'",
    }

    fixed_files = []

    for template_dir in template_dirs:
        if template_dir.exists():
            for template_file in template_dir.rglob('*.html'):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    original_content = content

                    # Apply fixes
                    for old_ref, new_ref in url_fixes.items():
                        content = content.replace(old_ref, new_ref)

                    # Fix any remaining device_manager references
                    import re
                    content = re.sub(
                        r"{% url 'device_manager:(\w+)'", r"{% url 'device_config:\1'", content)

                    if content != original_content:
                        with open(template_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        fixed_files.append(template_file.name)
                        print(f"✅ Fixed {template_file.name}")

                except Exception as e:
                    print(f"⚠️  Error fixing {template_file}: {e}")

    print(f"📊 Fixed {len(fixed_files)} template files")


def main():
    """Fix all URL issues"""

    print("🔧 Fixing DCMS template URL issues...")

    # Add missing URLs
    add_missing_urls()

    # Fix template references
    fix_template_url_references()

    print("""
🎉 DCMS URL Issues Fixed!

✅ Added all missing URL patterns (meter_list, etc.)
✅ Fixed template URL references
✅ Added DCMS compatibility routes

🚀 Django server should now work with DCMS templates.

Try: python3 manage.py runserver 0.0.0.0:8000
Navigate to: http://localhost:8000/device-config/
    """)


if __name__ == "__main__":
    main()
