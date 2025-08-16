from django.core.management.base import BaseCommand
from django.db import connection
from termcolor import colored


class Command(BaseCommand):
    help = 'Show PostgreSQL table schema information'

    def add_arguments(self, parser):
        parser.add_argument(
            'table_name',
            nargs='?',
            type=str,
            help='Name of the table to describe (without app prefix)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Show all tables in the database',
        )
        parser.add_argument(
            '--format',
            choices=['table', 'sql', 'django'],
            default='table',
            help='Output format',
        )

    def handle(self, **options):
        table_name = options.get('table_name')
        show_all = options.get('all')
        output_format = options.get('format')

        if not table_name and not show_all:
            self.stdout.write(
                colored('Please specify a table name or use --all flag', 'red'))
            return

        # Check if we're using PostgreSQL
        if 'postgresql' not in connection.settings_dict['ENGINE']:
            self.stdout.write(
                colored('This command is designed for PostgreSQL databases', 'yellow'))
            self.stdout.write('Current database engine: ' +
                              connection.settings_dict['ENGINE'])
            return

        try:
            with connection.cursor() as cursor:
                if show_all:
                    self.show_all_tables(cursor, output_format)
                else:
                    # Try to find the table with app prefix
                    actual_table_name = self.find_table_name(
                        cursor, table_name)
                    if actual_table_name:
                        self.describe_table(
                            cursor, actual_table_name, output_format)
                    else:
                        self.stdout.write(
                            colored(f"Table '{table_name}' not found", 'red'))
                        self.suggest_tables(cursor, table_name)

        except Exception as e:
            self.stdout.write(colored(f"Error: {e}", 'red'))

    def find_table_name(self, cursor, table_name):
        """Find the actual table name, considering Django app prefixes"""
        # Common Django app prefixes for this project
        possible_names = [
            table_name,
            f"meters_{table_name}",
            f"meters_meter{table_name}",
            f"meter_dashboard_{table_name}",
            f"device_config_{table_name}",
        ]

        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
        """)

        existing_tables = [row[0] for row in cursor.fetchall()]

        for name in possible_names:
            if name in existing_tables:
                return name

        # Try partial match
        for existing_table in existing_tables:
            if table_name.lower() in existing_table.lower():
                return existing_table

        return None

    def show_all_tables(self, cursor, output_format):
        """Show all tables in the database"""
        cursor.execute("""
            SELECT tablename, 
                   pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        tables = cursor.fetchall()

        self.stdout.write(
            colored('\nPostgreSQL Tables\n', 'cyan', attrs=['bold']))
        self.stdout.write('=' * 60)

        header = f"{'Table Name':<40} {'Size':<15}"
        self.stdout.write(colored(header, 'yellow', attrs=['bold']))
        self.stdout.write('-' * 60)

        for table_name, size in tables:
            row = f"{table_name:<40} {size:<15}"
            if 'meter' in table_name.lower():
                self.stdout.write(colored(row, 'green'))
            else:
                self.stdout.write(row)

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f"Total tables: {len(tables)}")

    def describe_table(self, cursor, table_name, output_format):
        """Describe a specific table"""
        if output_format == 'sql':
            self.show_create_table(cursor, table_name)
        elif output_format == 'django':
            self.show_django_model(cursor, table_name)
        else:
            self.show_table_info(cursor, table_name)

    def show_table_info(self, cursor, table_name):
        """Show detailed table information"""
        # Get table schema
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default,
                ordinal_position
            FROM information_schema.columns 
            WHERE table_name = %s 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """, [table_name])

        columns = cursor.fetchall()

        # Get indexes
        cursor.execute("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE tablename = %s 
            AND schemaname = 'public'
        """, [table_name])

        indexes = cursor.fetchall()

        # Get constraints
        cursor.execute("""
            SELECT 
                constraint_name,
                constraint_type
            FROM information_schema.table_constraints 
            WHERE table_name = %s 
            AND table_schema = 'public'
        """, [table_name])

        constraints = cursor.fetchall()

        self.stdout.write(
            colored(f'\nTable: {table_name}\n', 'cyan', attrs=['bold']))
        self.stdout.write('=' * 80)

        # Column information
        self.stdout.write(colored('\nColumns:', 'yellow', attrs=['bold']))
        header = f"{'Column':<25} {'Type':<20} {'Nullable':<10} {'Default':<20}"
        self.stdout.write(colored(header, 'yellow'))
        self.stdout.write('-' * 80)

        for col in columns:
            column_name, data_type, max_length, is_nullable, default, _ = col

            # Format data type
            if max_length and data_type in ['character varying', 'character']:
                type_str = f"{data_type}({max_length})"
            else:
                type_str = data_type

            nullable = "YES" if is_nullable == 'YES' else "NO"
            default_str = str(default)[:19] if default else ""

            row = f"{column_name:<25} {type_str:<20} {nullable:<10} {default_str:<20}"

            if 'id' in column_name.lower() or column_name.lower() in ['created_at', 'updated_at']:
                self.stdout.write(colored(row, 'blue'))
            else:
                self.stdout.write(row)

        # Indexes
        if indexes:
            self.stdout.write(colored(f'\nIndexes:', 'yellow', attrs=['bold']))
            for index_name, index_def in indexes:
                self.stdout.write(f"  {index_name}: {index_def}")

        # Constraints
        if constraints:
            self.stdout.write(
                colored(f'\nConstraints:', 'yellow', attrs=['bold']))
            for constraint_name, constraint_type in constraints:
                self.stdout.write(f"  {constraint_name}: {constraint_type}")

        self.stdout.write('\n' + '=' * 80)

    def show_create_table(self, cursor, table_name):
        """Show SQL CREATE TABLE statement"""
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length, 
                   is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position
        """, [table_name])

        columns = cursor.fetchall()

        self.stdout.write(f"-- SQL Schema for table: {table_name}")
        self.stdout.write(f"CREATE TABLE {table_name} (")

        column_defs = []
        for col in columns:
            column_name, data_type, max_length, is_nullable, default = col

            # Build column definition
            if max_length and data_type in ['character varying']:
                col_def = f"    {column_name} VARCHAR({max_length})"
            elif data_type == 'integer':
                col_def = f"    {column_name} INTEGER"
            elif data_type == 'bigint':
                col_def = f"    {column_name} BIGINT"
            elif data_type == 'double precision':
                col_def = f"    {column_name} DOUBLE PRECISION"
            elif data_type == 'timestamp with time zone':
                col_def = f"    {column_name} TIMESTAMP WITH TIME ZONE"
            elif data_type == 'boolean':
                col_def = f"    {column_name} BOOLEAN"
            else:
                col_def = f"    {column_name} {data_type.upper()}"

            if is_nullable == 'NO':
                col_def += " NOT NULL"

            if default:
                col_def += f" DEFAULT {default}"

            column_defs.append(col_def)

        self.stdout.write(',\n'.join(column_defs))
        self.stdout.write(");")

    def show_django_model(self, cursor, table_name):
        """Show equivalent Django model"""
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length, 
                   is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position
        """, [table_name])

        columns = cursor.fetchall()

        # Convert table name to model name
        model_name = ''.join(word.capitalize()
                             for word in table_name.replace('meters_', '').split('_'))

        self.stdout.write(f"# Django Model for table: {table_name}")
        self.stdout.write(f"class {model_name}(models.Model):")

        for col in columns:
            column_name, data_type, max_length, is_nullable, default = col

            # Skip Django auto fields
            if column_name == 'id':
                continue

            # Map PostgreSQL types to Django fields
            if data_type == 'character varying':
                field_def = f"models.CharField(max_length={max_length})"
            elif data_type == 'integer':
                field_def = "models.IntegerField()"
            elif data_type == 'bigint':
                field_def = "models.BigIntegerField()"
            elif data_type == 'double precision':
                field_def = "models.FloatField()"
            elif data_type == 'timestamp with time zone':
                if 'created' in column_name:
                    field_def = "models.DateTimeField(auto_now_add=True)"
                elif 'updated' in column_name:
                    field_def = "models.DateTimeField(auto_now=True)"
                else:
                    field_def = "models.DateTimeField()"
            elif data_type == 'boolean':
                field_def = "models.BooleanField()"
            else:
                field_def = f"models.TextField()  # {data_type}"

            # Add nullable parameter
            if is_nullable == 'YES' and 'auto_now' not in field_def:
                field_def = field_def.replace(')', ', null=True, blank=True)')

            self.stdout.write(f"    {column_name} = {field_def}")

    def suggest_tables(self, cursor, partial_name):
        """Suggest similar table names"""
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name ILIKE %s
        """, [f"%{partial_name}%"])

        suggestions = cursor.fetchall()

        if suggestions:
            self.stdout.write(
                colored('\nDid you mean one of these tables?', 'yellow'))
            for suggestion in suggestions:
                self.stdout.write(f"  - {suggestion[0]}")
