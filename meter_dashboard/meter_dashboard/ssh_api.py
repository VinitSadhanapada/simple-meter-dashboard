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
                # Add more named presets as needed
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
