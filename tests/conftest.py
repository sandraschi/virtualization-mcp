"""
Shared test fixtures for virtualization-mcp.

Dual testing strategy:
- `mock_vbox` / `mock_hyperv` fixtures: Use mocks (CI-safe).
- `real_vbox` fixture: Only works when VirtualBox is installed (skipped in CI).
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from virtualization_mcp.vbox.compat_adapter import VBoxManager

# ── Mocks ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_vbox():
    """VBoxManager with all subprocess calls mocked."""
    with (
        patch("virtualization_mcp.vbox.compat_adapter.VBoxManage"),
        patch("virtualization_mcp.vbox.compat_adapter.VBoxManager._validate_vboxmanage"),
        patch("virtualization_mcp.vbox.compat_adapter.VBoxManager._find_vboxmanage", return_value="VBoxManage"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture
def mock_vbox_manager():
    """A VBoxManager instance with mocked internals."""
    with (
        patch("virtualization_mcp.vbox.compat_adapter.VBoxManage"),
        patch("virtualization_mcp.vbox.compat_adapter.VBoxManager._validate_vboxmanage"),
        patch("virtualization_mcp.vbox.compat_adapter.VBoxManager._find_vboxmanage", return_value="VBoxManage"),
    ):
        mgr = VBoxManager()
        mgr.list_vms = MagicMock(return_value=[])
        mgr.vm_exists = MagicMock(return_value=False)
        mgr.get_vm_info = MagicMock(return_value={"name": "test-vm", "vmstate": "poweroff"})
        mgr.run_command = MagicMock(return_value={"success": True, "output": ""})
        yield mgr


# ── Real VirtualBox (requires installed VBoxManage) ──────────────────────────

def vbox_available() -> bool:
    """Check if VBoxManage is available on this system."""
    try:
        r = subprocess.run(
            [r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        return r.returncode == 0
    except Exception:
        return False


requires_vbox = pytest.mark.skipif(not vbox_available(), reason="VirtualBox not installed")


@pytest.fixture
def real_vbox():
    """Real VBoxManager (requires VBoxManage). Skip if not available."""
    if not vbox_available():
        pytest.skip("VirtualBox not installed")
    return VBoxManager()


# ── Test helpers ──────────────────────────────────────────────────────────────

@pytest.fixture
def sample_vm_config():
    return {
        "name": "test-ubuntu-dev",
        "os_type": "Ubuntu_64",
        "memory_mb": 2048,
        "disk_gb": 20,
        "cpus": 2,
    }


@pytest.fixture
def mock_hyperv_manager():
    """Mocked Hyper-V manager."""
    mgr = MagicMock()
    mgr.list_vms = MagicMock(return_value=[])
    mgr.create_vm = MagicMock(return_value={"status": "success", "vm_name": "test-hv"})
    mgr.start_vm = MagicMock(return_value={"status": "success"})
    mgr.stop_vm = MagicMock(return_value={"status": "success"})
    return mgr
