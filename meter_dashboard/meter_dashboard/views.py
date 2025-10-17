from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def api_live_page(request):
    return render(request, "api_live.html", {"page_title": "Live Meter API"})
from django.shortcuts import render
from device_config.models import MeterDevice
from django.utils import timezone
import os, sys

# ...existing code...


def main_dashboard(request):
    page_title = "Meter Dashboard"
    # Fetch meters, available_modes, failure_modes as needed
    meters = MeterDevice.objects.all()  # Example, adjust as needed
    available_modes = ["Normal", "Failure"]  # Example, adjust as needed
    failure_modes = {}  # Example, adjust as needed
    context = {
        "page_title": page_title,
        "meters": meters,
        "available_modes": available_modes,
        "failure_modes": failure_modes,
    }
    return render(request, "dashboard.html", context)
# ...existing code...


def _import_fetch_events():
    # Ensure repo root on sys.path so iot_scripts is importable when running server from different cwd
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        if base_dir not in sys.path:
            sys.path.append(base_dir)
    except Exception:
        pass
    try:
        from iot_scripts.alerting.celery_alert_tasks import fetch_recent_alert_events
        return fetch_recent_alert_events
    except Exception:
        # Fallback no-op
        def _empty(device_id=None, limit=100):
            return []
        return _empty


def alerts_dashboard(request):
    fetch_recent_alert_events = _import_fetch_events()
    device_id = request.GET.get('device_id')
    limit = int(request.GET.get('limit', '200'))
    events = fetch_recent_alert_events(device_id=device_id, limit=limit)
    # Derive simple active alerts: device_id -> list of (param, alert_type, value)
    active = {}
    for e in events:
        did = str(e.get('device_id'))
        at = e.get('alert_type')
        if at == 'recovered':
            if did in active and e.get('param'):
                active[did] = [t for t in active[did] if t[0] != e.get('param')]
                if not active[did]:
                    active.pop(did, None)
            continue
        active.setdefault(did, [])
        active[did] = [t for t in active[did] if t[0] != e.get('param')]
        active[did].append((e.get('param'), at, e.get('value')))

    context = {
        'events': events,
        'active_alerts': active,
        'now_ts': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    return render(request, 'alerts/alerts_dashboard.html', context)
