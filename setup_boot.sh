#!/bin/bash
#1. make the sudo pw-less to bypass the popup, first on pi with :
#a. sudo visudo
#b.Add this line at the end (replace pi with your actual username if needed) remove # before pi:
#pi ALL=(ALL) NOPASSWD: /usr/bin/apt-get
#then source this setup_boot.sh file to run the commands below.

# Configuration variables
INSTALL_DIR="/home/pi/deepak/enhanced_dashboard_system/"
NETWORK_DISPATCHER_DIR="/etc/NetworkManager/dispatcher.d/"

mkdir -p $INSTALL_DIR
cp check_and_install_ensure_pip_and_python.env.py $INSTALL_DIR/check_and_install_ensure_pip_and_python.env.py
cp 99runinstallscript $INSTALL_DIR/99runinstallscript
cp setup_boot.sh $INSTALL_DIR/setup_boot.sh
cp rtc_new.py $INSTALL_DIR/rtc_new.py
cp robust_git_venv_setup.py $INSTALL_DIR/robust_git_venv_setup.py

sudo cp 99runinstallscript $NETWORK_DISPATCHER_DIR/99runinstallscript

sudo chmod +x $NETWORK_DISPATCHER_DIR/99runinstallscript
sudo chmod +x $INSTALL_DIR/check_and_install_ensure_pip_and_python.env.py
sudo chmod +x $INSTALL_DIR/rtc_new.py
sudo chmod +x $INSTALL_DIR/robust_git_venv_setup.py
