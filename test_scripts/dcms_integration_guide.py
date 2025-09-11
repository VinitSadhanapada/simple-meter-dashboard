#!/usr/bin/env python3
"""
DCMS Integration Guide for Meter Dashboard

This module provides integration between DCMS (Device Configuration Management System)
and the meter dashboard system. DCMS is responsible for:

1. Managing Pi configurations via SSH
2. Writing config.jsonc and device_config.jsonc files to Pi
3. Monitoring Pi status and meter readings
4. Providing central management interface

Database Structure:
- dcms_pi_setup: Pi device information (managed by DCMS)
- meter_readings: Raw meter data (written by Pi script)
- meters_meterreading: Django app meter data (with Pi relationship)
"""


class DCMSIntegration:
    """
    Integration helper for DCMS and Meter Dashboard
    """

    def __init__(self, db_config):
        self.db_config = db_config

    def get_dcms_managed_pi_config(self, pi_details):
        """
        Generate config.jsonc structure for DCMS to write to Pi

        Args:
            pi_details: Dictionary with Pi information from DCMS

        Returns:
            Dictionary representing config.jsonc content
        """
        return {
            # Pi Identity (managed by DCMS)
            "PI_NAME": pi_details.get('pi_name', 'Pi_Unknown'),
            "LOCATION": pi_details.get('location', 'Unknown'),
            "SSH_USERNAME": pi_details.get('ssh_username', 'pi'),
            "DESCRIPTION": pi_details.get('description', f"Pi at {pi_details.get('location')}"),
            "CONTACT_PERSON": pi_details.get('contact_person', ''),
            "INSTALLATION_DATE": pi_details.get('installation_date', ''),

            # Hardware Configuration
            "PORT": pi_details.get('port', '/dev/ttyUSB0'),
            "SIMULATION_MODE": pi_details.get('simulation_mode', False),
            "READING_INTERVAL": pi_details.get('reading_interval', 60),
            "INTER_DEVICE_DELAY": pi_details.get('inter_device_delay', 0.5),

            # Database Configuration
            "DB_SERVER_IP": pi_details.get('db_server_ip', 'localhost'),
            "SERVER_API_IP": pi_details.get('server_api_ip', 'localhost'),

            # DCMS Management Metadata
            "MANAGED_BY_DCMS": True,
            "DCMS_CONFIG_VERSION": "1.0",
            "LAST_UPDATED_BY": pi_details.get('updated_by', 'DCMS System'),
            "CONFIG_CHECKSUM": pi_details.get('config_checksum', '')
        }

    def get_dcms_managed_device_config(self, devices_list):
        """
        Generate device_config.jsonc structure for DCMS to write to Pi

        Args:
            devices_list: List of device dictionaries from DCMS

        Returns:
            List representing device_config.jsonc content
        """
        device_config = []

        for device in devices_list:
            device_entry = {
                # Basic device info
                "name": device.get('name', 'Unknown_Device'),
                "model": device.get('model', 'Unknown_Model'),
                "address": device.get('address', 1),
                "location": device.get('location', 'Unknown'),
                "meter_type": device.get('meter_type', 'Energy Meter'),

                # Installation details
                "installation_date": device.get('installation_date', ''),
                "calibration_date": device.get('calibration_date', ''),
                "status": device.get('status', 'active'),

                # DCMS Management
                "managed_by_dcms": True,
                "dcms_device_id": device.get('dcms_device_id', ''),
                "last_updated_by": device.get('updated_by', 'DCMS System')
            }
            device_config.append(device_entry)

        return device_config

    def validate_pi_connection(self, pi_setup_id):
        """
        Check if Pi is actively sending data

        Args:
            pi_setup_id: ID of the Pi in dcms_pi_setup table

        Returns:
            Dictionary with connection status
        """
        from postgres_helper import PostgresHelper

        try:
            db = PostgresHelper(**self.db_config)
            db.connect()
            cursor = db.connection.cursor()

            # Check last reading time
            cursor.execute("""
                SELECT 
                    COUNT(*) as reading_count,
                    MAX(reading_time) as last_reading,
                    NOW() - MAX(reading_time) as time_since_last
                FROM meter_readings 
                WHERE pi_setup_id = %s 
                AND reading_time > NOW() - INTERVAL '1 hour'
            """, (pi_setup_id,))

            result = cursor.fetchone()
            reading_count, last_reading, time_since_last = result

            # Update Pi status
            if reading_count > 0:
                status = 'online'
            else:
                status = 'offline'

            cursor.execute("""
                UPDATE dcms_pi_setup 
                SET connection_status = %s, last_connected = %s
                WHERE id = %s
            """, (status, last_reading, pi_setup_id))

            db.connection.commit()
            db.close()

            return {
                'status': status,
                'reading_count': reading_count,
                'last_reading': last_reading,
                'time_since_last': str(time_since_last) if time_since_last else None
            }

        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def get_pi_dashboard_url(self, pi_ip):
        """
        Get the dashboard URL for a specific Pi

        Args:
            pi_ip: IP address of the Pi

        Returns:
            String with dashboard URL
        """
        return f"http://{pi_ip}:8000/device-config/"

