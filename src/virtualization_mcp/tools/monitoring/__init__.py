"""
Monitoring Tools for VBoxMCP

This module provides monitoring and metrics collection tools for the VBoxMCP system.
"""

from virtualization_mcp.tools.monitoring.metrics_tools import (
    MetricsManager,
    metrics_manager,
    prometheus_metrics,
    start_metrics_server,
    record_api_request,
    record_error,
    update_vm_metrics,
    update_system_metrics,
    get_metrics,
    MetricsMiddleware
)

# For backward compatibility
__all__ = [
    'MetricsManager',
    'metrics_manager',
    'prometheus_metrics',
    'start_metrics_server',
    'record_api_request',
    'record_error',
    'update_vm_metrics',
    'update_system_metrics',
    'get_metrics',
    'MetricsMiddleware'
]

__all__ = [
    'MetricsManager',
    'metrics_manager',
    'start_metrics_server',
    'record_api_request',
    'record_error',
    'update_vm_metrics',
    'update_system_metrics',
    'get_metrics'
]
