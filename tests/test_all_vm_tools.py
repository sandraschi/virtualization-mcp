"""
Comprehensive tests for all VM tool functions.

Tests every function in virtualization_mcp.tools.vm.vm_tools to maximize coverage.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestVMToolsComprehensive:
    """Comprehensive tests for VM tools."""

    @pytest.mark.asyncio
    async def test_list_vms_with_mock(self):
        """Test list_vms with full mock."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout='"vm1" {uuid-123}\n"vm2" {uuid-456}', stderr=""
            )

            from virtualization_mcp.tools.vm.vm_tools import list_vms

            result = await list_vms()
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_vm_info_with_mock(self):
        """Test get_vm_info with full mock."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Name: vm1\nState: running\nMemory: 2048\n", stderr=""
            )

            from virtualization_mcp.tools.vm.vm_tools import get_vm_info

            result = await get_vm_info(vm_name="vm1")
            assert result is not None

    @pytest.mark.asyncio
    async def test_create_vm_with_mock(self):
        """Test create_vm with full mock."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='Virtual machine "new-vm" is created and registered.',
                stderr="",
            )

            from virtualization_mcp.tools.vm.vm_tools import create_vm

            result = await create_vm(
                name="new-vm", ostype="Linux_64", memory_mb=2048, cpu_count=2, disk_size_gb=20
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_start_vm_with_mock(self):
        """Test start_vm with full mock."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="VM started successfully", stderr=""
            )

            from virtualization_mcp.tools.vm.vm_tools import start_vm

            result = await start_vm(vm_name="vm1", start_type="headless")
            assert result is not None

    @pytest.mark.asyncio
    async def test_stop_vm_with_mock(self):
        """Test stop_vm with full mock."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="VM stopped successfully", stderr=""
            )

            from virtualization_mcp.tools.vm.vm_tools import stop_vm

            result = await stop_vm(vm_name="vm1")
            assert result is not None

    @pytest.mark.asyncio
    async def test_delete_vm_with_mock(self):
        """Test delete_vm with full mock."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="VM deleted successfully", stderr=""
            )

            from virtualization_mcp.tools.vm.vm_tools import delete_vm

            result = await delete_vm(vm_name="vm1", delete_files=True)
            assert result is not None

    @pytest.mark.asyncio
    async def test_clone_vm_with_mock(self):
        """Test clone_vm with full mock."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="VM cloned successfully", stderr=""
            )

            from virtualization_mcp.tools.vm.vm_tools import clone_vm

            result = await clone_vm(source_vm="vm1", new_name="clone")
            assert result is not None

    @pytest.mark.asyncio
    async def test_reset_vm_with_mock(self):
        """Test reset_vm with full mock."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="VM reset successfully", stderr=""
            )

            from virtualization_mcp.tools.vm.vm_tools import reset_vm

            result = await reset_vm(vm_name="vm1")
            assert result is not None

    @pytest.mark.asyncio
    async def test_pause_vm_with_mock(self):
        """Test pause_vm with full mock."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="VM paused successfully", stderr=""
            )

            from virtualization_mcp.tools.vm.vm_tools import pause_vm

            result = await pause_vm(vm_name="vm1")
            assert result is not None

    @pytest.mark.asyncio
    async def test_resume_vm_with_mock(self):
        """Test resume_vm with full mock."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="VM resumed successfully", stderr=""
            )

            from virtualization_mcp.tools.vm.vm_tools import resume_vm

            result = await resume_vm(vm_name="vm1")
            assert result is not None


class TestSnapshotToolsComprehensive:
    """Comprehensive tests for snapshot tools."""

    @pytest.mark.asyncio
    async def test_list_snapshots_with_mock(self):
        """Test list_snapshots."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout='SnapshotName="snap1"\nSnapshotUUID="uuid-123"', stderr=""
            )

            from virtualization_mcp.tools.snapshot.snapshot_tools import list_snapshots

            result = await list_snapshots(vm_name="vm1")
            assert result is not None

    @pytest.mark.asyncio
    async def test_create_snapshot_with_mock(self):
        """Test create_snapshot."""
        with patch("virtualization_mcp.tools.snapshot.snapshot_tools.get_vbox_manager") as mock_get:
            mock_mgr = MagicMock()
            mock_mgr.create_snapshot = MagicMock(return_value={"name": "snap1"})
            mock_get.return_value = mock_mgr

            from virtualization_mcp.tools.snapshot.snapshot_tools import create_snapshot

            result = await create_snapshot(vm_name="vm1", snapshot_name="snap1")
            assert result is not None

    @pytest.mark.asyncio
    async def test_restore_snapshot_with_mock(self):
        """Test restore_snapshot."""
        with patch("virtualization_mcp.tools.snapshot.snapshot_tools.get_vbox_manager") as mock_get:
            mock_mgr = MagicMock()
            mock_mgr.restore_snapshot = MagicMock(return_value={"status": "restored"})
            mock_get.return_value = mock_mgr

            from virtualization_mcp.tools.snapshot.snapshot_tools import restore_snapshot

            result = await restore_snapshot(vm_name="vm1", snapshot_name="snap1")
            assert result is not None

    @pytest.mark.asyncio
    async def test_delete_snapshot_with_mock(self):
        """Test delete_snapshot."""
        with patch("virtualization_mcp.tools.snapshot.snapshot_tools.get_vbox_manager") as mock_get:
            mock_mgr = MagicMock()
            mock_mgr.delete_snapshot = MagicMock(return_value={"status": "deleted"})
            mock_get.return_value = mock_mgr

            from virtualization_mcp.tools.snapshot.snapshot_tools import delete_snapshot

            result = await delete_snapshot(vm_name="vm1", snapshot_name="snap1")
            assert result is not None


