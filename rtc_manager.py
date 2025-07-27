#!/usr/bin/env python3
"""
RTC Manager for Raspberry Pi Dashboard

Handles Real-Time Clock (RTC) module setup and time synchronization for offline operation.
Supports common RTC modules: DS3231, DS1307, PCF8523

This module provides:
- Automatic RTC module detection
- Kernel module loading
- Device node creation
- Time synchronization between system and RTC
- Offline time keeping capabilities

Author: Dashboard System
Date: 27/07/25
"""

import os
import subprocess
import time
import logging
from datetime import datetime
from pathlib import Path

class RTCManager:
    """Manages Real-Time Clock (RTC) operations for Raspberry Pi."""
    
    # Common RTC modules and their I2C addresses
    RTC_MODULES = {
        0x68: {
            'name': 'DS3231/DS1307/PCF8523',
            'possible_modules': [
                'DS3231 High Precision RTC',
                'DS1307 Basic RTC', 
                'PCF8523 Low Power RTC'
            ],
            'kernel_module': 'rtc-ds1307',
            'device_name': 'ds1307'
        },
        0x51: {
            'name': 'PCF8563',
            'possible_modules': ['PCF8563 Low Power RTC'],
            'kernel_module': 'rtc-pcf8563',
            'device_name': 'pcf8563'
        }
    }
    
    def __init__(self, logger=None):
        """Initialize RTC Manager.
        
        Args:
            logger: Optional logger instance. If None, creates default logger.
        """
        self.logger = logger or self._setup_default_logger()
        self.rtc_device_path = None
        self.rtc_address = None
        self.rtc_info = None
        
    def _setup_default_logger(self):
        """Setup default logger for RTC operations."""
        logger = logging.getLogger('RTCManager')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def run_command(self, cmd, check=True, capture_output=True):
        """Run system command with error handling.
        
        Args:
            cmd: Command to run (string or list)
            check: Whether to raise exception on failure
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            tuple: (success, stdout, stderr)
        """
        try:
            if isinstance(cmd, str):
                cmd = cmd.split()
            
            result = subprocess.run(
                cmd, 
                capture_output=capture_output, 
                text=True, 
                check=check
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout if e.stdout else "", e.stderr if e.stderr else str(e)
        except Exception as e:
            return False, "", str(e)
    
    def detect_rtc_modules(self):
        """Detect RTC modules on I2C bus.
        
        Returns:
            list: List of detected RTC addresses
        """
        self.logger.info("🔍 Scanning I2C bus for RTC modules...")
        
        # Check if I2C tools are available
        success, _, _ = self.run_command("which i2cdetect", check=False)
        if not success:
            self.logger.warning("⚠️ i2c-tools not installed. Install with: sudo apt install i2c-tools")
            return []
        
        # Scan I2C bus 1 (default for Raspberry Pi)
        success, stdout, stderr = self.run_command("i2cdetect -y 1", check=False)
        if not success:
            self.logger.error(f"❌ Failed to scan I2C bus: {stderr}")
            return []
        
        detected_addresses = []
        lines = stdout.strip().split('\n')[1:]  # Skip header
        
        for line in lines:
            parts = line.split()
            if len(parts) > 1:
                for i, part in enumerate(parts[1:], start=0):
                    if part != '--' and part != 'UU':
                        try:
                            addr = int(part, 16)
                            if addr in self.RTC_MODULES:
                                detected_addresses.append(addr)
                                self.logger.info(f"✅ RTC module detected at I2C address 0x{addr:02x}")
                                for module in self.RTC_MODULES[addr]['possible_modules']:
                                    self.logger.info(f"   Possible module: {module}")
                        except ValueError:
                            continue
        
        if not detected_addresses:
            self.logger.warning("⚠️ No RTC modules detected on I2C bus")
        
        return detected_addresses
    
    def load_kernel_module(self, module_name):
        """Load kernel module for RTC.
        
        Args:
            module_name: Name of kernel module to load
            
        Returns:
            bool: True if successful
        """
        self.logger.info(f"Loading kernel module: {module_name}")
        
        # Check if module is already loaded
        success, stdout, _ = self.run_command(f"lsmod | grep {module_name}", check=False)
        if success and module_name in stdout:
            self.logger.info(f"✅ Module {module_name} already loaded")
            return True
        
        # Load the module
        success, _, stderr = self.run_command(f"sudo modprobe {module_name}", check=False)
        if success:
            self.logger.info(f"✅ Module {module_name} loaded successfully")
            return True
        else:
            self.logger.error(f"❌ Failed to load module {module_name}: {stderr}")
            return False
    
    def create_rtc_device(self, address, device_name):
        """Create RTC device node.
        
        Args:
            address: I2C address of RTC module
            device_name: Device name for kernel
            
        Returns:
            bool: True if successful
        """
        device_path = f"/sys/class/i2c-adapter/i2c-1/new_device"
        device_string = f"{device_name} 0x{address:02x}"
        
        self.logger.info(f"Creating RTC device: {device_string}")
        
        # Check if device already exists
        rtc_devices = list(Path("/dev").glob("rtc*"))
        if rtc_devices:
            self.logger.info("✅ RTC device already exists")
            self.rtc_device_path = str(rtc_devices[0])
            return True
        
        # Create the device
        success, _, stderr = self.run_command(
            f"echo '{device_string}' | sudo tee {device_path}", 
            check=False
        )
        
        if success:
            # Wait for device to be created
            time.sleep(1)
            
            # Find the created RTC device
            rtc_devices = list(Path("/dev").glob("rtc*"))
            if rtc_devices:
                self.rtc_device_path = str(rtc_devices[0])
                self.logger.info(f"✅ RTC device created: {self.rtc_device_path}")
                return True
            else:
                self.logger.error("❌ RTC device not found after creation")
                return False
        else:
            self.logger.error(f"❌ Failed to create RTC device: {stderr}")
            return False
    
    def setup_rtc(self):
        """Setup RTC module automatically.
        
        Returns:
            bool: True if RTC setup successful
        """
        self.logger.info("🕐 Initializing RTC system...")
        
        # Detect RTC modules
        detected_addresses = self.detect_rtc_modules()
        if not detected_addresses:
            self.logger.warning("⚠️ No RTC modules detected")
            return False
        
        # Use the first detected module
        self.rtc_address = detected_addresses[0]
        self.rtc_info = self.RTC_MODULES[self.rtc_address]
        
        # Load kernel module
        if not self.load_kernel_module(self.rtc_info['kernel_module']):
            return False
        
        # Create device node
        if not self.create_rtc_device(self.rtc_address, self.rtc_info['device_name']):
            return False
        
        self.logger.info("✅ RTC system initialized successfully")
        return True
    
    def read_rtc_time(self):
        """Read time from RTC module.
        
        Returns:
            datetime or None: RTC time if successful
        """
        if not self.rtc_device_path:
            self.logger.error("❌ RTC device not initialized")
            return None
        
        success, stdout, stderr = self.run_command(f"sudo hwclock -r -f {self.rtc_device_path}", check=False)
        if success:
            try:
                # Parse hwclock output
                time_str = stdout.strip()
                # hwclock output format varies, try to parse it
                rtc_time = datetime.strptime(time_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
                self.logger.debug(f"RTC time: {rtc_time}")
                return rtc_time
            except Exception as e:
                self.logger.error(f"❌ Failed to parse RTC time: {e}")
                return None
        else:
            self.logger.error(f"❌ Failed to read RTC time: {stderr}")
            return None
    
    def write_system_time_to_rtc(self):
        """Write current system time to RTC.
        
        Returns:
            bool: True if successful
        """
        if not self.rtc_device_path:
            self.logger.error("❌ RTC device not initialized")
            return False
        
        self.logger.info("📝 Writing system time to RTC...")
        success, _, stderr = self.run_command(f"sudo hwclock -w -f {self.rtc_device_path}", check=False)
        
        if success:
            self.logger.info("✅ System time written to RTC")
            return True
        else:
            self.logger.error(f"❌ Failed to write time to RTC: {stderr}")
            return False
    
    def sync_system_time_from_rtc(self):
        """Sync system time from RTC.
        
        Returns:
            bool: True if successful
        """
        if not self.rtc_device_path:
            self.logger.error("❌ RTC device not initialized")
            return False
        
        self.logger.info("🕐 Syncing system time from RTC...")
        success, _, stderr = self.run_command(f"sudo hwclock -s -f {self.rtc_device_path}", check=False)
        
        if success:
            self.logger.info("✅ System time synced from RTC")
            return True
        else:
            self.logger.error(f"❌ Failed to sync time from RTC: {stderr}")
            return False
    
    def get_rtc_status(self):
        """Get comprehensive RTC status information.
        
        Returns:
            dict: RTC status information
        """
        status = {
            'initialized': self.rtc_device_path is not None,
            'device_path': self.rtc_device_path,
            'address': self.rtc_address,
            'module_info': self.rtc_info,
            'system_time': datetime.now(),
            'rtc_time': None,
            'time_difference': None
        }
        
        if self.rtc_device_path:
            rtc_time = self.read_rtc_time()
            if rtc_time:
                status['rtc_time'] = rtc_time
                status['time_difference'] = abs((status['system_time'] - rtc_time).total_seconds())
        
        return status
    
    def initialize_for_offline_operation(self):
        """Initialize RTC for offline operation.
        
        This method:
        1. Sets up the RTC module
        2. Syncs RTC with current system time
        3. Prepares for offline time keeping
        
        Returns:
            bool: True if successful
        """
        self.logger.info("Initializing RTC system for offline time keeping...")
        
        # Setup RTC hardware
        if not self.setup_rtc():
            self.logger.error("Failed to setup RTC hardware")
            return False
        
        # Write current system time to RTC
        if not self.write_system_time_to_rtc():
            self.logger.error("Failed to sync time to RTC")
            return False
        
        # Verify the setup
        status = self.get_rtc_status()
        if status['time_difference'] and status['time_difference'] > 2:  # More than 2 seconds difference
            self.logger.warning(f"⚠️ Time difference detected: {status['time_difference']:.1f} seconds")
        
        self.logger.info("✅ RTC initialized for offline operation")
        return True

def main():
    """Test RTC functionality."""
    print("=== RTC Manager Test ===")
    
    rtc = RTCManager()
    
    # Initialize RTC
    if rtc.initialize_for_offline_operation():
        print("✅ RTC initialization successful")
        
        # Show status
        status = rtc.get_rtc_status()
        print(f"\n📊 RTC Status:")
        print(f"  Device: {status['device_path']}")
        print(f"  Address: 0x{status['address']:02x}")
        print(f"  System Time: {status['system_time']}")
        print(f"  RTC Time: {status['rtc_time']}")
        if status['time_difference']:
            print(f"  Time Difference: {status['time_difference']:.1f} seconds")
    else:
        print("❌ RTC initialization failed")
        print("⚠️ RTC initialization failed - using system time only")

if __name__ == "__main__":
    main()
