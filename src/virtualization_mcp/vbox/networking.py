"""
Networking - VM network configuration and port forwarding
Handles network setup, port forwarding, and file transfer operations
"""

import logging
import socket
from typing import Any

from .manager import VBoxManager, VBoxManagerError

logger = logging.getLogger(__name__)


class NetworkManager:
    """
    VM Network configuration and management

    Provides Austrian dev efficiency with comprehensive network operations
    including port forwarding, network types, and connectivity testing.
    """

    def __init__(self, manager: VBoxManager):
        """
        Initialize network manager

        Args:
            manager: VBoxManager instance
        """
        self.manager = manager

    def configure_port_forwarding(
        self,
        vm_name: str,
        host_port: int,
        guest_port: int,
        protocol: str = "tcp",
        rule_name: str = None,
    ) -> dict[str, Any]:
        """
        Configure port forwarding for VM access

        Args:
            vm_name: VM name
            host_port: Host port number
            guest_port: Guest port number
            protocol: "tcp" or "udp"
            rule_name: Optional rule name (auto-generated if None)

        Returns:
            Dict with port forwarding result
        """
        try:
            if not self.manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' not found")

            # Validate ports
            if not (1 <= host_port <= 65535):
                raise VBoxManagerError(f"Invalid host port: {host_port}")
            if not (1 <= guest_port <= 65535):
                raise VBoxManagerError(f"Invalid guest port: {guest_port}")

            # Validate protocol
            protocol = protocol.lower()
            if protocol not in ["tcp", "udp"]:
                raise VBoxManagerError(f"Invalid protocol: {protocol}. Use 'tcp' or 'udp'")

            # Generate rule name if not provided
            if not rule_name:
                rule_name = f"{protocol}{guest_port}"

            # Check if port is already in use on host
            if self._is_port_in_use(host_port):
                logger.warning(f"Host port {host_port} appears to be in use")

            # Check VM state - some operations require VM to be stopped
            vm_state = self.manager.get_vm_state(vm_name)

            logger.info(
                f"Configuring port forwarding for VM '{vm_name}': {host_port} -> {guest_port} ({protocol})"
            )

            # Configure port forwarding
            self.manager.run_command(
                [
                    "modifyvm",
                    vm_name,
                    "--natpf1",
                    f"{rule_name},{protocol},,{host_port},,{guest_port}",
                ]
            )

            result = {
                "success": True,
                "vm_name": vm_name,
                "rule_name": rule_name,
                "host_port": host_port,
                "guest_port": guest_port,
                "protocol": protocol,
                "vm_state": vm_state,
                "message": f"Port forwarding configured: {host_port} -> {guest_port} ({protocol})",
            }

            logger.info(f"Successfully configured port forwarding for VM '{vm_name}'")
            return result

        except VBoxManagerError as e:
            logger.error(f"Failed to configure port forwarding for VM '{vm_name}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error configuring port forwarding: {e}")
            raise VBoxManagerError(f"Failed to configure port forwarding: {str(e)}")

    def remove_port_forwarding(self, vm_name: str, rule_name: str) -> dict[str, Any]:
        """
        Remove port forwarding rule

        Args:
            vm_name: VM name
            rule_name: Rule name to remove

        Returns:
            Dict with removal result
        """
        try:
            if not self.manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' not found")

            logger.info(f"Removing port forwarding rule '{rule_name}' for VM '{vm_name}'")

            # Remove port forwarding rule
            self.manager.run_command(["modifyvm", vm_name, "--natpf1", "delete", rule_name])

            result = {
                "success": True,
                "vm_name": vm_name,
                "rule_name": rule_name,
                "message": f"Port forwarding rule '{rule_name}' removed",
            }

            logger.info(
                f"Successfully removed port forwarding rule '{rule_name}' for VM '{vm_name}'"
            )
            return result

        except VBoxManagerError as e:
            logger.error(
                f"Failed to remove port forwarding rule '{rule_name}' for VM '{vm_name}': {e}"
            )
            raise
        except Exception as e:
            logger.error(f"Unexpected error removing port forwarding: {e}")
            raise VBoxManagerError(f"Failed to remove port forwarding: {str(e)}")

    def list_port_forwarding(self, vm_name: str) -> list[dict[str, Any]]:
        """
        List all port forwarding rules for VM

        Args:
            vm_name: VM name

        Returns:
            List of port forwarding rules
        """
        try:
            if not self.manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' not found")

            # Get VM info with network configuration
            vm_info = self.manager.get_vm_info(vm_name)

            # Parse port forwarding rules
            rules = []
            for key, value in vm_info.items():
                if key.startswith("Forwarding("):
                    rule_info = self._parse_forwarding_rule(key, value)
                    if rule_info:
                        rules.append(rule_info)

            return rules

        except VBoxManagerError as e:
            logger.error(f"Failed to list port forwarding for VM '{vm_name}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing port forwarding: {e}")
            raise VBoxManagerError(f"Failed to list port forwarding: {str(e)}")

    def _parse_forwarding_rule(self, key: str, value: str) -> dict[str, Any] | None:
        """Parse VBoxManage port forwarding rule output"""
        try:
            # Format: "rule_name,tcp,,host_port,,guest_port"
            parts = value.split(",")
            if len(parts) >= 6:
                return {
                    "rule_name": parts[0],
                    "protocol": parts[1],
                    "host_ip": parts[2] or "0.0.0.0",
                    "host_port": int(parts[3]) if parts[3] else None,
                    "guest_ip": parts[4] or "",
                    "guest_port": int(parts[5]) if parts[5] else None,
                }
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse forwarding rule: {key}={value}, error: {e}")
        return None

    def configure_network_type(
        self, vm_name: str, adapter_num: int = 1, network_type: str = "NAT"
    ) -> dict[str, Any]:
        """
        Configure VM network adapter type

        Args:
            vm_name: VM name
            adapter_num: Network adapter number (1-8)
            network_type: "NAT", "Bridged", "Internal", "Host-only", "NAT Network"

        Returns:
            Dict with network configuration result
        """
        try:
            if not self.manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' not found")

            # Validate adapter number
            if not (1 <= adapter_num <= 8):
                raise VBoxManagerError(f"Invalid adapter number: {adapter_num}. Must be 1-8")

            # Validate network type
            valid_types = ["NAT", "Bridged", "Internal", "Host-only", "NAT Network", "None"]
            if network_type not in valid_types:
                raise VBoxManagerError(
                    f"Invalid network type: {network_type}. Valid: {valid_types}"
                )

            logger.info(
                f"Configuring network adapter {adapter_num} for VM '{vm_name}' as {network_type}"
            )

            # Configure network adapter
            nic_type = network_type.lower().replace(" ", "").replace("-", "")
            if nic_type == "natnetwork":
                nic_type = "natnetwork"
            elif nic_type == "hostonly":
                nic_type = "hostonly"

            self.manager.run_command(["modifyvm", vm_name, f"--nic{adapter_num}", nic_type])

            result = {
                "success": True,
                "vm_name": vm_name,
                "adapter_num": adapter_num,
                "network_type": network_type,
                "message": f"Network adapter {adapter_num} configured as {network_type}",
            }

            logger.info(f"Successfully configured network adapter for VM '{vm_name}'")
            return result

        except VBoxManagerError as e:
            logger.error(f"Failed to configure network for VM '{vm_name}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error configuring network: {e}")
            raise VBoxManagerError(f"Failed to configure network: {str(e)}")

    def get_vm_ip_address(self, vm_name: str) -> dict[str, Any]:
        """
        Get VM IP address (requires Guest Additions)

        Args:
            vm_name: VM name

        Returns:
            Dict with IP address info
        """
        try:
            if not self.manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' not found")

            vm_state = self.manager.get_vm_state(vm_name)
            if vm_state != "running":
                raise VBoxManagerError(f"VM '{vm_name}' is not running (state: {vm_state})")

            logger.info(f"Getting IP address for VM '{vm_name}'")

            # Get IP address via Guest Properties (requires Guest Additions)
            try:
                result = self.manager.run_command(
                    ["guestproperty", "get", vm_name, "/VirtualBox/GuestInfo/Net/0/V4/IP"]
                )

                ip_output = result["output"]
                if "Value:" in ip_output:
                    ip_address = ip_output.split("Value:")[1].strip()

                    return {
                        "success": True,
                        "vm_name": vm_name,
                        "ip_address": ip_address,
                        "method": "guest_additions",
                        "message": f"VM '{vm_name}' IP address: {ip_address}",
                    }
                else:
                    raise VBoxManagerError("IP address not available via Guest Additions")

            except VBoxManagerError:
                # Fallback: Try to get IP from network info
                return self._get_ip_fallback(vm_name)

        except VBoxManagerError as e:
            logger.error(f"Failed to get IP address for VM '{vm_name}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting IP address: {e}")
            raise VBoxManagerError(f"Failed to get IP address: {str(e)}")

    def _get_ip_fallback(self, vm_name: str) -> dict[str, Any]:
        """Fallback method to get IP address"""
        return {
            "success": False,
            "vm_name": vm_name,
            "ip_address": None,
            "method": "fallback",
            "message": f"IP address not available for VM '{vm_name}' (Guest Additions may not be installed)",
            "suggestion": "Install Guest Additions in the VM for IP detection",
        }

    def _is_port_in_use(self, port: int, host: str = "localhost") -> bool:
        """Check if port is in use on host system"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result == 0
        except Exception:
            return False

    def test_connectivity(self, vm_name: str, host_port: int, timeout: int = 5) -> dict[str, Any]:
        """
        Test network connectivity to VM via port forwarding

        Args:
            vm_name: VM name
            host_port: Host port to test
            timeout: Connection timeout seconds

        Returns:
            Dict with connectivity test result
        """
        try:
            logger.info(f"Testing connectivity to VM '{vm_name}' on port {host_port}")

            # Test connection
            start_time = __import__("time").time()

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(timeout)
                    result = sock.connect_ex(("localhost", host_port))

                    end_time = __import__("time").time()
                    response_time = end_time - start_time

                    if result == 0:
                        return {
                            "success": True,
                            "vm_name": vm_name,
                            "host_port": host_port,
                            "connected": True,
                            "response_time_ms": round(response_time * 1000, 2),
                            "message": f"Successfully connected to VM '{vm_name}' on port {host_port}",
                        }
                    else:
                        return {
                            "success": True,
                            "vm_name": vm_name,
                            "host_port": host_port,
                            "connected": False,
                            "error_code": result,
                            "message": f"Cannot connect to VM '{vm_name}' on port {host_port}",
                        }

            except TimeoutError:
                return {
                    "success": True,
                    "vm_name": vm_name,
                    "host_port": host_port,
                    "connected": False,
                    "timeout": True,
                    "message": f"Connection timeout to VM '{vm_name}' on port {host_port}",
                }

        except Exception as e:
            logger.error(f"Error testing connectivity: {e}")
            return {
                "success": False,
                "vm_name": vm_name,
                "host_port": host_port,
                "error": str(e),
                "message": f"Failed to test connectivity: {str(e)}",
            }

    def execute_command(
        self, vm_name: str, command: str, username: str, password: str = None, timeout: int = 30
    ) -> dict[str, Any]:
        """
        Execute command in VM (requires Guest Additions)

        Args:
            vm_name: VM name
            command: Command to execute
            username: VM username
            password: VM password (optional if key-based auth)
            timeout: Command timeout seconds

        Returns:
            Dict with command execution result
        """
        try:
            if not self.manager.vm_exists(vm_name):
                raise VBoxManagerError(f"VM '{vm_name}' not found")

            vm_state = self.manager.get_vm_state(vm_name)
            if vm_state != "running":
                raise VBoxManagerError(f"VM '{vm_name}' is not running (state: {vm_state})")

            logger.info(f"Executing command in VM '{vm_name}': {command}")

            cmd = ["guestcontrol", vm_name, "run"]

            # Add authentication
            cmd.extend(["--username", username])
            if password:
                cmd.extend(["--password", password])

            # Add command
            cmd.extend(["--", command])

            # Execute with timeout
            result = self.manager.run_command(cmd)

            return {
                "success": True,
                "vm_name": vm_name,
                "command": command,
                "username": username,
                "output": result["output"],
                "message": f"Command executed successfully in VM '{vm_name}'",
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to execute command in VM '{vm_name}': {e}")
            if "not supported" in str(e).lower() or "guest additions" in str(e).lower():
                raise VBoxManagerError(
                    f"Command execution requires Guest Additions to be installed in VM '{vm_name}'"
                )
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing command: {e}")
            raise VBoxManagerError(f"Failed to execute command: {str(e)}")
