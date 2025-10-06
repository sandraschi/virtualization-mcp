"""
Type definitions for VM networking operations.

This module contains all the data models and type definitions used throughout
the networking module.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict, Union, Literal


class NetworkAdapterType(str, Enum):
    """Types of network adapters supported by VirtualBox."""
    NAT = "nat"
    NAT_NETWORK = "natnetwork"
    BRIDGED = "bridged"
    HOST_ONLY = "hostonly"
    INTERNAL = "internal"
    GENERIC = "generic"
    NONE = "none"


# Alias for compatibility
NetworkAttachmentType = NetworkAdapterType


class NetworkAdapterState(str, Enum):
    """Possible states of a network adapter."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    CABLE_DISCONNECTED = "cable_disconnected"
    NOT_CONFIGURED = "not_configured"


@dataclass
class NetworkAdapterConfig:
    """Configuration for a VM network adapter."""
    enabled: bool = True
    attachment_type: NetworkAttachmentType = NetworkAttachmentType.NAT
    adapter_type: Optional[str] = None  # Hardware adapter type like "82540EM"
    mac_address: Optional[str] = None
    cable_connected: bool = True
    
    # Type-specific configurations
    network_name: Optional[str] = None  # For NAT Network or Bridged
    hostonly_interface: Optional[str] = None  # For Host-Only
    internal_network: Optional[str] = None  # For Internal
    
    # Promiscuous mode settings
    promiscuous_mode: str = "deny"  # deny | allow-vms | allow-all
    
    # Additional properties
    properties: Dict[str, str] = field(default_factory=dict)


@dataclass
class PortForwardingRule:
    """Port forwarding rule configuration."""
    name: str
    protocol: str  # 'tcp' or 'udp'
    host_ip: str
    host_port: int
    guest_ip: str
    guest_port: int


class NetworkOperationResult(TypedDict, total=False):
    """Standard response format for network operations."""
    status: Literal["success", "error"]
    vm_name: str
    adapter_number: Optional[int]
    message: str
    error: Optional[str]
    troubleshooting: List[str]
    
    # Additional operation-specific fields
    previous_state: Optional[str]
    current_state: Optional[NetworkAdapterState]
    rules: Optional[List[PortForwardingRule]]
    adapters: Optional[List[Dict[str, Any]]]



