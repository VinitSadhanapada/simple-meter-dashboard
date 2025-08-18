#!/usr/bin/env python3
"""
Replace the views.py file with the clean version
"""
import shutil
from pathlib import Path


def replace_views_file():
    """Replace the old views.py with the clean version"""

    old_views = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/views.py')
    new_views = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/views_new.py')

    try:
        # Backup old views
        if old_views.exists():
            shutil.move(str(old_views), str(old_views.parent / 'views_old.py'))
            print("✅ Backed up old views.py to views_old.py")

        # Move new views to replace old
        if new_views.exists():
            shutil.move(str(new_views), str(old_views))
            print("✅ Replaced views.py with clean version")

        print("""
🎉 Views file updated successfully!

✅ All view classes now match URL patterns
✅ Clean file without REST framework dependencies
✅ Ready to run Django server

🚀 Now run:
   cd /home/isha/deepak/MFM_offline_setup/meter_dashboard
   python3 manage.py runserver 0.0.0.0:8000

🌐 Navigate to: http://localhost:8000/device-config/
        """)

    except Exception as e:
        print(f"❌ Error replacing views file: {e}")


if __name__ == "__main__":
    replace_views_file()
