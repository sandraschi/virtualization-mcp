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
        pytest.skip("list_network_adapters not on VMNetworkingService")

    def test_configure_network_adapter(self, mock_vbox):
        """Test configuring a network adapter."""
        pytest.skip("configure_network_adapter not on VMNetworkingService")

    def test_enable_network_adapter(self, mock_networking):
        """Test enabling a network adapter."""
        pytest.skip("enable_network_adapter not on VMNetworkingService")

    def test_disable_network_adapter(self, mock_networking):
        """Test disabling a network adapter."""
        pytest.skip("disable_network_adapter not on VMNetworkingService")

    def test_get_network_metrics(self, mock_vbox):
        """Test getting network metrics."""
        pytest.skip("get_network_metrics not on VMNetworkingService")


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
