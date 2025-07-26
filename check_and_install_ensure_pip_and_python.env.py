import subprocess
import sys
import os
import datetime


VENV_DIR = "venv1"


def create_venv():
    if not os.path.isdir(VENV_DIR):
        print("🔧 Creating virtual environment...")
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
    # Use SUDO_USER if running as root via sudo, else use current user, else fallback to 'isha'
    user = os.environ.get("SUDO_USER") or os.environ.get("USER") or "isha"
    if user == "root":
        user = "isha"  # fallback to your actual username
    home_dir = os.path.expanduser(f"~{user}")
    return os.path.join(home_dir, "Desktop", "pkg.status_succ")


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
    required = ["python3-venv", "python3-pip", "python3-tk"]
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
    else:
        print("❌ Failed to install some pip packages. Please install them manually.")
        sys.exit(1)


if __name__ == "__main__":
    main()
