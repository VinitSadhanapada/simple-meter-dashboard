# To work on having automatic repo cloning and running initial.py
# This script checks for the presence of Python, pip, and required packages,
# installs them if missing, and sets up a virtual environment.
# keep the track of user variable in get_desktop_path function, adjust it if needed to pi or isha.



import subprocess
import sys
import os
import datetime


# Set the global USER variable for all user-specific operations
USER = os.environ.get("SUDO_USER") or os.environ.get("LOGNAME") or os.environ.get("USER") or "isha"
if USER == "root":
    USER = "isha"  # fallback to your actual username, change to 'pi' if needed

# Always use the Desktop project directory for venv and all files
PROJECT_DIR = os.path.join(os.path.expanduser(f"~{USER}"), "Desktop", "simple-meter-dashboard")
VENV_DIR = os.path.join(PROJECT_DIR, "venv")


def create_venv():
    if not os.path.isdir(PROJECT_DIR):
        print(f"🔧 Creating project directory at {PROJECT_DIR} ...")
        print(f"   Creating as user: {os.getenv('USER', 'unknown')} (detected user: {USER})")
        os.makedirs(PROJECT_DIR, exist_ok=True)
    if not os.path.isdir(VENV_DIR):
        print(f"🔧 Creating virtual environment at {VENV_DIR} ...")
        print(f"   Creating as user: {os.getenv('USER', 'unknown')} (detected user: {USER})")
        subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])
        print("✓ Virtual environment created.")
    else:
        print("✓ Virtual environment already exists.")


def get_venv_python():
    return os.path.join(VENV_DIR, "bin", "python")


def is_package_installed(pkg_name):
    try:
        subprocess.run(
            ["dpkg", "-s", pkg_name],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False


def install_package(pkg_name):
    print(f"🔧 Installing {pkg_name} (requires sudo)...")
    ret = os.system(
        f"sudo apt-get update && sudo apt-get install -y {pkg_name}")
    if ret == 0:
        print(f"✓ {pkg_name} installed successfully.")
        return True
    else:
        print(f"❌ Failed to install {pkg_name}. Please install it manually.")
        return False


def show_success_popup():
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Installation Complete",
                            "All required packages have been installed successfully!")
        root.destroy()
    except Exception as e:
        print(f"Could not show GUI popup: {e}")


def get_desktop_path():
    # Use global USER variable - place status file directly on Desktop, not in project folder
    home_dir = os.path.expanduser(f"~{USER}")
    return os.path.join(home_dir, "Desktop", "pkg.status_succ")


def clone_repo_to_desktop(repo_url, folder_name=None):
    """
    Clone the given git repo directly onto the user's Desktop. If folder_name is not provided, use the repo name.
    """
    # Use global USER variable and clone directly to Desktop
    home_dir = os.path.expanduser(f"~{USER}")
    desktop_dir = os.path.join(home_dir, "Desktop")
    if not os.path.isdir(desktop_dir):
        print(f"❌ Desktop directory not found: {desktop_dir}")
        return
    if not repo_url:
        print("❌ No repo URL provided to clone.")
        return
    if folder_name is None:
        folder_name = os.path.splitext(os.path.basename(
            repo_url.rstrip('/').replace('.git', '')))[0]
    dest_path = os.path.join(desktop_dir, folder_name)
    if os.path.exists(dest_path):
        print(f"⚠️ Repo folder already exists at {dest_path}. Updating repository...")
        # Check if it's already a git repository
        git_dir = os.path.join(dest_path, ".git")
        if os.path.exists(git_dir):
            try:
                # It's already a git repo, just pull the latest changes
                print("   Pulling latest changes from existing git repository...")
                subprocess.check_call(["git", "-C", dest_path, "fetch", "origin"])
                subprocess.check_call(["git", "-C", dest_path, "checkout", "feature/device-config-and-rpi-setup"])
                subprocess.check_call(["git", "-C", dest_path, "pull", "origin", "feature/device-config-and-rpi-setup"])
                print(f"✓ Repository updated at {dest_path}")
                return
            except Exception as e:
                print(f"❌ Failed to update existing git repo: {e}")
                print("   Falling back to fresh clone...")
        
        # If not a git repo or update failed, initialize as new git repo
        try:
            subprocess.check_call(["git", "-C", dest_path, "init"])
            subprocess.check_call(["git", "-C", dest_path, "remote", "add", "origin", repo_url])
            subprocess.check_call(["git", "-C", dest_path, "fetch", "origin"])
            subprocess.check_call(["git", "-C", dest_path, "checkout", "-b", "feature/device-config-and-rpi-setup", "origin/feature/device-config-and-rpi-setup"])
            print(f"✓ Repository initialized and updated at {dest_path}")
            return
        except Exception as e:
            print(f"❌ Failed to initialize git repo in existing directory: {e}")
            return
    
    print(f"🔧 Cloning repo {repo_url} to {dest_path} ...")
    try:
        subprocess.check_call(
            ["git", "clone", "--branch", "feature/device-config-and-rpi-setup", "--single-branch", repo_url, dest_path])
        print(f"✓ Repo cloned to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to clone repo: {e}")


