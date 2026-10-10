"""Tests for full Hyper-V lifecycle (VMConnect parity)."""

import json

import pytest

from virtualization_mcp.services.hyperv_manager import HyperVManager
from virtualization_mcp.tools.portmanteau.hyperv_management import HYPERV_ACTIONS


@pytest.fixture()
def manager(monkeypatch):
    m = HyperVManager()
    monkeypatch.setattr(m, "_check_available", True)

    async def fake_is_available():
        return True

    monkeypatch.setattr(m, "is_available", fake_is_available)
    return m


@pytest.mark.asyncio
async def test_delete_vm_runs_remove_vm(manager, monkeypatch):
    seen = []

    async def fake_run(cmd):
        seen.append(cmd)
        return ""

    monkeypatch.setattr(manager, "_run_ps", fake_run)
    monkeypatch.setattr("os.path.isdir", lambda _p: False)
    result = await manager.delete_vm("TestVM", delete_vhd=False)
    assert result["status"] == "success"
    assert any("Remove-VM" in c and "TestVM" in c for c in seen)


@pytest.mark.asyncio
async def test_checkpoint_crud_cmdlets(manager, monkeypatch):
    seen = []

    async def fake_run(cmd):
        seen.append(cmd)
        if "Get-VMSnapshot" in cmd:
            return json.dumps({"Name": "cp1", "SnapshotType": "Standard", "CreationTime": "t", "Id": "1"})
        return ""

    monkeypatch.setattr(manager, "_run_ps", fake_run)
    cps = await manager.list_checkpoints("VM1")
    assert cps and cps[0]["name"] == "cp1"
    assert (await manager.create_checkpoint("VM1", "cp2"))["status"] == "success"
    assert (await manager.restore_checkpoint("VM1", "cp2"))["status"] == "success"
    assert (await manager.remove_checkpoint("VM1", "cp2"))["status"] == "success"
    joined = "\n".join(seen)
    assert "Checkpoint-VM" in joined
    assert "Restore-VMSnapshot" in joined
    assert "Remove-VMSnapshot" in joined


@pytest.mark.asyncio
async def test_switch_crud_cmdlets(manager, monkeypatch):
    seen = []

    async def fake_run(cmd):
        seen.append(cmd)
        if "Get-VMSwitch" in cmd:
            return json.dumps({"Name": "Default Switch", "SwitchType": "Internal"})
        return ""

    monkeypatch.setattr(manager, "_run_ps", fake_run)
    switches = await manager.list_switches()
    assert switches and switches[0]["name"] == "Default Switch"
    assert (await manager.create_switch("TestSw", "Bogus"))["status"] == "success"
    assert "Internal" in seen[-1]  # invalid type falls back to Internal
    assert (await manager.connect_network("VM1", "TestSw"))["status"] == "success"
    assert any("Connect-VMNetworkAdapter" in c for c in seen)


@pytest.mark.asyncio
async def test_attach_iso_rejects_missing_file(manager):
    result = await manager.attach_iso("VM1", "C:/definitely/not/here.iso")
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_enhanced_session_cmdlets(manager, monkeypatch):
    seen = []

    async def fake_run(cmd):
        seen.append(cmd)
        if "Get-VMHost" in cmd:
            return json.dumps({"EnableEnhancedSessionMode": True})
        return ""

    monkeypatch.setattr(manager, "_run_ps", fake_run)
    got = await manager.get_enhanced_session()
    assert got["enabled"] is True
    set_result = await manager.set_enhanced_session(False)
    assert set_result["status"] == "success"
    assert any("Set-VMHost" in c for c in seen)


def test_connect_command_format(manager):
    cmd = manager.connect_command("VM1")
    assert cmd["command"] == "vmconnect.exe localhost VM1"
    assert "/edit" in cmd["edit_command"]


@pytest.mark.asyncio
async def test_quote_escaping(manager, monkeypatch):
    seen = []

    async def fake_run(cmd):
        seen.append(cmd)
        return ""

    monkeypatch.setattr(manager, "_run_ps", fake_run)
    await manager.start_vm("O'Brien")
    assert "O''Brien" in seen[-1]


def test_portmanteau_covers_vmconnect_parity():
    for action in (
        "list",
        "get",
        "create",
        "delete",
        "start",
        "stop",
        "pause",
        "resume",
        "checkpoint_list",
        "checkpoint_create",
        "checkpoint_restore",
        "checkpoint_delete",
        "switch_list",
        "switch_create",
        "network_connect",
        "iso_attach",
        "iso_detach",
        "enhanced_get",
        "enhanced_set",
        "console",
    ):
        assert action in HYPERV_ACTIONS
