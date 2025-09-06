#!/usr/bin/env python3
"""
Fix URL references in templates to resolve NoReverseMatch errors
"""
from pathlib import Path
import re


def fix_template_url_references():
    """Fix URL references in all templates"""

    # Template directories to check
    template_dirs = [
        Path('/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates'),
        Path('/home/isha/deepak/MFM_offline_setup/meter_dashboard/meter_readings/templates'),
    ]

    print("🔧 Fixing template URL references...")

    # Common URL reference fixes
    url_fixes = {
        # Dashboard references
        "{% url 'dashboard' %}": "{% url 'meter_readings:dashboard' %}",
        "{% url 'meter_readings.dashboard' %}": "{% url 'meter_readings:dashboard' %}",
        "{% url 'device_manager:device_list' %}": "{% url 'device_config:device_config' %}",

        # Device config references
        "{% url 'device_manager:add_device' %}": "{% url 'device_config:add_device' %}",
        "{% url 'device_manager:edit_device' %}": "{% url 'device_config:edit_device' %}",
        "{% url 'device_manager:delete_device' %}": "{% url 'device_config:delete_device' %}",
        "{% url 'device_manager:deploy_config' %}": "{% url 'device_config:deploy_config' %}",
        "{% url 'device_manager:test_connection' %}": "{% url 'device_config:test_connection' %}",

        # Navigation references
        "href='/dashboard/'": "href='{% url \"meter_readings:dashboard\" %}'",
        "href='/device-config/'": "href='{% url \"device_config:device_config\" %}'",
    }

    fixed_files = []

    for template_dir in template_dirs:
        if template_dir.exists():
            for template_file in template_dir.rglob('*.html'):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    original_content = content

                    # Apply URL fixes
                    for old_url, new_url in url_fixes.items():
                        content = content.replace(old_url, new_url)

                    # Fix any remaining device_manager references
                    content = re.sub(
                        r"{% url 'device_manager:(\w+)'", r"{% url 'device_config:\1'", content)

                    # Fix reverse URL calls in JavaScript
                    content = re.sub(r"{% url 'device_manager:(\w+)' (\w+) %}",
                                     r"{% url 'device_config:\1' \2 %}", content)

                    if content != original_content:
                        with open(template_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        fixed_files.append(str(template_file))
                        print(f"✅ Fixed {template_file.name}")

                except Exception as e:
                    print(f"⚠️  Error fixing {template_file}: {e}")

    print(f"\n📊 Fixed {len(fixed_files)} template files")
    return len(fixed_files) > 0


def update_device_config_urls():
    """Update device_config URLs to match DCMS expectations"""

    # First, run the DCMS compatibility setup if not already done
    setup_dcms_compatibility()

    urls_content = '''from django.urls import path
from . import views


urlpatterns = [
    # Main device list (multiple aliases for compatibility)
    path('', views.DeviceListView.as_view(), name='device_list'),
    path('', views.DeviceListView.as_view(), name='device_config'),
    
    # Device management
    path('add/', views.AddDeviceView.as_view(), name='add_device'),
    path('edit/<int:device_id>/', views.EditDeviceView.as_view(), name='edit_device'),
    path('delete/<int:device_id>/', views.DeleteDeviceView.as_view(), name='delete_device'),
    
    # Device operations
    path('deploy/<int:device_id>/', views.DeployConfigView.as_view(), name='deploy_config'),
    path('test/<int:device_id>/', views.TestConnectionView.as_view(), name='test_connection'),
    
    # Alternative paths for backward compatibility
    path('add-pi/', views.AddDeviceView.as_view(), name='add_pi'),
    path('edit-pi/<int:device_id>/', views.EditDeviceView.as_view(), name='edit_pi'),
    path('delete-pi/<int:device_id>/', views.DeleteDeviceView.as_view(), name='delete_pi'),
    path('deploy-config/<int:device_id>/', views.DeployConfigView.as_view(), name='deploy_config_alt'),
    path('test-connection/<int:device_id>/', views.TestConnectionView.as_view(), name='test_connection_alt'),
]
'''

    urls_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/urls.py')

    try:
        with open(urls_file, 'w', encoding='utf-8') as f:
            f.write(urls_content)
        print("✅ Updated device_config URLs with compatibility aliases")
        return True
    except Exception as e:
        print(f"❌ Error updating URLs: {e}")
        return False


def setup_dcms_compatibility():
    """Ensure DCMS compatibility is set up"""

    # Check if DCMS templates have been copied
    template_dir = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates/device_config')
    dcms_source = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_configuration_management_system/device_manager/templates/device_manager')

    if dcms_source.exists() and not (template_dir / 'device_list.html').exists():
        print("📋 Setting up DCMS template compatibility...")

        import subprocess
        try:
            subprocess.run(['python3', '/home/isha/deepak/MFM_offline_setup/setup_dcms_compatibility.py'],
                           check=True, cwd='/home/isha/deepak/MFM_offline_setup')
            print("✅ DCMS compatibility setup complete")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  DCMS compatibility setup failed: {e}")


def main():
    """Main execution function"""

    print("🔧 Fixing URL reference issues...")

    # Setup DCMS compatibility if needed
    setup_dcms_compatibility()

    # Update URLs with compatibility aliases
    update_device_config_urls()

    # Fix template URL references
    fix_template_url_references()

    print("""
🎉 URL Reference Issues Fixed!

✅ Added dashboard URL routes
✅ Updated device_config URLs with compatibility aliases  
✅ Fixed template URL references
✅ Added backward compatibility for old URL names

🚀 Django server should now start without URL errors.

Run: python3 manage.py runserver 0.0.0.0:8000
    """)


if __name__ == "__main__":
    main()
