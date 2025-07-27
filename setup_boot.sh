#!/bin/bash
#1. make the sudo pw-less to bypass the popup, first on pi with :
#a. sudo visudo
#b.Add this line at the end (replace pi with your actual username if needed) remove # before pi:
#pi ALL=(ALL) NOPASSWD: /usr/bin/apt-get
#then source this setup_boot.sh file to run the commands below.

mkdir -p /home/pi/deepak/enhanced_dashboard_system/
cp check_and_install_ensure_pip_and_python.env.py /home/pi/deepak/enhanced_dashboard_system/check_and_install_ensure_pip_and_python.env.py
sudo cp 99runinstallscript /etc/NetworkManager/dispatcher.d/99runinstallscript

sudo chmod +x /etc/NetworkManager/dispatcher.d/99runinstallscript
sudo chmod +x /home/pi/deepak/enhanced_dashboard_system/check_and_install_ensure_pip_and_python.env.py
