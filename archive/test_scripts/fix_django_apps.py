#!/usr/bin/env python3
"""
Create the missing meter_readings Django app and fix the setup
"""
from pathlib import Path
import os


def create_meter_readings_app():
    """Create the basic meter_readings Django app"""

    base_dir = Path('/home/isha/deepak/MFM_offline_setup/meter_dashboard')
    app_dir = base_dir / 'meter_readings'

    print("📱 Creating meter_readings app...")

    # Create app directory
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

    with open(app_dir / 'apps.py', 'w', encoding='utf-8') as f:
        f.write(apps_content)

    # Create models.py
    models_content = '''from django.db import models

class MeterReading(models.Model):
    """Model for meter readings"""
    
    # Pi identification
    pi_setup_id = models.IntegerField(null=True, blank=True)
    pi_name = models.CharField(max_length=100, null=True, blank=True)
    pi_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Basic info
    location = models.CharField(max_length=100)
    device_id = models.CharField(max_length=50)
    meter_name = models.CharField(max_length=100)
    time = models.DateTimeField()
    model = models.CharField(max_length=50)
    
    # Power measurements
    watts_total = models.FloatField(null=True, blank=True)
    watts_r_ph = models.FloatField(null=True, blank=True)
    watts_y_ph = models.FloatField(null=True, blank=True)
    watts_b_ph = models.FloatField(null=True, blank=True)
    
    # Power factor
    pf_ave = models.FloatField(null=True, blank=True)
    pf_r_ph = models.FloatField(null=True, blank=True)
    pf_y_ph = models.FloatField(null=True, blank=True)
    pf_b_ph = models.FloatField(null=True, blank=True)
    
    # Voltage
    vln_average = models.FloatField(null=True, blank=True)
    v_r_ph = models.FloatField(null=True, blank=True)
    v_y_ph = models.FloatField(null=True, blank=True)
    v_b_ph = models.FloatField(null=True, blank=True)
    
    # Current
    a_average = models.FloatField(null=True, blank=True)
    a_r_ph = models.FloatField(null=True, blank=True)
    a_y_ph = models.FloatField(null=True, blank=True)
    a_b_ph = models.FloatField(null=True, blank=True)
    
    # Other measurements
    frequency = models.FloatField(null=True, blank=True)
    wh_received = models.FloatField(null=True, blank=True)
    load_hours_delivered = models.FloatField(null=True, blank=True)
    no_of_interruption = models.FloatField(null=True, blank=True)
    on_hours = models.CharField(max_length=20, null=True, blank=True)
    
    # Harmonics
    v_r_harmonics = models.FloatField(null=True, blank=True)
    v_y_harmonics = models.FloatField(null=True, blank=True)
    v_b_harmonics = models.FloatField(null=True, blank=True)
    a_r_harmonics = models.FloatField(null=True, blank=True)
    a_y_harmonics = models.FloatField(null=True, blank=True)
    a_b_harmonics = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['-time']
        indexes = [
            models.Index(fields=['time']),
            models.Index(fields=['location']),
            models.Index(fields=['pi_name']),
        ]
    
    def __str__(self):
        return f"{self.meter_name} at {self.time}"
'''

    with open(app_dir / 'models.py', 'w', encoding='utf-8') as f:
        f.write(models_content)

    # Create views.py
    views_content = '''from django.shortcuts import render
from django.http import JsonResponse
from .models import MeterReading
import json

def dashboard(request):
    """Main dashboard view"""
    
    # Get latest readings
    latest_readings = MeterReading.objects.all()[:50]
    
    context = {
        'latest_readings': latest_readings,
        'page_title': 'Meter Readings Dashboard',
    }
    
    return render(request, 'meter_readings/dashboard.html', context)

def api_meter_reading(request):
    """API endpoint for meter readings"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create meter reading from API data
            reading = MeterReading.objects.create(
                location=data.get('location'),
                device_id=data.get('device_id'),
                meter_name=data.get('meter_name'),
                time=data.get('time'),
                model=data.get('model'),
                watts_total=data.get('watts_total'),
                watts_r_ph=data.get('watts_r_ph'),
                watts_y_ph=data.get('watts_y_ph'),
                watts_b_ph=data.get('watts_b_ph'),
                pf_ave=data.get('pf_ave'),
                pf_r_ph=data.get('pf_r_ph'),
                pf_y_ph=data.get('pf_y_ph'),
                pf_b_ph=data.get('pf_b_ph'),
                vln_average=data.get('vln_average'),
                v_r_ph=data.get('v_r_ph'),
                v_y_ph=data.get('v_y_ph'),
                v_b_ph=data.get('v_b_ph'),
                a_average=data.get('a_average'),
                a_r_ph=data.get('a_r_ph'),
                a_y_ph=data.get('a_y_ph'),
                a_b_ph=data.get('a_b_ph'),
                frequency=data.get('frequency'),
                wh_received=data.get('wh_received'),
                load_hours_delivered=data.get('load_hours_delivered'),
                no_of_interruption=data.get('no_of_interruption'),
                on_hours=data.get('on_hours'),
                v_r_harmonics=data.get('v_r_harmonics'),
                v_y_harmonics=data.get('v_y_harmonics'),
                v_b_harmonics=data.get('v_b_harmonics'),
                a_r_harmonics=data.get('a_r_harmonics'),
                a_y_harmonics=data.get('a_y_harmonics'),
                a_b_harmonics=data.get('a_b_harmonics'),
            )
            
            return JsonResponse({'success': True, 'id': reading.id})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
'''

    with open(app_dir / 'views.py', 'w', encoding='utf-8') as f:
        f.write(views_content)

    # Create urls.py
    urls_content = '''from django.urls import path
from . import views

app_name = 'meter_readings'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/meter/', views.api_meter_reading, name='api_meter_reading'),
]
'''

    with open(app_dir / 'urls.py', 'w', encoding='utf-8') as f:
        f.write(urls_content)

    # Create templates directory
    template_dir = app_dir / 'templates' / 'meter_readings'
    template_dir.mkdir(parents=True, exist_ok=True)

    # Create basic dashboard template
    dashboard_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page_title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{% url 'meter_readings:dashboard' %}">
                <i class="fas fa-chart-line"></i> MFM Dashboard
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{% url 'meter_readings:dashboard' %}">
                    <i class="fas fa-chart-line"></i> Dashboard
                </a>
                <a class="nav-link" href="/device-config/">
                    <i class="fas fa-cogs"></i> Device Config
                </a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="fas fa-bolt"></i> Latest Meter Readings
                        </h5>
                    </div>
                    <div class="card-body">
                        {% if latest_readings %}
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Time</th>
                                            <th>Pi Name</th>
                                            <th>Location</th>
                                            <th>Meter</th>
                                            <th>Model</th>
                                            <th>Total Watts</th>
                                            <th>Voltage (Avg)</th>
                                            <th>Current (Avg)</th>
                                            <th>Frequency</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for reading in latest_readings %}
                                        <tr>
                                            <td>{{ reading.time|date:"Y-m-d H:i:s" }}</td>
                                            <td>{{ reading.pi_name|default:"N/A" }}</td>
                                            <td>{{ reading.location }}</td>
                                            <td>{{ reading.meter_name }}</td>
                                            <td>{{ reading.model }}</td>
                                            <td>{{ reading.watts_total|floatformat:2 }} W</td>
                                            <td>{{ reading.vln_average|floatformat:2 }} V</td>
                                            <td>{{ reading.a_average|floatformat:2 }} A</td>
                                            <td>{{ reading.frequency|floatformat:2 }} Hz</td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        {% else %}
                            <div class="text-center py-5">
                                <i class="fas fa-chart-line fa-3x text-muted mb-3"></i>
                                <h5 class="text-muted">No meter readings found</h5>
                                <p class="text-muted">Start your Pi data collection to see readings here</p>
                            </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

    with open(template_dir / 'dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_template)

    print("✅ meter_readings app created!")


def fix_main_urls():
    """Create correct main URLs file"""

    urls_content = '''from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('meter_readings.urls')),
    path('device-config/', include('device_config.urls')),
]
'''

    main_urls_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/meter_dashboard/urls.py')

    with open(main_urls_file, 'w', encoding='utf-8') as f:
        f.write(urls_content)

    print("✅ Main URLs fixed!")


def fix_settings():
    """Update settings.py to include both apps"""

    settings_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/meter_dashboard/settings.py')

    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find INSTALLED_APPS and update it
        if 'INSTALLED_APPS' in content:
            # Replace the INSTALLED_APPS section
            new_installed_apps = '''INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'meter_readings',
    'device_config',
]'''

            # Find and replace INSTALLED_APPS
            import re
            pattern = r'INSTALLED_APPS\s*=\s*\[(.*?)\]'
            content = re.sub(pattern, new_installed_apps,
                             content, flags=re.DOTALL)

            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(content)

            print("✅ Settings.py updated!")
        else:
            print("⚠️  Could not find INSTALLED_APPS in settings.py")

    except Exception as e:
        print(f"⚠️  Error updating settings: {e}")


if __name__ == "__main__":
    print("🔧 Fixing Django app structure...")

    # Create meter_readings app
    create_meter_readings_app()

    # Fix main URLs
    fix_main_urls()

    # Fix settings
    fix_settings()

    print("""
✅ Django apps structure fixed!

🚀 Next steps:
   1. Run migrations:
      cd /home/isha/deepak/MFM_offline_setup/meter_dashboard
      python3 manage.py makemigrations
      python3 manage.py migrate
   
   2. Restart Django server:
      python3 manage.py runserver 0.0.0.0:8000
   
   3. Access your apps:
      - Main dashboard: http://localhost:8000/
      - Device config: http://localhost:8000/device-config/
    """)
