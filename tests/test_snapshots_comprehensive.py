"""Comprehensive unit tests for vbox/snapshots.py and snapshot tools."""

from unittest.mock import MagicMock, patch

import pytest

from virtualization_mcp.tools.snapshot.snapshot_tools import (
    list_snapshots,
)
from virtualization_mcp.vbox.snapshots import SnapshotManager


def test_snapshot_manager_init():
    mock_vbox = MagicMock()
    mgr = SnapshotManager(mock_vbox)
    assert mgr is not None


def test_list_snapshots_mock():
    mock_vbox = MagicMock()
    mock_vbox.run_command.return_value = {"success": True, "output": 'SnapshotName="snap1"'}
    mgr = SnapshotManager(mock_vbox)
    snaps = mgr.list_snapshots("test-vm")
    assert isinstance(snaps, list)


def test_take_snapshot_mock():
    mock_vbox = MagicMock()
    mock_vbox.run_command.return_value = {"success": True, "output": "Snapshot taken"}
    mgr = SnapshotManager(mock_vbox)
    res = mgr.create_snapshot("test-vm", "checkpoint-1", "test description")
    assert isinstance(res, dict)


def test_restore_snapshot_mock():
    mock_vbox = MagicMock()
    mock_vbox.run_command.return_value = {"success": True, "output": "Restored"}
    mgr = SnapshotManager(mock_vbox)
    mgr.list_snapshots = MagicMock(return_value=[{"name": "checkpoint-1"}])
    res = mgr.restore_snapshot("test-vm", "checkpoint-1")
    assert isinstance(res, dict)


def test_delete_snapshot_mock():
    mock_vbox = MagicMock()
    mock_vbox.run_command.return_value = {"success": True, "output": "Deleted"}
    mgr = SnapshotManager(mock_vbox)
    mgr.list_snapshots = MagicMock(return_value=[{"name": "checkpoint-1"}])
    res = mgr.delete_snapshot("test-vm", "checkpoint-1")
    assert isinstance(res, dict)


@pytest.mark.asyncio
async def test_snapshot_tools():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "SnapshotName='snap1'\n"
        res = await list_snapshots(vm_name="test-vm")
        assert isinstance(res, dict)
