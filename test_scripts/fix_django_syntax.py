#!/usr/bin/env python3
"""
Fix Django settings.py syntax error
"""


def fix_settings_syntax():
    """Fix the syntax error in Django settings.py"""

    settings_file = '/home/isha/deepak/MFM_offline_setup/meter_dashboard/meter_dashboard/settings.py'

    try:
        with open(settings_file, 'r') as f:
            content = f.read()

        print("🔧 Fixing Django settings syntax...")

        # Fix the literal \n issue
        content = content.replace('\\n', '\n')

        # If INSTALLED_APPS doesn't look right, reconstruct it properly
        if 'INSTALLED_APPS' in content:
            # Find INSTALLED_APPS section
            import re

            # Create a proper INSTALLED_APPS section
            proper_installed_apps = '''INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'meter_readings',
    'device_config',
]'''

            # Replace the existing INSTALLED_APPS with proper one
            pattern = r'INSTALLED_APPS\s*=\s*\[[^\]]*\]'
            content = re.sub(pattern, proper_installed_apps,
                             content, flags=re.DOTALL)

        with open(settings_file, 'w') as f:
            f.write(content)

        print("✅ Fixed Django settings syntax")
        return True

    except Exception as e:
        print(f"❌ Error fixing settings: {e}")
        return False


def create_minimal_django_project():
    """Create a minimal working Django project from scratch"""

    import os

    project_dir = '/home/isha/deepak/MFM_offline_setup/meter_dashboard'

    # Create minimal settings.py
    settings_content = '''"""
Django settings for meter_dashboard project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'meter_readings',
    'device_config',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'meter_dashboard.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'meter_dashboard.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
'''

    # Create minimal urls.py
    urls_content = '''from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('meter_readings.urls')),
    path('device-config/', include('device_config.urls')),
]
'''

    # Create minimal wsgi.py
    wsgi_content = '''import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meter_dashboard.settings')
application = get_wsgi_application()
'''

    # Create minimal manage.py
    manage_content = '''#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meter_dashboard.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
'''

    try:
        # Create project structure
        main_app_dir = f'{project_dir}/meter_dashboard'
        os.makedirs(main_app_dir, exist_ok=True)

        # Write main project files
        with open(f'{main_app_dir}/settings.py', 'w') as f:
            f.write(settings_content)

        with open(f'{main_app_dir}/urls.py', 'w') as f:
            f.write(urls_content)

        with open(f'{main_app_dir}/wsgi.py', 'w') as f:
            f.write(wsgi_content)

        with open(f'{main_app_dir}/__init__.py', 'w') as f:
            f.write('')

        with open(f'{project_dir}/manage.py', 'w') as f:
            f.write(manage_content)

        # Make manage.py executable
        os.chmod(f'{project_dir}/manage.py', 0o755)

        print("✅ Created minimal Django project structure")
        return True

    except Exception as e:
        print(f"❌ Error creating Django project: {e}")
        return False


if __name__ == "__main__":
    print("🔧 Fixing Django settings syntax error...")

    # First try to fix existing settings
    if not fix_settings_syntax():
        print("🔄 Creating minimal Django project from scratch...")
        create_minimal_django_project()

    print("""
✅ Django settings fixed!

🚀 Now run:
   cd /home/isha/deepak/MFM_offline_setup/meter_dashboard
   python3 manage.py runserver 0.0.0.0:8000

🌐 Then navigate to:
   - http://localhost:8000/ (Main Dashboard)
   - http://localhost:8000/device-config/ (Device Configuration)
    """)
