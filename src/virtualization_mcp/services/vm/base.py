"""
Base VM service module containing the core VMService class and shared functionality.
"""

import logging

from ...config import get_vbox_manage_path
from ...vbox.manager import VBoxManager
from ...vbox.vm_operations import VMOperations

logger = logging.getLogger(__name__)


class VMService:
    """Service for managing VirtualBox VMs."""

    def __init__(self):
        """Initialize the VM service with a VBoxManager instance."""
        self.vbox_manager = VBoxManager(vbox_manage_path=get_vbox_manage_path())
        self.vm_operations = VMOperations(self.vbox_manager)

        # Initialize submodules
        self._setup_submodules()

    def _setup_submodules(self):
        """Initialize and attach submodules to the VMService instance."""
        from . import devices, lifecycle, metrics, snapshots, storage, templates
        from .network.service import VMNetworkingService

        # Initialize each submodule with required dependencies
        self.lifecycle = lifecycle.VMLifecycleMixin(self)
        self.snapshots = snapshots.VMSnapshotMixin(self)
        self.networking = VMNetworkingService(self)
        self.storage = storage.VMStorageMixin(self)
        self.templates = templates.VMTemplateMixin(self)
        self.metrics = metrics.VMMetricsMixin(self)
        self.devices = devices.VMDeviceMixin(self)

        # Add methods from mixins to the main service
        self._add_methods_from_mixin(self.lifecycle)
        self._add_methods_from_mixin(self.snapshots)
        self._add_methods_from_mixin(self.networking)
        self._add_methods_from_mixin(self.storage)
        self._add_methods_from_mixin(self.templates)
        self._add_methods_from_mixin(self.metrics)
        self._add_methods_from_mixin(self.devices)

    def _add_methods_from_mixin(self, mixin):
        """Add methods from a mixin to the VMService instance."""
        for method_name in dir(mixin):
            if not method_name.startswith("_") and callable(getattr(mixin, method_name)):
                setattr(self, method_name, getattr(mixin, method_name))
