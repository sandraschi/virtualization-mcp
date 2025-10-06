"""
Tests for the vboxmcp storage functionality.
"""
import pytest
from unittest.mock import MagicMock, patch, call

from virtualization_mcp.services.vm.storage import VMStorageMixin
from virtualization_mcp.services.vm.types import StorageControllerType, StorageBus, StorageMedium

class TestVMStorageMixin:
    """Tests for the VMStorageMixin class."""
    
    @pytest.fixture(autouse=True)
    def setup(self, mock_vbox):
        """Set up test fixtures."""
        self.vm_service = MagicMock()
        self.vm_service.vbox_manager = mock_vbox
        self.storage = VMStorageMixin(self.vm_service)
        self.vm_name = "test-vm"
        
    def test_list_storage_controllers(self, mock_vbox):
        """Test listing storage controllers."""
        # Setup mock
        mock_controller = MagicMock()
        mock_controller.name = "SATA Controller"
        mock_controller.bus = StorageBus.SATA
        mock_vbox.machine.get_storage_controllers.return_value = [mock_controller]
        
        # Call the method
        result = self.storage.list_storage_controllers(self.vm_name)
        
        # Assertions
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "SATA Controller"
        mock_vbox.find_machine.assert_called_once_with(self.vm_name)
        
    def test_create_storage_controller(self, mock_vbox):
        """Test creating a storage controller."""
        # Call the method
        result = self.storage.create_storage_controller(
            self.vm_name,
            "SATA Controller",
            StorageControllerType.PIIX4,
            StorageBus.SATA
        )
        
        # Assertions
        assert result["status"] == "success"
        mock_vbox.find_machine.assert_called_once_with(self.vm_name)
        mock_vbox.machine.add_storage_controller.assert_called_once()
        
    def test_attach_storage_medium(self, mock_vbox):
        """Test attaching a storage medium to a VM."""
        # Setup test data
        medium = StorageMedium(
            path="/path/to/disk.vdi",
            format_="vdi",
            type_="normal"
        )
        
        # Call the method
        result = self.storage.attach_storage_medium(
            self.vm_name,
            "SATA Controller",
            port=0,
            device=0,
            medium=medium
        )
        
        # Assertions
        assert result["status"] == "success"
        mock_vbox.find_machine.assert_called_once_with(self.vm_name)
        
    @pytest.mark.asyncio
    async def test_create_disk_image(self, mock_vbox):
        """Test creating a disk image."""
        # Setup mock
        mock_vbox.create_hard_disk.return_value = "/path/to/new/disk.vdi"
        
        # Call the method
        result = await self.storage.create_disk_image(
            "/path/to/new/disk.vdi",
            size_gb=20,
            format_="vdi"
        )
        
        # Assertions
        assert result["status"] == "success"
        assert result["path"] == "/path/to/new/disk.vdi"
        mock_vbox.create_hard_disk.assert_called_once()
        
    def test_list_attached_media(self, mock_vbox):
        """Test listing attached storage media."""
        # Setup mock
        mock_controller = MagicMock()
        mock_controller.name = "SATA Controller"
        mock_medium = MagicMock()
        mock_medium.location = "/path/to/disk.vdi"
        mock_controller.get_medium_attachments.return_value = [
            {"medium": mock_medium, "port": 0, "device": 0}
        ]
        mock_vbox.machine.get_storage_controller.return_value = mock_controller
        
        # Call the method
        result = self.storage.list_attached_media(
            self.vm_name,
            "SATA Controller"
        )
        
        # Assertions
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["path"] == "/path/to/disk.vdi"
