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
    "MetricsMiddleware",
    "get_metrics",
    "metrics_manager",
    "prometheus_metrics",
    "record_api_request",
    "record_error",
    "start_metrics_server",
    "update_system_metrics",
    "update_vm_metrics",
]

__all__ = [
    "MetricsManager",
    "get_metrics",
    "metrics_manager",
    "record_api_request",
    "record_error",
    "start_metrics_server",
    "update_system_metrics",
    "update_vm_metrics",
]
