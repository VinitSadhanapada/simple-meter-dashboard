import psycopg2
from django.conf import settings
def latest_readings(request):
    # Use settings or hardcoded DB config
    db_settings = getattr(settings, 'DATABASES', {}).get('default', {})
    conn = psycopg2.connect(
        dbname=db_settings.get('NAME', 'mfmdb'),
        user=db_settings.get('USER', 'mfmuser'),
        password=db_settings.get('PASSWORD', 'devi'),
        host=db_settings.get('HOST', 'localhost'),
        port=db_settings.get('PORT', 5432)
    )
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM meterreadings ORDER BY time DESC LIMIT 10;')
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
    finally:
        cur.close()
        conn.close()
    return render(request, 'meter_readings/latest_readings.html', {
        'columns': columns,
        'rows': rows,
        'page_title': 'Latest Meter Readings'
    })

import psycopg2
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
import json
import os

# Path to the shared failure modes JSON file (project root, absolute path)
FAILURE_MODES_FILE = '/home/pi/Desktop/FinalMerge/clubbed_mfm_16aug/failure_modes.json'

def load_failure_modes():
    try:
        with open(FAILURE_MODES_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_failure_modes(modes):
    try:
        with open(FAILURE_MODES_FILE, 'w') as f:
            json.dump(modes, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Could not write to {FAILURE_MODES_FILE}: {e}")
        raise

def get_meter_list():
    # Load from device_config.json
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'device_config.json')
    try:
        with open(config_path, 'r') as f:
            # Remove comments if any
            lines = [line for line in f if not line.strip().startswith('//')]
            return json.loads(''.join(lines))
    except Exception:
        return []

def dashboard(request):
    meters = get_meter_list()
    failure_modes = load_failure_modes()
    available_modes = ['phase_loss', 'overcurrent', 'bad_pf', 'overvoltage', 'reverse_power', 'freq_drift', None]
    return render(request, 'meter_readings/dashboard.html', {
        'page_title': 'Meter Readings Dashboard',
        'meters': meters,
        'failure_modes': failure_modes,
        'available_modes': available_modes
    })

def api_set_failure_mode(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST only')
    try:
        data = json.loads(request.body.decode('utf-8'))
        meter_name = data['meter_name']
        mode = data['mode']
        modes = load_failure_modes()
        modes[meter_name] = mode
        save_failure_modes(modes)
        return JsonResponse({'status': 'ok', 'meter_name': meter_name, 'mode': mode})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)})
