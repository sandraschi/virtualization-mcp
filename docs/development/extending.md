# Extending virtualization-mcp

This guide explains how to extend virtualization-mcp with custom functionality, including creating plugins, adding new VM operations, and integrating with other tools.

## Table of Contents
1. [Plugin System](#plugin-system)
2. [Creating a New Plugin](#creating-a-new-plugin)
3. [Adding New VM Operations](#adding-new-vm-operations)
4. [Custom Network Configurations](#custom-network-configurations)
5. [Integrating with External Tools](#integrating-with-external-tools)
6. [Testing Your Extensions](#testing-your-extensions)
7. [Best Practices](#best-practices)

## Plugin System

virtualization-mcp uses a plugin architecture that allows you to add new functionality without modifying the core code. Plugins are Python modules that can:

- Add new API endpoints
- Register new VM operations
- Modify existing behavior
- Add custom configuration options

## Creating a New Plugin

1. **Create a new Python package** in the `virtualization-mcp/plugins` directory:

```
virtualization-mcp/
└── plugins/
    └── my_plugin/
        ├── __init__.py
        ├── models.py
        └── api.py
```

2. **Define your plugin** in `__init__.py`:

```python
from typing import Dict, Any
from fastapi import APIRouter
from virtualization-mcp.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.router = APIRouter()
        self.setup_routes()
    
    def setup_routes(self):
        @self.router.get("/my-endpoint")
        async def my_endpoint():
            return {"message": "Hello from my plugin!"}
    
    def get_router(self):
        return self.router
```

3. **Register your plugin** in `virtualization-mcp/plugins/__init__.py`:

```python
from .my_plugin import MyPlugin

PLUGINS = {
    "my_plugin": MyPlugin
}
```

## Adding New VM Operations

You can extend the VM operations by creating a new operation class:

```python
from typing import Dict, Any
from virtualization-mcp.vm_operations import VMOperation

class MyCustomOperation(VMOperation):
    """Custom VM operation for specialized tasks."""
    
    def __init__(self, vm_manager):
        super().__init__(vm_manager)
    
    async def execute(self, vm_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the custom operation."""
        vm = await self.vm_manager.get_vm(vm_name)
        
        # Your custom logic here
        result = await self._do_something(vm, params)
        
        return {
            "status": "success",
            "result": result
        }
    
    async def _do_something(self, vm, params):
        # Implementation details
        pass
```

Register the operation in your plugin:

```python
class MyPlugin(BasePlugin):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.custom_op = MyCustomOperation(config.get("vm_manager"))
        self.setup_routes()
    
    def setup_routes(self):
        @self.router.post("/vms/{vm_name}/custom-operation")
        async def custom_operation(
            vm_name: str,
            params: Dict[str, Any] = {}
        ):
            return await self.custom_op.execute(vm_name, params)
```

## Custom Network Configurations

Create custom network configurations by extending the `NetworkManager`:

```python
from virtualization-mcp.vbox.networking import NetworkManager

class CustomNetworkManager(NetworkManager):
    """Extended network manager with custom configurations."""
    
    async def create_custom_network(
        self,
        network_name: str,
        network_type: str = "intnet",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a custom network configuration."""
        # Your custom network creation logic
        pass
```

## Integrating with External Tools

### Example: Integrating with Prometheus for Monitoring

```python
from prometheus_client import start_http_server, Gauge
from virtualization-mcp.plugins.base import BasePlugin

class MonitoringPlugin(BasePlugin):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.metrics = {
            'vm_cpu_usage': Gauge(
                'virtualization-mcp_vm_cpu_usage',
                'CPU usage per VM',
                ['vm_name']
            ),
            'vm_memory_usage': Gauge(
                'virtualization-mcp_vm_memory_usage',
                'Memory usage per VM',
                ['vm_name']
            )
        }
        
        # Start Prometheus metrics server
        start_http_server(8000)
    
    async def update_metrics(self):
        """Update all metrics."""
        vms = await self.vm_manager.list_vms()
        for vm in vms:
            stats = await self.vm_manager.get_vm_stats(vm['name'])
            self.metrics['vm_cpu_usage'].labels(vm['name']).set(stats['cpu_usage'])
            self.metrics['vm_memory_usage'].labels(vm['name']).set(stats['memory_usage'])
```

## Testing Your Extensions

Create tests in the `tests/plugins` directory:

```python
import pytest
from virtualization-mcp.plugins.my_plugin import MyPlugin

@pytest.fixture
def plugin_config():
    return {"some_setting": "value"}

@pytest.fixture
def my_plugin(plugin_config):
    return MyPlugin(plugin_config)

def test_my_plugin_initialization(my_plugin):
    assert my_plugin is not None
    # Add more assertions
```

## Best Practices

1. **Modularity**: Keep your extensions focused and single-purpose
2. **Configuration**: Use the config system for customizable settings
3. **Error Handling**: Implement proper error handling and logging
4. **Documentation**: Document your extensions with docstrings and examples
5. **Testing**: Write tests for all new functionality
6. **Compatibility**: Ensure compatibility with different VirtualBox versions
7. **Security**: Follow security best practices, especially for network operations

### Example: Secure API Endpoint

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != "your-secure-key":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

@router.get("/secure-endpoint", dependencies=[Depends(verify_api_key)])
async def secure_endpoint():
    return {"message": "This is a secure endpoint"}
```

### Performance Considerations

- Use asynchronous I/O for network operations
- Cache frequently accessed data
- Implement pagination for large result sets
- Use connection pooling for database operations

### Logging

```python
import logging

logger = logging.getLogger(__name__)

class MyPlugin(BasePlugin):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(f"virtualization-mcp.plugins.{self.__class__.__name__}")
    
    async def some_operation(self):
        try:
            # Operation that might fail
            self.logger.info("Starting operation")
            # ...
        except Exception as e:
            self.logger.error(f"Operation failed: {str(e)}")
            raise
```

## Next Steps

- [API Reference](../api/README.md)
- [Development Guide](guide.md)
- [Contributing](../../CONTRIBUTING.md)



