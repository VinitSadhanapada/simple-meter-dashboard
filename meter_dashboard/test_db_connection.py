#!/usr/bin/env python3
"""
Test Django Database Connection

This script tests your Django database configuration.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meter_dashboard.settings')

try:
    django.setup()
    from django.db import connection
    from django.core.management.color import no_style

    def test_database_connection():
        """Test database connection"""
        print("🔍 Testing Django database connection...")

        try:
            # Test basic connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] == 1:
                    print("✅ Database connection successful!")
                    return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def get_database_info():
        """Get database information"""
        try:
            with connection.cursor() as cursor:
                # Get database name
                cursor.execute("SELECT current_database()")
                db_name = cursor.fetchone()[0]

                # Get PostgreSQL version
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]

                print(f"📊 Database Info:")
                print(f"   Database: {db_name}")
                print(f"   Version: {version}")

                # Get table count
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                table_count = cursor.fetchone()[0]
                print(f"   Tables: {table_count}")

                return True
        except Exception as e:
            print(f"❌ Error getting database info: {e}")
            return False

    def check_django_tables():
        """Check if Django tables exist"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE 'django_%'
                """)
                django_tables = cursor.fetchall()

                if django_tables:
                    print(f"✅ Found {len(django_tables)} Django tables")
                    for table in django_tables:
                        print(f"   - {table[0]}")
                else:
                    print("⚠️ No Django tables found. Run migrations!")
                    print("   python3 manage.py migrate")

                return len(django_tables) > 0
        except Exception as e:
            print(f"❌ Error checking Django tables: {e}")
            return False

    def main():
        print("🧪 Django Database Connection Test")
        print("=" * 50)

        # Test connection
        if not test_database_connection():
            print("\n❌ Database connection failed!")
            print("💡 Check your database settings in settings.py")
            print("💡 Make sure PostgreSQL is running")
            print("💡 Check your .env file credentials")
            return

        # Get database info
        get_database_info()

        # Check Django tables
        check_django_tables()

        print("\n🎉 Database test completed!")
        print("\n💡 Next steps if migrations needed:")
        print("   python3 manage.py makemigrations")
        print("   python3 manage.py migrate")

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"❌ Django setup failed: {e}")
    print("💡 Make sure you're in the Django project directory")
    print("💡 Check your DJANGO_SETTINGS_MODULE")
except Exception as e:
    print(f"❌ Error: {e}")
    print("💡 Check your database configuration")
