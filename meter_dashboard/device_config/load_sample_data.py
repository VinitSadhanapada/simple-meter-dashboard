from django.core.management.base import BaseCommand
from device_config.models import RaspberryPi, MeterDevice, SystemConfiguration


class Command(BaseCommand):
    help = 'Load sample data based on the provided JSON examples'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Loading sample data...'))

        # Create Raspberry Pi
        pi, created = RaspberryPi.objects.get_or_create(
            pi_ip='172.20.10.4',
            defaults={
                'pi_name': 'SP Block',
                'location': 'SP3 PH',
                'is_active': True,
                'ssh_username': 'pi',
                'ssh_password': 'devi',  # Update this to your actual Pi password
                'ssh_port': 22,
                'config_path': '/home/pi/meter_config'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Created Raspberry Pi: {pi.pi_name}'))
        else:
            self.stdout.write(f'Raspberry Pi already exists: {pi.pi_name}')

        # Create sample meters based on your JSON data
        meters_data = [
            {
                'meter_name': 'EB INCOMER',
                'meter_address': 1,
                'meter_model': 'LG6400',
                'location': 'SP3 PH'
            },
            {
                'meter_name': 'SP3',
                'meter_address': 2,
                'meter_model': 'LG+5220',
                'location': 'SP3 PH'
            },
            {
                'meter_name': 'SP4',
                'meter_address': 3,
                'meter_model': 'LG+5310',
                'location': 'SP3 PH'
            }
        ]

        for meter_data in meters_data:
            meter, created = MeterDevice.objects.get_or_create(
                meter_address=meter_data['meter_address'],
                raspberry_pi=pi,
                defaults={
                    'meter_name': meter_data['meter_name'],
                    'meter_model': meter_data['meter_model'],
                    'location': meter_data['location'],
                    'is_active': True
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'Created meter: {meter.meter_name}'))
            else:
                self.stdout.write(f'Meter already exists: {meter.meter_name}')

        # Create system configuration
        system_config, created = SystemConfiguration.objects.get_or_create(
            raspberry_pi=pi,
            defaults={
                'simulation_mode': False,
                'reading_interval': 30,
                'inter_device_delay': 0.1,
                'port': '/dev/ttyUSB0',
                'enable_mqtt': False,
                'enable_rtc': True,
                'log_level': 'INFO'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Created system configuration for {pi.pi_name}'))
        else:
            self.stdout.write(
                f'System configuration already exists for {pi.pi_name}')

        self.stdout.write(self.style.SUCCESS('Sample data loading completed!'))
        self.stdout.write(self.style.WARNING(
            'Note: Update SSH credentials in settings.py before deploying configurations'))
