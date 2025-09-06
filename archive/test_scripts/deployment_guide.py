#!/usr/bin/env python3
"""
Quick guide and verification for SSH deployment functionality
"""


def show_deployment_guide():
    """Show where to find SSH deployment in the interface"""

    print("""
🎯 SSH DEPLOYMENT GUIDE - Where to Find It:

📍 LOCATION: Main Dashboard
   URL: http://192.168.43.128:8000/device-config/

🔍 HOW TO FIND:
   1. Go to the main dashboard
   2. Look for your device cards (grid layout)
   3. In each device card, find the GREEN section labeled:
      "🚀 SSH Deployment"

⚡ DEPLOYMENT BUTTONS:
   ┌─────────────────────────────────────┐
   │  Device: Building-A-Pi              │
   │  Status: [●] Online                 │
   │  ───────────────────────────────────│
   │  📊 Meter Configuration             │
   │  • Main_Meter_1 (Address: 1)       │
   │  • Sub_Meter_2 (Address: 2)        │
   │  ───────────────────────────────────│
   │  🚀 SSH Deployment                  │
   │  Deploy meter configuration via SSH │
   │  ┌──────────┐ ┌─────────────┐      │
   │  │Test SSH  │ │Deploy Config│      │
   │  └──────────┘ └─────────────┘      │
   │  SSH: pi@192.168.1.100             │
   │  ───────────────────────────────────│
   │  [Edit] [Delete]                   │
   └─────────────────────────────────────┘

🔧 HOW TO USE:
   1. Test SSH: Click to verify connection works
   2. Deploy Config: Click to push meter config to Pi

💡 WHAT HAPPENS:
   - Creates device_config.jsonc on Pi
   - Uploads via SSH to /home/pi/MFM_offline_setup/
   - Shows success/error popup
    """)


def verify_deployment_functionality():
    """Verify that SSH deployment is properly set up"""

    from pathlib import Path

    # Check if views have the deployment functionality
    views_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/views.py')

    if views_file.exists():
        with open(views_file, 'r') as f:
            content = f.read()

        if 'DeployConfigView' in content and 'TestConnectionView' in content:
            print("✅ SSH deployment views are present")
        else:
            print("❌ SSH deployment views missing")
            return False
    else:
        print("❌ Views file not found")
        return False

    # Check if URLs are configured
    urls_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/urls.py')

    if urls_file.exists():
        with open(urls_file, 'r') as f:
            content = f.read()

        if 'deploy/' in content and 'test/' in content:
            print("✅ SSH deployment URLs are configured")
        else:
            print("❌ SSH deployment URLs missing")
            return False
    else:
        print("❌ URLs file not found")
        return False

    # Check if template has the deployment section
    template_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates/device_config/device_list.html')

    if template_file.exists():
        with open(template_file, 'r') as f:
            content = f.read()

        if 'deployment-section' in content and 'deployConfig' in content:
            print("✅ SSH deployment UI is present in template")
        else:
            print("❌ SSH deployment UI missing from template")
            return False
    else:
        print("❌ Template file not found")
        return False

    print("\n🎉 SSH deployment functionality is properly configured!")
    return True


def create_deployment_troubleshooting():
    """Create troubleshooting guide for deployment issues"""

    from pathlib import Path

    troubleshooting_content = '''# SSH Deployment Troubleshooting Guide

## If you don't see the deployment buttons:

### 1. Clear browser cache and refresh
```bash
Ctrl+F5 (or Cmd+Shift+R on Mac)
```

### 2. Check if template was updated
```bash
cd /home/isha/deepak/MFM_offline_setup/meter_dashboard
python3 manage.py collectstatic --noinput
```

### 3. Restart Django server
```bash
cd /home/isha/deepak/MFM_offline_setup/meter_dashboard
python3 manage.py runserver 0.0.0.0:8000
```

### 4. Check browser console for errors
- Press F12 -> Console tab
- Look for any JavaScript errors

## If deployment fails:

### 1. Install paramiko
```bash
pip install paramiko
```

### 2. Check SSH connectivity manually
```bash
ssh pi@192.168.1.100
```

### 3. Verify Pi credentials in device config

### 4. Check firewall settings on Pi

## Expected deployment process:
1. Click "Test SSH" -> Should show connection details
2. Click "Deploy Config" -> Should show success message
3. Check Pi: `/home/pi/MFM_offline_setup/device_config.jsonc` should exist
'''

    guide_file = Path(
        '/home/isha/deepak/MFM_offline_setup/SSH_DEPLOYMENT_GUIDE.md')

    with open(guide_file, 'w') as f:
        f.write(troubleshooting_content)

    print(f"✅ Created troubleshooting guide: {guide_file}")


def main():
    """Show deployment guide and verify setup"""

    print("🔍 SSH Deployment Location & Verification...")

    # Show where to find deployment
    show_deployment_guide()

    # Verify functionality is set up
    if verify_deployment_functionality():
        print("\n✅ Everything is configured correctly!")
        print("\n🚀 Go to: http://192.168.43.128:8000/device-config/")
        print("   Look for the GREEN 'SSH Deployment' section in each device card")
    else:
        print("\n❌ Some issues found. Run the setup scripts again:")
        print("   python3 create_old_style_dcms.py")

    # Create troubleshooting guide
    create_deployment_troubleshooting()


if __name__ == "__main__":
    main()