def write_status_file(installed_packages):
    desktop_path = get_desktop_path()
    try:
        with open(desktop_path, "w") as f:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"Installed packages (last updated: {now}):\n")
            for pkg in installed_packages:
                f.write(pkg + "\n")
        print(f"✓ Status file written to {desktop_path}")
    except Exception as e:
        print(f"❌ Could not write status file: {e}")


def main():
    required = ["python3-venv", "python3-pip", "python3-tk", "git"]
    missing = [pkg for pkg in required if not is_package_installed(pkg)]

    # Create venv if not exists
    create_venv()
    venv_python = get_venv_python()

    if not missing:
        print("✓ python3-venv and python3-pip are already installed.")
    else:
        print(f"Missing packages: {', '.join(missing)}")
        pkg_str = " ".join(missing)
        print(f"🔧 Installing {pkg_str} (requires sudo)...")
        ret = os.system(
            f"sudo apt-get update && sudo apt-get install -y {pkg_str}")
        if ret == 0:
            print(f"✓ {pkg_str} installed successfully.")
            print(
                "All required packages are now installed. Continuing to pip dependencies...")
        else:
            print(
                f"❌ Failed to install {pkg_str}. Please install them manually.")
            sys.exit(1)

    required_pip = [
        "pymodbus==2.5.3",
        "pyserial==3.5",
        "paho-mqtt==2.1.0",
        "termcolor==3.1.0",
        "flask==2.3.3",
        "numpy==1.24.3",
        "pandas==2.0.3"
    ]

    print("🔧 Ensuring all required pip packages (with correct versions) are installed...")
    ret = os.system(f"{venv_python} -m pip install --upgrade " +
                    " ".join(required_pip))

    if ret == 0:
        print("✓ All pip packages installed successfully.")
        # Get installed pip packages for the status file
        try:
            installed = subprocess.check_output(
                [venv_python, "-m", "pip", "freeze"], text=True
            ).splitlines()
        except Exception as e:
            print(f"❌ Could not check installed pip packages: {e}")
            installed = required_pip
        show_success_popup()
        write_status_file(installed)

        # Clone a dummy git repo to Desktop
        dummy_repo_url = "https://github.com/VinitSadhanapada/simple-meter-dashboard.git"
        clone_repo_to_desktop(dummy_repo_url)

        # Change ownership of the project directory and all its contents to the user
        try:
            import pwd
            uid = pwd.getpwnam(USER).pw_uid
            gid = pwd.getpwnam(USER).pw_gid
            for root, dirs, files in os.walk(PROJECT_DIR):
                os.chown(root, uid, gid)
                for d in dirs:
                    os.chown(os.path.join(root, d), uid, gid)
                for f in files:
                    os.chown(os.path.join(root, f), uid, gid)
            print(f"✓ Changed ownership of {PROJECT_DIR} and its contents to {USER}")
        except Exception as e:
            print(f"❌ Could not change ownership: {e}")
    else:
        print("❌ Failed to install some pip packages. Please install them manually.")
        sys.exit(1)


if __name__ == "__main__":
    main()
