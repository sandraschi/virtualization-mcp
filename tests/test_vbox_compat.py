"""
Test script for VirtualBox compatibility layer.

This script tests the core functionality of the VirtualBox compatibility layer,
including VM lifecycle operations and snapshot management.
"""

import logging
import sys
import time
from pathlib import Path

import pytest

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from virtualization_mcp.vbox.compat_adapter import get_vbox_manager  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("test_vbox_compat.log")],
)

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="Real VBox integration test - VM can be locked, needs manual cleanup")
def test_vm_lifecycle():
    """Test VM lifecycle operations."""
    vbox = get_vbox_manager()
    test_vm_name = "test-vm-compat"

    try:
        # Check if test VM already exists and delete it
        if vbox.vm_exists(test_vm_name):
            logger.info(f"Test VM '{test_vm_name}' already exists, deleting...")
            vbox.delete_vm(test_vm_name, delete_disks=True)

        # Create a new VM - with all required params
        logger.info(f"Creating test VM '{test_vm_name}'...")
        vbox.create_vm(
            name=test_vm_name,
            ostype="Ubuntu_64",
            memory_mb=2048,
            cpu_count=2,
            vram_mb=16,
            storage_controllers=[{"name": "SATA Controller", "type": "IntelAhci", "port_count": 2}],
        )

        # Verify VM was created
        assert vbox.vm_exists(test_vm_name), "VM was not created successfully"
        logger.info("✓ VM created successfully")

        # Get VM info
        vm_info = vbox.get_vm_info(test_vm_name)
        assert vm_info["name"] == test_vm_name, "VM name does not match"
        logger.info(f"✓ VM info retrieved: {vm_info}")

        # Test VM state management
        logger.info("Testing VM state management...")

        # Start the VM
        logger.info("Starting VM...")
        vbox.start_vm(test_vm_name, headless=True)

        # Wait a bit for VM to start
        time.sleep(5)

        # Check VM state
        state = vbox.get_vm_state(test_vm_name).lower()
        assert state == "running", f"Expected VM to be running, got {state}"
        logger.info("✓ VM started successfully")

        # Pause the VM
        logger.info("Pausing VM...")
        vbox.pause_vm(test_vm_name)

        # Check VM state
        state = vbox.get_vm_state(test_vm_name).lower()
        assert state == "paused", f"Expected VM to be paused, got {state}"
        logger.info("✓ VM paused successfully")

        # Resume the VM
        logger.info("Resuming VM...")
        vbox.resume_vm(test_vm_name)

        # Check VM state
        state = vbox.get_vm_state(test_vm_name).lower()
        assert state == "running", f"Expected VM to be running, got {state}"
        logger.info("✓ VM resumed successfully")

        # Test snapshots
        logger.info("Testing snapshot functionality...")

        # Take a snapshot
        snapshot_name = "test-snapshot"
        logger.info(f"Creating snapshot '{snapshot_name}'...")
        snapshot = vbox.take_snapshot(test_vm_name, snapshot_name, "Test snapshot")
        assert "uuid" in snapshot, "Snapshot creation failed"
        logger.info(f"✓ Snapshot created: {snapshot}")

        # List snapshots
        snapshots = vbox.list_snapshots(test_vm_name)
        assert len(snapshots) > 0, "No snapshots found"
        logger.info(f"✓ Found {len(snapshots)} snapshot(s)")

        # Stop the VM
        logger.info("Stopping VM...")
        vbox.stop_vm(test_vm_name, force=True)

        # Check VM state
        state = vbox.get_vm_state(test_vm_name).lower()
        assert state in ["poweroff", "saved"], f"Expected VM to be powered off, got {state}"
        logger.info("✓ VM stopped successfully")

        # Clean up
        logger.info("Cleaning up test VM...")
        vbox.delete_vm(test_vm_name, delete_disks=True)

        # Verify VM was deleted
        assert not vbox.vm_exists(test_vm_name), "VM was not deleted successfully"
        logger.info("✓ Test VM cleaned up successfully")

        logger.info("\n✅ All tests passed successfully!")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        # Clean up if something went wrong
        try:
            if vbox.vm_exists(test_vm_name):
                logger.info("Cleaning up after test failure...")
                vbox.delete_vm(test_vm_name, delete_disks=True)
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")
        raise


if __name__ == "__main__":
    logger.info("Starting VirtualBox compatibility layer tests...")
    test_vm_lifecycle()
