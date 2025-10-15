"""
Comprehensive VM Service Tests

Target: vm_service.py (446 lines at 11% → 50% = +175 lines = +1.95% coverage!)

Test EVERY method with:
- Success paths
- Error paths
- Different parameters
- Edge cases
"""

from unittest.mock import MagicMock, patch

import pytest

from virtualization_mcp.services.vm_service import VMService
from virtualization_mcp.vbox.compat_adapter import VBoxManagerError


class TestVMServiceInit:
    """Test VMService initialization."""

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_init_with_python_api(self, mock_vm_ops, mock_get_manager):
        """Test VMService init with Python API backend."""
        mock_manager = MagicMock()
        mock_manager.api = MagicMock()  # Has API attribute
        mock_get_manager.return_value = mock_manager

        service = VMService()

        assert service.vbox_manager == mock_manager
        mock_vm_ops.assert_called_once_with(mock_manager)

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_init_with_vboxmanage_cli(self, mock_vm_ops, mock_get_manager):
        """Test VMService init with VBoxManage CLI backend."""
        mock_manager = MagicMock()
        # No API attribute - uses CLI
        if hasattr(mock_manager, "api"):
            delattr(mock_manager, "api")
        mock_get_manager.return_value = mock_manager

        service = VMService()

        assert service.vbox_manager == mock_manager


class TestVMServiceGetState:
    """Test get_vm_state method with all paths."""

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_get_vm_state_success(self, mock_vm_ops, mock_get_manager):
        """Test successful get_vm_state."""
        mock_manager = MagicMock()
        mock_manager.vm_exists.return_value = True
        mock_manager.get_vm_state.return_value = "Running"
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.get_vm_state("test-vm")

        assert result["status"] == "success"
        assert result["vm_name"] == "test-vm"
        assert result["state"] == "running"
        assert "message" in result
        assert "troubleshooting" in result

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_get_vm_state_vm_not_exists(self, mock_vm_ops, mock_get_manager):
        """Test get_vm_state when VM doesn't exist."""
        mock_manager = MagicMock()
        mock_manager.vm_exists.return_value = False
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.get_vm_state("nonexistent-vm")

        assert result["status"] == "error"
        assert result["vm_name"] == "nonexistent-vm"
        assert "error" in result
        assert "does not exist" in result["error"]

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_get_vm_state_error(self, mock_vm_ops, mock_get_manager):
        """Test get_vm_state when error occurs."""
        mock_manager = MagicMock()
        mock_manager.vm_exists.return_value = True
        mock_manager.get_vm_state.side_effect = VBoxManagerError("Connection failed")
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.get_vm_state("test-vm")

        assert result["status"] == "error"
        assert "Connection failed" in result["error"]


class TestVMServiceCreateVM:
    """Test create_vm method with all paths."""

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_create_vm_success_default(self, mock_vm_ops, mock_get_manager):
        """Test successful VM creation with defaults."""
        mock_manager = MagicMock()
        mock_manager.create_vm.return_value = {"id": "vm-123", "name": "test-vm"}
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.create_vm("test-vm")

        # Should call create_vm with template settings
        assert mock_manager.create_vm.called

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_create_vm_with_overrides(self, mock_vm_ops, mock_get_manager):
        """Test VM creation with resource overrides."""
        mock_manager = MagicMock()
        mock_manager.create_vm.return_value = {"id": "vm-123", "name": "test-vm"}
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.create_vm("test-vm", template="ubuntu-dev", memory_mb=4096, disk_gb=50)

        assert mock_manager.create_vm.called


class TestVMServiceListVMs:
    """Test list_vms method."""

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_list_vms_success(self, mock_vm_ops, mock_get_manager):
        """Test successful list_vms."""
        mock_manager = MagicMock()
        mock_manager.list_vms.return_value = [
            {"name": "vm1", "state": "running"},
            {"name": "vm2", "state": "poweroff"},
        ]
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.list_vms()

        assert isinstance(result, (list, dict))


