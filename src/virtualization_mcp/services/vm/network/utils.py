"""
Utility functions for VM networking operations.

This module contains helper functions used throughout the networking module.
"""

import ipaddress
import re


def validate_ip_address(ip: str) -> bool:
    """
    Validate an IP address (IPv4 or IPv6).

    Args:
        ip: IP address to validate

    Returns:
        bool: True if the IP address is valid, False otherwise
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_mac_address(mac: str) -> bool:
    """
    Validate a MAC address.

    Args:
        mac: MAC address to validate

    Returns:
        bool: True if the MAC address is valid, False otherwise
    """
    # Pattern for MAC address (supports various common formats)
    pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$|^([0-9A-Fa-f]{12})$"
    return bool(re.fullmatch(pattern, mac))


def parse_port_forwarding_rule(rule_str: str) -> tuple[str, str, str, str, str, str]:
    """
    Parse a port forwarding rule string into its components.

    The expected format is: "name,proto,host_ip,host_port,guest_ip,guest_port"

    Args:
        rule_str: Port forwarding rule string

    Returns:
        Tuple containing (name, protocol, host_ip, host_port, guest_ip, guest_port)

    Raises:
        ValueError: If the rule string is invalid
    """
    parts = rule_str.split(",")
    if len(parts) != 6:
        raise ValueError("Invalid port forwarding rule format")

    name, proto, host_ip, host_port, guest_ip, guest_port = parts

    # Validate protocol
    if proto.lower() not in ("tcp", "udp"):
        raise ValueError(f"Invalid protocol: {proto}. Must be 'tcp' or 'udp'")

    # Validate ports
    try:
        int(host_port)
        int(guest_port)
    except ValueError:
        raise ValueError("Ports must be integers")

    return name, proto, host_ip, host_port, guest_ip, guest_port


def format_mac_address(mac: str) -> str:
    """
    Format a MAC address in the standard format (lowercase with colons).

    Args:
        mac: Input MAC address (can be in various formats)

    Returns:
        Formatted MAC address (e.g., '01:23:45:67:89:ab')
    """
    # Remove any non-hex characters and convert to lowercase
    clean_mac = re.sub(r"[^0-9A-Fa-f]", "", mac).lower()

    # Insert colons every 2 characters
    return ":".join(clean_mac[i : i + 2] for i in range(0, 12, 2))


def is_port_available(port: int, host: str = "0.0.0.0") -> bool:
    """
    Check if a network port is available.

    Args:
        port: Port number to check
        host: Host address to check (default: all interfaces)

    Returns:
        bool: True if the port is available, False if in use
    """
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False
