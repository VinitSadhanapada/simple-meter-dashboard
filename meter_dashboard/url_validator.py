#!/usr/bin/env python3
"""
URL Configuration Validator for Django Projects

This script validates your URL configuration and suggests improvements.
"""

import re
import os
import sys


def analyze_urls_file(file_path):
    """Analyze a urls.py file for best practices"""
    with open(file_path, 'r') as f:
        content = f.read()

    suggestions = []

    # Check for app_name
    if 'app_name =' not in content and 'urls.py' in file_path and 'management' not in file_path:
        # Skip main project urls
        if not file_path.endswith('meter_dashboard/urls.py'):
            suggestions.append("❌ Missing app_name for URL namespacing")

    # Check for unnamed URLs
    unnamed_count = content.count('name=')
    total_paths = content.count('path(')
    if unnamed_count < total_paths:
        suggestions.append(
            f"⚠️  Found {total_paths - unnamed_count} URLs without names")

    # Check for commented documentation
    if '# ' not in content:
        suggestions.append("💡 Consider adding comments to document URL groups")

    # Check for consistent naming
    url_names = re.findall(r"name='([^']*)'", content)
    url_names.extend(re.findall(r'name="([^"]*)"', content))

    inconsistent_naming = []
    for name in url_names:
        if '-' in name and '_' in name:
            inconsistent_naming.append(name)

    if inconsistent_naming:
        suggestions.append(
            f"⚠️  Inconsistent naming (mix of - and _): {inconsistent_naming}")

    return suggestions


def check_url_organization():
    """Check overall URL organization"""
    print("🔍 Django URL Organization Analysis")
    print("=" * 50)

    # Find all urls.py files
    urls_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file == 'urls.py':
                urls_files.append(os.path.join(root, file))

    print(f"Found {len(urls_files)} URL configuration files:")

    all_suggestions = []
    for file_path in urls_files:
        print(f"\n📄 {file_path}")
        suggestions = analyze_urls_file(file_path)

        if suggestions:
            for suggestion in suggestions:
                print(f"   {suggestion}")
            all_suggestions.extend(suggestions)
        else:
            print("   ✅ Looks good!")

    # Overall recommendations
    print(f"\n📊 Summary:")
    print(f"   Files analyzed: {len(urls_files)}")
    print(f"   Issues found: {len(all_suggestions)}")

    if len(all_suggestions) == 0:
        print("   🎉 All URL files follow best practices!")
    else:
        print("\n💡 General Recommendations:")
        print("   1. Use consistent naming conventions (prefer underscores)")
        print("   2. Add app_name to all app-level urls.py files")
        print("   3. Name all your URLs for reverse lookups")
        print("   4. Group related URLs with comments")
        print("   5. Consider API versioning for future compatibility")


def suggest_url_structure():
    """Suggest improved URL structure based on current project"""
    print(f"\n🏗️  Suggested URL Structure for Your Project:")
    print("=" * 50)

    print("""
    # Main project urls.py
    urlpatterns = [
        path('admin/', admin.site.urls),
        path('api/v1/', include('meters.api_urls')),  # API endpoints
        path('', include('meters.web_urls')),         # Web interface
    ]
    
    # meters/api_urls.py (separate API URLs)
    app_name = 'api'
    urlpatterns = [
        path('meter/', meter_data, name='meter_data'),
        path('dashboard/', live_dashboard, name='live_dashboard'),
        path('devices/', device_list, name='device_list'),
        path('devices/<str:pi_device_id>/', device_detail, name='device_detail'),
        path('devices/<str:pi_device_id>/config/', device_config, name='device_config'),
        path('devices/<str:pi_device_id>/status/', device_status, name='device_status'),
    ]
    
    # meters/web_urls.py (separate web interface URLs)
    app_name = 'web'
    urlpatterns = [
        path('', dashboard_home, name='home'),
        path('charts/', dashboard_charts, name='charts'),
        path('devices/', device_management, name='devices'),
        path('devices/<int:device_id>/', device_detail_page, name='device_detail'),
    ]
    """)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--suggest':
        suggest_url_structure()
    else:
        check_url_organization()

    print(f"\n🚀 Quick Commands:")
    print(f"   python3 manage.py list_urls                    # List all URLs")
    print(f"   python3 manage.py list_urls --app meters       # Filter by app")
    print(f"   python3 test_urls.py                           # Test all URLs")
    print(f"   python3 url_validator.py --suggest             # Get structure suggestions")
