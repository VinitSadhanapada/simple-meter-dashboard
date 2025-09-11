#!/usr/bin/env python3
"""
Debug script to check server connectivity for offline_rpi_dashboard_db.py
"""
import json
import requests
import time
from pathlib import Path


def strip_jsonc_comments(text):
    import re
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def load_jsonc_config(path):
    with open(path, 'r') as f:
        content = f.read()
        return json.loads(strip_jsonc_comments(content))


def test_server_connectivity():
    """Test if the Django server is reachable"""

    script_dir = Path(__file__).parent.absolute()
    config_path = script_dir / "config.jsonc"

    try:
        config = load_jsonc_config(config_path)
        server_ip = config.get('SERVER_API_IP', 'localhost')
        server_url = f"http://{server_ip}:8000/api/meter/"

        print(f"🔍 Testing server connectivity...")
        print(f"📡 Server URL: {server_url}")
        print(f"⚙️  Server IP from config: {server_ip}")
        print("-" * 50)

        # Test 1: Basic connectivity
        print("1️⃣  Testing basic connectivity...")
        try:
            response = requests.get(server_url, timeout=5)
            print(f"✅ Server is reachable!")
            print(f"📊 Status Code: {response.status_code}")
            print(f"📝 Response: {response.text[:200]}...")
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection Error: Cannot connect to {server_url}")
            print("💡 Possible issues:")
            print("   - Django server is not running")
            print("   - Wrong IP address in config.jsonc")
            print("   - Firewall blocking the connection")
            return False
        except requests.exceptions.Timeout:
            print(f"⏱️  Timeout: Server took too long to respond")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

        # Test 2: Test POST request (like your Pi script does)
        print("\n2️⃣  Testing POST request...")
        test_data = {
            'device_id': 'TEST_DEVICE',
            'location': 'TEST_LOCATION',
            'meter_name': 'TEST_METER',
            'time': '2024-01-01T12:00:00',
            'model': 'TEST_MODEL',
            'watts_total': 1000.0,
            'vln_average': 230.0,
            'frequency': 50.0
        }

        try:
            response = requests.post(server_url, json=test_data, timeout=10)
            print(f"✅ POST request successful!")
            print(f"📊 Status Code: {response.status_code}")
            if response.status_code in [200, 201]:
                print("🎉 Data posting should work!")
            else:
                print(f"⚠️  Unexpected status code: {response.status_code}")
                print(f"📝 Response: {response.text}")
        except Exception as e:
            print(f"❌ POST request failed: {e}")
            return False

        return True

    except FileNotFoundError:
        print(f"❌ Config file not found: {config_path}")
        print("💡 Make sure config.jsonc exists in the same directory")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        return False


def check_django_server():
    """Check if Django server is running"""
    print("\n3️⃣  Checking Django server status...")

    common_urls = [
        "http://localhost:8000/",
        "http://127.0.0.1:8000/",
        "http://localhost:8000/api/meter/",
        "http://127.0.0.1:8000/api/meter/"
    ]

    for url in common_urls:
        try:
            response = requests.get(url, timeout=3)
            print(f"✅ {url} is responding (Status: {response.status_code})")
        except:
            print(f"❌ {url} is not responding")


def show_config_details():
    """Show current configuration"""
    script_dir = Path(__file__).parent.absolute()
    config_path = script_dir / "config.jsonc"

    print("\n4️⃣  Configuration Details:")
    print("-" * 30)

    try:
        config = load_jsonc_config(config_path)
        print(f"📄 Config file: {config_path}")
        print(f"🌐 SERVER_API_IP: {config.get('SERVER_API_IP', 'NOT SET')}")
        print(f"🔌 PORT: {config.get('PORT', 'NOT SET')}")
        print(
            f"🔄 READING_INTERVAL: {config.get('READING_INTERVAL', 'NOT SET')}")
        print(f"🧪 SIMULATION_MODE: {config.get('SIMULATION_MODE', 'NOT SET')}")
    except Exception as e:
        print(f"❌ Error reading config: {e}")


def suggest_fixes():
    """Suggest possible fixes"""
    print("\n🔧 Suggested Fixes:")
    print("=" * 40)
    print("1. Start Django server:")
    print("   cd /home/isha/deepak/MFM_offline_setup/meter_dashboard")
    print("   python3 manage.py runserver 0.0.0.0:8000")
    print()
    print("2. Check config.jsonc SERVER_API_IP:")
    print("   - Use 'localhost' if running on same machine")
    print("   - Use actual IP address if running on different machine")
    print()
    print("3. Test API endpoint manually:")
    print("   curl -X GET http://localhost:8000/api/meter/")
    print()
    print("4. Check firewall settings:")
    print("   sudo ufw status")
    print("   sudo ufw allow 8000")
    print()
    print("5. Disable server posting temporarily:")
    print("   Edit offline_rpi_dashboard_db.py")
    print("   Set SERVER_CONFIG['enabled'] = False")


if __name__ == "__main__":
    print("🔍 MFM Dashboard Server Connectivity Test")
    print("=" * 50)

    show_config_details()
    check_django_server()

    if test_server_connectivity():
        print("\n🎉 All tests passed! Server connectivity is working.")
    else:
        print("\n❌ Server connectivity test failed!")
        suggest_fixes()
