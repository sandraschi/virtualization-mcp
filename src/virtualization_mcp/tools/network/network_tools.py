"""
Network Configuration Tools

This module contains tools for managing virtual network adapters and configurations.
"""

import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

async def configure_network_adapter(
    vm_name: str,
    adapter_id: int,
    enabled: bool = True,
    network_type: str = "nat",
    mac_address: Optional[str] = None
) -> Dict[str, Any]:
    """
    Configure a network adapter for a VM.
    
    Args:
        vm_name: Name or UUID of the VM
        adapter_id: NIC adapter ID (1-4)
        enabled: Whether to enable the adapter
        network_type: Network type (nat, bridged, intnet, hostonly, generic, natnetwork, none)
        mac_address: Custom MAC address (optional)
        
    Returns:
        Dictionary containing configuration status
    """
    try:
        # Validate adapter ID
        if not 1 <= adapter_id <= 4:
            return {
                "status": "error",
                "message": "Adapter ID must be between 1 and 4"
            }
        
        # Validate network type
        valid_network_types = ["nat", "bridged", "intnet", "hostonly", "generic", "natnetwork", "none"]
        if network_type not in valid_network_types:
            return {
                "status": "error",
                "message": f"Invalid network type. Must be one of: {', '.join(valid_network_types)}"
            }
        
        # Build the base command
        cmd = ["VBoxManage", "modifyvm", vm_name]
        
        # Enable/disable the adapter
        if enabled:
            cmd.extend([f"--nic{adapter_id}", network_type])
            
            # Set MAC address if provided
            if mac_address:
                cmd.extend([f"--macaddress{adapter_id}", mac_address])
        else:
            cmd.extend([f"--nic{adapter_id}", "none"])
        
        # Execute the command
        await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "message": f"Network adapter {adapter_id} configured successfully",
            "configuration": {
                "enabled": enabled,
                "type": network_type if enabled else "none",
                "mac_address": mac_address if enabled and mac_address else "auto"
            }
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error configuring network adapter: {e}")
        return {
            "status": "error",
            "message": f"Failed to configure network adapter: {e.stderr}"
        }

