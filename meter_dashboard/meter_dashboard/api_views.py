from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def set_failure_mode(request):
    if request.method == 'POST':
        import json, os
        data = json.loads(request.body.decode('utf-8'))
        meter_name = data.get('meter_name')
        mode = data.get('mode', 'none')
        # Store all meter failure modes in a single file
        mode_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '../iot_scripts/failure_modes.json')
        # Read existing modes
        try:
            with open(mode_path, 'r') as f:
                all_modes = json.load(f)
        except Exception:
            all_modes = {}
        # Update the mode for this meter
        if meter_name:
            all_modes[meter_name] = mode
            with open(mode_path, 'w') as f:
                json.dump(all_modes, f)
            return JsonResponse({'status': 'ok', 'meter_name': meter_name, 'mode': mode})
        else:
            return JsonResponse({'error': 'meter_name required'}, status=400)
    return JsonResponse({'error': 'POST required'}, status=400)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import psycopg2
import json
import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
def _safe_fetch_recent_alert_events(device_id=None, limit=100):
    """Attempt to import and call Redis-backed alert fetcher; fall back to empty list on any error."""
    try:
        import os, sys
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        if base_dir not in sys.path:
            sys.path.append(base_dir)
        from iot_scripts.alerting.celery_alert_tasks import fetch_recent_alert_events as _fetch
        return _fetch(device_id=device_id, limit=limit)
    except Exception:
        return []
import math

@csrf_exempt
def api_root(request):

    # Get all readings for the latest timestamp (synchronized cycle for all meters)
    latest_readings = []
    from django.conf import settings
    db_settings = settings.DATABASES['default']
    try:
        conn = psycopg2.connect(
            dbname=db_settings['NAME'],
            user=db_settings['USER'],
            password=db_settings['PASSWORD'],
            host=db_settings['HOST'],
            port=db_settings['PORT']
        )
        cur = conn.cursor()
        # Return the latest reading for each meter (previous logic)
        cur.execute("""
            SELECT DISTINCT ON (meter_name) *
            FROM meter_readings
            ORDER BY meter_name, time DESC
        """)
        colnames = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        for row in rows:
            latest_readings.append(dict(zip(colnames, row)))
        cur.close()
        conn.close()
    except Exception as e:
        latest_readings = []

    # Get current alerts from file
    alert_state_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '../iot_scripts/current_alerts.json')
    try:
        with open(alert_state_path, 'r') as f:
            alert_state = json.load(f)
    except Exception:
        alert_state = {'active_alerts': [], 'timestamp': None}

    return JsonResponse({
        'latest_readings': latest_readings,
        'alert_state': alert_state
    })


# New API endpoint for alert events from Redis
def api_alert_events(request):
    device_id = request.GET.get('device_id')
    limit = int(request.GET.get('limit', 100))
    events = _safe_fetch_recent_alert_events(device_id=device_id, limit=limit)
    return JsonResponse({'events': events})


# Geomap-ready aggregation of active alert devices
def api_alerts_geomap(request):
    try:
        # 1) Pull recent alert events and compute active status per device
        events = _safe_fetch_recent_alert_events(limit=1000)
        last_by_key = {}
        for e in events:
            # Normalize device_id to string for consistent dict keys
            did = str(e.get('device_id')) if e.get('device_id') is not None else None
            param = e.get('param')
            if did is None or not param:
                continue
            last_by_key[(did, param)] = e

        active_params_by_device = {}
        last_ts_by_device = {}
        for (did, param), e in last_by_key.items():
            if e.get('alert_type') != 'recovered':
                active_params_by_device.setdefault(did, set()).add(param)
                # Track latest timestamp per device for tooltip
                ts = e.get('ts') or e.get('timestamp')
                last_ts_by_device[did] = ts

        # 2) Build device_id -> meter_name mapping from DB
        dev_to_meter = {}
        from django.conf import settings
        db_settings = settings.DATABASES['default']
        try:
            conn = psycopg2.connect(
                dbname=db_settings['NAME'],
                user=db_settings['USER'],
                password=db_settings['PASSWORD'],
                host=db_settings['HOST'],
                port=db_settings['PORT']
            )
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT ON (device_id) device_id, meter_name
                FROM meter_readings
                WHERE device_id IS NOT NULL
                ORDER BY device_id, time DESC
            """)
            for row in cur.fetchall():
                did, mname = row
                if did is not None and mname:
                    dev_to_meter[str(did)] = mname
            cur.close(); conn.close()
        except Exception:
            pass

        # 3) Determine full meter list from existing readings (no migrations needed)
        meter_list = []  # list of (meter_name, device_id or None)
        meter_to_dev = {}
        from django.conf import settings
        db_settings = settings.DATABASES['default']
        try:
            conn = psycopg2.connect(
                dbname=db_settings['NAME'],
                user=db_settings['USER'],
                password=db_settings['PASSWORD'],
                host=db_settings['HOST'],
                port=db_settings['PORT']
            )
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT ON (meter_name) meter_name, device_id
                FROM meter_readings
                WHERE meter_name IS NOT NULL
                ORDER BY meter_name, time DESC
            """)
            for row in cur.fetchall():
                mname, did = row
                meter_list.append((mname, did))
                if did is not None:
                    meter_to_dev[mname] = str(did)
            cur.close(); conn.close()
        except Exception:
            # If DB fails, fall back to devices present in alert events
            for did, mname in dev_to_meter.items():
                meter_list.append((mname, did))
                meter_to_dev[mname] = str(did)

        # Fallback if still empty
        if not meter_list:
            # As a last resort, synthesize from active alerts only
            for did in sorted(active_params_by_device.keys()):
                meter_list.append((dev_to_meter.get(did, f"Device {did}"), did))

        # 4) Prepare markers with synthetic circle layout for all meters
        center_lat = float(request.GET.get('center_lat', 10.975588))
        center_lon = float(request.GET.get('center_lon', 76.737517))
        radius = float(request.GET.get('radius', 0.01))

        # Sort meters alphabetically by name for stable layout
        meter_list.sort(key=lambda t: t[0] or '')
        n = max(len(meter_list), 1)

        markers = []
        for idx, (mname, did_val) in enumerate(meter_list):
            angle = 2 * math.pi * (idx / n)
            lat = center_lat + radius * math.sin(angle)
            lon = center_lon + radius * math.cos(angle)
            # Normalize device id string
            did_str = str(did_val) if did_val is not None else meter_to_dev.get(mname)
            meter_name = mname or dev_to_meter.get(did_str, f"Device {did_str}")
            params = sorted(list(active_params_by_device.get(did_str, []))) if did_str else []
            markers.append({
                'device_id': did_str,
                'meter_name': meter_name,
                'active': True if params else False,
                'alert_params': params,
                'last_event_ts': last_ts_by_device.get(did_str) if did_str else None,
                'latitude': lat,
                'longitude': lon,
                'source': 'synthetic',
            })

        return JsonResponse({'markers': markers, 'count': len(markers)})
    except Exception as e:
        return JsonResponse({'markers': [], 'error': str(e)}, status=500)