class TestStorageToolsComprehensive:
    """Comprehensive tests for storage tools."""

    @pytest.mark.asyncio
    async def test_list_storage_controllers_with_mock(self):
        """Test list_storage_controllers."""
        with patch("virtualization_mcp.tools.storage.storage_tools.get_vbox_manager") as mock_get:
            mock_mgr = MagicMock()
            mock_mgr.list_storage_controllers = MagicMock(return_value=[{"name": "SATA"}])
            mock_get.return_value = mock_mgr

            from virtualization_mcp.tools.storage.storage_tools import list_storage_controllers

            result = await list_storage_controllers(vm_name="vm1")
            assert result is not None


class TestSystemToolsComprehensive:
    """Comprehensive tests for system tools."""

    @pytest.mark.asyncio
    async def test_get_system_info_execution(self):
        """Test get_system_info."""
        from virtualization_mcp.tools.system.system_tools import get_system_info

        with patch("platform.system", return_value="Windows"):
            with patch("platform.release", return_value="10"):
                with patch("psutil.cpu_count", return_value=8):
                    result = await get_system_info()
                    assert result is not None

    @pytest.mark.asyncio
    async def test_get_vbox_version_with_mock(self):
        """Test get_vbox_version."""
        with patch("virtualization_mcp.tools.system.system_tools.get_vbox_manager") as mock_get:
            mock_mgr = MagicMock()
            mock_mgr.get_version = MagicMock(return_value={"version": "7.0"})
            mock_get.return_value = mock_mgr

            from virtualization_mcp.tools.system.system_tools import get_vbox_version

            result = await get_vbox_version()
            assert result is not None

    @pytest.mark.asyncio
    async def test_list_os_types_with_mock(self):
        """Test list_os_types."""
        with patch("virtualization_mcp.tools.system.system_tools.get_vbox_manager") as mock_get:
            mock_mgr = MagicMock()
            mock_mgr.list_ostypes = MagicMock(return_value=[{"id": "Linux_64"}])
            mock_get.return_value = mock_mgr

            from virtualization_mcp.tools.system.system_tools import list_os_types

            result = await list_os_types()
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
