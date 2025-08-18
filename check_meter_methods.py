#!/usr/bin/env python3
"""
Check MeterDevice methods and fix method calls
"""


def check_meter_device_methods():
    """Check what methods MeterDevice actually has"""

    try:
        import sys
        sys.path.append('/home/isha/deepak/MFM_offline_setup')

        from meter_device import MeterDevice
        from macros import PARAMETERS

        print("🔍 Checking MeterDevice methods...")

        # Create a test device
        test_device = MeterDevice(
            name="TEST",
            model="LG6400",
            parameters=PARAMETERS,
            client=None,
            error_file=None,
            simulation_mode=True,
            device_address=1
        )

        # Check available methods
        methods = [method for method in dir(
            test_device) if not method.startswith('_')]
        print(f"📋 Available methods: {methods}")

        # Try different method names that might exist
        possible_methods = ['read_parameters', 'read_all',
                            'read_data', 'get_readings', 'read']

        for method_name in possible_methods:
            if hasattr(test_device, method_name):
                print(f"✅ Found method: {method_name}")
                try:
                    method = getattr(test_device, method_name)
                    if callable(method):
                        print(f"  📞 {method_name} is callable")
                        # Try calling it (carefully)
                        try:
                            result = method()
                            print(
                                f"  📊 {method_name}() returned: {type(result)} with {len(result) if hasattr(result, '__len__') else 'unknown'} items")
                        except Exception as e:
                            print(f"  ⚠️  {method_name}() failed: {e}")
                except Exception as e:
                    print(f"  ❌ Error with {method_name}: {e}")
            else:
                print(f"❌ No method: {method_name}")

        return True

    except Exception as e:
        print(f"❌ Error checking MeterDevice: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    check_meter_device_methods()
