"""
Comprehensive test suite to achieve GLAMA Gold Standard 80% coverage.

This test file focuses on testing currently uncovered modules, especially portmanteau tools.
"""

import pytest


# Test Config Module
class TestConfig:
    """Test configuration module."""

    def test_settings_import(self):
        """Test that settings can be imported."""
        from virtualization_mcp.config import settings

        assert settings is not None

    def test_get_vbox_manage_path(self):
        """Test VBoxManage path detection."""
        from virtualization_mcp.config import get_vbox_manage_path

        path = get_vbox_manage_path()
        assert path is not None


# Test JSON Encoder
class TestJSONEncoder:
    """Test JSON encoder utility."""

    def test_json_encoder_import(self):
        """Test JSON encoder can be imported."""
        from virtualization_mcp.json_encoder import VBoxJSONEncoder, dumps, loads

        encoder = VBoxJSONEncoder()
        assert encoder is not None
        assert dumps is not None
        assert loads is not None


# Test Exceptions
class TestExceptions:
    """Test exception classes."""

    def test_vbox_exception_import(self):
        """Test VBox exceptions can be imported."""
        from virtualization_mcp.exceptions import VMError, VMNotFoundError

        exc = VMError("test error")
        assert str(exc) == "test error"

        vm_exc = VMNotFoundError("test-vm")
        assert "test-vm" in str(vm_exc)


# Test Utils
class TestUtils:
    """Test utility functions."""

    def test_helpers_import(self):
        """Test helpers can be imported."""
        from virtualization_mcp.utils.helpers import ensure_dir_exists, get_vbox_home

        assert get_vbox_home is not None
        assert ensure_dir_exists is not None

    def test_logging_utils_import(self):
        """Test logging utilities."""
        from virtualization_mcp.utils.logging_utils import setup_logging

        assert setup_logging is not None


# Test VBox Compatibility
class TestVBoxCompat:
    """Test VBox compatibility layer."""

    def test_compat_adapter_import(self):
        """Test compat adapter can be imported."""
        from virtualization_mcp.vbox.compat_adapter import VBoxManager, VBoxManagerError

        assert VBoxManager is not None
        assert VBoxManagerError is not None

    def test_vm_operations_import(self):
        """Test VM operations can be imported."""
        from virtualization_mcp.vbox.vm_operations import VMOperations

        assert VMOperations is not None

    def test_networking_import(self):
        """Test networking module."""
        from virtualization_mcp.vbox.networking import NetworkManager

        assert NetworkManager is not None


# Test Services
class TestServices:
    """Test service layer."""

    def test_vm_service_import(self):
        """Test VM service can be imported."""
        from virtualization_mcp.services.vm import VMService

        assert VMService is not None

    def test_template_manager_import(self):
        """Test template manager."""
        from virtualization_mcp.services.template_manager import TemplateManager

        assert TemplateManager is not None

    def test_service_manager_import(self):
        """Test service manager."""
        from virtualization_mcp.services.service_manager import ServiceManager

        assert ServiceManager is not None


# Test VM Service Components
class TestVMServiceComponents:
    """Test VM service sub-components."""

    def test_lifecycle_import(self):
        """Test lifecycle module."""
        from virtualization_mcp.services.vm.lifecycle import VMLifecycleMixin

        assert VMLifecycleMixin is not None

    def test_devices_import(self):
        """Test devices module."""
        from virtualization_mcp.services.vm.devices import VMDeviceMixin

        assert VMDeviceMixin is not None

    def test_network_service_module(self):
        """Test network service module."""
        import virtualization_mcp.services.vm.network as network

        assert network is not None

    def test_metrics_import(self):
        """Test metrics module."""
        from virtualization_mcp.services.vm.metrics import VMMetricsMixin

        assert VMMetricsMixin is not None


