#!/usr/bin/env python3
"""
Download new packages for offline installation
Downloads Django, cryptography, and other new packages to packages_folder
"""
import subprocess
import sys
import os


def download_packages():
    """Download new packages to packages_folder for offline installation"""

    packages_dir = "/home/isha/deepak/MFM_offline_setup/packages_folder"

    # New packages we need to download
    new_packages = [
        "Django==5.2.4",
        "djangorestframework==3.16.0",
        "sqlparse==0.5.3",
        "asgiref==3.9.1",
        "cryptography",  # Latest compatible version
        "python-dotenv==1.1.1",
        "typing_extensions==4.14.1",
        "pymodbus==3.9.2",  # Updated version
        "cffi",  # Dependency for cryptography
        "pycparser"  # Dependency for cffi
    ]

    print("📦 Downloading new packages for offline installation...")
    print(f"📁 Target directory: {packages_dir}")

    for package in new_packages:
        print(f"\n🔽 Downloading {package}...")
        try:
            cmd = [
                sys.executable, "-m", "pip", "download",
                "--dest", packages_dir,
                "--platform", "linux_x86_64",
                "--platform", "linux_aarch64",
                "--platform", "any",
                "--python-version", "310",
                "--python-version", "311",
                "--abi", "cp310",
                "--abi", "cp311",
                "--abi", "none",
                package
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"   ✅ Successfully downloaded {package}")
            else:
                print(f"   ❌ Failed to download {package}: {result.stderr}")

        except Exception as e:
            print(f"   ❌ Error downloading {package}: {e}")

    print(f"\n📊 Package folder contents:")
    try:
        files = os.listdir(packages_dir)
        wheel_files = [f for f in files if f.endswith('.whl')]
        print(f"   📦 Total .whl files: {len(wheel_files)}")

        # Show new files
        django_files = [f for f in wheel_files if 'django' in f.lower()]
        crypto_files = [f for f in wheel_files if 'crypto' in f.lower()]

        if django_files:
            print(f"   🔸 Django files: {len(django_files)}")
            for f in django_files[:3]:  # Show first 3
                print(f"      - {f}")

        if crypto_files:
            print(f"   🔒 Cryptography files: {len(crypto_files)}")
            for f in crypto_files[:3]:  # Show first 3
                print(f"      - {f}")

    except Exception as e:
        print(f"   ❌ Error listing files: {e}")


def create_offline_install_script():
    """Create script for offline installation"""

    script_content = '''#!/bin/bash
# Offline Package Installation Script
# Installs all packages from the packages_folder for offline deployment

PACKAGES_DIR="/home/isha/deepak/MFM_offline_setup/packages_folder"

echo "🚀 Starting offline package installation..."
echo "📁 Installing from: $PACKAGES_DIR"

# Install all wheel files
pip install --no-index --find-links "$PACKAGES_DIR" \\
    Django==5.2.4 \\
    djangorestframework==3.16.0 \\
    sqlparse==0.5.3 \\
    asgiref==3.9.1 \\
    cryptography \\
    python-dotenv==1.1.1 \\
    typing_extensions==4.14.1 \\
    pymodbus==3.9.2 \\
    cffi \\
    pycparser \\
    --force-reinstall

if [ $? -eq 0 ]; then
    echo "✅ Offline installation completed successfully!"
else
    echo "❌ Offline installation failed!"
    exit 1
fi

echo "📋 Verifying installation..."
python3 -c "
import django
import rest_framework  
import cryptography
import dotenv
print('✅ All critical packages imported successfully!')
print(f'Django version: {django.get_version()}')
"
'''

    script_path = "/home/isha/deepak/MFM_offline_setup/install_offline_packages.sh"

    with open(script_path, 'w') as f:
        f.write(script_content)

    # Make executable
    os.chmod(script_path, 0o755)

    print(f"📜 Created offline installation script: {script_path}")


if __name__ == "__main__":
    print("🔽 Package Download for Offline Installation")
    print("=" * 50)

    try:
        download_packages()
        create_offline_install_script()

        print("\n✅ Package download process completed!")
        print("\n📋 Next steps:")
        print("1. Review downloaded packages in packages_folder")
        print("2. Use install_offline_packages.sh for offline installation")
        print("3. Test installation in clean environment")

    except Exception as e:
        print(f"\n❌ Error during package download: {e}")
        sys.exit(1)
