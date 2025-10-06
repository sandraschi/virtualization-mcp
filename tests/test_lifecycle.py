"""
Tests for the vboxmcp VM lifecycle functionality.
"""
import pytest
from unittest.mock import MagicMock, patch, call

from virtualization_mcp.services.vm.lifecycle import VMLifecycleMixin
from virtualization_mcp.services.vm.types import VMState, VMPowerState

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
        # Setup mock
        mock_vbox.list_vms.return_value = [{"name": self.vm_name, "state": "PoweredOff"}]
        
        # Call the method
        result = self.lifecycle.list_vms()
        
        # Assertions
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == self.vm_name
        mock_vbox.list_vms.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_start_vm(self, mock_vbox):
        """Test starting a VM."""
        # Setup mock
        mock_vm = mock_vbox.machine
        mock_vm.get_machine_state.return_value = "PoweredOff"
        
        # Call the method
        result = await self.lifecycle.start_vm(self.vm_name)
        
        # Assertions
        assert result["status"] == "success"
        mock_vbox.find_machine.assert_called_once_with(self.vm_name)
        mock_vm.launch_vm_process.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_stop_vm(self, mock_vbox):
        """Test stopping a VM."""
        # Setup mock
        mock_session = MagicMock()
        mock_vm = mock_vbox.machine
        mock_vm.get_machine_state.return_value = "Running"
        
        # Call the method
        result = await self.lifecycle.stop_vm(self.vm_name)
        
        # Assertions
        assert result["status"] == "success"
        mock_vbox.find_machine.assert_called_once_with(self.vm_name)
        mock_vm.get_session.assert_called_once()
        
    def test_get_vm_state(self, mock_vbox):
        """Test getting VM state."""
        # Setup mock
        mock_vm = mock_vbox.machine
        mock_vm.get_machine_state.return_value = "Running"
        
        # Call the method
        result = self.lifecycle.get_vm_state(self.vm_name)
        
        # Assertions
        assert "state" in result
        assert result["state"] == VMState.RUNNING
        mock_vbox.find_machine.assert_called_once_with(self.vm_name)
        
    @pytest.mark.parametrize("state_str,expected_state", [
        ("PoweredOff", VMState.POWERED_OFF),
        ("Running", VMState.RUNNING),
        ("Paused", VMState.PAUSED),
        ("Saved", VMState.SAVED),
        ("Unknown", VMState.UNKNOWN)
    ])
    def test_parse_vm_state(self, state_str, expected_state):
        """Test parsing VM state strings."""
        result = self.lifecycle._parse_vm_state(state_str)
        assert result == expected_state
        
    def test_create_snapshot(self, mock_vbox):
        """Test creating a VM snapshot."""
        # Setup mock
        snapshot_name = "test-snapshot"
        snapshot_desc = "Test snapshot"
        
        # Call the method
        result = self.lifecycle.create_snapshot(
            self.vm_name,
            snapshot_name,
            snapshot_desc
        )
        
        # Assertions
        assert result["status"] == "success"
        mock_vbox.find_machine.assert_called_once_with(self.vm_name)
        mock_vbox.machine.take_snapshot.assert_called_once_with(
            snapshot_name,
            snapshot_desc,
            False  # Not live
        )
