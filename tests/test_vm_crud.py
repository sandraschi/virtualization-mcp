"""Tests for VM CRUD operations via vm_operations (template-based creation path)."""

from unittest.mock import patch

import pytest

from virtualization_mcp.vbox.compat_adapter import VBoxManager, VBoxManagerError
from virtualization_mcp.vbox.vm_operations import VMOperations


@pytest.fixture
def mock_vbox():
    """VBoxManager with mocked subprocess calls."""
    with (
        patch("virtualization_mcp.vbox.compat_adapter.VBoxManage") as mock_cls,
        patch("virtualization_mcp.vbox.compat_adapter.VBoxManager._validate_vboxmanage"),
        patch("virtualization_mcp.vbox.compat_adapter.VBoxManager._find_vboxmanage", return_value="VBoxManage"),
        patch("subprocess.run") as mock_run,
    ):
        mock_cls.return_value.version = "7.2.6"
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        mgr = VBoxManager()
        yield mgr, mock_run


@pytest.fixture
def ops(mock_vbox):
    """VMOperations instance with mocked VBoxManager."""
    mgr, mock_run = mock_vbox
    with patch.object(mgr, "get_vm_info", return_value={"name": "test-vm", "vmstate": "poweroff", "memory": "1024"}):
        yield VMOperations(mgr), mock_run


class TestCreateVM:
    """Template-based VM creation."""

    def test_create_vm_success(self, ops):
        vm_ops, mock_run = ops
        result = vm_ops.create_vm(name="test-vm", template="ubuntu-dev")
        assert result["success"] is True
        assert result["vm_name"] == "test-vm"
        # Should have called createvm, modifyvm, storagectl, storageattach
        calls = [args[0][0] for args in mock_run.call_args_list]
        creatvm_calls = [c for c in calls if "createvm" in str(c)]
        assert len(creatvm_calls) >= 1

    def test_create_vm_invalid_name(self, ops):
        vm_ops, _mock_run = ops
        with pytest.raises(VBoxManagerError, match="Invalid VM name"):
            vm_ops.create_vm(name="my/vm")

    def test_create_vm_duplicate(self, ops):
        vm_ops, _mock_run = ops
        # First call succeeds
        with patch.object(vm_ops.manager, "vm_exists", return_value=True):
            with pytest.raises(VBoxManagerError, match="already exists"):
                vm_ops.create_vm(name="existing-vm")

    def test_create_vm_bad_template(self, ops):
        vm_ops, _mock_run = ops
        with pytest.raises(VBoxManagerError, match="Template.*not found"):
            vm_ops.create_vm(name="test-vm", template="nonexistent")

    def test_create_vm_with_overrides(self, ops):
        vm_ops, _mock_run = ops
        result = vm_ops.create_vm(name="test-vm", template="ubuntu-dev", memory_mb=8192, disk_gb=50, cpus=4)
        assert result["success"] is True
        assert result["configuration"]["memory_mb"] == 8192
        assert result["configuration"]["disk_gb"] == 50
        assert result["configuration"]["cpus"] == 4


class TestAttachISO:
    """ISO attachment to VM."""

    def test_attach_iso_calls_subprocess(self, ops):
        vm_ops, mock_run = ops
        result = vm_ops.attach_iso("test-vm", r"D:\isos\ubuntu.iso")
        assert result["success"] is True
        # Check subprocess was called with storageattach
        calls = mock_run.call_args_list
        attach_calls = [c for c in calls if "storageattach" in str(c)]
        assert len(attach_calls) >= 1
        # Check IDE controller was added
        ide_calls = [c for c in calls if "storagectl" in str(c)]
        assert len(ide_calls) >= 1

    def test_attach_iso_failure_reported(self, ops):
        vm_ops, mock_run = ops
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "VBoxManage: error: VM not found"
        result = vm_ops.attach_iso("nonexistent-vm", r"D:\isos\ubuntu.iso")
        assert result["success"] is False
        assert "error" in result


class TestDeleteVM:
    """VM deletion."""

    def test_delete_vm_success(self, ops):
        vm_ops, _mock_run = ops
        with patch.object(vm_ops.manager, "vm_exists", return_value=True):
            result = vm_ops.delete_vm("test-vm")
            assert result["success"] is True

    def test_delete_vm_not_found(self, ops):
        vm_ops, _mock_run = ops
        with patch.object(vm_ops.manager, "vm_exists", return_value=False):
            with pytest.raises(VBoxManagerError, match="not found"):
                vm_ops.delete_vm("nonexistent")


class TestListVMs:
    """VM listing."""

    def test_list_vms_success(self, ops):
        vm_ops, _mock_run = ops
        with patch.object(vm_ops.manager, "list_vms", return_value=[
            {"name": "vm1", "state": "running"},
            {"name": "vm2", "state": "poweroff"},
        ]):
            result = vm_ops.list_vms()
            assert result["success"] is True
            assert len(result["vms"]) == 2

    def test_list_vms_empty(self, ops):
        vm_ops, _mock_run = ops
        with patch.object(vm_ops.manager, "list_vms", return_value=[]):
            result = vm_ops.list_vms()
            assert result["success"] is True
            assert result["vms"] == []
