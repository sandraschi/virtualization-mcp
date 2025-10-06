# virtualization-mcp Plugins

## Overview

virtualization-mcp's plugin system allows you to extend and customize the functionality of the virtualization management platform. Plugins can add new API endpoints, background tasks, and integrate with external systems.

## Plugin Types

virtualization-mcp supports several types of plugins:

1. **Core Plugins**: Built-in functionality (VM management, networking, storage)
2. **Security Plugins**: Security scanning, compliance checks, access control
3. **Monitoring Plugins**: Performance metrics, logging, alerting
4. **Integration Plugins**: Third-party system integrations
5. **Utility Plugins**: Additional tools and utilities

## Available Plugins

### Core Plugins

- [Hyper-V Manager](./hyperv_manager.md) - Manage Hyper-V virtual machines
- [Windows Sandbox](./windows_sandbox.md) - Lightweight, disposable Windows environments
- [VirtualBox Manager](./virtualbox_manager.md) - Manage Oracle VirtualBox VMs

### Security Plugins

- [Security Analyzer](./security_analyzer.md) - Scan VMs for vulnerabilities
- [Network Analyzer](./network_analyzer.md) - Monitor and analyze network traffic
- [Malware Analyzer](./malware_analyzer.md) - Detect and analyze malware in isolated environments

### Monitoring Plugins

- [Metrics Collector](./metrics_collector.md) - Collect and analyze performance metrics
- [Log Aggregator](./log_aggregator.md) - Centralized logging for all components
- [Alert Manager](./alert_manager.md) - Configure and manage alerts

### Integration Plugins

- [Docker Integration](./docker_integration.md) - Manage Docker containers
- [Kubernetes Integration](./kubernetes_integration.md) - Deploy and manage Kubernetes clusters
- [Cloud Providers](./cloud_providers.md) - Integration with AWS, Azure, and GCP

## Plugin Management

### Enabling/Disabling Plugins

Plugins can be enabled or disabled in the configuration file:

```yaml
plugins:
  hyperv_manager:
    enabled: true
  security_analyzer:
    enabled: true
    config:
      scan_schedule: "0 0 * * *"  # Daily at midnight
```

### Plugin Configuration

Each plugin can have its own configuration section:

```yaml
plugins:
  windows_sandbox:
    enabled: true
    config:
      memory_mb: 4096
      vcpu_count: 2
      shared_folders:
        - host_path: C:\shared
          read_only: false
```

### Plugin Dependencies

Plugins can specify dependencies that must be loaded first:

```python
class SecurityAnalyzerPlugin(BasePlugin):
    dependencies = ["network_analyzer"]
    
    async def startup(self):
        network_analyzer = self.manager.get_plugin("network_analyzer")
        # Use network_analyzer...
```

## Creating Custom Plugins

### Plugin Structure

A basic plugin has the following structure:

```
my_plugin/
├── __init__.py
├── plugin.py
├── models.py
├── routes.py
└── config.py
```

### Example Plugin

```python
# my_plugin/plugin.py
from virtualization-mcp.plugins.base import BasePlugin
from .routes import router

class MyPlugin(BasePlugin):
    """My custom plugin for virtualization-mcp."""
    
    def __init__(self, config):
        super().__init__(config)
        self.router = router
    
    async def startup(self):
        """Initialize the plugin."""
        await super().startup()
        # Initialization code here
    
    async def shutdown(self):
        """Clean up resources."""
        await super().shutdown()
        # Cleanup code here
```

### Registering a Plugin

Plugins are automatically discovered if they're in the `virtualization-mcp.plugins` namespace package or in a directory listed in the `PLUGIN_DIRS` configuration.

## Plugin Hooks

Plugins can implement the following hooks:

- `startup()`: Called when the plugin is loaded
- `shutdown()`: Called when the plugin is unloaded
- `setup_routes()`: Register FastAPI routes
- `register_models()`: Register database models
- `register_commands()`: Register CLI commands
- `register_events()`: Register event handlers

## Best Practices

1. **Error Handling**: Implement comprehensive error handling
2. **Logging**: Use the built-in logger
3. **Configuration**: Make your plugin configurable
4. **Documentation**: Document your plugin's functionality
5. **Testing**: Include unit and integration tests
6. **Dependencies**: Keep dependencies to a minimum
7. **Performance**: Optimize for performance
8. **Security**: Follow security best practices

## Plugin Development Guide

See the [Plugin Development Guide](../development/plugins.md) for detailed instructions on creating and testing plugins.

## Troubleshooting

### Common Issues

1. **Plugin not loading**: Check the logs for errors
2. **Missing dependencies**: Ensure all dependencies are installed
3. **Configuration errors**: Verify your plugin's configuration
4. **Permission issues**: Check file and directory permissions

### Getting Help

For help with plugins, please:

1. Check the [FAQ](../faq.md)
2. Search the [GitHub issues](https://github.com/yourorg/virtualization-mcp/issues)
3. Ask in the [community forum](https://community.example.com)
4. Open a [GitHub issue](https://github.com/yourorg/virtualization-mcp/issues/new)

## Contributing

We welcome contributions! Please see our [Contributing Guide](../CONTRIBUTING.md) for details on how to contribute plugins to the virtualization-mcp ecosystem.



