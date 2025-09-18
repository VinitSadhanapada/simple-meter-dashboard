import os
import subprocess
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class SSHKeyManager:
    """Utility class for managing SSH keys and connections to Raspberry Pi devices"""

    @staticmethod
    def generate_ssh_key(key_path: str, key_name: str = "pi_management") -> Tuple[bool, str]:
        """
        Generate SSH key pair if it doesn't exist

        Args:
            key_path: Directory where to store the key
            key_name: Name of the key file

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Ensure the .ssh directory exists
            os.makedirs(key_path, mode=0o700, exist_ok=True)

            private_key_path = os.path.join(key_path, key_name)
            public_key_path = f"{private_key_path}.pub"

            # Check if key already exists
            if os.path.exists(private_key_path) and os.path.exists(public_key_path):
                return True, f"SSH key already exists at {private_key_path}"

            # Generate new SSH key
            cmd = [
                "ssh-keygen",
                "-t", "rsa",
                "-b", "4096",
                "-f", private_key_path,
                "-N", "",  # No passphrase
                "-C", f"Django Device Manager - {key_name}"
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True)

            # Set proper permissions
            os.chmod(private_key_path, 0o600)
            os.chmod(public_key_path, 0o644)

            logger.info(
                f"SSH key generated successfully at {private_key_path}")
            return True, f"SSH key generated successfully at {private_key_path}"

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to generate SSH key: {e.stderr}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error generating SSH key: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    @staticmethod
    def copy_ssh_key_to_pi(pi_ip: str, username: str, password: str,
                           public_key_path: str, ssh_port: int = 22) -> Tuple[bool, str]:
        """
        Copy SSH public key to Raspberry Pi

        Args:
            pi_ip: IP address of the Pi
            username: SSH username
            password: SSH password
            public_key_path: Path to public key file
            ssh_port: SSH port number

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Check if sshpass is available
            if subprocess.run(["which", "sshpass"], capture_output=True).returncode != 0:
                return False, "sshpass is not installed. Please install it: sudo apt install sshpass"

            # Check if public key exists
            if not os.path.exists(public_key_path):
                return False, f"Public key not found at {public_key_path}"

            # Copy SSH key using ssh-copy-id with sshpass
            cmd = [
                "sshpass", "-p", password,
                "ssh-copy-id",
                "-i", public_key_path,
                "-p", str(ssh_port),
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                f"{username}@{pi_ip}"
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True)

            logger.info(f"SSH key copied successfully to {username}@{pi_ip}")
            return True, f"SSH key copied successfully to {username}@{pi_ip}"

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to copy SSH key to Pi: {e.stderr}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error copying SSH key: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    @staticmethod
    def test_ssh_connection(pi_ip: str, username: str, private_key_path: str,
                            ssh_port: int = 22) -> Tuple[bool, str]:
        """
        Test SSH connection using private key

        Args:
            pi_ip: IP address of the Pi
            username: SSH username
            private_key_path: Path to private key file
            ssh_port: SSH port number

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            cmd = [
                "ssh",
                "-i", private_key_path,
                "-p", str(ssh_port),
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "ConnectTimeout=10",
                f"{username}@{pi_ip}",
                "echo 'SSH connection successful'"
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True)

            if "SSH connection successful" in result.stdout:
                return True, "SSH connection successful"
            else:
                return False, "SSH connection failed - unexpected response"

        except subprocess.CalledProcessError as e:
            error_msg = f"SSH connection failed: {e.stderr}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error testing SSH connection: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
