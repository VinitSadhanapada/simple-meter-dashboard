import os
import shutil
import subprocess
import sys

def detect_user():
    import pwd
    if os.path.isdir("/home/pi"):
        print("[USER DETECT] Using 'pi' because /home/pi exists.")
        return "pi"
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user and sudo_user != "root":
        print(f"[USER DETECT] Using SUDO_USER={sudo_user}")
        return sudo_user
    for var in ("LOGNAME", "USER"):
        val = os.environ.get(var)
        if val and val != "root":
            print(f"[USER DETECT] Using {var}={val}")
            return val
    if os.path.isdir("/home/isha"):
        print("[USER DETECT] Using 'isha' because /home/isha exists.")
        return "isha"
    try:
        home_users = [d for d in os.listdir("/home") if os.path.isdir(os.path.join("/home", d))]
        if home_users:
            print(f"[USER DETECT] Using first user in /home: {home_users[0]}")
            return home_users[0]
    except Exception:
        pass
    try:
        user = pwd.getpwuid(os.getuid()).pw_name
        print(f"[USER DETECT] Using current user id: {user}")
        return user
    except Exception:
        pass
    print("[USER DETECT] Defaulting to 'pi'")
    return "pi"

USER = detect_user()
home_path = os.path.expanduser(f"~{USER}")
if home_path == f"~{USER}" or not os.path.isdir(home_path):
    home_path = f"/home/{USER}"
print(f"[USER DETECT] USER={USER}, home_path={home_path}")

PROJECT_DIR = os.path.join(home_path, "Desktop", "simple-meter-dashboard")
VENV_DIR = os.path.join(PROJECT_DIR, "venv")
REPO_URL = "https://github.com/VinitSadhanapada/simple-meter-dashboard.git"
BRANCH = "feature/device-config-and-rpi-setup"
REQUIREMENTS = [
    "pymodbus==2.5.3",
    "pyserial==3.5",
    "paho-mqtt==2.1.0",
    "termcolor==3.1.0",
    "flask==2.3.3",
    "numpy==1.24.3",
    "pandas==2.0.3"
]

def ensure_venv():
    if not os.path.isdir(PROJECT_DIR):
        os.makedirs(PROJECT_DIR, exist_ok=True)
    if not os.path.isdir(VENV_DIR):
        print(f"[VENV] Creating virtual environment at {VENV_DIR}")
        subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])
    else:
        print(f"[VENV] Virtual environment already exists at {VENV_DIR}")

def robust_clone_or_update():
    if os.path.exists(PROJECT_DIR):
        venv_backup = None
        if os.path.exists(VENV_DIR):
            venv_backup = VENV_DIR + "_backup"
            if os.path.exists(venv_backup):
                shutil.rmtree(venv_backup)
            print(f"[VENV] Backing up virtual environment...")
            shutil.move(VENV_DIR, venv_backup)
        
        # Remove the entire project directory
        print(f"[GIT] Removing existing project directory...")
        shutil.rmtree(PROJECT_DIR)
        
        # Clone fresh to the now-empty location
        print(f"[GIT] Cloning fresh repo to {PROJECT_DIR}")
        subprocess.check_call([
            "git", "clone", "--branch", BRANCH, "--single-branch", REPO_URL, PROJECT_DIR
        ])
        
        # Restore venv
        if venv_backup and os.path.exists(venv_backup):
            print(f"[VENV] Restoring virtual environment...")
            shutil.move(venv_backup, VENV_DIR)
    else:
        print(f"[GIT] Cloning repo to {PROJECT_DIR}")
        subprocess.check_call([
            "git", "clone", "--branch", BRANCH, "--single-branch", REPO_URL, PROJECT_DIR
        ])

def ensure_dependencies():
    venv_python = os.path.join(VENV_DIR, "bin", "python")
    print("[PIP] Ensuring all required pip packages are installed...")
    subprocess.check_call([venv_python, "-m", "pip", "install", "--upgrade"] + REQUIREMENTS)

def main():
    robust_clone_or_update()
    ensure_venv()
    ensure_dependencies()
    print("[DONE] Repo is up-to-date, venv is ready, and all dependencies are installed.")

if __name__ == "__main__":
    main()
