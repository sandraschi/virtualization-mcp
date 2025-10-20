"""
VirtualBox VM management service.

This package provides a modular interface for managing VirtualBox virtual machines.
The functionality is split into logical submodules for better maintainability.
"""

from .base import VMService
from .devices import *  # noqa: F403
from .lifecycle import *  # noqa: F403
from .metrics import *  # noqa: F403
from .network.service import VMNetworkingService
from .snapshots import *  # noqa: F403
from .storage import *  # noqa: F403
from .templates import *  # noqa: F403

__all__ = [
    "VMService",
    "VMNetworkingService",
    # Add other exported symbols as needed
]
