#!/usr/bin/env python3
"""
Copy templates from existing DCMS system to new device_config app
"""
import shutil
from pathlib import Path


def copy_dcms_templates():
    """Copy templates from existing DCMS to device_config app"""

    # Source directory (existing DCMS templates)
    source_dir = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_configuration_management_system/device_manager/templates/device_manager')

    # Destination directory (new device_config app)
    dest_dir = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates/device_config')

    print("📋 Copying DCMS templates to device_config app...")

    if not source_dir.exists():
        print(f"❌ Source directory not found: {source_dir}")
        return False

    # Create destination directory
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Copy all template files
    copied_files = []

    try:
        for template_file in source_dir.glob('*.html'):
            dest_file = dest_dir / template_file.name
            shutil.copy2(template_file, dest_file)
            copied_files.append(template_file.name)
            print(f"✅ Copied {template_file.name}")

        print(f"\n📊 Successfully copied {len(copied_files)} template files:")
        for filename in copied_files:
            print(f"   - {filename}")

        return True

    except Exception as e:
        print(f"❌ Error copying templates: {e}")
        return False


def update_template_references():
    """Update template references to match new app structure"""

    dest_dir = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates/device_config')

    print("\n🔧 Updating template references...")

    # Update template references from device_manager to device_config
    for template_file in dest_dir.glob('*.html'):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Update template references
            updated_content = content

            # Update extends and include references
            updated_content = updated_content.replace(
                "{% extends 'device_manager/base.html' %}",
                "{% extends 'device_config/base.html' %}"
            )

            updated_content = updated_content.replace(
                "{% include 'device_manager/",
                "{% include 'device_config/"
            )

            # Update URL references from device_manager to device_config
            updated_content = updated_content.replace(
                "{% url 'device_manager:",
                "{% url 'device_config:"
            )

            # Update app name references
            updated_content = updated_content.replace(
                "'device_manager'",
                "'device_config'"
            )

            # Write back updated content
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            print(f"✅ Updated references in {template_file.name}")

        except Exception as e:
            print(f"⚠️  Error updating {template_file.name}: {e}")


def update_urls_to_match_templates():
    """Update URLs to match the template structure"""

    urls_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/urls.py')

    # Check what templates we have and ensure URLs match
    template_dir = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates/device_config')
    templates = [f.stem for f in template_dir.glob(
        '*.html') if f.stem != 'base']

    print(f"\n📋 Found templates: {templates}")

    # Generate URL patterns based on available templates
    url_patterns = []

    # Common URL patterns based on DCMS structure
    common_urls = {
        'device_list': "path('', views.DeviceListView.as_view(), name='device_list'),",
        'add_device': "path('add/', views.AddDeviceView.as_view(), name='add_device'),",
        'edit_device': "path('edit/<int:device_id>/', views.EditDeviceView.as_view(), name='edit_device'),",
        'delete_device': "path('delete/<int:device_id>/', views.DeleteDeviceView.as_view(), name='delete_device'),",
        'deploy_config': "path('deploy/<int:device_id>/', views.DeployConfigView.as_view(), name='deploy_config'),",
        'test_connection': "path('test/<int:device_id>/', views.TestConnectionView.as_view(), name='test_connection'),",
    }

    # Map template names to URL names
    template_to_url = {
        'device_config': 'device_list',
        'add_pi': 'add_device',
        'edit_pi': 'edit_device',
        'pi_list': 'device_list',
        'device_manager': 'device_list'
    }

    for template in templates:
        if template in template_to_url:
            url_name = template_to_url[template]
            if url_name in common_urls:
                url_patterns.append(common_urls[url_name])

    # If no specific templates found, use default structure
    if not url_patterns:
        url_patterns = list(common_urls.values())

    urls_content = f'''from django.urls import path
from . import views

app_name = 'device_config'

urlpatterns = [
    {chr(10).join("    " + url for url in url_patterns)}
]
'''

    try:
        with open(urls_file, 'w', encoding='utf-8') as f:
            f.write(urls_content)
        print(f"✅ Updated URLs to match template structure")
    except Exception as e:
        print(f"❌ Error updating URLs: {e}")


def main():
    """Main execution function"""

    print("🚀 Copying DCMS templates to device_config app...")

    if copy_dcms_templates():
        update_template_references()
        update_urls_to_match_templates()

        print("""
🎉 Successfully copied DCMS templates!

✅ Templates copied from device_configuration_management_system
✅ Template references updated to device_config
✅ URL patterns updated to match templates

📁 Templates available in:
   /home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates/device_config/

🚀 Next steps:
   1. cd /home/isha/deepak/MFM_offline_setup/meter_dashboard
   2. python3 manage.py runserver 0.0.0.0:8000
   3. Navigate to http://localhost:8000/device-config/
        """)
    else:
        print("💥 Failed to copy templates from DCMS system")


if __name__ == "__main__":
    main()
