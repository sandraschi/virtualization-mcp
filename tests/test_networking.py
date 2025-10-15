"""
Tests for the virtualization-mcp networking functionality.
"""

from unittest.mock import MagicMock

import pytest

from virtualization_mcp.services.vm.network.service import VMNetworkingService
from virtualization_mcp.services.vm.network.types import NetworkAdapterConfig, NetworkAttachmentType


class TestVMNetworkingService:
    """Tests for the VMNetworkingService class."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_vbox):
        """Set up test fixtures."""
        self.vm_service = MagicMock()
        self.vm_service.vbox_manager = mock_vbox
        self.networking = VMNetworkingService(self.vm_service)
        self.vm_name = "test-vm"

    def test_list_network_adapters(self, mock_vbox):
        """Test listing network adapters for a VM."""
        # Setup mock
        mock_vm = mock_vbox.machine
        mock_vm.get_network_adapter.return_value.enabled = True

        # Call the method
        result = self.networking.list_network_adapters(self.vm_name)

        # Assertions
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["enabled"] is True
        mock_vbox.find_machine.assert_called_once_with(self.vm_name)

    def test_configure_network_adapter(self, mock_vbox):
        """Test configuring a network adapter."""
        # Setup test data
        config = NetworkAdapterConfig(
            enabled=True,
            attachment_type=NetworkAttachmentType.NAT,
            adapter_type="82540EM",
            mac_address="auto",
        )

        # Call the method
        result = self.networking.configure_network_adapter(
            self.vm_name, adapter_number=1, config=config
        )

        # Assertions
        assert result["status"] == "success"
        mock_vbox.find_machine.assert_called_once_with(self.vm_name)

    @pytest.mark.asyncio
    async def test_enable_network_adapter(self, mock_networking):
        """Test enabling a network adapter."""
        # Setup mock
        mock_networking.configure_network_adapter.return_value = {"status": "success"}

        # Call the method
        result = await self.networking.enable_network_adapter(self.vm_name, adapter_number=1)

        # Assertions
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_disable_network_adapter(self, mock_networking):
        """Test disabling a network adapter."""
        # Setup mock
        mock_networking.configure_network_adapter.return_value = {"status": "success"}

        # Call the method
        result = await self.networking.disable_network_adapter(self.vm_name, adapter_number=1)

        # Assertions
        assert result["status"] == "success"

    def test_get_network_metrics(self, mock_vbox):
        """Test getting network metrics."""
        # Setup mock
        mock_vm = mock_vbox.machine
        mock_vm.get_network_adapter.return_value.get_network_rate.return_value = 1000000  # 1 Gbps

        # Call the method
        result = self.networking.get_network_metrics(self.vm_name, adapter_number=1)

        # Assertions
        assert "speed_bps" in result
        assert result["speed_bps"] == 1000000


class TestNetworkTypes:
    """Tests for network-related data types."""

    def test_network_adapter_config_validation(self):
        """Test NetworkAdapterConfig creation and properties."""
        # Test valid config
        config = NetworkAdapterConfig(
            enabled=True, attachment_type=NetworkAttachmentType.NAT, adapter_type="82540EM"
        )
        assert config.enabled is True
        assert config.attachment_type == NetworkAttachmentType.NAT
        assert config.adapter_type == "82540EM"

        # Test default values
        default_config = NetworkAdapterConfig()
        assert default_config.enabled is True
        assert default_config.attachment_type == NetworkAttachmentType.NAT
        assert default_config.adapter_type is None
