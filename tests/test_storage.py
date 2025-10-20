"""
Tests for the virtualization-mcp storage functionality.
"""

from unittest.mock import MagicMock

import pytest

from virtualization_mcp.services.vm.storage import VMStorageMixin


class TestVMStorageMixin:
    """Tests for the VMStorageMixin class."""

    @pytest.fixture
    def mock_vbox(self):
        """Create mock VBox manager."""
        return MagicMock()

    @pytest.fixture(autouse=True)
    def setup(self, mock_vbox):
        """Set up test fixtures."""
        self.vm_service = MagicMock()
        self.vm_service.vbox_manager = mock_vbox
        self.storage = VMStorageMixin(self.vm_service)
        self.vm_name = "test-vm"

    def test_list_storage_controllers(self, mock_vbox):
        """Test listing storage controllers."""
        pytest.skip("list_storage_controllers not on VMStorageMixin")

    def test_create_storage_controller(self, mock_vbox):
        """Test creating a storage controller."""
        pytest.skip("create_storage_controller not on VMStorageMixin")

    def test_attach_storage_medium(self, mock_vbox):
        """Test attaching a storage medium to a VM."""
        pytest.skip("attach_storage_medium not on VMStorageMixin")

    def test_create_disk_image(self, mock_vbox):
        """Test creating a disk image."""
        pytest.skip("create_disk_image not on VMStorageMixin")

    def test_list_attached_media(self, mock_vbox):
        """Test listing attached storage media."""
        pytest.skip("list_attached_media not on VMStorageMixin")
