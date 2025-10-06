"""
Tests for the virtualization-mcp VM metrics functionality.
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta

from virtualization_mcp.services.vm.metrics import VMMetricsMixin

class TestVMMetricsMixin:
    """Tests for the VMMetricsMixin class."""
    
    @pytest.fixture(autouse=True)
    def setup(self, mock_vbox):
        """Set up test fixtures."""
        self.vm_service = MagicMock()
        self.vm_service.vbox_manager = mock_vbox
        self.metrics = VMMetricsMixin(self.vm_service)
        self.vm_name = "test-vm"
        
    def test_get_cpu_metrics(self, mock_vbox):
        """Test getting CPU metrics for a VM."""
        # Setup mock
        mock_vm = mock_vbox.machine
        mock_vm.get_cpu_load.return_value = 75.5
        
        # Call the method
        result = self.metrics.get_cpu_metrics(self.vm_name)
        
        # Assertions
        assert "cpu_usage_percent" in result
        assert result["cpu_usage_percent"] == 75.5
        mock_vbox.find_machine.assert_called_once_with(self.vm_name)
        
    def test_get_memory_metrics(self, mock_vbox):
        """Test getting memory metrics for a VM."""
        # Setup mock
        mock_vm = mock_vbox.machine
        mock_vm.get_memory_info.return_value = {
            "total_mb": 4096,
            "free_mb": 2048,
            "balloon_mb": 1024
        }
        
        # Call the method
        result = self.metrics.get_memory_metrics(self.vm_name)
        
        # Assertions
        assert "total_mb" in result
        assert result["total_mb"] == 4096
        assert result["free_mb"] == 2048
        assert result["used_mb"] == 2048  # total - free
        
    def test_get_disk_metrics(self, mock_vbox):
        """Test getting disk metrics for a VM."""
        # Setup mock
        mock_medium = MagicMock()
        mock_medium.logical_size = 30 * 1024 * 1024 * 1024  # 30 GB
        mock_medium.actual_size = 10 * 1024 * 1024 * 1024  # 10 GB
        
        mock_vm = mock_vbox.machine
        mock_vm.get_medium_attachments.return_value = [
            {"medium": mock_medium, "port": 0, "device": 0}
        ]
        
        # Call the method
        result = self.metrics.get_disk_metrics(self.vm_name)
        
        # Assertions
        assert "total_gb" in result
        assert result["total_gb"] == 30.0
        assert result["used_gb"] == 10.0
        assert result["free_gb"] == 20.0
        
    def test_get_network_metrics(self, mock_vbox):
        """Test getting network metrics for a VM."""
        # Setup mock
        mock_adapter = MagicMock()
        mock_adapter.get_received_bytes.return_value = 1024 * 1024  # 1 MB
        mock_adapter.get_sent_bytes.return_value = 512 * 1024  # 0.5 MB
        
        mock_vm = mock_vbox.machine
        mock_vm.get_network_adapter.return_value = mock_adapter
        
        # Call the method
        result = self.metrics.get_network_metrics(self.vm_name, adapter_number=1)
        
        # Assertions
        assert "bytes_received" in result
        assert result["bytes_received"] == 1024 * 1024
        assert result["bytes_sent"] == 512 * 1024
        
    @pytest.mark.asyncio
    async def test_collect_metrics(self, mock_vbox):
        """Test collecting all metrics for a VM."""
        # Setup mocks
        mock_vm = mock_vbox.machine
        mock_vm.get_cpu_load.return_value = 50.0
        mock_vm.get_memory_info.return_value = {"total_mb": 4096, "free_mb": 2048, "balloon_mb": 1024}
        
        mock_medium = MagicMock()
        mock_medium.logical_size = 30 * 1024 * 1024 * 1024
        mock_medium.actual_size = 10 * 1024 * 1024 * 1024
        mock_vm.get_medium_attachments.return_value = [{"medium": mock_medium}]
        
        mock_adapter = MagicMock()
        mock_adapter.get_received_bytes.return_value = 1024 * 1024
        mock_adapter.get_sent_bytes.return_value = 512 * 1024
        mock_vm.get_network_adapter.return_value = mock_adapter
        
        # Call the method
        result = await self.metrics.collect_metrics(self.vm_name)
        
        # Assertions
        assert "cpu" in result
        assert "memory" in result
        assert "disk" in result
        assert "network" in result
        assert result["cpu"]["usage_percent"] == 50.0
        assert result["memory"]["total_mb"] == 4096
        assert result["disk"]["total_gb"] == 30.0
        assert result["network"]["bytes_received"] == 1024 * 1024



