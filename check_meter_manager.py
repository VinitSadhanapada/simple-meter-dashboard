#!/usr/bin/env python3
"""
Check MeterManager methods and parameters
"""
import sys
sys.path.append('/home/isha/deepak/MFM_offline_setup')


def check_meter_manager():
    """Check MeterManager methods and their signatures"""

    try:
        from meter_manager import MeterManager
        from macros import PARAMETERS
        from meter_device import MeterDevice

        print("🔍 Checking MeterManager...")

        # Create a test meter device
        test_meter = MeterDevice(
            name="TEST",
            model="LG6400",
            parameters=PARAMETERS,
            client=None,
            error_file=None,
            simulation_mode=True,
            device_address=1
        )

        # Create a test manager
        test_manager = MeterManager(
            [test_meter],
            PARAMETERS,
            ["test.csv"],
            location="TEST_LOCATION",
            mqtt_client=None,
            publish_mqtt=False
        )

        # Check available methods
        methods = [method for method in dir(
            test_manager) if not method.startswith('_')]
        print(f"📋 Available methods: {methods}")

        # Check read_all method signature
        import inspect
        if hasattr(test_manager, 'read_all'):
            sig = inspect.signature(test_manager.read_all)
            print(f"🔧 read_all signature: {sig}")

            # Try calling it with different parameters
            try:
                result = test_manager.read_all()
                print(f"✅ read_all() works (no params): {type(result)}")
                if result:
                    print(
                        f"📊 Sample result: {result[0] if len(result) > 0 else 'Empty'}")
            except Exception as e:
                print(f"❌ read_all() failed: {e}")

            try:
                result = test_manager.read_all(inter_device_delay=0.1)
                print(
                    f"✅ read_all(inter_device_delay=0.1) works: {type(result)}")
                if result:
                    print(
                        f"📊 Sample result: {result[0] if len(result) > 0 else 'Empty'}")
            except Exception as e:
                print(f"❌ read_all(inter_device_delay=0.1) failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Error checking MeterManager: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    check_meter_manager()
