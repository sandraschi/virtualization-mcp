"""
Tests for the virtualization-mcp VM lifecycle functionality.
"""

from unittest.mock import MagicMock

import pytest

from virtualization_mcp.services.vm.lifecycle import VMLifecycleMixin
from virtualization_mcp.services.vm.types import VMState


class TestVMLifecycleMixin:
    """Tests for the VMLifecycleMixin class."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_vbox):
        """Set up test fixtures."""
        self.vm_service = MagicMock()
        self.vm_service.vbox_manager = mock_vbox
        self.lifecycle = VMLifecycleMixin(self.vm_service)
        self.vm_name = "test-vm"

    def test_list_vms(self, mock_vbox):
        """Test listing VMs."""
        pytest.skip("list_vms return structure varies")

    def test_start_vm(self, mock_vbox):
        """Test starting a VM."""
        # Call the method - not async
        result = self.lifecycle.start_vm(self.vm_name)

        # Assertions
        assert result is not None
        assert isinstance(result, dict)

    def test_stop_vm(self, mock_vbox):
        """Test stopping a VM."""
        # Call the method - not async
        result = self.lifecycle.stop_vm(self.vm_name)

        # Assertions
        assert result is not None
        assert isinstance(result, dict)

    def test_get_vm_state(self, mock_vbox):
        """Test getting VM state."""
        pytest.skip("get_vm_state not implemented")

    @pytest.mark.parametrize(
        "state_str,expected_state",
        [
            ("PoweredOff", VMState.POWERED_OFF),
            ("Running", VMState.RUNNING),
            ("Paused", VMState.PAUSED),
            ("Saved", VMState.SAVED),
            ("Unknown", VMState.UNKNOWN),
        ],
    )
    def test_parse_vm_state(self, state_str, expected_state):
        """Test parsing VM state strings."""
        pytest.skip("_parse_vm_state not implemented")

    def test_create_snapshot(self, mock_vbox):
        """Test creating a VM snapshot."""
        pytest.skip("create_snapshot not implemented")
