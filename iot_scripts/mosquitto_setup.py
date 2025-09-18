import subprocess
import os

def update_mosquitto_config():
    config_path = '/etc/mosquitto/conf.d/default.conf'
    config_lines = [
        'allow_anonymous false\n',
        'password_file /etc/mosquitto/passwd\n'
    ]
    try:
        # Check if config file exists
        rewrite_needed = True
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                existing = f.read().strip()
            # Check if config matches exactly
            expected = ''.join(config_lines).strip()
            if existing == expected:
                rewrite_needed = False
        if rewrite_needed:
            with open(config_path, 'w') as f:
                f.writelines(config_lines)
            print(f"✅ Mosquitto config replaced at {config_path}")
        else:
            print(f"✅ Mosquitto config already correct at {config_path}")
    except Exception as e:
        print(f"❌ Error updating Mosquitto config: {e}")

def setup_mosquitto():
    print("Starting and enabling Mosquitto service...")
    subprocess.run(['sudo', 'systemctl', 'start', 'mosquitto'])
    subprocess.run(['sudo', 'systemctl', 'enable', 'mosquitto'])
    print("Checking Mosquitto service status...")
    subprocess.run(['sudo', 'systemctl', 'status', 'mosquitto', '--no-pager'])
    update_mosquitto_config()

if __name__ == "__main__":
    setup_mosquitto()
