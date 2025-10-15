"""
Monitoring Tools for virtualization-mcp

This module provides monitoring and metrics collection tools for the virtualization-mcp system.
"""

from virtualization_mcp.tools.monitoring.metrics_tools import (
    MetricsManager,
    MetricsMiddleware,
    get_metrics,
    metrics_manager,
    prometheus_metrics,
    record_api_request,
    record_error,
    start_metrics_server,
    update_system_metrics,
    update_vm_metrics,
)

# For backward compatibility
__all__ = [
    "MetricsManager",
    "metrics_manager",
    "prometheus_metrics",
    "start_metrics_server",
    "record_api_request",
    "record_error",
    "update_vm_metrics",
    "update_system_metrics",
    "get_metrics",
    "MetricsMiddleware",
]

__all__ = [
    "MetricsManager",
    "metrics_manager",
    "start_metrics_server",
    "record_api_request",
    "record_error",
    "update_vm_metrics",
    "update_system_metrics",
    "get_metrics",
]
