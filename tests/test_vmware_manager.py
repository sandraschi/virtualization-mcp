"""Phase 2 tests for VmwareManager (no real Workstation needed)."""

from unittest.mock import AsyncMock, patch

import pytest

from virtualization_mcp.services.vmware_manager import VmwareManager


def test_parse_list_output():
    out = "Total running VMs: 2\nC:\\VMs\\a\\a.vmx\nC:\\VMs\\b\\b.vmx\n"
    assert VmwareManager.parse_list_output(out) == ["C:\\VMs\\a\\a.vmx", "C:\\VMs\\b\\b.vmx"]
    assert VmwareManager.parse_list_output("") == []
    assert VmwareManager.parse_list_output("garbage") == []


def test_parse_vmx(tmp_path):
    vmx = tmp_path / "test.vmx"
    vmx.write_text('displayName = "macos26"\nguestOS = "darwin23-64"\nmemsize = "16384"\n# comment\n')
    meta = VmwareManager.parse_vmx(vmx)
    assert meta["displayName"] == "macos26"
    assert meta["guestOS"] == "darwin23-64"
    assert meta["memsize"] == "16384"
    assert VmwareManager.parse_vmx(tmp_path / "missing.vmx") == {}


def test_is_available_false_without_vmrun(tmp_path):
    mgr = VmwareManager(vmrun_path=tmp_path / "nope.exe")
    assert mgr.vmrun_path is None
    assert mgr.is_available() is False


@pytest.mark.asyncio
async def test_list_vms_merges_running_and_inventory(tmp_path):
    mgr = VmwareManager(vmrun_path=tmp_path / "nope.exe")
    mgr.vmrun_path = tmp_path / "vmrun.exe"  # bypass None guard for _run_vmrun mock
    running_stdout = "Total running VMs: 1\nC:\\VMs\\a\\a.vmx\n"
    with (
        patch.object(mgr, "_run_vmrun", AsyncMock(return_value=running_stdout)),
        patch.object(
            mgr,
            "scan_inventory",
            return_value=[
                {"name": "a", "vmx_path": "C:\\VMs\\a\\a.vmx", "provider": "vmware"},
                {"name": "b", "vmx_path": "C:\\VMs\\b\\b.vmx", "provider": "vmware"},
            ],
        ),
    ):
        vms = await mgr.list_vms()
    by_path = {v["vmx_path"]: v["state"] for v in vms}
    assert by_path == {"C:\\VMs\\a\\a.vmx": "running", "C:\\VMs\\b\\b.vmx": "stopped"}


@pytest.mark.asyncio
async def test_start_stop_build_correct_vmrun_args(tmp_path):
    mgr = VmwareManager(vmrun_path=tmp_path / "nope.exe")
    mgr.vmrun_path = tmp_path / "vmrun.exe"
    with patch.object(mgr, "_run_vmrun", AsyncMock(return_value="")) as m:
        await mgr.start_vm("C:\\VMs\\a\\a.vmx")
        m.assert_awaited_with("-T", "ws", "start", "C:\\VMs\\a\\a.vmx", "nogui", timeout=120)
    with patch.object(mgr, "_run_vmrun", AsyncMock(return_value="")) as m:
        await mgr.stop_vm("C:\\VMs\\a\\a.vmx", hard=True)
        m.assert_awaited_with("-T", "ws", "stop", "C:\\VMs\\a\\a.vmx", "hard", timeout=120)


def test_parse_snapshot_list():
    assert VmwareManager.parse_snapshot_list("clean\nbefore-xcode\n") == ["clean", "before-xcode"]
    assert VmwareManager.parse_snapshot_list("") == []


@pytest.mark.asyncio
async def test_phase2_actions_build_correct_args(tmp_path):
    mgr = VmwareManager(vmrun_path=tmp_path / "nope.exe")
    mgr.vmrun_path = tmp_path / "vmrun.exe"
    cases = [
        ("reset_vm", ("C:\\VMs\\a.vmx",), ("-T", "ws", "reset", "C:\\VMs\\a.vmx"), {"timeout": 120}),
        ("suspend_vm", ("C:\\VMs\\a.vmx",), ("-T", "ws", "suspend", "C:\\VMs\\a.vmx"), {"timeout": 180}),
        ("pause_vm", ("C:\\VMs\\a.vmx",), ("-T", "ws", "pause", "C:\\VMs\\a.vmx"), {}),
        ("unpause_vm", ("C:\\VMs\\a.vmx",), ("-T", "ws", "unpause", "C:\\VMs\\a.vmx"), {}),
    ]
    for method, args, expected, kw in cases:
        with patch.object(mgr, "_run_vmrun", AsyncMock(return_value="")) as m:
            await getattr(mgr, method)(*args)
            m.assert_awaited_with(*expected, **kw)
    with patch.object(mgr, "_run_vmrun", AsyncMock(return_value="")) as m:
        await mgr.create_snapshot("C:\\VMs\\a.vmx", "clean")
        m.assert_awaited_with("-T", "ws", "snapshot", "C:\\VMs\\a.vmx", "clean", timeout=180)
    with patch.object(mgr, "_run_vmrun", AsyncMock(return_value="clean\n")) as m:
        snaps = await mgr.list_snapshots("C:\\VMs\\a.vmx")
        assert snaps == [{"name": "clean", "vmx_path": "C:\\VMs\\a.vmx"}]
    with patch.object(mgr, "_run_vmrun", AsyncMock(return_value="192.168.1.10\n")) as m:
        ip = await mgr.get_guest_ip("C:\\VMs\\a.vmx")
        assert ip["ip"] == "192.168.1.10"
