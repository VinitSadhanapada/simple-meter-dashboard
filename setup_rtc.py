#!/usr/bin/env python3
"""
RTC Setup Script for Raspberry Pi

This script provides automated setup for Real-Time Clock (RTC) modules on Raspberry Pi.
It handles the initial configuration and system integration for offline time keeping.

Features:
- Interactive RTC module selection
- System configuration file updates
- Service integration setup
- Hardware validation and testing

Usage:
    python3 setup_rtc.py                    # Interactive setup
    python3 setup_rtc.py --auto             # Automatic setup
    python3 setup_rtc.py --test             # Test existing RTC
    python3 setup_rtc.py --remove           # Remove RTC configuration

Author: Dashboard System
Date: 27/07/25
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from rtc_manager import RTCManager

class RTCSetup:
    """Handles RTC setup and system integration."""
    
    def __init__(self):
        self.rtc_manager = RTCManager()
        
    def check_prerequisites(self):
        """Check system prerequisites for RTC setup.
        
        Returns:
            bool: True if all prerequisites met
        """
        print("🔍 Checking Prerequisites...")
        issues = []
        
        # Check if running as root or with sudo
        if os.geteuid() != 0:
            issues.append("❌ Root privileges required. Run with: sudo python3 setup_rtc.py")
        else:
            print("✅ Root privileges available")
        
        # Check if I2C is enabled
        i2c_enabled = Path("/dev/i2c-1").exists()
        if i2c_enabled:
            print("✅ I2C interface enabled")
        else:
            issues.append("❌ I2C interface not enabled. Enable with: sudo raspi-config")
        
        # Check for i2c-tools
        result = subprocess.run(["which", "i2cdetect"], capture_output=True)
        if result.returncode == 0:
            print("✅ i2c-tools installed")
        else:
            print("⚠️ i2c-tools not found. Installing...")
            if self._install_i2c_tools():
                print("✅ i2c-tools installed successfully")
            else:
                issues.append("❌ Failed to install i2c-tools")
        
        # Check boot config
        boot_config = Path("/boot/config.txt")
        if boot_config.exists():
            content = boot_config.read_text()
            if "dtparam=i2c_arm=on" in content:
                print("✅ I2C enabled in boot config")
            else:
                issues.append("⚠️ I2C may not be enabled in /boot/config.txt")
        
        if issues:
            print("\n❌ Prerequisites not met:")
            for issue in issues:
                print(f"  {issue}")
            return False
        
        print("✅ All prerequisites met")
        return True
    
    def _install_i2c_tools(self):
        """Install i2c-tools package.
        
        Returns:
            bool: True if successful
        """
        try:
            subprocess.run(["apt", "update"], check=True, capture_output=True)
            subprocess.run(["apt", "install", "-y", "i2c-tools"], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def interactive_setup(self):
        """Run interactive RTC setup."""
        print("=" * 50)
        print("🕐 Raspberry Pi RTC Setup")
        print("=" * 50)
        
        if not self.check_prerequisites():
            return False
        
        print("\n🔍 Scanning for RTC modules...")
        detected = self.rtc_manager.detect_rtc_modules()
        
        if not detected:
            print("\n❌ No RTC modules detected!")
            print("\n💡 Troubleshooting:")
            print("1. Check RTC module is properly connected")
            print("2. Verify I2C connections (SDA to GPIO2, SCL to GPIO3)")
            print("3. Ensure I2C is enabled: sudo raspi-config -> Interface Options -> I2C")
            print("4. Check power connections (VCC to 3.3V or 5V, GND to GND)")
            return False
        
        print(f"\n✅ Found {len(detected)} RTC module(s)")
        
        # Show detected modules
        for addr in detected:
            info = self.rtc_manager.RTC_MODULES[addr]
            print(f"\n📍 Address 0x{addr:02x}: {info['name']}")
            print("   Possible modules:")
            for module in info['possible_modules']:
                print(f"     - {module}")
        
        # Confirm setup
        print(f"\n🚀 Ready to setup RTC at address 0x{detected[0]:02x}")
        response = input("Continue with setup? (y/N): ").lower()
        
        if response != 'y':
            print("Setup cancelled.")
            return False
        
        # Perform setup
        return self._perform_setup()
    
    def automatic_setup(self):
        """Run automatic RTC setup."""
        print("🤖 Automatic RTC Setup")
        
        if not self.check_prerequisites():
            return False
        
        return self._perform_setup()
    
    def _perform_setup(self):
        """Perform the actual RTC setup.
        
        Returns:
            bool: True if successful
        """
        print("\n🔧 Setting up RTC...")
        
        # Initialize RTC
        if not self.rtc_manager.initialize_for_offline_operation():
            print("❌ RTC setup failed")
            return False
        
        # Update system configuration
        if not self._update_system_config():
            print("⚠️ System configuration update failed")
            return False
        
        # Test the setup
        if not self._test_rtc():
            print("⚠️ RTC test failed")
            return False
        
        print("\n✅ RTC setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. RTC will now maintain time when system is powered off")
        print("2. Time will be restored from RTC on boot")
        print("3. Dashboard will use RTC for offline time keeping")
        
        return True
    
    def _update_system_config(self):
        """Update system configuration files.
        
        Returns:
            bool: True if successful
        """
        print("📝 Updating system configuration...")
        
        try:
            # Add RTC module to /etc/modules
            modules_file = Path("/etc/modules")
            if modules_file.exists():
                content = modules_file.read_text()
                rtc_module = self.rtc_manager.rtc_info['kernel_module']
                
                if rtc_module not in content:
                    with modules_file.open("a") as f:
                        f.write(f"\n# RTC module for dashboard\n{rtc_module}\n")
                    print(f"✅ Added {rtc_module} to /etc/modules")
                else:
                    print(f"✅ {rtc_module} already in /etc/modules")
            
            # Create udev rule for RTC device
            udev_rule = Path("/etc/udev/rules.d/99-rtc.rules")
            rule_content = f'''# RTC device rule for dashboard
KERNEL=="rtc0", SUBSYSTEM=="rtc", OWNER="root", GROUP="dialout", MODE="0664"
'''
            udev_rule.write_text(rule_content)
            print("✅ Created udev rule for RTC device")
            
            # Reload udev rules
            subprocess.run(["udevadm", "control", "--reload-rules"], check=True, capture_output=True)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to update system config: {e}")
            return False
    
    def _test_rtc(self):
        """Test RTC functionality.
        
        Returns:
            bool: True if test successful
        """
        print("🧪 Testing RTC functionality...")
        
        # Get RTC status
        status = self.rtc_manager.get_rtc_status()
        
        if not status['initialized']:
            print("❌ RTC not initialized")
            return False
        
        print(f"✅ RTC device: {status['device_path']}")
        print(f"✅ RTC address: 0x{status['address']:02x}")
        print(f"✅ System time: {status['system_time']}")
        
        if status['rtc_time']:
            print(f"✅ RTC time: {status['rtc_time']}")
            if status['time_difference']:
                if status['time_difference'] < 2:
                    print(f"✅ Time sync good ({status['time_difference']:.1f}s difference)")
                else:
                    print(f"⚠️ Time difference: {status['time_difference']:.1f}s")
        else:
            print("❌ Could not read RTC time")
            return False
        
        return True
    
    def test_existing_rtc(self):
        """Test existing RTC setup."""
        print("🧪 Testing Existing RTC Setup")
        print("=" * 30)
        
        # Try to initialize RTC
        if self.rtc_manager.setup_rtc():
            return self._test_rtc()
        else:
            print("❌ No RTC found or setup failed")
            return False
    
    def remove_rtc_config(self):
        """Remove RTC configuration from system.
        
        Returns:
            bool: True if successful
        """
        print("🗑️ Removing RTC Configuration")
        
        if os.geteuid() != 0:
            print("❌ Root privileges required")
            return False
        
        try:
            # Remove from /etc/modules
            modules_file = Path("/etc/modules")
            if modules_file.exists():
                content = modules_file.read_text()
                lines = [line for line in content.split('\n') 
                        if not any(rtc in line for rtc in ['rtc-ds1307', 'rtc-pcf8563'])]
                modules_file.write_text('\n'.join(lines))
                print("✅ Removed RTC modules from /etc/modules")
            
            # Remove udev rule
            udev_rule = Path("/etc/udev/rules.d/99-rtc.rules")
            if udev_rule.exists():
                udev_rule.unlink()
                print("✅ Removed RTC udev rule")
            
            # Reload udev
            subprocess.run(["udevadm", "control", "--reload-rules"], check=True, capture_output=True)
            
            print("✅ RTC configuration removed")
            return True
            
        except Exception as e:
            print(f"❌ Failed to remove RTC config: {e}")
            return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="RTC Setup for Raspberry Pi Dashboard")
    parser.add_argument("--auto", action="store_true", help="Automatic setup")
    parser.add_argument("--test", action="store_true", help="Test existing RTC")
    parser.add_argument("--remove", action="store_true", help="Remove RTC configuration")
    
    args = parser.parse_args()
    
    setup = RTCSetup()
    
    if args.test:
        success = setup.test_existing_rtc()
    elif args.remove:
        success = setup.remove_rtc_config()
    elif args.auto:
        success = setup.automatic_setup()
    else:
        success = setup.interactive_setup()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
