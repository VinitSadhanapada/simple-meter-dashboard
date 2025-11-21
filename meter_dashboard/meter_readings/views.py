import psycopg2
import os
import sys
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.conf import settings


def api_meter_readings(request):
    db_settings = getattr(settings, 'DATABASES', {}).get('default', {})
    conn = None
    cur = None
    rows = []
    columns = []
    try:
        conn = psycopg2.connect(
            dbname=db_settings.get('NAME', 'mfmdb'),
            user=db_settings.get('USER', 'mfmuser'),
            password=db_settings.get('PASSWORD', 'devi'),
            host=db_settings.get('HOST', 'localhost'),
            port=db_settings.get('PORT', 5432)
        )
        cur = conn.cursor()
        try:
            cur.execute('SELECT * FROM meter_readings ORDER BY time DESC LIMIT 10;')
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
        except Exception:
            # Table may not exist yet; return empty result
            rows, columns = [], []
    finally:
        try:
            if cur is not None:
                cur.close()
        finally:
            if conn is not None:
                conn.close()
    # Return as JSON: list of dicts
    data = [dict(zip(columns, row)) for row in rows]
    return JsonResponse({'readings': data})


def _fetch_recent_alert_events(device_id=None, limit=300):
    """Import-safe helper to fetch alert events from Redis via Celery task module."""
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        if base_dir not in sys.path:
            sys.path.append(base_dir)
        from iot_scripts.alerting.celery_alert_tasks import fetch_recent_alert_events
        return fetch_recent_alert_events(device_id=device_id, limit=limit)
    except Exception:
        return []


def latest_readings(request):

    # Show only meters with actual readings
    import psycopg2
    db_settings = getattr(settings, 'DATABASES', {}).get('default', {})
    conn = None
    cur = None
    readings = []
    columns = []
    try:
        conn = psycopg2.connect(
            dbname=db_settings.get('NAME', 'mfmdb'),
            user=db_settings.get('USER', 'mfmuser'),
            password=db_settings.get('PASSWORD', 'devi'),
            host=db_settings.get('HOST', 'localhost'),
            port=db_settings.get('PORT', 5432)
        )
        cur = conn.cursor()
        try:
            cur.execute("SELECT DISTINCT ON (meter_name) * FROM meter_readings ORDER BY meter_name, time DESC;")
            readings = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
        except Exception:
            readings, columns = [], []
    finally:
        try:
            if cur is not None:
                cur.close()
        finally:
            if conn is not None:
                conn.close()
    all_rows = readings
    # Debug after computing all_rows
    try:
        print("DEBUG all_rows:", all_rows)
    except Exception:
        pass

    # Compute active alerts from Redis events (no current_alerts.json)
    events = _fetch_recent_alert_events(limit=500)
    # Determine active devices: last event per (device,param); if not 'recovered' => active
    active_devices = set()
    last_by_key = {}
    for e in events:
        key = (str(e.get('device_id')), e.get('param'))
        last_by_key[key] = e
    for (did, _), e in last_by_key.items():
        if e.get('alert_type') != 'recovered':
            active_devices.add(did)

    # Prepare rows with alert flags for easier templating
    try:
        device_id_index = columns.index('device_id')
    except ValueError:
        device_id_index = None
    rows_aug = []
    for r in all_rows:
        dev_id_val = None
        if device_id_index is not None and len(r) > device_id_index:
            try:
                dev_id_val = str(r[device_id_index])
            except Exception:
                dev_id_val = None
        rows_aug.append({
            'cells': r,
            'has_alert': (dev_id_val in active_devices)
        })

    return render(request, 'meter_readings/latest_readings.html', {
        'columns': columns,
        'rows': all_rows,  # kept for backward compatibility (unused by template now)
        'rows_aug': rows_aug,
        'page_title': 'Latest Readings for All Meters',
        'alert_state': {'active_alerts': {}, 'source': 'redis_events'},
    })


# Path to the shared failure modes JSON file (project-relative, inside iot_scripts)
FAILURE_MODES_FILE = os.path.abspath(os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'iot_scripts', 'failure_modes.json'
))


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
    config_path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(__file__))), 'device_config.json')
    try:
        with open(config_path, 'r') as f:
            # Remove comments if any
            lines = [line for line in f if not line.strip().startswith('//')]
            return json.loads(''.join(lines))
    except Exception:
        return []


def dashboard(request):
    from device_config.models import MeterDevice
    meters = MeterDevice.objects.all()
    failure_modes = load_failure_modes()
    available_modes = ['phase_loss', 'overcurrent', 'bad_pf',
                       'overvoltage', 'reverse_power', 'freq_drift', None]
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
