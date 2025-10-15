"""
VirtualBox VM management service.

This package provides a modular interface for managing VirtualBox virtual machines.
The functionality is split into logical submodules for better maintainability.
"""

from .base import VMService
from .devices import *
from .lifecycle import *
from .metrics import *
from .network.service import VMNetworkingService
from .snapshots import *
from .storage import *
from .templates import *

__all__ = [
    "VMService",
    "VMNetworkingService",
    # Add other exported symbols as needed
]
