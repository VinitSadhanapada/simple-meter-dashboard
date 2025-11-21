#!/usr/bin/env bash
set -euo pipefail

# Install Docker Engine, Buildx, and Compose plugin on Ubuntu
# Usage: sudo bash scripts/install_docker.sh

if [[ $(id -u) -ne 0 ]]; then
  echo "Please run as root (use: sudo bash scripts/install_docker.sh)" >&2
  exit 1
fi

apt-get update -y
apt-get install -y ca-certificates curl gnupg lsb-release

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

ARCH=$(dpkg --print-architecture)
CODENAME=$(lsb_release -cs)
echo "deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${CODENAME} stable" > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y \
  docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

systemctl enable --now docker

if id -nG "$SUDO_USER" 2>/dev/null | grep -qw docker; then
  echo "User '$SUDO_USER' is already in the docker group."
else
  usermod -aG docker "$SUDO_USER" || true
  echo "Added '$SUDO_USER' to docker group. Please log out and back in (or reboot) to apply group membership."
fi

docker --version || true
docker compose version || true
echo "Docker installation complete."
