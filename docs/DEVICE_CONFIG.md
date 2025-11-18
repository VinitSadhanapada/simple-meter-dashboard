# Device Configuration Guide

## 📊 Customizing Your Meter Devices

Both `print_dashboard2.py` and `simple_rpi_dashboard.py` now support easy device configuration.

## 🔧 Configuration Location

In both scripts, look for the `DEVICE_CONFIG` section:

```python
# Device Configuration - Customize your meters here
DEVICE_CONFIG = [
    {"name": "Main Panel", "address": 1, "model": "LG6400"},
    {"name": "Generator Set", "address": 2, "model": "LG6400"},
    {"name": "UPS System", "address": 3, "model": "LG6400"},
    # Add more devices as needed:
    # {"name": "Your Device Name", "address": 4, "model": "LG6400"},
    # {"name": "Another Device", "address": 5, "model": "EN8410"},
]
```

## 📋 Configuration Parameters

Each device requires three parameters:

| Parameter | Description | Example Values |
|-----------|-------------|----------------|
| **name** | Display name for the device | "Main Panel", "Generator", "UPS" |
| **address** | Modbus device address (1-247) | 1, 2, 3, 4, etc. |
| **model** | Device model type | "LG6400", "EN8410", "LG5220", etc. |

## 🔢 Supported Device Models

- **LG6400** - Elmeasure LG6400 series
- **EN8410** - Elmeasure EN8410 series  
- **EN8400** - Elmeasure EN8400 series
- **EN8100** - Elmeasure EN8100 series
- **LG+5220** - Elmeasure LG5220 series
- **LG+5310** - Elmeasure LG5310 series
- **ELR300** - Elmeasure iELR300 series

## 📝 Configuration Examples

### **Single Device Setup:**
```python
DEVICE_CONFIG = [
    {"name": "Main Meter", "address": 1, "model": "LG6400"},
]
```

### **Multiple Same-Model Devices:**
```python
DEVICE_CONFIG = [
    {"name": "Building A", "address": 1, "model": "LG6400"},
    {"name": "Building B", "address": 2, "model": "LG6400"},
    {"name": "Building C", "address": 3, "model": "LG6400"},
]
```

### **Mixed Device Models:**
```python
DEVICE_CONFIG = [
    {"name": "Main Panel", "address": 1, "model": "LG6400"},
    {"name": "Generator", "address": 2, "model": "EN8410"},
    {"name": "Solar Inverter", "address": 3, "model": "LG5220"},
    {"name": "UPS System", "address": 4, "model": "ELR300"},
]
```

### **Large Installation (10+ devices):**
```python
DEVICE_CONFIG = [
    {"name": "Main Incomer", "address": 1, "model": "LG6400"},
    {"name": "Floor 1 Panel", "address": 2, "model": "LG6400"},
    {"name": "Floor 2 Panel", "address": 3, "model": "LG6400"},
    {"name": "Floor 3 Panel", "address": 4, "model": "LG6400"},
    {"name": "HVAC System", "address": 5, "model": "EN8410"},
    {"name": "Lighting Panel", "address": 6, "model": "EN8410"},
    {"name": "Generator Set", "address": 7, "model": "LG6400"},
    {"name": "UPS Panel", "address": 8, "model": "ELR300"},
    {"name": "Solar Inverter 1", "address": 9, "model": "LG5220"},
    {"name": "Solar Inverter 2", "address": 10, "model": "LG5220"},
]
```

## ⚠️ Important Notes

1. **Unique Addresses**: Each device must have a unique Modbus address (1-247)
2. **Device Names**: Can contain spaces and special characters for display
3. **CSV Files**: Generated using cleaned device names (spaces/special chars removed)
4. **Model Matching**: Ensure the model matches your actual hardware

## 🔧 Making Changes

1. **Edit the configuration** in your chosen script
2. **Save the file**
3. **Restart the application** - changes take effect immediately

## 📁 File Naming

CSV files are automatically named based on device names:
- "Main Panel" → `Main_Panel_20250724.csv`
- "Generator Set" → `Generator_Set_20250724.csv`
- "UPS System" → `UPS_System_20250724.csv`

## 🚀 Quick Test

To verify your configuration works:

```bash
# Desktop mode (interactive)
python print_dashboard2.py

# RPi mode (service)
python3 simple_rpi_dashboard.py --run
```

The dashboard will show all your configured devices in the display table and create corresponding CSV files for data logging.

## 🔍 Troubleshooting

- **Device not responding**: Check address and model settings
- **Wrong data**: Verify model matches actual hardware
- **CSV files**: Check `csv_data/` directory for output files
- **Display issues**: Device names appear as configured

This flexible configuration system allows you to easily adapt the dashboard to any installation size and device mix!
