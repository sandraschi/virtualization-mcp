"""
Dual-mode VirtualBox testing infrastructure.

Automatically detects VirtualBox availability and switches between:
- REAL VirtualBox testing (local development with VBox installed)
- MOCKED testing (CI/CD where VirtualBox isn't available)
"""

import logging
import subprocess
from functools import wraps
from typing import Any
from unittest.mock import MagicMock

import pytest

logger = logging.getLogger(__name__)


def check_vbox_available() -> bool:
    """Check if VirtualBox is installed and accessible."""
    try:
        result = subprocess.run(
            ["VBoxManage", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False
        )
        available = result.returncode == 0
        if available:
            version = result.stdout.strip()
            logger.info(f">>> VirtualBox detected: {version}")
        else:
            logger.info(">>> VirtualBox not available - using mocks")
        return available
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.info(">>> VirtualBox not found - using mocks")
        return False


# Global flag - checked once at module load
VBOX_AVAILABLE = check_vbox_available()


def requires_vbox(test_func):
    """Decorator to skip test if VirtualBox isn't available.

    Use this for tests that MUST use real VirtualBox.
    """
    @wraps(test_func)
    def wrapper(*args, **kwargs):
        if not VBOX_AVAILABLE:
            pytest.skip("VirtualBox not available - test requires real VBox")
        return test_func(*args, **kwargs)
    return wrapper


def get_vbox_manager_or_mock():
    """Get real VBoxManager if available, otherwise return mock."""
    if VBOX_AVAILABLE:
        from virtualization_mcp.vbox.compat_adapter import get_vbox_manager
        return get_vbox_manager()
    else:
        # Return mock for CI/CD
        mock = MagicMock()
        mock.list_vms.return_value = []
        mock.vm_exists.return_value = False
        mock.get_vm_info.return_value = {"name": "test-vm", "state": "poweroff"}
        mock.get_vm_state.return_value = "poweroff"
        return mock


class VBoxTestHelper:
    """Helper class for dual-mode VirtualBox testing."""

    @staticmethod
    def create_test_vm(name: str, cleanup: bool = True) -> dict[str, Any]:
        """Create a test VM (real or mocked).

        Args:
            name: VM name
            cleanup: If True, registers VM for cleanup after test

        Returns:
            VM info dict
        """
        if VBOX_AVAILABLE:
            from virtualization_mcp.vbox.compat_adapter import get_vbox_manager
            manager = get_vbox_manager()
            result = manager.create_vm(
                name=name,
                ostype="Ubuntu_64",
                memory=1024,  # Minimal for testing
                cpus=1
            )
            if cleanup:
                # Register for cleanup
                pytest.test_vms_to_cleanup = getattr(pytest, 'test_vms_to_cleanup', [])
                pytest.test_vms_to_cleanup.append(name)
            return result
        else:
            # Return mocked result
            return {
                "uuid": "mock-uuid",
                "name": name,
                "status": "created"
            }

    @staticmethod
    def cleanup_test_vms():
        """Clean up all test VMs created during tests."""
        if not VBOX_AVAILABLE:
            return

        test_vms = getattr(pytest, 'test_vms_to_cleanup', [])
        if not test_vms:
            return

        from virtualization_mcp.vbox.compat_adapter import get_vbox_manager
        manager = get_vbox_manager()

        for vm_name in test_vms:
            try:
                if manager.vm_exists(vm_name):
                    # Stop if running
                    state = manager.get_vm_state(vm_name)
                    if state.lower() in ["running", "paused"]:
                        manager.stop_vm(vm_name, force=True)
                    # Delete
                    manager.delete_vm(vm_name, delete_disks=True)
                    logger.info(f"Cleaned up test VM: {vm_name}")
            except Exception as e:
                logger.warning(f"Failed to cleanup test VM {vm_name}: {e}")

        # Clear the list
        pytest.test_vms_to_cleanup = []


# Export
__all__ = [
    "VBOX_AVAILABLE",
    "requires_vbox",
    "get_vbox_manager_or_mock",
    "VBoxTestHelper",
    "check_vbox_available",
]


