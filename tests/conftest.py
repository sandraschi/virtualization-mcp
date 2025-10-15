"""
Pytest configuration and fixtures for virtualization-mcp tests.

Provides common fixtures and test utilities for achieving GLAMA Gold Standard coverage.
"""

import asyncio
import os
import sys
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_vbox_manager():
    """Mock VirtualBox manager for testing."""
    manager = Mock()
    manager.list_vms = AsyncMock(
        return_value=[
            {"name": "TestVM1", "state": "running", "uuid": "uuid1"},
            {"name": "TestVM2", "state": "stopped", "uuid": "uuid2"},
        ]
    )
    manager.get_vm_info = AsyncMock(
        return_value={
            "name": "TestVM",
            "state": "running",
            "memory": 4096,
            "cpus": 2,
            "uuid": "test-uuid",
        }
    )
    manager.create_vm = AsyncMock(return_value={"created": True, "uuid": "new-uuid"})
    manager.start_vm = AsyncMock(return_value={"started": True})
    manager.stop_vm = AsyncMock(return_value={"stopped": True})
    manager.delete_vm = AsyncMock(return_value={"deleted": True})
    manager.clone_vm = AsyncMock(return_value={"cloned": True, "new_uuid": "cloned-uuid"})
    return manager


@pytest.fixture
def mock_network_manager():
    """Mock network manager for testing."""
    manager = Mock()
    manager.list_networks = AsyncMock(
        return_value=[
            {"name": "vboxnet0", "ip": "192.168.56.1", "netmask": "255.255.255.0"},
            {"name": "vboxnet1", "ip": "192.168.57.1", "netmask": "255.255.255.0"},
        ]
    )
    manager.create_network = AsyncMock(return_value={"created": True})
    manager.remove_network = AsyncMock(return_value={"removed": True})
    return manager


@pytest.fixture
def mock_storage_manager():
    """Mock storage manager for testing."""
    manager = Mock()
    manager.list_controllers = AsyncMock(
        return_value=[
            {"name": "SATA Controller", "type": "sata", "port_count": 30},
            {"name": "IDE Controller", "type": "ide", "port_count": 2},
        ]
    )
    manager.create_controller = AsyncMock(return_value={"created": True})
    manager.remove_controller = AsyncMock(return_value={"removed": True})
    return manager


@pytest.fixture
def mock_snapshot_manager():
    """Mock snapshot manager for testing."""
    manager = Mock()
    manager.list_snapshots = AsyncMock(
        return_value=[
            {"name": "snapshot1", "uuid": "snap1-uuid", "timestamp": "2024-01-01T12:00:00Z"},
            {"name": "snapshot2", "uuid": "snap2-uuid", "timestamp": "2024-01-02T12:00:00Z"},
        ]
    )
    manager.create_snapshot = AsyncMock(return_value={"created": True, "uuid": "new-snap-uuid"})
    manager.restore_snapshot = AsyncMock(return_value={"restored": True})
    manager.delete_snapshot = AsyncMock(return_value={"deleted": True})
    return manager


@pytest.fixture
def mock_system_manager():
    """Mock system manager for testing."""
    manager = Mock()
    manager.get_system_info = AsyncMock(
        return_value={"hostname": "test-host", "os": "Windows 11", "cpu_count": 8, "memory_gb": 16}
    )
    manager.get_vbox_version = AsyncMock(return_value={"version": "7.0.0", "build": "123456"})
    manager.list_ostypes = AsyncMock(
        return_value=[
            {"id": "Windows10_64", "description": "Windows 10 (64-bit)"},
            {"id": "Ubuntu_64", "description": "Ubuntu (64-bit)"},
        ]
    )
    return manager


