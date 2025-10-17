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
from iot_scripts.alerting.celery_alert_tasks import fetch_recent_alert_events

@csrf_exempt
def api_root(request):

    # Get all readings for the latest timestamp (synchronized cycle for all meters)
    latest_readings = []
    try:
        conn = psycopg2.connect(dbname='mfmdb', user='mfmuser', password='devi', host='localhost', port='5432')
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
    events = fetch_recent_alert_events(device_id=device_id, limit=limit)
    return JsonResponse({'events': events})
