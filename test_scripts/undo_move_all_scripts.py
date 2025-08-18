import os
from pathlib import Path

base = Path(__file__).parent
scripts_dir = base / 'test_scripts'

# List of files to move back
files_to_move = [
    'elmeasure_LG5220.py',
    'deploy_ssh_functionality.py',
    'elmeasure_EN8410.py',
    'mqtt_client.py',
    'check_and_install_ensure_pip_and_python.env.py',
    'add_missing_functions.py',
    'test_db_connection.py',
    'DB_readings.py',
    'fix_django_syntax.py',
    'fix_url_references.py',
    'fix_django_apps.py',
    'live_console_monitor.py',
    'elmeasure_iELR300.py',
    'fix_dcms_table.py',
    'venv_utils.py',
    'create_complete_device_views.py',
    'api_improvements.py',
    'rtc_new.py',
    'quick_fix_dcms.py',
    'pi_registration_fix.py',
    'copy_exact_dcms_frontend.py',
    'elmeasure_LG5310.py',
    'fix_script_structure.py',
    'setup_dcms_compatibility.py',
    'simple_db_setup.py',
    'advanced_features.py',
    'offline_rpi_dashboard_db.py',
    'enhanced_models.py',
    'check_main_structure.py',
    'clean_duplicates.py',
    'fix_django_setup.py',
    'setup_device_config_system.py',
    'copy_dcms_templates.py',
    'fix_method_calls.py',
    'offline_rpi_dashboard.py',
    'fix_main_script.py',
    'add_missing_dcms_functionality.py',
    'security_monitoring.py',
    'usb_csv_auto_copy.py',
    'offline_rpi_dashboard_debug.py',
    'organize_scripts.py',
    'macros.py',
    'meter_device.py',
    'create_device_config_templates.py',
    'test_pgadmin_connection.py',
    'postgres_helper.py',
    'check_meter_methods.py',
    'fix_table_columns.py',
    'elmeasure_LG6400.py',
    'meter_manager.py',
    'diagnose_simulation.py',
    'check_meter_manager.py',
    'replace_views.py',
    'fix_dcms_urls.py',
    'create_device_config_views.py',
]

for fname in files_to_move:
    src = scripts_dir / fname
    dst = base / fname
    if src.exists():
        src.rename(dst)
        print(f"Moved back: {fname}")
    else:
        print(f"Not found in test_scripts: {fname}")

print("All listed scripts have been moved back to the main directory.")
