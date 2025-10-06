"""
Networking module for VirtualBox VM management.

This package provides a modular approach to VM networking configuration,
split across multiple focused modules for better maintainability.
"""

from typing import Dict, Any, List, Optional

# Re-export common types for easier access
from .types import (
    NetworkAdapterConfig,
    NetworkAdapterState,
    PortForwardingRule,
    NetworkOperationResult,
)

# Re-export the main networking service
from .service import VMNetworkingService

__all__ = [
    'VMNetworkingService',
    'NetworkAdapterConfig',
    'NetworkAdapterState',
    'PortForwardingRule',
    'NetworkOperationResult',
]
