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


# Command Centre: Meter Health Status API
@csrf_exempt
def api_command_centre_health(request):
    """
    Returns health status for all meters with threshold-based fault detection.
    
    Response format:
    {
        "meters": [
            {
                "meter_name": "SnakeSideTower",
                "meter_identifier": "elm_serial_no_1",
                "location_name": "Drishti",
                "latitude": 10.981210,
                "longitude": 76.733467,
                "gateway_ip": "192.168.112.71",
                "last_reading_time": "2026-01-02T12:45:30",
                "health_status": "ok" | "warning" | "critical" | "offline",
                "faults": [
                    {"parameter": "v_r_ph", "value": 185.5, "issue": "V_R too low: 185.5V (min 200V)"},
                    ...
                ],
                "readings": {
                    "v_r_ph": 225.3, "v_y_ph": 228.1, "v_b_ph": 230.2,
                    "a_r_ph": 12.5, "a_y_ph": 13.2, "a_b_ph": 11.8,
                    "frequency": 50.1, "watts_total": 8500, ...
                }
            },
            ...
        ],
        "summary": {
            "total": 8,
            "ok": 5,
            "warning": 1,
            "critical": 1,
            "offline": 1
        }
    }
    """
    
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    # Thresholds (matching meter_threshold_alerts.py)
    THRESHOLDS = {
        'voltage_min': 200.0,
        'voltage_max': 250.0,
        'current_min': 0.1,
        'frequency_min': 49.5,
        'frequency_max': 50.5,
    }
    
    VOLTAGE_PHASES = ['v_r_ph', 'v_y_ph', 'v_b_ph']
    CURRENT_PHASES = ['a_r_ph', 'a_y_ph', 'a_b_ph']
    PHASE_LABELS = {
        'v_r_ph': 'V_R', 'v_y_ph': 'V_Y', 'v_b_ph': 'V_B',
        'a_r_ph': 'I_R', 'a_y_ph': 'I_Y', 'a_b_ph': 'I_B'
    }
    
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
        
        # Get latest readings with GPS coordinates from device_config_meterdevice
        cur.execute("""
            WITH latest_readings AS (
                SELECT DISTINCT ON (meter_name) 
                    meter_name,
                    time,
                    v_r_ph, v_y_ph, v_b_ph,
                    a_r_ph, a_y_ph, a_b_ph,
                    frequency,
                    watts_total, watts_r_ph, watts_y_ph, watts_b_ph,
                    pf_ave, pf_r_ph, pf_y_ph, pf_b_ph,
                    vln_average,
                    a_average
                FROM meter_readings
                WHERE meter_name IS NOT NULL
                ORDER BY meter_name, time DESC
            )
            SELECT 
                lr.*,
                dcm.meter_model,
                rpi.location as location_name,
                dcm.latitude,
                dcm.longitude,
                rpi.pi_name as gateway_name,
                rpi.pi_ip as gateway_ip
            FROM latest_readings lr
            LEFT JOIN device_config_meterdevice dcm ON lr.meter_name = dcm.meter_name
            LEFT JOIN device_config_raspberrypi rpi ON dcm.raspberry_pi_id = rpi.id
            ORDER BY lr.meter_name
        """)
        
        colnames = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        meters = []
        summary = {'total': 0, 'ok': 0, 'warning': 0, 'critical': 0, 'offline': 0}
        
        from datetime import datetime, timedelta
        now = datetime.now()
        
        for row in rows:
            data = dict(zip(colnames, row))
            meter_name = data.get('meter_name')
            last_reading_time = data.get('time')
            
            # Check if meter is offline (no data in last 15 minutes)
            is_offline = False
            if last_reading_time:
                time_diff = now - last_reading_time
                is_offline = time_diff > timedelta(minutes=15)
            else:
                is_offline = True
            
            # Initialize fault detection
            faults = []
            
            if not is_offline:
                # Check voltage phases
                for phase in VOLTAGE_PHASES:
                    value = data.get(phase)
                    if value is not None:
                        abs_value = abs(value)
                        if abs_value < THRESHOLDS['voltage_min']:
                            faults.append({
                                'parameter': phase,
                                'value': abs_value,
                                'issue': f"{PHASE_LABELS[phase]} too low: {abs_value:.1f}V (min {THRESHOLDS['voltage_min']}V)",
                                'severity': 'critical'
                            })
                        elif abs_value > THRESHOLDS['voltage_max']:
                            faults.append({
                                'parameter': phase,
                                'value': abs_value,
                                'issue': f"{PHASE_LABELS[phase]} too high: {abs_value:.1f}V (max {THRESHOLDS['voltage_max']}V)",
                                'severity': 'critical'
                            })
                        elif abs_value < 1.0:
                            faults.append({
                                'parameter': phase,
                                'value': abs_value,
                                'issue': f"{PHASE_LABELS[phase]} near zero: {abs_value:.2f}V",
                                'severity': 'critical'
                            })
                
                # Check current phases
                for phase in CURRENT_PHASES:
                    value = data.get(phase)
                    if value is not None:
                        abs_value = abs(value)
                        if abs_value < THRESHOLDS['current_min']:
                            faults.append({
                                'parameter': phase,
                                'value': abs_value,
                                'issue': f"{PHASE_LABELS[phase]} near zero: {abs_value:.3f}A (min {THRESHOLDS['current_min']}A)",
                                'severity': 'warning'
                            })
                
                # Check frequency
                freq = data.get('frequency')
                if freq is not None:
                    if freq < THRESHOLDS['frequency_min']:
                        faults.append({
                            'parameter': 'frequency',
                            'value': freq,
                            'issue': f"Frequency too low: {freq:.2f}Hz (min {THRESHOLDS['frequency_min']}Hz)",
                            'severity': 'critical'
                        })
                    elif freq > THRESHOLDS['frequency_max']:
                        faults.append({
                            'parameter': 'frequency',
                            'value': freq,
                            'issue': f"Frequency too high: {freq:.2f}Hz (max {THRESHOLDS['frequency_max']}Hz)",
                            'severity': 'critical'
                        })
                    elif freq < 1.0:
                        faults.append({
                            'parameter': 'frequency',
                            'value': freq,
                            'issue': f"Frequency near zero: {freq:.2f}Hz",
                            'severity': 'critical'
                        })
            
            # Determine overall health status
            if is_offline:
                health_status = 'offline'
            elif not faults:
                health_status = 'ok'
            elif any(f['severity'] == 'critical' for f in faults):
                health_status = 'critical'
            else:
                health_status = 'warning'
            
            # Build meter object
            meter_obj = {
                'meter_name': meter_name,
                'meter_identifier': data.get('meter_identifier'),
                'location_name': data.get('location_name'),
                'latitude': float(data['latitude']) if data.get('latitude') else None,
                'longitude': float(data['longitude']) if data.get('longitude') else None,
                'gateway_name': data.get('gateway_name'),
                'gateway_ip': str(data['gateway_ip']) if data.get('gateway_ip') else None,
                'last_reading_time': last_reading_time.isoformat() if last_reading_time else None,
                'health_status': health_status,
                'faults': faults,
                'readings': {
                    'v_r_ph': data.get('v_r_ph'),
                    'v_y_ph': data.get('v_y_ph'),
                    'v_b_ph': data.get('v_b_ph'),
                    'a_r_ph': data.get('a_r_ph'),
                    'a_y_ph': data.get('a_y_ph'),
                    'a_b_ph': data.get('a_b_ph'),
                    'frequency': data.get('frequency'),
                    'watts_total': data.get('watts_total'),
                    'watts_r_ph': data.get('watts_r_ph'),
                    'watts_y_ph': data.get('watts_y_ph'),
                    'watts_b_ph': data.get('watts_b_ph'),
                    'pf_ave': data.get('pf_ave'),
                    'vln_average': data.get('vln_average'),
                    'a_average': data.get('a_average'),
                }
            }
            
            meters.append(meter_obj)
            summary['total'] += 1
            summary[health_status] += 1
        
        response = JsonResponse({
            'meters': meters,
            'summary': summary,
            'thresholds': THRESHOLDS,
            'timestamp': now.isoformat()
        })
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
        
    except Exception as e:
        import traceback
        response = JsonResponse({
            'meters': [],
            'summary': {'total': 0, 'ok': 0, 'warning': 0, 'critical': 0, 'offline': 0},
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
        response['Access-Control-Allow-Origin'] = '*'
        return response


@csrf_exempt
def api_update_meter_gis(request):
    """
    Update GPS coordinates for a meter in device_config_meterdevice table.
    
    POST body:
    {
        "meter_name": "20_WAY_UPS_DB_2",
        "latitude": 10.981210,
        "longitude": 76.733467,
        "location_name": "Drishti",  // Optional - updates Pi location
        "gateway_ip": "192.168.112.71"  // Ignored - Pi IP is managed separately
    }
    """
    
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    if request.method != 'POST':
        response = JsonResponse({'error': 'POST method required'}, status=405)
        response['Access-Control-Allow-Origin'] = '*'
        return response
    
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        response = JsonResponse({'error': 'Invalid JSON'}, status=400)
        response['Access-Control-Allow-Origin'] = '*'
        return response
    
    meter_name = data.get('meter_name')
    if not meter_name:
        response = JsonResponse({'error': 'meter_name is required'}, status=400)
        response['Access-Control-Allow-Origin'] = '*'
        return response
    
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    # Validate coordinates
    if latitude is not None:
        try:
            latitude = float(latitude)
            if latitude < -90 or latitude > 90:
                raise ValueError("Latitude must be between -90 and 90")
        except (TypeError, ValueError) as e:
            response = JsonResponse({'error': f'Invalid latitude: {e}'}, status=400)
            response['Access-Control-Allow-Origin'] = '*'
            return response
    
    if longitude is not None:
        try:
            longitude = float(longitude)
            if longitude < -180 or longitude > 180:
                raise ValueError("Longitude must be between -180 and 180")
        except (TypeError, ValueError) as e:
            response = JsonResponse({'error': f'Invalid longitude: {e}'}, status=400)
            response['Access-Control-Allow-Origin'] = '*'
            return response
    
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
        
        # Check if meter exists in device_config_meterdevice
        cur.execute("""
            SELECT id FROM device_config_meterdevice WHERE meter_name = %s
        """, (meter_name,))
        existing = cur.fetchone()
        
        if not existing:
            response = JsonResponse({'error': f'Meter {meter_name} not found in device configuration'}, status=404)
            response['Access-Control-Allow-Origin'] = '*'
            cur.close()
            conn.close()
            return response
        
        # Update GPS coordinates
        update_fields = []
        update_values = []
        
        if latitude is not None:
            update_fields.append("latitude = %s")
            update_values.append(latitude)
        if longitude is not None:
            update_fields.append("longitude = %s")
            update_values.append(longitude)
        
        if update_fields:
            update_values.append(meter_name)
            cur.execute(f"""
                UPDATE device_config_meterdevice
                SET {', '.join(update_fields)}
                WHERE meter_name = %s
            """, update_values)
        
        conn.commit()
        cur.close()
        conn.close()
        
        response = JsonResponse({
            'success': True,
            'action': 'updated',
            'meter_name': meter_name,
            'latitude': latitude,
            'longitude': longitude,
        })
        response['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        import traceback
        response = JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
        response['Access-Control-Allow-Origin'] = '*'
        return response
