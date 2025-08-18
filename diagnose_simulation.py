#!/usr/bin/env python3
"""
Quick diagnostic for simulation mode and data population issues
"""
import sys
sys.path.append('/home/isha/deepak/MFM_offline_setup')


def diagnose_simulation_mode():
    """Check simulation mode configuration and data flow"""

    try:
        # Check config loading
        from offline_rpi_dashboard_db import CONFIG, DEVICE_CONFIG

        print("🔍 Diagnosing simulation mode...")
        print(f"📋 CONFIG loaded: {bool(CONFIG)}")
        print(f"📋 DEVICE_CONFIG loaded: {bool(DEVICE_CONFIG)}")

        if CONFIG:
            print(
                f"🎛️  SIMULATION_MODE: {CONFIG.get('SIMULATION_MODE', 'NOT FOUND')}")
            print(f"🔌 PORT: {CONFIG.get('PORT', 'NOT FOUND')}")
            print(
                f"⏱️  READING_INTERVAL: {CONFIG.get('READING_INTERVAL', 'NOT FOUND')}")
            print(
                f"⏳ INTER_DEVICE_DELAY: {CONFIG.get('INTER_DEVICE_DELAY', 'NOT FOUND')}")

        if DEVICE_CONFIG:
            print(f"📊 Number of devices: {len(DEVICE_CONFIG)}")
            for i, device in enumerate(DEVICE_CONFIG):
                print(
                    f"  Device {i+1}: {device.get('meter_name', device.get('name', 'Unknown'))}")

        # Check if simulation data generation works
        print("\n🧪 Testing simulation data generation...")
        from macros import PARAMETERS
        print(f"📊 Available parameters: {len(PARAMETERS)}")
        print(f"🏷️  Parameter type: {type(PARAMETERS)}")

        # Handle both list and dict parameter formats
        if isinstance(PARAMETERS, dict):
            print(f"📋 Parameter names: {list(PARAMETERS.keys())}")
        elif isinstance(PARAMETERS, list):
            print(
                f"📋 First few parameters: {PARAMETERS[:5] if len(PARAMETERS) > 5 else PARAMETERS}")

        # Test meter device creation
        from meter_device import MeterDevice

        if DEVICE_CONFIG and len(DEVICE_CONFIG) > 0:
            device = DEVICE_CONFIG[0]
            meter_name = device.get("meter_name", device.get("name", "TEST"))
            meter_model = device.get(
                "meter_model", device.get("model", "LG6400"))
            meter_address = device.get(
                "meter_address", device.get("address", 1))

            print(f"\n🔧 Testing meter device creation:")
            print(f"  Name: {meter_name}")
            print(f"  Model: {meter_model}")
            print(f"  Address: {meter_address}")

            test_meter = MeterDevice(
                name=meter_name,
                model=meter_model,
                parameters=PARAMETERS,
                client=None,  # No client in simulation mode
                error_file=None,
                simulation_mode=True,  # Force simulation mode
                device_address=meter_address
            )

            print("✅ Meter device created successfully")

            # Test reading parameters
            print("\n📊 Testing parameter reading in simulation mode...")
            test_data = test_meter.read_parameters()
            print(f"📈 Generated {len(test_data)} data points")

            if test_data and len(test_data) > 0:
                print("✅ Simulation data generation working")
                # Show first few values
                if isinstance(PARAMETERS, dict):
                    for i, (param_name, value) in enumerate(zip(PARAMETERS.keys(), test_data)):
                        if i < 5:  # Show first 5
                            print(f"  {param_name}: {value}")
                        elif i == 5:
                            print(
                                f"  ... and {len(test_data) - 5} more values")
                            break
                else:
                    # PARAMETERS is a list
                    for i, value in enumerate(test_data):
                        if i < 5:  # Show first 5
                            param_name = PARAMETERS[i] if i < len(
                                PARAMETERS) else f"param_{i}"
                            print(f"  {param_name}: {value}")
                        elif i == 5:
                            print(
                                f"  ... and {len(test_data) - 5} more values")
                            break
            else:
                print("❌ No simulation data generated")
                print("🔍 This might be why --run is not populating data!")

        return True

    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    diagnose_simulation_mode()
