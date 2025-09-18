from django.core.management.base import BaseCommand
from django.urls import get_resolver
from termcolor import colored


class Command(BaseCommand):
    help = 'List all URLs in the Django project with detailed information'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Filter URLs by app name',
        )
        parser.add_argument(
            '--pattern',
            type=str,
            help='Filter URLs containing this pattern',
        )
        parser.add_argument(
            '--format',
            choices=['table', 'json', 'markdown'],
            default='table',
            help='Output format',
        )

    def handle(self, **options):
        resolver = get_resolver()
        urls = self.get_all_urls(resolver)

        # Filter by app if specified
        if options['app']:
            urls = [url for url in urls if options['app'] in url['namespace']]

        # Filter by pattern if specified
        if options['pattern']:
            pattern = options['pattern'].lower()
            urls = [url for url in urls if pattern in url['pattern'].lower() or
                    pattern in url['name'].lower()]

        # Output in specified format
        if options['format'] == 'table':
            self.print_table(urls)
        elif options['format'] == 'json':
            self.print_json(urls)
        elif options['format'] == 'markdown':
            self.print_markdown(urls)

    def get_all_urls(self, resolver, namespace=''):
        urls = []

        for pattern in resolver.url_patterns:
            if hasattr(pattern, 'url_patterns'):
                # This is an include() - recurse into it
                new_namespace = f"{namespace}:{pattern.namespace}" if pattern.namespace else namespace
                urls.extend(self.get_all_urls(pattern, new_namespace))
            else:
                # This is a URL pattern
                url_info = {
                    'pattern': str(pattern.pattern),
                    'name': pattern.name or 'unnamed',
                    'namespace': namespace.strip(':') if namespace else '',
                    'full_name': f"{namespace.strip(':')}:{pattern.name}" if namespace and pattern.name else pattern.name or 'unnamed',
                    'view': self.get_view_name(pattern),
                }
                urls.append(url_info)

        return urls

    def get_view_name(self, pattern):
        """Extract view name from URL pattern"""
        if hasattr(pattern, 'callback'):
            if hasattr(pattern.callback, '__name__'):
                return pattern.callback.__name__
            elif hasattr(pattern.callback, 'view_class'):
                return pattern.callback.view_class.__name__
            else:
                return str(pattern.callback)
        return 'Unknown'

    def print_table(self, urls):
        """Print URLs in a formatted table"""
        self.stdout.write(
            colored('\nDjango URL Patterns\n', 'cyan', attrs=['bold']))
        self.stdout.write('=' * 80)

        # Headers
        header = f"{'Pattern':<30} {'Name':<25} {'View':<20} {'Namespace':<15}"
        self.stdout.write(colored(header, 'yellow', attrs=['bold']))
        self.stdout.write('-' * 80)

        # URLs
        for url in urls:
            pattern = url['pattern'][:29] if len(
                url['pattern']) > 29 else url['pattern']
            name = url['name'][:24] if len(url['name']) > 24 else url['name']
            view = url['view'][:19] if len(url['view']) > 19 else url['view']
            namespace = url['namespace'][:14] if len(
                url['namespace']) > 14 else url['namespace']

            row = f"{pattern:<30} {name:<25} {view:<20} {namespace:<15}"
            self.stdout.write(row)

        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(f"Total URLs: {len(urls)}")

    def print_json(self, urls):
        """Print URLs in JSON format"""
        import json
        self.stdout.write(json.dumps(urls, indent=2))

    def print_markdown(self, urls):
        """Print URLs in Markdown table format"""
        self.stdout.write("# Django URL Patterns\n")
        self.stdout.write("| Pattern | Name | View | Namespace | Full Name |")
        self.stdout.write("|---------|------|------|-----------|-----------|")

        for url in urls:
            self.stdout.write(
                f"| `{url['pattern']}` | `{url['name']}` | `{url['view']}` | `{url['namespace']}` | `{url['full_name']}` |")

        self.stdout.write(f"\nTotal URLs: {len(urls)}")