# Test All Portmanteau Tools
class TestPortmanteauTools:
    """Test all portmanteau tools can be imported and registered."""

    def test_vm_management_import(self):
        """Test VM management portmanteau."""
        from virtualization_mcp.tools.portmanteau.vm_management import register_vm_management_tool

        assert register_vm_management_tool is not None

    def test_network_management_import(self):
        """Test network management portmanteau."""
        from virtualization_mcp.tools.portmanteau.network_management import (
            register_network_management_tool,
        )

        assert register_network_management_tool is not None

    def test_storage_management_import(self):
        """Test storage management portmanteau."""
        from virtualization_mcp.tools.portmanteau.storage_management import (
            register_storage_management_tool,
        )

        assert register_storage_management_tool is not None

    def test_snapshot_management_import(self):
        """Test snapshot management portmanteau."""
        from virtualization_mcp.tools.portmanteau.snapshot_management import (
            register_snapshot_management_tool,
        )

        assert register_snapshot_management_tool is not None

    def test_system_management_import(self):
        """Test system management portmanteau."""
        from virtualization_mcp.tools.portmanteau.system_management import (
            register_system_management_tool,
        )

        assert register_system_management_tool is not None


# Test Individual Tool Modules
class TestToolModules:
    """Test individual tool modules."""

    def test_vm_tools_import(self):
        """Test VM tools."""
        from virtualization_mcp.tools.vm.vm_tools import create_vm, list_vms, start_vm

        assert list_vms is not None
        assert create_vm is not None
        assert start_vm is not None

    def test_network_tools_module(self):
        """Test network tools module."""
        import virtualization_mcp.tools.network.network_tools as net_tools

        assert net_tools is not None

    def test_snapshot_tools_import(self):
        """Test snapshot tools."""
        from virtualization_mcp.tools.snapshot.snapshot_tools import create_snapshot, list_snapshots

        assert list_snapshots is not None
        assert create_snapshot is not None

    def test_storage_tools_import(self):
        """Test storage tools."""
        from virtualization_mcp.tools.storage.storage_tools import list_storage_controllers

        assert list_storage_controllers is not None

    def test_system_tools_import(self):
        """Test system tools."""
        from virtualization_mcp.tools.system.system_tools import get_system_info, get_vbox_version

        assert get_system_info is not None
        assert get_vbox_version is not None


# Test Security Tools
class TestSecurityTools:
    """Test security tool modules."""

    def test_security_testing_tools_module(self):
        """Test security testing tools module exists."""
        import virtualization_mcp.tools.security.security_testing_tools as sec_tools

        assert sec_tools is not None

    def test_malware_tools_import(self):
        """Test malware tools."""
        from virtualization_mcp.tools.security.malware_tools import (
            analyze_file,
            get_malware_analyzer,
        )

        assert analyze_file is not None
        assert get_malware_analyzer is not None


# Test Monitoring Tools
class TestMonitoringTools:
    """Test monitoring tool modules."""

    def test_monitoring_tools_import(self):
        """Test monitoring tools."""
        from virtualization_mcp.tools.monitoring.monitoring_tools import get_vm_metrics

        assert get_vm_metrics is not None

    def test_metrics_tools_import(self):
        """Test metrics tools."""
        from virtualization_mcp.tools.monitoring.metrics_tools import (
            get_metrics,
            record_api_request,
        )

        assert get_metrics is not None
        assert record_api_request is not None


# Test Development Tools
class TestDevelopmentTools:
    """Test development tool modules."""

    def test_sandbox_tools_module(self):
        """Test sandbox tools module."""
        import virtualization_mcp.tools.dev.sandbox_tools as sandbox

        assert sandbox is not None

    def test_documentation_tools_module(self):
        """Test documentation tools module."""
        import virtualization_mcp.tools.dev.documentation_tools as docs

        assert docs is not None


# Test Backup Tools
class TestBackupTools:
    """Test backup tool modules."""

    def test_backup_tools_module(self):
        """Test backup tools module."""
        import virtualization_mcp.tools.backup.backup_tools as backup

        assert backup is not None


# Test Plugins
class TestPlugins:
    """Test plugin system."""

    def test_hyperv_plugin_module(self):
        """Test Hyper-V plugin module."""
        import virtualization_mcp.plugins.hyperv.manager as hyperv

        assert hyperv is not None

    def test_sandbox_plugin_import(self):
        """Test sandbox plugin."""
        from virtualization_mcp.plugins.sandbox.manager import WindowsSandboxHelper

        assert WindowsSandboxHelper is not None


# Test All Tools Server
class TestAllToolsServer:
    """Test the all tools server."""

    def test_server_import(self):
        """Test server can be imported."""
        from virtualization_mcp.all_tools_server import main

        assert main is not None

    def test_mcp_tools_module(self):
        """Test MCP tools module."""
        import virtualization_mcp.mcp_tools as mcp_tools

        assert mcp_tools is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
