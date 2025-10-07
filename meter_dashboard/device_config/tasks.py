from celery import shared_task
import os
from django.utils import timezone
from .models import OTADeployment


@shared_task(time_limit=3600)  # 1 hour timeout in seconds
def run_ota_deployment(ota_id):
    ota = OTADeployment.objects.get(id=ota_id)
    pi = ota.raspberry_pi
    excludes = []
    if ota.exclude_file and os.path.exists(ota.exclude_file):
        with open(ota.exclude_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    excludes.append(f"--exclude={line}")
    exclude_str = " ".join(excludes)
    source_dir = ota.source_dir.rstrip('/')
    dest_dir = pi.config_path.rstrip('/')
    mkdir_cmd = (
        f"sshpass -p '{pi.ssh_password}' "
        f"ssh -p {pi.ssh_port} -o StrictHostKeyChecking=no "
        f"{pi.ssh_username}@{pi.pi_ip} 'mkdir -p {dest_dir}'"
    )
    os.system(mkdir_cmd)
    rsync_cmd = (
        f"sshpass -p '{pi.ssh_password}' "
        f"rsync -avz --delete -e \"ssh -p {pi.ssh_port} -o StrictHostKeyChecking=no\" "
        f"{exclude_str} {source_dir}/ {pi.ssh_username}@{pi.pi_ip}:{dest_dir}/"
    )
    result = os.system(rsync_cmd)
    ota.completed_at = timezone.now()
    if result == 0:
        ota.status = 'SUCCESS'
        ota.result_message = 'Deployment successful'
    else:
        ota.status = 'FAILED'
        ota.result_message = f'rsync failed with code {result}'
    ota.save()
