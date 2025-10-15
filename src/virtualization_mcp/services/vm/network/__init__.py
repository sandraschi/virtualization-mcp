"""
Networking module for VirtualBox VM management.

This package provides a modular approach to VM networking configuration,
split across multiple focused modules for better maintainability.
"""

from typing import Any, Dict, List, Optional

# Re-export the main networking service
from .service import VMNetworkingService

# Re-export common types for easier access
from .types import (
    NetworkAdapterConfig,
    NetworkAdapterState,
    NetworkOperationResult,
    PortForwardingRule,
)

__all__ = [
    "VMNetworkingService",
    "NetworkAdapterConfig",
    "NetworkAdapterState",
    "PortForwardingRule",
    "NetworkOperationResult",
]
