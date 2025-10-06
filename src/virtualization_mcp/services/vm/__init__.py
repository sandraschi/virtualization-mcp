"""
VirtualBox VM management service.

This package provides a modular interface for managing VirtualBox virtual machines.
The functionality is split into logical submodules for better maintainability.
"""

from .base import VMService
from .lifecycle import *
from .snapshots import *
from .network.service import VMNetworkingService
from .storage import *
from .templates import *
from .metrics import *
from .devices import *

__all__ = [
    'VMService',
    'VMNetworkingService',
    # Add other exported symbols as needed
]



