from django.core.management.base import BaseCommand
from device_config.models import RaspberryPi


class Command(BaseCommand):
    help = 'Set up SSH keys for Raspberry Pi devices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pi-ip',
            type=str,
            help='Set up SSH key for specific Pi IP address',
        )
        parser.add_argument(
            '--pi-name',
            type=str,
            help='Set up SSH key for specific Pi name',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Set up SSH keys for all Pis',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regenerate SSH keys even if they exist',
        )

    def handle(self, *args, **options):
        pis = []

        if options['pi_ip']:
            try:
                pi = RaspberryPi.objects.get(pi_ip=options['pi_ip'])
                pis = [pi]
            except RaspberryPi.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f'No Pi found with IP: {options["pi_ip"]}')
                )
                return
        elif options['pi_name']:
            try:
                pi = RaspberryPi.objects.get(pi_name=options['pi_name'])
                pis = [pi]
            except RaspberryPi.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f'No Pi found with name: {options["pi_name"]}')
                )
                return
        elif options['all']:
            pis = RaspberryPi.objects.filter(is_active=True)
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --pi-ip, --pi-name, or --all')
            )
            return

        if not pis:
            self.stdout.write(self.style.WARNING('No Pis found to set up'))
            return

        for pi in pis:
            self.stdout.write(
                f'Setting up SSH key for {pi.pi_name} ({pi.pi_ip})...')

            if not pi.ssh_password:
                self.stdout.write(
                    self.style.ERROR(
                        f'No SSH password set for {pi.pi_name}. Please set it in admin first.')
                )
                continue

            success, message = pi.setup_ssh_key(
                force_regenerate=options['force'])

            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {pi.pi_name}: {message}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ {pi.pi_name}: {message}')
                )