# Example usage for DCMS developers:


def example_dcms_workflow():
    """
    Example of how DCMS would manage a Pi configuration
    """

    # 1. DCMS has Pi information
    pi_info_from_dcms = {
        'pi_name': 'Pi_Nandi_001',
        'location': 'Nandi Hills',
        'pi_ip': '192.168.1.101',
        'ssh_username': 'pi',
        'description': 'Main data collection Pi at Nandi Hills',
        'contact_person': 'Field Engineer',
        'installation_date': '2024-01-15',
        'port': '/dev/ttyUSB0',
        'simulation_mode': False,
        'reading_interval': 60,
        'db_server_ip': 'localhost',
        'server_api_ip': '192.168.1.100'
    }

    # 2. DCMS has device information
    devices_from_dcms = [
        {
            'name': 'LG_METER_001',
            'model': 'LG+5220',
            'address': 1,
            'location': 'Nandi Hills',
            'meter_type': 'Energy Meter',
            'dcms_device_id': 'DEV_001_NANDI'
        },
        {
            'name': 'SCHNEIDER_METER_002',
            'model': 'PM2120',
            'address': 2,
            'location': 'Nandi Hills',
            'meter_type': 'Power Meter',
            'dcms_device_id': 'DEV_002_NANDI'
        }
    ]

    # 3. Generate configuration files
    dcms = DCMSIntegration({})

    config_jsonc = dcms.get_dcms_managed_pi_config(pi_info_from_dcms)
    device_config_jsonc = dcms.get_dcms_managed_device_config(
        devices_from_dcms)

    print("📄 Generated config.jsonc:")
    import json
    print(json.dumps(config_jsonc, indent=2))

    print("\n📄 Generated device_config.jsonc:")
    print(json.dumps(device_config_jsonc, indent=2))

    # 4. DCMS would then:
    # - SSH to Pi
    # - Write these files to /home/pi/meter_dashboard/
    # - Restart the meter dashboard service
    # - Monitor the Pi status

    print("\n💡 DCMS Workflow:")
    print("1. Generate config files using DCMSIntegration.get_dcms_managed_*_config()")
    print("2. SSH to Pi and write config.jsonc and device_config.jsonc")
    print("3. Restart meter dashboard service: sudo systemctl restart meter-dashboard")
    print("4. Monitor Pi status using DCMSIntegration.validate_pi_connection()")
    print(
        f"5. Access Pi dashboard at: {dcms.get_pi_dashboard_url(pi_info_from_dcms['pi_ip'])}")

# Database Integration Functions


def setup_dcms_integration_tables():
    """
    Run this to set up all necessary tables for DCMS integration
    """
    print("🔧 Setting up DCMS integration tables...")

    # Import database setup
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))

    from migrate_enhanced_tables import migrate_database_structure

    if migrate_database_structure():
        print("✅ DCMS integration database setup complete!")
        print("\n📋 Tables created/updated:")
        print("- dcms_pi_setup: Pi device management (DCMS managed)")
        print("- meter_readings: Raw meter data (Pi script writes)")
        print("- meters_meterreading: Django app data (linked to Pi)")

        print("\n🔗 Foreign Key Relationships:")
        print("- meter_readings.pi_setup_id → dcms_pi_setup.id")
        print("- meters_meterreading.pi_setup_id → dcms_pi_setup.id")

        return True
    else:
        print("❌ DCMS integration setup failed!")
        return False


if __name__ == "__main__":
    print("🚀 DCMS Integration Guide")
    print("=" * 50)

    # Run example workflow
    example_dcms_workflow()

    print("\n" + "=" * 50)
    print("📚 DCMS Integration Summary:")
    print("✅ Single source of truth: DCMS manages all Pi configurations")
    print("✅ Standardized config files: config.jsonc and device_config.jsonc")
    print("✅ Proper database relationships: Pi ↔ Meter readings")
    print("✅ Remote management: SSH-based configuration deployment")
    print("✅ Monitoring: Connection status and data validation")
