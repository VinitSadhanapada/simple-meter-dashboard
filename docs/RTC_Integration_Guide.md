Wa# RTC (Real-Time Clock) Integration Guide

## Overview
The dashboard now includes Real-Time Clock (RTC) support for accurate time keeping during offline operation. This ensures your meter readings have correct timestamps even when internet is unavailable.

## Supported RTC Modules
- **DS3231**: High precision RTC with temperature compensation (±2ppm accuracy)
- **DS1307**: Basic RTC module (affordable option)
- **PCF8523**: Low power RTC with integrated crystal

## Hardware Setup

### 1. Connection Diagram
```
Raspberry Pi    RTC Module
-----------     ----------
3.3V/5V    ---> VCC
GND        ---> GND
GPIO2(SDA) ---> SDA
GPIO3(SCL) ---> SCL
```

### 2. Enable I2C Interface
```bash
sudo raspi-config
# Navigate to: Interface Options -> I2C -> Enable
# Reboot: sudo reboot
```

## Software Setup

### 1. Test RTC Hardware
```bash
# Check if RTC is detected
sudo python3 setup_rtc.py --test
```

### 2. Full RTC Setup
```bash
# Interactive setup (recommended for first time)
sudo python3 setup_rtc.py

# Or automatic setup
sudo python3 setup_rtc.py --auto
```

### 3. Verify Installation
```bash
# Check system time vs RTC time
date
sudo hwclock -r

# Should show similar times (within a few seconds)
```

## Dashboard Configuration

### Enable/Disable RTC
In `simple_rpi_dashboard.py`, set:
```python
CONFIG = {
    "ENABLE_RTC": True,   # Enable RTC functionality
    # ... other settings
}
```

### RTC Status in Logs
When dashboard starts, you'll see:
```
2025-07-27 15:30:00 - INFO - Initializing RTC system for offline time keeping...
2025-07-27 15:30:01 - INFO - ✅ RTC module detected at I2C address 0x68
2025-07-27 15:30:02 - INFO - ✅ RTC system ready for offline operation
```

## Offline Operation Benefits

### ✅ **Internet Connection Available**
- Dashboard syncs time with network (NTP)
- RTC gets updated with accurate time
- Normal operation with network timestamps

### ✅ **Internet Connection Lost**
- RTC maintains accurate time independently
- Dashboard continues with correct timestamps
- CSV files get proper time stamps
- No data corruption or time jumps

### ✅ **Power Loss + Reboot (No Internet)**
- RTC battery maintains time during power-off
- On boot: System reads time from RTC
- Dashboard starts with correct time
- Seamless operation without network dependency

## Time Accuracy

### DS3231 (Recommended)
- **Accuracy**: ±2ppm (±1 minute per year)
- **Temperature compensation**: Yes
- **Battery life**: 5-10 years (CR2032)

### DS1307 (Budget Option)
- **Accuracy**: ±1 minute per month
- **Temperature compensation**: No
- **Battery life**: 5-10 years (CR2032)

## Troubleshooting

### RTC Not Detected
```bash
# Check I2C is enabled
sudo i2cdetect -y 1

# Should show device at address 68 (or 51 for PCF8563)
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 60: -- -- -- -- -- -- -- -- 68 -- -- -- -- -- -- --
```

### Common Issues
1. **"No RTC modules detected"**
   - Check wiring connections
   - Verify I2C is enabled in raspi-config
   - Ensure RTC module has power

2. **"RTC initialization failed"**
   - Run setup with sudo: `sudo python3 setup_rtc.py`
   - Check if i2c-tools installed: `sudo apt install i2c-tools`

3. **Time difference warnings**
   - Normal if system was offline for extended period
   - RTC will sync with system time on next startup

### Manual Commands
```bash
# Read RTC time
sudo hwclock -r

# Write system time to RTC
sudo hwclock -w

# Read system time from RTC
sudo hwclock -s

# Show RTC device info
ls -la /dev/rtc*
```

## Dashboard Integration

The RTC is automatically integrated into your dashboard:

1. **Startup**: RTC initializes and syncs time
2. **Operation**: All timestamps use accurate time
3. **CSV Logging**: Meter readings get correct timestamps
4. **Offline**: Time continues accurately without internet
5. **Recovery**: Time restored from RTC after power loss

## Battery Replacement

### When to Replace
- Typically every 5-10 years
- If time starts drifting significantly
- If RTC doesn't maintain time during power-off

### Replacement Process
1. Power off Raspberry Pi
2. Remove old CR2032 battery
3. Insert new CR2032 battery (+ side up)
4. Power on and run: `sudo python3 setup_rtc.py --test`

## Configuration Examples

### Maximum Reliability Setup
```python
CONFIG = {
    "ENABLE_RTC": True,
    "SIMULATION_MODE": False,
    "READING_INTERVAL": 10,
    "INTER_DEVICE_DELAY": 0.1,
    # ... other settings
}
```

### Testing/Development Setup
```python
CONFIG = {
    "ENABLE_RTC": False,  # Disable for testing
    "SIMULATION_MODE": True,
    # ... other settings
}
```

## Maintenance Commands

```bash
# Test RTC functionality
sudo python3 setup_rtc.py --test

# Remove RTC configuration
sudo python3 setup_rtc.py --remove

# Check RTC status in dashboard
grep -i rtc logs/dashboard_*.log
```

---

## Summary

With RTC integration, your meter dashboard now provides:
- ✅ **Accurate timestamps** during internet outages
- ✅ **Continuous operation** regardless of network status
- ✅ **Data integrity** with proper time synchronization
- ✅ **Reliable CSV logging** with correct timestamps
- ✅ **Automatic recovery** after power loss

Your meter readings will always have accurate timestamps, making your data reliable for analysis and reporting even in areas with unstable internet connectivity.
