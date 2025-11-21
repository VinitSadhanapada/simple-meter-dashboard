from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import paramiko
import json
from device_config.models import MeterDevice, RaspberryPi
import shlex

@csrf_exempt

def ssh_command_view(request):
    """
    Execute an SSH command on the RaspberryPi linked to a given meter or directly by pi_id.
    Request JSON: { meter_id: int, command: str } OR { pi_id: int, command: str }
    Uses RaspberryPi.ssh_username, ssh_key_path (if configured) or ssh_password.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    meter_id = data.get('meter_id')
    pi_id = data.get('pi_id')
    command = data.get('command')
    if not command or (not meter_id and not pi_id):
        return JsonResponse({'error': 'pi_id or meter_id and command are required'}, status=400)

    pi = None
    if meter_id:
        try:
            meter = MeterDevice.objects.select_related('raspberry_pi').get(id=meter_id)
            pi = meter.raspberry_pi
        except MeterDevice.DoesNotExist:
            return JsonResponse({'error': 'Meter not found'}, status=404)
    elif pi_id:
        try:
            pi = RaspberryPi.objects.get(id=pi_id)
        except RaspberryPi.DoesNotExist:
            return JsonResponse({'error': 'Pi not found'}, status=404)

    if not pi:
        return JsonResponse({'error': 'No Pi found for SSH'}, status=404)

    hostname = pi.pi_ip
    username = pi.ssh_username or 'pi'
    key_path = pi.ssh_key_path if getattr(pi, 'ssh_key_configured', False) else ''
    password = pi.ssh_password or None

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if key_path:
            try:
                pkey = paramiko.RSAKey.from_private_key_file(key_path)
            except Exception:
                pkey = None
        else:
            pkey = None

        ssh.connect(hostname, username=username, password=password if not pkey else None, pkey=pkey, port=pi.ssh_port, timeout=10)

        # Handle preset command sequences safely
        if command.startswith('__RUN_PRESET__:'):
            preset = command.split(':', 1)[1].strip()
            sequences = {
                'basic_setup': [
                    'uname -a',
                    'python3 --version',
                    'pip3 --version',
                    'df -h',
                    'free -h',
                ],
                'bringup': [
                    'bash -lc "echo ==== STEP 1/6: Ensure logs directory ===="',
                    # Ensure logs dir
                    'bash -lc "mkdir -p /home/pi/logs"',
                    'bash -lc "echo ==== STEP 2/6: Start Mosquitto (MQTT broker) ===="',
                    # Start MQTT broker (mosquitto)
                    'bash -lc "(sudo -n systemctl start mosquitto || sudo -n service mosquitto start || true) && systemctl is-active mosquitto || true"',
                    'bash -lc "echo ==== STEP 3/6: Start PostgreSQL ===="',
                    # Start PostgreSQL
                    'bash -lc "(sudo -n systemctl start postgresql || sudo -n service postgresql start || true) && systemctl is-active postgresql || true"',
                    'bash -lc "echo ==== STEP 4/6: Start Redis ===="',
                    # Start Redis
                    'bash -lc "(sudo -n systemctl start redis-server || sudo -n service redis-server start || redis-server --daemonize yes || true) && (systemctl is-active redis-server || true)"',
                    'bash -lc "echo ==== STEP 5/6: Start Celery worker and Ingestion ===="',
                    # Start Celery worker (background)
                    'bash -lc "cd /home/pi/Desktop/simple-meter-dashboard/meter_dashboard && /home/pi/Desktop/simple-meter-dashboard/venv/bin/celery -A meter_dashboard worker -l info > /home/pi/logs/celery_worker.log 2>&1 & echo CELERY_WORKER_PID:$!"',
                    # Start MQTT→DB ingestion (background)
                    'bash -lc "/home/pi/Desktop/simple-meter-dashboard/venv/bin/python /home/pi/Desktop/simple-meter-dashboard/iot_scripts/mqtt_to_db_ingest.py > /home/pi/logs/ingest.log 2>&1 & echo INGEST_PID:$!"',
                    'bash -lc "echo ==== STEP 6/6: Start Offline Dashboard ===="',
                    # Offline dashboard runner using offline_rpi_dashboard_db.py (no debug script)
                    'bash -lc "if [ -f /home/pi/Desktop/simple-meter-dashboard/iot_scripts/offline_rpi_dashboard_db.py ]; then /home/pi/Desktop/simple-meter-dashboard/venv/bin/python /home/pi/Desktop/simple-meter-dashboard/iot_scripts/offline_rpi_dashboard_db.py --run > /home/pi/logs/offline_rpi_dashboard_db.log 2>&1 & echo OFFLINE_DB_PID:$!; else echo \"offline_rpi_dashboard_db.py not found, skipping\"; fi"',
                    'bash -lc "echo ==== Bringup complete ===="',
                ],
                'status': [
                    # Service states
                    'bash -lc "(systemctl is-active --quiet mosquitto && echo MOSQUITTO:active) || (service mosquitto status >/dev/null 2>&1 && echo MOSQUITTO:active) || echo MOSQUITTO:inactive"',
                    'bash -lc "(systemctl is-active --quiet postgresql && echo POSTGRESQL:active) || (service postgresql status >/dev/null 2>&1 && echo POSTGRESQL:active) || echo POSTGRESQL:inactive"',
                    'bash -lc "(systemctl is-active --quiet redis-server && echo REDIS:active) || (service redis-server status >/dev/null 2>&1 && echo REDIS:active) || echo REDIS:inactive"',
                    # Running PIDs (space-separated)
                    'bash -lc "CEL=$(pgrep -f \"celery -A meter_dashboard worker\" | paste -sd\' \" \" - 2>/dev/null); [ -n \"$CEL\" ] && echo \"Celery PIDs: $CEL\" || echo \"Celery: not running\""',
                    'bash -lc "ING=$(pgrep -f mqtt_to_db_ingest.py | paste -sd\' \" \" - 2>/dev/null); [ -n \"$ING\" ] && echo \"Ingest PIDs: $ING\" || echo \"Ingest: not running\""',
                    'bash -lc "OFF=$(pgrep -f offline_rpi_dashboard_db.py | paste -sd\' \" \" - 2>/dev/null); [ -n \"$OFF\" ] && echo \"Offline DB PIDs: $OFF\" || echo \"Offline DB: not running\""',
                ],
                'stop': [
                    # Stop Celery worker
                    'bash -lc "pkill -f \"celery -A meter_dashboard worker\" || true; sleep 1; pgrep -f \"celery -A meter_dashboard worker\" >/dev/null 2>&1 && echo \"Celery: still running\" || echo \"Celery: stopped\""',
                    # Stop ingestion
                    'bash -lc "pkill -f mqtt_to_db_ingest.py || true; sleep 1; pgrep -f mqtt_to_db_ingest.py >/dev/null 2>&1 && echo \"Ingest: still running\" || echo \"Ingest: stopped\""',
                    # Stop offline dashboard db runner
                    'bash -lc "pkill -f offline_rpi_dashboard_db.py || true; sleep 1; pgrep -f offline_rpi_dashboard_db.py >/dev/null 2>&1 && echo \"Offline DB: still running\" || echo \"Offline DB: stopped\""',
                ],
            }
            cmds = sequences.get(preset)
            if not cmds:
                ssh.close()
                return JsonResponse({'error': f'Unknown preset: {preset}'}, status=400)
            combined_out = []
            for c in cmds:
                stdin, stdout, stderr = ssh.exec_command(c)
                out = stdout.read().decode('utf-8')
                err = stderr.read().decode('utf-8')
                err_text = f"\nERR: {err}" if err else ""
                combined_out.append(f"$ {c}\n{out}{err_text}")
            ssh.close()
            return JsonResponse({'output': '\n'.join(combined_out)})
        else:
            # Single ad-hoc command
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            ssh.close()
            return JsonResponse({'output': output, 'error': error})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
