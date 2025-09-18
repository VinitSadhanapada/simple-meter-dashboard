#!/usr/bin/env python3
"""
URL Testing Script for Meter Dashboard

This script helps test all your Django URLs and API endpoints.
Run this from your Django project root directory.
"""

import os
import sys
import django
from django.test import Client
from django.urls import reverse, NoReverseMatch
from django.apps import apps
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meter_dashboard.settings')
django.setup()


class URLTester:
    def __init__(self):
        self.client = Client()
        self.results = []

    def test_all_urls(self):
        """Test all URLs in the project"""
        print("🔍 Testing Django URLs...")
        print("=" * 50)

        # Test specific meter app URLs
        test_urls = [
            # API endpoints
            ('meters:meter_data', 'GET', {}),
            ('meters:live_dashboard', 'GET', {}),
            ('meters:get_device_config', 'GET', {'pi_device_id': 'pi001'}),

            # Web interface
            ('meters:dashboard_charts', 'GET', {}),
            ('meters:device_management', 'GET', {}),
        ]

        for url_name, method, kwargs in test_urls:
            self.test_url(url_name, method, kwargs)

        self.print_summary()

    def test_url(self, url_name, method='GET', kwargs=None):
        """Test a specific URL"""
        kwargs = kwargs or {}

        try:
            url = reverse(url_name, kwargs=kwargs)
            print(f"\n📍 Testing: {url_name}")
            print(f"   URL: {url}")
            print(f"   Method: {method}")

            if method == 'GET':
                response = self.client.get(url)
            elif method == 'POST':
                response = self.client.post(url, data={})
            else:
                print(f"   ❌ Method {method} not supported in this tester")
                return

            status_code = response.status_code
            if status_code == 200:
                print(f"   ✅ Success: {status_code}")
            elif status_code in [301, 302]:
                print(f"   🔄 Redirect: {status_code}")
            elif status_code == 404:
                print(f"   ❌ Not Found: {status_code}")
            elif status_code == 500:
                print(f"   💥 Server Error: {status_code}")
            else:
                print(f"   ⚠️  Status: {status_code}")

            self.results.append({
                'url_name': url_name,
                'url': url,
                'method': method,
                'status_code': status_code,
                'success': status_code in [200, 301, 302]
            })

        except NoReverseMatch as e:
            print(f"   ❌ URL Reverse Error: {e}")
            self.results.append({
                'url_name': url_name,
                'url': 'ERROR',
                'method': method,
                'status_code': 'REVERSE_ERROR',
                'success': False
            })
        except Exception as e:
            print(f"   💥 Test Error: {e}")
            self.results.append({
                'url_name': url_name,
                'url': 'ERROR',
                'method': method,
                'status_code': 'TEST_ERROR',
                'success': False
            })

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)

        total = len(self.results)
        passed = len([r for r in self.results if r['success']])
        failed = total - passed

        print(f"Total URLs tested: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")

        if failed > 0:
            print(f"\n🔴 Failed URLs:")
            for result in self.results:
                if not result['success']:
                    print(
                        f"   - {result['url_name']}: {result['status_code']}")


def test_api_endpoints():
    """Test API endpoints with sample data"""
    print("\n🌐 Testing API Endpoints with curl examples:")
    print("=" * 50)

    base_url = "http://localhost:8000"

    endpoints = [
        ("GET", "/api/meter/", "Get meter data"),
        ("GET", "/api/dashboard/", "Get dashboard data"),
        ("GET", "/api/config/pi001/", "Get device config"),
        ("POST", "/api/status/pi001/", "Update device status"),
    ]

    for method, endpoint, description in endpoints:
        print(f"\n📡 {description}")
        print(f"   curl -X {method} {base_url}{endpoint}")
        if method == "POST":
            print(f"        -H 'Content-Type: application/json'")
            print(f"        -d '{{'status': 'active'}}'")


if __name__ == "__main__":
    print("🚀 Django URL Tester")
    print("=" * 50)

    try:
        tester = URLTester()
        tester.test_all_urls()
        test_api_endpoints()

        print(f"\n💡 Tip: Run 'python manage.py list_urls' to see all URLs")
        print(f"💡 Tip: Check URL_DOCUMENTATION.md for detailed API docs")

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        print("Make sure you're in the Django project directory and Django is properly configured.")
