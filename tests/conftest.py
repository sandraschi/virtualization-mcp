"""
Pytest configuration and fixtures for virtualization-mcp tests.
"""
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fixtures for mocking VirtualBox components
@pytest.fixture
def mock_vbox():
    """Mock the VirtualBox SDK."""
    with patch('virtualization-mcp.vbox.manager.VBoxManager') as mock_vbox_manager:
        # Mock the VirtualBox manager
        mock_mgr = MagicMock()
        mock_vbox_manager.return_value = mock_mgr
        
        # Mock the VirtualBox constants
        mock_constants = MagicMock()
        
        # Set up mock VM
        mock_vm = MagicMock()
        mock_vm.name = "test-vm"
        mock_vm.get_machine_state.return_value = "PoweredOff"
        
        # Set up mock network adapter
        mock_adapter = MagicMock()
        mock_adapter.enabled = True
        mock_adapter.attachment_type = "NAT"
        mock_vm.get_network_adapter.return_value = mock_adapter
        
        mock_mgr.machine = mock_vm
        
        yield mock_mgr

@pytest.fixture
def mock_networking():
    """Mock the networking service."""
    with patch('virtualization-mcp.services.vm.network.service.VMNetworkingService') as mock_service:
        mock_instance = MagicMock()
        mock_service.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_lifecycle():
    """Mock the VM lifecycle service."""
    with patch('virtualization-mcp.services.vm.lifecycle.VMLifecycleMixin') as mock_mixin:
        mock_instance = MagicMock()
        mock_mixin.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_storage():
    """Mock the storage service."""
    with patch('virtualization-mcp.services.vm.storage.VMStorageMixin') as mock_mixin:
        mock_instance = MagicMock()
        mock_mixin.return_value = mock_instance
        yield mock_instance

# Async test support
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.WindowsProactorEventLoopPolicy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

# Test data directory
@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return Path(__file__).parent / "data"

# Test VM configuration
@pytest.fixture
def test_vm_config():
    """Return a test VM configuration."""
    return {
        "name": "test-vm",
        "memory_mb": 2048,
        "cpus": 2,
        "ostype": "Ubuntu_64",
        "storage": {
            "size_gb": 20,
            "controller": "SATA",
            "type": "vdi"
        },
        "network": [
            {
                "type": "nat",
                "adapter": 1
            }
        ]
    }



