"""Comprehensive unit & integration tests for Windows Sandbox bringup paths and sandbox_management tools."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from virtualization_mcp.tools.portmanteau.sandbox_management import sandbox_management
from virtualization_mcp.utils.windows_sandbox_helper import WindowsSandboxError, WindowsSandboxHelper


def _bare_helper(tmp_path):
    helper = WindowsSandboxHelper.__new__(WindowsSandboxHelper)
    helper.sandbox_dir = tmp_path
    helper._sandbox_processes = {}
    return helper


def test_launch_scripts_exist():
    repo_root = Path(__file__).resolve().parent.parent
    consumer_script = repo_root / "scripts" / "Launch-ConsumerSandbox.ps1"
    devinfra_script = repo_root / "scripts" / "Launch-DevInfraSandbox.ps1"

    assert consumer_script.exists(), "Launch-ConsumerSandbox.ps1 must exist"
    assert devinfra_script.exists(), "Launch-DevInfraSandbox.ps1 must exist"


def test_windows_sandbox_helper_is_running():
    with patch("psutil.process_iter") as mock_iter:
        mock_proc = MagicMock()
        mock_proc.info = {"name": "WindowsSandboxClient.exe"}
        mock_iter.return_value = [mock_proc]

        running = WindowsSandboxHelper.is_sandbox_running()
        assert running is True


def _sandbox_module():
    import virtualization_mcp.utils.windows_sandbox_helper as mod

    return mod


def test_windows_sandbox_helper_terminate_active_graceful():
    # Ladder phase 1: clients close cleanly, no per-process kill needed.
    with (
        patch.object(
            WindowsSandboxHelper,
            "sandbox_process_snapshot",
            return_value=[{"pid": 111, "name": "WindowsSandbox.exe", "via": "psutil"}],
        ),
        patch.object(WindowsSandboxHelper, "graceful_close_clients", return_value=True) as mock_graceful,
        patch("psutil.process_iter") as mock_iter,
    ):
        detail = WindowsSandboxHelper.terminate_active_sandbox_detailed()
        assert detail["present"] is True
        assert detail["gone"] is True
        assert detail["method"] == "graceful-close"
        mock_graceful.assert_called_once()
        mock_iter.assert_not_called()


def test_windows_sandbox_helper_terminate_active_via_terminate():
    # Ladder phase 2: graceful fails, terminate() clears it, running-check confirms.
    mock_proc = MagicMock()
    mock_proc.info = {"pid": 1234, "name": "WindowsSandbox.exe"}
    mock_proc.pid = 1234
    with (
        patch.object(
            WindowsSandboxHelper,
            "sandbox_process_snapshot",
            return_value=[{"pid": 1234, "name": "WindowsSandbox.exe", "via": "psutil"}],
        ),
        patch.object(WindowsSandboxHelper, "graceful_close_clients", return_value=False),
        patch.object(WindowsSandboxHelper, "_tasklist_snapshot", return_value=[]),
        patch.object(WindowsSandboxHelper, "is_sandbox_running", return_value=False),
        patch("psutil.process_iter", return_value=[mock_proc]),
        patch("psutil.wait_procs", return_value=([mock_proc], [])) as mock_wait,
        patch("time.sleep"),
    ):
        detail = WindowsSandboxHelper.terminate_active_sandbox_detailed()
        assert detail["gone"] is True
        assert detail["method"] == "terminate"
        assert detail["access_denied"] is False
        mock_proc.terminate.assert_called_once()
        mock_wait.assert_called_once()
    # Compat wrapper: present AND gone -> True.
    with patch.object(
        WindowsSandboxHelper, "terminate_active_sandbox_detailed", return_value={"present": True, "gone": True}
    ):
        assert WindowsSandboxHelper.terminate_active_sandbox() is True


def test_windows_sandbox_helper_terminate_nothing_present():
    # Empty snapshot: nothing to do (gone), but the compat wrapper reports
    # False since no sandbox was ever present.
    with patch.object(WindowsSandboxHelper, "sandbox_process_snapshot", return_value=[]):
        detail = WindowsSandboxHelper.terminate_active_sandbox_detailed()
        assert detail == {
            "present": False,
            "gone": True,
            "access_denied": False,
            "still_running": [],
            "method": "none",
        }
    with patch.object(
        WindowsSandboxHelper, "terminate_active_sandbox_detailed", return_value={"present": False, "gone": True}
    ):
        assert WindowsSandboxHelper.terminate_active_sandbox() is False


def test_windows_sandbox_helper_terminate_access_denied_flag():
    # Every stage denied: terminate/kill raise AccessDenied, taskkill rc=1,
    # box still reported running -> gone False, access_denied True (the
    # signal to fire the elevated SYSTEM task, not a silent success).
    import psutil as _psutil

    mock_proc = MagicMock()
    mock_proc.info = {"pid": 4321, "name": "vmmemWindowsSandbox.exe"}
    mock_proc.pid = 4321
    mock_proc.terminate.side_effect = _psutil.AccessDenied(pid=4321, name="vmmemWindowsSandbox.exe")
    mock_proc.kill.side_effect = _psutil.AccessDenied(pid=4321, name="vmmemWindowsSandbox.exe")
    fake_tk = MagicMock()
    fake_tk.returncode = 1
    with (
        patch.object(
            WindowsSandboxHelper,
            "sandbox_process_snapshot",
            return_value=[{"pid": 4321, "name": "vmmemWindowsSandbox.exe", "via": "psutil"}],
        ),
        patch.object(WindowsSandboxHelper, "graceful_close_clients", return_value=False),
        patch.object(WindowsSandboxHelper, "_tasklist_snapshot", return_value=[]),
        patch.object(WindowsSandboxHelper, "is_sandbox_running", return_value=True),
        patch("psutil.process_iter", return_value=[mock_proc]),
        patch("psutil.wait_procs", return_value=([], [mock_proc])),
        patch.object(_sandbox_module(), "subprocess") as mock_sub,
        patch("time.sleep"),
    ):
        mock_sub.run.return_value = fake_tk
        detail = WindowsSandboxHelper.terminate_active_sandbox_detailed()
        assert detail["present"] is True
        assert detail["gone"] is False
        assert detail["access_denied"] is True
        assert detail["method"] == "failed"
    with patch.object(
        WindowsSandboxHelper,
        "terminate_active_sandbox_detailed",
        return_value={"present": True, "gone": False, "access_denied": True},
    ):
        assert WindowsSandboxHelper.terminate_active_sandbox() is False


@pytest.mark.asyncio
async def test_windows_sandbox_execute_in_sandbox(tmp_path):
    # Real behavior, mocked transport: no live Sandbox ever boots here.
    helper = _bare_helper(tmp_path)
    with patch.object(
        helper,
        "_run_oneshot",
        new=AsyncMock(return_value={"status": "completed", "exit_code": 0, "stdout": "Hello Sandbox", "stderr": ""}),
    ) as mock_run:
        res = await helper.execute_in_sandbox(name="test_sb", command="echo Hello Sandbox")
    assert res["success"] is True
    assert res["command"] == "echo Hello Sandbox"
    assert res["stdout"] == "Hello Sandbox"
    assert res["exit_code"] == 0
    mock_run.assert_awaited_once()


@pytest.mark.asyncio
async def test_windows_sandbox_execute_failing_exit(tmp_path):
    helper = _bare_helper(tmp_path)
    with patch.object(
        helper,
        "_run_oneshot",
        new=AsyncMock(return_value={"status": "completed", "exit_code": 1, "stdout": "", "stderr": "boom"}),
    ):
        res = await helper.execute_in_sandbox(name="test_sb", command="exit 1")
    assert res["success"] is False
    assert res["exit_code"] == 1
    assert res["stderr"] == "boom"


@pytest.mark.asyncio
async def test_windows_sandbox_oneshot_busy_singleton(tmp_path):
    # Singleton running -> explicit busy error before any launch attempt.
    helper = _bare_helper(tmp_path)
    with (
        patch.object(WindowsSandboxHelper, "is_sandbox_running", return_value=True),
        patch.object(helper, "_launch_wsb") as mock_launch,
    ):
        with pytest.raises(WindowsSandboxError, match="already running"):
            await helper._run_oneshot("echo hi", timeout=5)
        mock_launch.assert_not_called()


@pytest.mark.asyncio
async def test_windows_sandbox_execute_command_detached(tmp_path):
    import asyncio as _asyncio

    helper = _bare_helper(tmp_path)
    with patch.object(
        helper,
        "_run_oneshot",
        new=AsyncMock(return_value={"status": "completed", "exit_code": 0, "stdout": "", "stderr": ""}),
    ) as mock_run:
        res = await helper.execute_command("job1", "echo hi", wait=False)
        assert res["status"] == "started"
        await _asyncio.sleep(0)  # let the detached task run the stub
        mock_run.assert_awaited_once()


@pytest.mark.asyncio
async def test_windows_sandbox_upload_missing_source(tmp_path):
    helper = _bare_helper(tmp_path)
    with pytest.raises(FileNotFoundError):
        await helper.upload_file("job1", tmp_path / "nope.bin")


@pytest.mark.asyncio
async def test_windows_sandbox_upload_success(tmp_path):
    src = tmp_path / "payload.bin"
    src.write_bytes(b"data")
    helper = _bare_helper(tmp_path)
    with patch.object(
        helper,
        "_run_oneshot",
        new=AsyncMock(return_value={"status": "completed", "exit_code": 0, "stdout": "", "stderr": ""}),
    ) as mock_run:
        res = await helper.upload_file("job1", src)
    assert res["status"] == "success"
    assert res["size"] == 4
    assert "Desktop" in res["destination_path"]
    sent_files = mock_run.await_args.kwargs["files"]
    assert sent_files[f"payload_{src.name}"] == b"data"


@pytest.mark.asyncio
async def test_windows_sandbox_download_success(tmp_path):
    helper = _bare_helper(tmp_path)
    dest = tmp_path / "out.bin"
    with patch.object(
        helper,
        "_run_oneshot",
        new=AsyncMock(
            return_value={
                "status": "completed",
                "exit_code": 0,
                "stdout": "",
                "stderr": "",
                "collected": b"guest-bytes",
            }
        ),
    ):
        res = await helper.download_file("job1", r"C:\Job\result.bin", dest)
    assert res["status"] == "success"
    assert dest.read_bytes() == b"guest-bytes"
    assert res["size"] == len(b"guest-bytes")


@pytest.mark.asyncio
async def test_windows_sandbox_download_missing_guest_file(tmp_path):
    helper = _bare_helper(tmp_path)
    with patch.object(
        helper,
        "_run_oneshot",
        new=AsyncMock(
            return_value={"status": "completed", "exit_code": 1, "stdout": "", "stderr": "not found", "collected": None}
        ),
    ):
        with pytest.raises(WindowsSandboxError, match="Failed to download"):
            await helper.download_file("job1", r"C:\missing.bin", tmp_path / "out.bin")


@pytest.mark.asyncio
async def test_windows_sandbox_list_unmanaged_singleton(tmp_path):
    helper = _bare_helper(tmp_path)
    with patch.object(WindowsSandboxHelper, "is_sandbox_running", return_value=True):
        items = await helper.list_sandboxes()
    assert len(items) == 1
    assert items[0]["status"] == "running"
    assert items[0]["singleton_running"] is True


@pytest.mark.asyncio
async def test_windows_sandbox_terminate_unknown():
    helper = WindowsSandboxHelper.__new__(WindowsSandboxHelper)
    helper._sandbox_processes = {}
    with pytest.raises(WindowsSandboxError, match="not found"):
        await helper.terminate_sandbox("ghost")


@pytest.mark.asyncio
async def test_sandbox_management_win_status():
    with (
        patch(
            "virtualization_mcp.tools.portmanteau.sandbox_management.WindowsSandboxHelper.is_sandbox_running",
            return_value=False,
        ),
        patch(
            "virtualization_mcp.tools.portmanteau.sandbox_management.WindowsSandboxHelper.check_prerequisites",
            return_value={"ready": True},
        ),
    ):
        res = await sandbox_management(action="win_sandbox_status")
        assert res["success"] is True
        assert res["running"] is False


@pytest.mark.asyncio
async def test_sandbox_management_win_terminate():
    with patch(
        "virtualization_mcp.tools.portmanteau.sandbox_management.WindowsSandboxHelper.terminate_active_sandbox",
        return_value=True,
    ):
        res = await sandbox_management(action="win_sandbox_terminate")
        assert res["success"] is True
        assert res["terminated"] is True


@pytest.mark.asyncio
async def test_sandbox_management_win_launch_consumer():
    with patch("subprocess.Popen") as mock_popen:
        res = await sandbox_management(action="win_sandbox_launch_consumer", install_claude_desktop=True)
        assert res["success"] is True
        assert res["action"] == "win_sandbox_launch_consumer"
        mock_popen.assert_called_once()


@pytest.mark.asyncio
async def test_sandbox_management_win_launch_devinfra():
    with patch("subprocess.Popen") as mock_popen:
        res = await sandbox_management(action="win_sandbox_launch_devinfra")
        assert res["success"] is True
        assert res["action"] == "win_sandbox_launch_devinfra"
        mock_popen.assert_called_once()


@pytest.mark.asyncio
async def test_sandbox_management_win_naked_test():
    # Dispatch is fire-and-forget by design: the action validates, creates
    # the job dir, and hands the lifecycle to a background task. Patch the
    # lifecycle (not subprocess.Popen) so no real Sandbox ever boots here.
    import asyncio
    import shutil

    import virtualization_mcp.tools.portmanteau.sandbox_management as sm

    with patch.object(sm, "_naked_test_lifecycle", new=AsyncMock()) as mock_lifecycle:
        res = await sandbox_management(
            action="win_sandbox_naked_test",
            repo="sandraschi/virtualization-mcp",
            branch="main",
            observe_sec=45,
        )
        assert res["success"] is True
        assert res["action"] == "win_sandbox_naked_test"
        assert "job_id" in res
        assert "naked-virtualization-mcp-" in res["job_id"]
        mock_lifecycle.assert_called_once()
        await asyncio.sleep(0)  # let the background task run the stub
        mock_lifecycle.assert_awaited_once()
        awaited_jid = mock_lifecycle.await_args.args[0]
        assert awaited_jid == res["job_id"]
    shutil.rmtree(res.get("run_dir", ""), ignore_errors=True)


@pytest.mark.asyncio
async def test_sandbox_management_win_naked_test_status():
    res = await sandbox_management(action="win_sandbox_naked_test_status", job_id="nonexistent-job-xyz")
    assert res["success"] is False
    assert "Unknown job" in res["error"]


@pytest.mark.asyncio
async def test_sandbox_management_win_naked_test_list():
    res = await sandbox_management(action="win_sandbox_naked_test_list")
    assert res["success"] is True
    assert "jobs" in res
