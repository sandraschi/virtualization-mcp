"""Comprehensive unit & integration tests for Windows Sandbox bringup paths and sandbox_management tools."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from virtualization_mcp.tools.portmanteau.sandbox_management import sandbox_management
from virtualization_mcp.utils.windows_sandbox_helper import WindowsSandboxHelper


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


def test_windows_sandbox_helper_terminate_active():
    with patch("psutil.process_iter") as mock_iter, patch("time.sleep"):
        mock_proc = MagicMock()
        mock_proc.info = {"pid": 1234, "name": "WindowsSandbox.exe"}
        mock_iter.return_value = [mock_proc]

        terminated = WindowsSandboxHelper.terminate_active_sandbox()
        assert terminated is True
        mock_proc.terminate.assert_called_once()


@pytest.mark.asyncio
async def test_windows_sandbox_execute_in_sandbox(tmp_path):
    helper = WindowsSandboxHelper.__new__(WindowsSandboxHelper)
    helper.sandbox_dir = tmp_path
    helper._sandbox_processes = {}

    res = await helper.execute_in_sandbox(name="test_sb", command="echo Hello Sandbox")
    assert res["success"] is True
    assert res["command"] == "echo Hello Sandbox"
    assert Path(res["script_path"]).exists()


@pytest.mark.asyncio
async def test_sandbox_management_win_status():
    with patch("virtualization_mcp.tools.portmanteau.sandbox_management.WindowsSandboxHelper.is_sandbox_running", return_value=False), \
         patch("virtualization_mcp.tools.portmanteau.sandbox_management.WindowsSandboxHelper.check_prerequisites", return_value={"ready": True}):
        res = await sandbox_management(action="win_sandbox_status")
        assert res["success"] is True
        assert res["running"] is False


@pytest.mark.asyncio
async def test_sandbox_management_win_terminate():
    with patch("virtualization_mcp.tools.portmanteau.sandbox_management.WindowsSandboxHelper.terminate_active_sandbox", return_value=True):
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
