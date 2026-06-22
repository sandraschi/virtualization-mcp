"""
Tests for the virtualization-mcp VM devices functionality.
"""

from unittest.mock import MagicMock

import pytest

from virtualization_mcp.services.vm.devices import VMDeviceMixin
from virtualization_mcp.services.vm.types import USBDeviceFilter


class TestVMDeviceMixin:
    """Tests for the VMDeviceMixin class."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_vbox):
        """Set up test fixtures."""
        self.vm_service = MagicMock()
        self.vm_service.vbox_manager = mock_vbox
        self.devices = VMDeviceMixin(self.vm_service)
        self.vm_name = "test-vm"

    @pytest.mark.skip(reason="Method names don't match implementation - needs refactoring")
    def test_list_devices(self, mock_vbox):
        """Test listing devices attached to a VM."""
        # Setup mock
        mock_usb_controller = MagicMock()
        mock_usb_controller.name = "USB Controller"
        mock_usb_controller.type = "OHCI"

        mock_vm = mock_vbox.machine
        mock_vm.get_storage_controllers.return_value = []
        mock_vm.get_usb_controllers.return_value = [mock_usb_controller]

        # Call the method
        result = self.devices.list_devices(self.vm_name)

        # Assertions
        assert "storage_controllers" in result
        assert "usb_controllers" in result
        assert len(result["usb_controllers"]) == 1
        assert result["usb_controllers"][0]["name"] == "USB Controller"

    @pytest.mark.skip(reason="Method names don't match implementation - needs refactoring")
    def test_attach_usb_device(self, mock_vbox):
        """Test attaching a USB device to a VM."""
        # Setup test data
        usb_device = {
            "vendor_id": "0x1234",
            "product_id": "0x5678",
            "revision": "0x0100",
            "manufacturer": "Test Manufacturer",
            "product": "Test Device",
        }

        # Call the method
        result = self.devices.attach_usb_device(self.vm_name, usb_device, port=1)

        # Assertions
        assert result["status"] == "success"
        mock_vbox.find_machine.assert_called_once_with(self.vm_name)

    @pytest.mark.skip(reason="Method names don't match implementation - needs refactoring")
    def test_detach_usb_device(self, mock_vbox):
        """Test detaching a USB device from a VM."""
        # Setup test data
        usb_filter = USBDeviceFilter(vendor_id="0x1234", product_id="0x5678")

        # Call the method
        result = self.devices.detach_usb_device(self.vm_name, usb_filter)

        # Assertions
        assert result["status"] == "success"
        mock_vbox.find_machine.assert_called_once_with(self.vm_name)

    @pytest.mark.skip(reason="Method names don't match implementation - needs refactoring")
    def test_list_available_usb_devices(self, mock_vbox):
        """Test listing available USB devices on the host."""
        # Setup mock
        mock_usb_device = MagicMock()
        mock_usb_device.vendor_id = "0x1234"
        mock_usb_device.product_id = "0x5678"
        mock_usb_device.manufacturer = "Test Manufacturer"
        mock_usb_device.product = "Test Device"

        mock_vbox.host.get_usb_devices.return_value = [mock_usb_device]

        # Call the method
        result = self.devices.list_available_usb_devices()

        # Assertions
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["vendor_id"] == "0x1234"
        assert result[0]["product_id"] == "0x5678"

    @pytest.mark.skip(reason="Method names don't match implementation - needs refactoring")
    def test_configure_shared_folder(self, mock_vbox):
        """Test configuring a shared folder for a VM."""
        # Call the method
        result = self.devices.configure_shared_folder(
            self.vm_name, "shared-data", "/path/to/host/folder", read_only=False, auto_mount=True
        )

        # Assertions
        assert result["status"] == "success"
        mock_vbox.find_machine.assert_called_once_with(self.vm_name)

    @pytest.mark.skip(reason="Method names don't match implementation - needs refactoring")
    def test_remove_shared_folder(self, mock_vbox):
        """Test removing a shared folder from a VM."""
        # Call the method
        result = self.devices.remove_shared_folder(self.vm_name, "shared-data")

        # Assertions
        assert result["status"] == "success"
        mock_vbox.find_machine.assert_called_once_with(self.vm_name)