class TestVMServiceStartStopVM:
    """Test start/stop VM methods."""

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_start_vm_success(self, mock_vm_ops, mock_get_manager):
        """Test successful VM start."""
        mock_manager = MagicMock()
        mock_manager.start_vm.return_value = {"status": "success"}
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.start_vm("test-vm")

        mock_manager.start_vm.assert_called_once_with("test-vm", gui=False)

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_start_vm_with_gui(self, mock_vm_ops, mock_get_manager):
        """Test VM start with GUI mode."""
        mock_manager = MagicMock()
        mock_manager.start_vm.return_value = {"status": "success"}
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.start_vm("test-vm", gui=True)

        mock_manager.start_vm.assert_called_once_with("test-vm", gui=True)

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_stop_vm_success(self, mock_vm_ops, mock_get_manager):
        """Test successful VM stop."""
        mock_manager = MagicMock()
        mock_manager.stop_vm.return_value = {"status": "success"}
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.stop_vm("test-vm")

        mock_manager.stop_vm.assert_called_once()

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_stop_vm_force(self, mock_vm_ops, mock_get_manager):
        """Test force stop VM."""
        mock_manager = MagicMock()
        mock_manager.stop_vm.return_value = {"status": "success"}
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.stop_vm("test-vm", force=True)

        mock_manager.stop_vm.assert_called_once()


class TestVMServiceDeleteVM:
    """Test delete_vm method."""

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_delete_vm_success(self, mock_vm_ops, mock_get_manager):
        """Test successful VM deletion."""
        mock_manager = MagicMock()
        mock_manager.delete_vm.return_value = {"status": "success"}
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.delete_vm("test-vm")

        mock_manager.delete_vm.assert_called_once()


class TestVMServiceCloneVM:
    """Test clone_vm method."""

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_clone_vm_success(self, mock_vm_ops, mock_get_manager):
        """Test successful VM cloning."""
        mock_manager = MagicMock()
        mock_manager.clone_vm.return_value = {"status": "success"}
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.clone_vm("source-vm", "clone-vm")

        mock_manager.clone_vm.assert_called_once()


class TestVMServiceSnapshots:
    """Test snapshot-related methods."""

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_create_snapshot(self, mock_vm_ops, mock_get_manager):
        """Test snapshot creation."""
        mock_manager = MagicMock()
        mock_manager.create_snapshot.return_value = {"status": "success"}
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.create_snapshot("test-vm", "snapshot-1")

        mock_manager.create_snapshot.assert_called_once()

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_restore_snapshot(self, mock_vm_ops, mock_get_manager):
        """Test snapshot restoration."""
        mock_manager = MagicMock()
        mock_manager.restore_snapshot.return_value = {"status": "success"}
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.restore_snapshot("test-vm", "snapshot-1")

        mock_manager.restore_snapshot.assert_called_once()

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_delete_snapshot(self, mock_vm_ops, mock_get_manager):
        """Test snapshot deletion."""
        mock_manager = MagicMock()
        mock_manager.delete_snapshot.return_value = {"status": "success"}
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.delete_snapshot("test-vm", "snapshot-1")

        mock_manager.delete_snapshot.assert_called_once()

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_list_snapshots(self, mock_vm_ops, mock_get_manager):
        """Test snapshot listing."""
        mock_manager = MagicMock()
        mock_manager.list_snapshots.return_value = [{"name": "snap1", "uuid": "123"}]
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.list_snapshots("test-vm")

        mock_manager.list_snapshots.assert_called_once()


class TestVMServiceModifyVM:
    """Test modify_vm method."""

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_modify_vm_memory(self, mock_vm_ops, mock_get_manager):
        """Test modifying VM memory."""
        mock_manager = MagicMock()
        mock_manager.modify_vm.return_value = {"status": "success"}
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.modify_vm("test-vm", memory_mb=4096)

        mock_manager.modify_vm.assert_called_once()

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_modify_vm_cpus(self, mock_vm_ops, mock_get_manager):
        """Test modifying VM CPUs."""
        mock_manager = MagicMock()
        mock_manager.modify_vm.return_value = {"status": "success"}
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.modify_vm("test-vm", cpus=4)

        mock_manager.modify_vm.assert_called_once()


class TestVMServiceGetInfo:
    """Test get_vm_info method."""

    @patch("virtualization_mcp.services.vm_service.get_vbox_manager")
    @patch("virtualization_mcp.services.vm_service.VMOperations")
    def test_get_vm_info_success(self, mock_vm_ops, mock_get_manager):
        """Test successful get_vm_info."""
        mock_manager = MagicMock()
        mock_manager.get_vm_info.return_value = {
            "name": "test-vm",
            "state": "running",
            "memory": 2048,
            "cpus": 2,
        }
        mock_get_manager.return_value = mock_manager

        service = VMService()
        result = service.get_vm_info("test-vm")

        assert isinstance(result, dict)
        mock_manager.get_vm_info.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
