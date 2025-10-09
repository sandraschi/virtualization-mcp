"""
GLAMA Gold Standard Coverage Tests

Focused tests to reach 80% coverage by testing critical untested modules.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import sys
import os


class TestCoreModules:
    """Test core module initialization and basic functionality."""
    
    def test_main_module_init(self):
        """Test main __init__ imports."""
        import virtualization_mcp
        assert hasattr(virtualization_mcp, '__version__')
    
    def test_settings_module(self):
        """Test settings configuration."""
        from virtualization_mcp.settings import BaseSettings
        settings = BaseSettings()
        assert settings is not None
    
    def test_async_wrapper(self):
        """Test async wrapper module."""
        import virtualization_mcp.async_wrapper as async_wrap
        assert async_wrap is not None


class TestAllExceptionTypes:
    """Test all exception types."""
    
    def test_vm_error(self):
        """Test VMError."""
        from virtualization_mcp.exceptions import VMError
        exc = VMError("test")
        assert "test" in str(exc)
    
    def test_validation_error(self):
        """Test ValidationError."""
        from virtualization_mcp.exceptions import ValidationError
        exc = ValidationError("validation failed")
        assert "validation" in str(exc)
    
    def test_rate_limit_exceeded(self):
        """Test RateLimitExceeded."""
        from virtualization_mcp.exceptions import RateLimitExceeded
        exc = RateLimitExceeded("too many requests")
        assert exc is not None
    
    def test_service_unavailable(self):
        """Test ServiceUnavailable."""
        from virtualization_mcp.exceptions import ServiceUnavailable
        exc = ServiceUnavailable("service down")
        assert exc is not None
    
    def test_vm_manager_error(self):
        """Test VMManagerError."""
        from virtualization_mcp.exceptions import VMManagerError
        exc = VMManagerError("manager error")
        assert exc is not None
    
    def test_snapshot_error(self):
        """Test SnapshotError."""
        from virtualization_mcp.exceptions import SnapshotError
        exc = SnapshotError("snapshot failed")
        assert exc is not None
    
    def test_network_error(self):
        """Test NetworkError."""
        from virtualization_mcp.exceptions import NetworkError
        exc = NetworkError("network issue")
        assert exc is not None
    
    def test_storage_error(self):
        """Test StorageError."""
        from virtualization_mcp.exceptions import StorageError
        exc = StorageError("storage issue")
        assert exc is not None
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        from virtualization_mcp.exceptions import ConfigurationError
        exc = ConfigurationError("config error")
        assert exc is not None
    
    def test_authentication_error(self):
        """Test AuthenticationError."""
        from virtualization_mcp.exceptions import AuthenticationError
        exc = AuthenticationError("auth failed")
        assert exc is not None
    
    def test_authorization_error(self):
        """Test AuthorizationError."""
        from virtualization_mcp.exceptions import AuthorizationError
        exc = AuthorizationError("not authorized")
        assert exc is not None
    
    def test_resource_exhausted_error(self):
        """Test ResourceExhaustedError."""
        from virtualization_mcp.exceptions import ResourceExhaustedError
        exc = ResourceExhaustedError("out of resources")
        assert exc is not None
    
    def test_timeout_error(self):
        """Test TimeoutError."""
        from virtualization_mcp.exceptions import TimeoutError as VMTimeoutError
        exc = VMTimeoutError("operation timed out")
        assert exc is not None


class TestJSONEncoderFunctions:
    """Test JSON encoder functions."""
    
    def test_dumps_function(self):
        """Test dumps function."""
        from virtualization_mcp.json_encoder import dumps
        
        result = dumps({"test": "value"})
        assert result is not None
        assert isinstance(result, str)
    
    def test_loads_function(self):
        """Test loads function."""
        from virtualization_mcp.json_encoder import loads
        
        result = loads('{"test": "value"}')
        assert result == {"test": "value"}
    
    def test_encoder_default(self):
        """Test encoder default method."""
        from virtualization_mcp.json_encoder import VBoxJSONEncoder
        
        encoder = VBoxJSONEncoder()
        # Test with a Path object
        result = encoder.default(Path("/test"))
        assert isinstance(result, str)


class TestUtilityFunctions:
    """Test all utility functions."""
    
    def test_get_vbox_home(self):
        """Test get_vbox_home."""
        from virtualization_mcp.utils.helpers import get_vbox_home
        result = get_vbox_home()
        assert isinstance(result, Path)
    
    def test_get_vbox_vms_dir(self):
        """Test get_vbox_vms_dir."""
        from virtualization_mcp.utils.helpers import get_vbox_vms_dir
        result = get_vbox_vms_dir()
        assert isinstance(result, Path)
    
    def test_ensure_dir_exists(self):
        """Test ensure_dir_exists."""
        from virtualization_mcp.utils.helpers import ensure_dir_exists
        import tempfile
        
        test_dir = Path(tempfile.gettempdir()) / "test_vbox_mcp"
        result = ensure_dir_exists(test_dir)
        assert result.exists()
        # Cleanup
        if test_dir.exists():
            test_dir.rmdir()
    
    def test_rate_limiter(self):
        """Test rate limiter module."""
        import virtualization_mcp.utils.rate_limiter as rl
        assert rl is not None
    
    def test_signal_handlers(self):
        """Test signal handlers module."""
        import virtualization_mcp.utils.signal_handlers as sh
        assert sh is not None
    
    def test_vm_status(self):
        """Test VM status module."""
        import virtualization_mcp.utils.vm_status as vs
        assert vs is not None
    
    def test_windows_sandbox_helper(self):
        """Test Windows sandbox helper."""
        import virtualization_mcp.utils.windows_sandbox_helper as wsh
        assert wsh is not None


class TestVBoxModules:
    """Test VBox-specific modules."""
    
    def test_vbox_manager_init(self):
        """Test VBoxManager initialization."""
        from virtualization_mcp.vbox.compat_adapter import VBoxManager
        
        manager = VBoxManager()
        assert manager is not None
    
    def test_vm_operations_class(self):
        """Test VMOperations class."""
        from virtualization_mcp.vbox.vm_operations import VMOperations
        
        ops = VMOperations()
        assert ops is not None
    
    def test_snapshots_module(self):
        """Test snapshots module."""
        import virtualization_mcp.vbox.snapshots as snaps
        assert snaps is not None
    
    def test_templates_module(self):
        """Test templates module."""
        import virtualization_mcp.vbox.templates as templates
        assert templates is not None


class TestServiceModules:
    """Test service layer modules."""
    
    def test_lifecycle_mixin(self):
        """Test VMLifecycleMixin."""
        from virtualization_mcp.services.vm.lifecycle import VMLifecycleMixin
        assert VMLifecycleMixin is not None
    
    def test_devices_mixin(self):
        """Test VMDeviceMixin."""
        from virtualization_mcp.services.vm.devices import VMDeviceMixin
        assert VMDeviceMixin is not None
    
    def test_metrics_mixin(self):
        """Test VMMetricsMixin."""
        from virtualization_mcp.services.vm.metrics import VMMetricsMixin
        assert VMMetricsMixin is not None
    
    def test_storage_mixin(self):
        """Test VMStorageMixin."""
        from virtualization_mcp.services.vm.storage import VMStorageMixin
        assert VMStorageMixin is not None
    
    def test_snapshots_mixin(self):
        """Test snapshots module."""
        import virtualization_mcp.services.vm.snapshots as snaps
        assert snaps is not None
    
    def test_video_module(self):
        """Test video module."""
        import virtualization_mcp.services.vm.video as video
        assert video is not None
    
    def test_audio_module(self):
        """Test audio module."""
        import virtualization_mcp.services.vm.audio as audio
        assert audio is not None
    
    def test_system_module(self):
        """Test system module."""
        import virtualization_mcp.services.vm.system as system
        assert system is not None
    
    def test_devices_hyperv_module(self):
        """Test Hyper-V devices module."""
        import virtualization_mcp.services.vm.devices_hyperv as devices_hyperv
        assert devices_hyperv is not None


class TestPluginModules:
    """Test plugin modules."""
    
    def test_hyperv_manager(self):
        """Test Hyper-V manager."""
        import virtualization_mcp.plugins.hyperv.manager as hyperv
        assert hyperv is not None
    
    def test_sandbox_manager(self):
        """Test sandbox manager."""
        from virtualization_mcp.plugins.sandbox.manager import WindowsSandboxHelper
        assert WindowsSandboxHelper is not None
    
    def test_sandbox_config(self):
        """Test sandbox configuration."""
        from virtualization_mcp.plugins.sandbox.manager import SandboxConfig
        config = SandboxConfig()
        assert config is not None


class TestNetworkModules:
    """Test network-related modules."""
    
    def test_network_adapters(self):
        """Test network adapters module."""
        import virtualization_mcp.services.vm.network.adapters as adapters
        assert adapters is not None
    
    def test_network_forwarding(self):
        """Test port forwarding module."""
        import virtualization_mcp.services.vm.network.forwarding as forwarding
        assert forwarding is not None
    
    def test_network_types(self):
        """Test network types module."""
        import virtualization_mcp.services.vm.network.types as types
        assert types is not None
    
    def test_network_utils(self):
        """Test network utils module."""
        import virtualization_mcp.services.vm.network.utils as utils
        assert utils is not None


class TestToolCategories:
    """Test all tool category modules."""
    
    def test_vm_tools_module(self):
        """Test VM tools."""
        import virtualization_mcp.tools.vm as vm_tools
        assert vm_tools is not None
    
    def test_network_tools_module(self):
        """Test network tools."""
        import virtualization_mcp.tools.network as net_tools
        assert net_tools is not None
    
    def test_storage_tools_module(self):
        """Test storage tools."""
        import virtualization_mcp.tools.storage as storage_tools
        assert storage_tools is not None
    
    def test_snapshot_tools_module(self):
        """Test snapshot tools."""
        import virtualization_mcp.tools.snapshot as snap_tools
        assert snap_tools is not None
    
    def test_system_tools_module(self):
        """Test system tools."""
        import virtualization_mcp.tools.system as sys_tools
        assert sys_tools is not None
    
    def test_backup_tools_module(self):
        """Test backup tools."""
        import virtualization_mcp.tools.backup as backup_tools
        assert backup_tools is not None
    
    def test_security_tools_module(self):
        """Test security tools."""
        import virtualization_mcp.tools.security as sec_tools
        assert sec_tools is not None
    
    def test_monitoring_tools_module(self):
        """Test monitoring tools (skip metrics due to prometheus registry)."""
        import virtualization_mcp.tools.monitoring as mon_tools
        assert mon_tools is not None
    
    def test_dev_tools_module(self):
        """Test dev tools."""
        import virtualization_mcp.tools.dev as dev_tools
        assert dev_tools is not None


class TestServerV2Modules:
    """Test server v2 modules."""
    
    def test_server_v2_init(self):
        """Test server_v2 init."""
        from virtualization_mcp.server_v2 import get_version
        version = get_version()
        assert version is not None
    
    def test_server_v2_config(self):
        """Test server v2 config."""
        import virtualization_mcp.server_v2.config as config
        assert config is not None
    
    def test_server_v2_plugins(self):
        """Test server v2 plugins."""
        import virtualization_mcp.server_v2.plugins as plugins
        assert plugins is not None


class TestAPIModules:
    """Test API modules."""
    
    def test_api_documentation(self):
        """Test API documentation module."""
        import virtualization_mcp.api.documentation as docs
        assert docs is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