async def list_host_network_interfaces() -> Dict[str, Any]:
    """
    List all available host network interfaces.
    
    Returns:
        Dictionary containing the list of network interfaces
    """
    try:
        cmd = ["VBoxManage", "list", "bridgedifs"]
        
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        interfaces = []
        current_iface = {}
        
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                if current_iface:
                    interfaces.append(current_iface)
                    current_iface = {}
                continue
                
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                current_iface[key] = value
        
        if current_iface:  # Add the last interface
            interfaces.append(current_iface)
            
        return {
            "status": "success",
            "interfaces": interfaces
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error listing host network interfaces: {e}")
        return {
            "status": "error",
            "message": f"Failed to list host network interfaces: {e.stderr}"
        }

async def create_nat_network(
    network_name: str,
    network: str,
    enable_dhcp: bool = True,
    dhcp_lower: str = "",
    dhcp_upper: str = ""
) -> Dict[str, Any]:
    """
    Create a new NAT network.
    
    Args:
        network_name: Name for the new NAT network
        network: Network address in CIDR format (e.g., '192.168.15.0/24')
        enable_dhcp: Whether to enable DHCP server
        dhcp_lower: Lower bound of DHCP address range (e.g., '192.168.15.10')
        dhcp_upper: Upper bound of DHCP address range (e.g., '192.168.15.254')
        
    Returns:
        Dictionary with NAT network creation status
    """
    try:
        # Create the NAT network
        cmd = [
            "VBoxManage", "natnetwork", "add",
            "--netname", network_name,
            "--network", network,
            "--enable"
        ]
        
        await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Configure DHCP if enabled
        if enable_dhcp and dhcp_lower and dhcp_upper:
            dhcp_cmd = [
                "VBoxManage", "natnetwork", "modify",
                "--netname", network_name,
                "--dhcp", "on",
                "--port-forward-4", "delete-all"
            ]
            
            # Add DHCP range
            dhcp_cmd.extend(["--dhcp-lower-ip", dhcp_lower])
            dhcp_cmd.extend(["--dhcp-upper-ip", dhcp_upper])
            
            await asyncio.to_thread(
                subprocess.run,
                dhcp_cmd,
                capture_output=True,
                text=True,
                check=True
            )
        
        return {
            "status": "success",
            "message": f"NAT network '{network_name}' created successfully",
            "network": {
                "name": network_name,
                "network": network,
                "dhcp_enabled": enable_dhcp,
                "dhcp_range": f"{dhcp_lower}-{dhcp_upper}" if (enable_dhcp and dhcp_lower and dhcp_upper) else "disabled"
            }
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating NAT network: {e}")
        return {
            "status": "error",
            "message": f"Failed to create NAT network: {e.stderr}"
        }

async def remove_nat_network(network_name: str) -> Dict[str, Any]:
    """
    Remove a NAT network.
    
    Args:
        network_name: Name of the NAT network to remove
        
    Returns:
        Dictionary with NAT network removal status
    """
    try:
        cmd = ["VBoxManage", "natnetwork", "remove", "--netname", network_name]
        
        await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "message": f"NAT network '{network_name}' removed successfully"
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error removing NAT network: {e}")
        return {
            "status": "error",
            "message": f"Failed to remove NAT network: {e.stderr}"
        }

async def list_nat_networks() -> Dict[str, Any]:
    """
    List all NAT networks.
    
    Returns:
        Dictionary containing the list of NAT networks
    """
    try:
        cmd = ["VBoxManage", "list", "natnetworks"]
        
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        networks = []
        current_net = {}
        
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                if current_net:
                    networks.append(current_net)
                    current_net = {}
                continue
                
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                current_net[key] = value
        
        if current_net:  # Add the last network
            networks.append(current_net)
            
        return {
            "status": "success",
            "networks": networks
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error listing NAT networks: {e}")
        return {
            "status": "error",
            "message": f"Failed to list NAT networks: {e.stderr}"
        }

async def add_port_forwarding(
    vm_name: str,
    rule_name: str,
    protocol: str,
    host_port: int,
    guest_ip: str,
    guest_port: int,
    adapter_id: int = 1
) -> Dict[str, Any]:
    """
    Add a port forwarding rule to a VM's NAT adapter.
    
    Args:
        vm_name: Name or UUID of the VM
        rule_name: Name for the port forwarding rule
        protocol: Protocol (tcp or udp)
        host_port: Host port to forward from
        guest_ip: Guest IP address to forward to
        guest_port: Guest port to forward to
        adapter_id: NIC adapter ID (1-4, default: 1)
        
    Returns:
        Dictionary with port forwarding rule addition status
    """
    try:
        # Validate protocol
        protocol = protocol.lower()
        if protocol not in ["tcp", "udp"]:
            return {
                "status": "error",
                "message": "Protocol must be 'tcp' or 'udp'"
            }
        
        # Validate adapter ID
        if not 1 <= adapter_id <= 4:
            return {
                "status": "error",
                "message": "Adapter ID must be between 1 and 4"
            }
        
        # Add the port forwarding rule
        cmd = [
            "VBoxManage", "modifyvm", vm_name,
            f"--natpf{adapter_id}", 
            f"{rule_name},{protocol},,{host_port},{guest_ip},{guest_port}"
        ]
        
        await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "message": f"Port forwarding rule '{rule_name}' added successfully",
            "rule": {
                "name": rule_name,
                "protocol": protocol,
                "host_port": host_port,
                "guest_ip": guest_ip,
                "guest_port": guest_port,
                "adapter_id": adapter_id
            }
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error adding port forwarding rule: {e}")
        return {
            "status": "error",
            "message": f"Failed to add port forwarding rule: {e.stderr}"
        }

async def remove_port_forwarding(
    vm_name: str,
    rule_name: str,
    adapter_id: int = 1
) -> Dict[str, Any]:
    """
    Remove a port forwarding rule from a VM's NAT adapter.
    
    Args:
        vm_name: Name or UUID of the VM
        rule_name: Name of the port forwarding rule to remove
        adapter_id: NIC adapter ID (1-4, default: 1)
        
    Returns:
        Dictionary with port forwarding rule removal status
    """
    try:
        # Validate adapter ID
        if not 1 <= adapter_id <= 4:
            return {
                "status": "error",
                "message": "Adapter ID must be between 1 and 4"
            }
        
        # Remove the port forwarding rule
        cmd = [
            "VBoxManage", "modifyvm", vm_name,
            f"--natpf{adapter_id}", 
            f"delete",
            rule_name
        ]
        
        await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "message": f"Port forwarding rule '{rule_name}' removed successfully"
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error removing port forwarding rule: {e}")
        return {
            "status": "error",
            "message": f"Failed to remove port forwarding rule: {e.stderr}"
        }

async def list_port_forwarding_rules(
    vm_name: str,
    adapter_id: int = 1
) -> Dict[str, Any]:
    """
    List all port forwarding rules for a VM's NAT adapter.
    
    Args:
        vm_name: Name or UUID of the VM
        adapter_id: NIC adapter ID (1-4, default: 1)
        
    Returns:
        Dictionary containing the list of port forwarding rules
    """
    try:
        # Get VM info
        cmd = ["VBoxManage", "showvminfo", vm_name, "--machinereadable"]
        
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        rules = []
        
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or '=' not in line:
                continue
                
            key, value = line.split('=', 1)
            key = key.strip('"')
            value = value.strip('"')
            
            # Look for port forwarding rules
            if key == f"Forwarding({adapter_id-1})":
                # Format: "rule1,tcp,,2222,,22"
                parts = value.split(',')
                if len(parts) >= 6:
                    rules.append({
                        "name": parts[0],
                        "protocol": parts[1],
                        "host_ip": parts[2] if parts[2] else "0.0.0.0",
                        "host_port": int(parts[3]) if parts[3] else 0,
                        "guest_ip": parts[4] if parts[4] else "",
                        "guest_port": int(parts[5]) if parts[5] else 0
                    })
        
        return {
            "status": "success",
            "adapter_id": adapter_id,
            "rules": rules
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error listing port forwarding rules: {e}")
        return {
            "status": "error",
            "message": f"Failed to list port forwarding rules: {e.stderr}"
        }


async def list_hostonly_networks() -> Dict[str, Any]:
    """
    List all host-only networks.
    
    Returns:
        Dictionary containing the list of host-only networks
    """
    try:
        result = await asyncio.create_subprocess_shell(
            'VBoxManage list hostonlyifs',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await result.communicate()
        
        if result.returncode != 0:
            return {"status": "error", "message": "Failed to list host-only networks"}
            
        networks = []
        current = {}
        for line in stdout.decode().splitlines():
            line = line.strip()
            if not line and current:
                networks.append(current)
                current = {}
            elif ':' in line:
                key, value = line.split(':', 1)
                current[key.strip()] = value.strip()
        
        if current:
            networks.append(current)
            
        return {"status": "success", "networks": networks}
        
    except Exception as e:
        logger.error(f"Error listing host-only networks: {e}")
        return {"status": "error", "message": str(e)}


async def create_hostonly_network(
    network_name: str,
    ip: str,
    netmask: str = "255.255.255.0"
) -> Dict[str, Any]:
    """
    Create a new host-only network.
    
    Args:
        network_name: Name for the new network
        ip: IP address for the host interface
        netmask: Netmask for the host interface
        
    Returns:
        Dictionary with creation status
    """
    try:
        # Create the host-only interface
        result = await asyncio.create_subprocess_shell(
            'VBoxManage hostonlyif create',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            return {"status": "error", "message": stderr.decode().strip()}
            
        # Get the interface name (e.g., 'vboxnet0')
        interface = stdout.decode().strip().split()[-1].strip("'")
        
        # Configure the interface
        result = await asyncio.create_subprocess_shell(
            f'VBoxManage hostonlyif ipconfig {interface} --ip {ip} --netmask {netmask}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await result.communicate()
        
        if result.returncode != 0:
            return {"status": "error", "message": stderr.decode().strip()}
            
        return {
            "status": "success",
            "interface": interface,
            "ip": ip,
            "netmask": netmask
        }
        
    except Exception as e:
        logger.error(f"Error creating host-only network: {e}")
        return {"status": "error", "message": str(e)}


async def remove_hostonly_network(interface: str) -> Dict[str, Any]:
    """
    Remove a host-only network.
    
    Args:
        interface: Name of the interface to remove (e.g., 'vboxnet0')
        
    Returns:
        Dictionary with removal status
    """
    try:
        # Remove the host-only interface
        result = await asyncio.create_subprocess_shell(
            f'VBoxManage hostonlyif remove {interface}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await result.communicate()
        
        if result.returncode != 0:
            return {"status": "error", "message": stderr.decode().strip()}
            
        return {"status": "success", "message": f"Removed {interface}"}
        
    except Exception as e:
        logger.error(f"Error removing host-only network: {e}")
        return {"status": "error", "message": str(e)}