@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for testing."""
    server = Mock()
    server.tool = Mock()
    server.call = AsyncMock()
    return server


@pytest.fixture
def sample_vm_config():
    """Sample VM configuration for testing."""
    return {
        "name": "TestVM",
        "os_type": "Windows10_64",
        "memory_mb": 4096,
        "disk_size_gb": 50,
        "cpus": 2,
    }


@pytest.fixture
def sample_network_config():
    """Sample network configuration for testing."""
    return {
        "name": "TestNetwork",
        "ip_address": "192.168.56.1",
        "netmask": "255.255.255.0",
        "dhcp_enabled": True,
    }


@pytest.fixture
def sample_storage_config():
    """Sample storage configuration for testing."""
    return {"controller_name": "SATA Controller", "controller_type": "sata", "port_count": 30}


@pytest.fixture
def sample_snapshot_config():
    """Sample snapshot configuration for testing."""
    return {
        "vm_name": "TestVM",
        "snapshot_name": "TestSnapshot",
        "description": "Test snapshot for testing",
    }


@pytest.fixture(autouse=True)
def mock_virtualbox_availability():
    """Mock VirtualBox availability for all tests."""
    with patch("virtualization_mcp.config.get_vbox_manage_path", return_value="VBoxManage.exe"):
        yield


@pytest.fixture(autouse=True)
def mock_logging():
    """Mock logging to avoid log output during tests."""
    with patch("virtualization_mcp.tools.portmanteau.vm_management.logger"):
        with patch("virtualization_mcp.tools.portmanteau.network_management.logger"):
            with patch("virtualization_mcp.tools.portmanteau.storage_management.logger"):
                with patch("virtualization_mcp.tools.portmanteau.snapshot_management.logger"):
                    with patch("virtualization_mcp.tools.portmanteau.system_management.logger"):
                        yield


# Test data factories
class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_vm_data(name: str = "TestVM", state: str = "running") -> dict[str, Any]:
        """Create VM test data."""
        return {
            "name": name,
            "state": state,
            "uuid": f"{name.lower()}-uuid",
            "memory": 4096,
            "cpus": 2,
            "os_type": "Windows10_64",
        }

    @staticmethod
    def create_network_data(name: str = "vboxnet0") -> dict[str, Any]:
        """Create network test data."""
        return {
            "name": name,
            "ip": "192.168.56.1",
            "netmask": "255.255.255.0",
            "dhcp_enabled": True,
        }

    @staticmethod
    def create_snapshot_data(name: str = "TestSnapshot") -> dict[str, Any]:
        """Create snapshot test data."""
        return {
            "name": name,
            "uuid": f"{name.lower()}-uuid",
            "timestamp": "2024-01-01T12:00:00Z",
            "description": f"Test snapshot: {name}",
        }


@pytest.fixture
def test_data_factory():
    """Provide test data factory."""
    return TestDataFactory


# Async test utilities
@pytest.fixture
def async_test_utils():
    """Provide async test utilities."""

    class AsyncTestUtils:
        @staticmethod
        async def wait_for_condition(condition_func, timeout=5.0):
            """Wait for a condition to be true."""
            import asyncio

            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < timeout:
                if await condition_func():
                    return True
                await asyncio.sleep(0.1)
            return False

        @staticmethod
        async def mock_async_function(return_value=None, side_effect=None):
            """Create a mock async function."""
            func = AsyncMock()
            if return_value is not None:
                func.return_value = return_value
            if side_effect is not None:
                func.side_effect = side_effect
            return func

    return AsyncTestUtils()


# Coverage helpers
@pytest.fixture
def coverage_helpers():
    """Provide coverage testing helpers."""

    class CoverageHelpers:
        @staticmethod
        def assert_coverage_improvement(
            old_coverage: float, new_coverage: float, min_improvement: float = 0.1
        ):
            """Assert that coverage has improved by at least min_improvement."""
            improvement = new_coverage - old_coverage
            assert improvement >= min_improvement, (
                f"Coverage improvement {improvement:.2%} is less than required {min_improvement:.2%}"
            )

        @staticmethod
        def assert_minimum_coverage(coverage: float, minimum: float = 0.8):
            """Assert that coverage meets minimum requirement."""
            assert coverage >= minimum, (
                f"Coverage {coverage:.2%} is below minimum requirement {minimum:.2%}"
            )

    return CoverageHelpers()


# Performance testing helpers
@pytest.fixture
def performance_helpers():
    """Provide performance testing helpers."""

    class PerformanceHelpers:
        @staticmethod
        async def measure_execution_time(func, *args, **kwargs):
            """Measure execution time of an async function."""
            import time

            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()

            return {"result": result, "execution_time": end_time - start_time}

        @staticmethod
        def assert_response_time(execution_time: float, max_time: float = 1.0):
            """Assert that response time is within acceptable limits."""
            assert execution_time <= max_time, (
                f"Execution time {execution_time:.3f}s exceeds maximum {max_time}s"
            )

    return PerformanceHelpers()
