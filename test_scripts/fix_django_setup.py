#!/usr/bin/env python3
"""
Quick setup script to install required dependencies and fix Django issues
"""
import subprocess
import sys
from pathlib import Path


def install_required_packages():
    """Install all required packages"""

    packages = [
        'django',
        'djangorestframework',
        'psycopg2-binary',
        'paramiko',
        'requests'
    ]

    print("📦 Installing required packages...")

    for package in packages:
        try:
            print(f"   Installing {package}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', package],
                           check=True, capture_output=True)
            print(f"   ✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to install {package}: {e}")
            return False

    return True


def fix_django_settings():
    """Fix Django settings to remove REST framework dependency"""

    settings_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/meter_dashboard/settings.py')

    if not settings_file.exists():
        print("❌ Django settings file not found")
        return False

    try:
        with open(settings_file, 'r') as f:
            content = f.read()

        # Remove rest_framework from INSTALLED_APPS if present
        if "'rest_framework'," in content:
            content = content.replace("'rest_framework',", "")
            print("🔧 Removed rest_framework from INSTALLED_APPS")

        # Ensure device_config is in INSTALLED_APPS
        if "'device_config'," not in content and 'INSTALLED_APPS' in content:
            content = content.replace(
                "'django.contrib.staticfiles',",
                "'django.contrib.staticfiles',\\n    'device_config',"
            )
            print("✅ Added device_config to INSTALLED_APPS")

        with open(settings_file, 'w') as f:
            f.write(content)

        print("✅ Django settings updated")
        return True

    except Exception as e:
        print(f"❌ Error updating Django settings: {e}")
        return False


def create_simple_meter_readings_app():
    """Create a simple meter_readings app"""

    app_dir = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/meter_readings')
    app_dir.mkdir(exist_ok=True)

    # Create __init__.py
    (app_dir / '__init__.py').touch()

    # Create apps.py
    apps_content = '''from django.apps import AppConfig

class MeterReadingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'meter_readings'
    verbose_name = 'Meter Readings'
'''

    with open(app_dir / 'apps.py', 'w') as f:
        f.write(apps_content)

    # Create views.py
    views_content = '''from django.shortcuts import render
from django.http import JsonResponse

def dashboard(request):
    """Simple dashboard view"""
    return render(request, 'meter_readings/dashboard.html', {
        'page_title': 'Meter Readings Dashboard'
    })

def api_meter_readings(request):
    """Simple API endpoint for meter readings"""
    return JsonResponse({
        'status': 'success',
        'message': 'Meter readings API endpoint'
    })
'''

    with open(app_dir / 'views.py', 'w') as f:
        f.write(views_content)

    # Create urls.py
    urls_content = '''from django.urls import path
from . import views

app_name = 'meter_readings'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/meter/', views.api_meter_readings, name='api_meter_readings'),
]
'''

    with open(app_dir / 'urls.py', 'w') as f:
        f.write(urls_content)

    # Create templates directory and basic template
    template_dir = app_dir / 'templates' / 'meter_readings'
    template_dir.mkdir(parents=True, exist_ok=True)

    dashboard_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page_title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-chart-line"></i> Meter Dashboard
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Dashboard</a>
                <a class="nav-link" href="/device-config/">Device Config</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">Meter Readings Dashboard</h5>
                    </div>
                    <div class="card-body">
                        <div class="text-center py-5">
                            <h4>Welcome to Meter Dashboard</h4>
                            <p class="text-muted">Your offline RPi dashboard is running successfully!</p>
                            <a href="/device-config/" class="btn btn-primary">
                                Manage Device Configuration
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

    with open(template_dir / 'dashboard.html', 'w') as f:
        f.write(dashboard_template)

    print("✅ Created meter_readings app")


def fix_main_urls():
    """Fix main Django URLs"""

    urls_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/meter_dashboard/urls.py')

    urls_content = '''from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('meter_readings.urls')),
    path('device-config/', include('device_config.urls')),
]
'''

    try:
        with open(urls_file, 'w') as f:
            f.write(urls_content)
        print("✅ Updated main URLs")
        return True
    except Exception as e:
        print(f"❌ Error updating main URLs: {e}")
        return False


def update_settings_installed_apps():
    """Update settings.py to include both apps"""

    settings_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/meter_dashboard/settings.py')

    try:
        with open(settings_file, 'r') as f:
            content = f.read()

        # Add both apps to INSTALLED_APPS
        if 'INSTALLED_APPS' in content:
            if "'meter_readings'," not in content:
                content = content.replace(
                    "'django.contrib.staticfiles',",
                    "'django.contrib.staticfiles',\\n    'meter_readings',"
                )

            if "'device_config'," not in content:
                content = content.replace(
                    "'meter_readings',",
                    "'meter_readings',\\n    'device_config',"
                )

        with open(settings_file, 'w') as f:
            f.write(content)

        print("✅ Updated INSTALLED_APPS with both meter_readings and device_config")
        return True

    except Exception as e:
        print(f"❌ Error updating settings: {e}")
        return False


def main():
    """Main setup function"""

    print("🚀 Setting up Django environment for device configuration management...")

    # Step 1: Install required packages
    if not install_required_packages():
        print("💥 Failed to install required packages")
        return False

    # Step 2: Create meter_readings app
    create_simple_meter_readings_app()

    # Step 3: Fix Django settings
    if not fix_django_settings():
        print("💥 Failed to fix Django settings")
        return False

    # Step 4: Update INSTALLED_APPS
    if not update_settings_installed_apps():
        print("💥 Failed to update INSTALLED_APPS")
        return False

    # Step 5: Fix main URLs
    if not fix_main_urls():
        print("💥 Failed to fix main URLs")
        return False

    print("""
🎉 Django setup complete!

✅ All required packages installed
✅ meter_readings app created
✅ device_config app ready
✅ Django settings updated
✅ URL routing configured

🚀 Next steps:
   1. cd /home/isha/deepak/MFM_offline_setup/meter_dashboard
   2. python3 manage.py runserver 0.0.0.0:8000
   3. Navigate to http://localhost:8000/device-config/

📋 Available URLs:
   - http://localhost:8000/ (Main Dashboard)
   - http://localhost:8000/device-config/ (Device Configuration Management)
    """)

    return True


if __name__ == "__main__":
    main()
