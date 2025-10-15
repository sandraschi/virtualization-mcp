"""
Monitoring Tools for virtualization-mcp.

This module provides monitoring and metrics collection tools for the virtualization-mcp system.
"""

import logging
from typing import Any

from prometheus_client import Counter, Gauge, generate_latest, start_http_server

logger = logging.getLogger(__name__)


class MetricsManager:
    """Manages metrics collection and exposure for the virtualization-mcp system."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the MetricsManager.

        Args:
            config: Configuration dictionary with optional keys:
                - metrics_port: Port to expose metrics on (default: 8001)
                - metrics_path: URL path for metrics (default: /metrics)
        """
        config = config or {}
        self.metrics_port = config.get("metrics_port", 8001)
        self.metrics_path = config.get("metrics_path", "/metrics")
        self.metrics: dict[str, Any] = {}
        self._setup_metrics()

    def _setup_metrics(self) -> None:
        """Set up Prometheus metrics."""
        # VM metrics
        self.metrics["vm_count"] = Gauge("virtualization-mcp_vm_count", "Number of VMs")

        self.metrics["vm_cpu_usage"] = Gauge(
            "virtualization-mcp_vm_cpu_usage_percent", "CPU usage percentage per VM", ["vm_name"]
        )

        self.metrics["vm_memory_usage"] = Gauge(
            "virtualization-mcp_vm_memory_usage_bytes", "Memory usage in bytes per VM", ["vm_name"]
        )

        # API metrics
        self.metrics["api_requests_total"] = Counter(
            "virtualization-mcp_api_requests_total",
            "Total number of API requests",
            ["endpoint", "method", "status"],
        )

        # Error metrics
        self.metrics["errors_total"] = Counter(
            "virtualization-mcp_errors_total", "Total number of errors", ["type"]
        )

        # Performance metrics
        self.metrics["request_duration_seconds"] = Gauge(
            "virtualization-mcp_request_duration_seconds",
            "Request duration in seconds",
            ["endpoint", "method"],
        )

        # Resource usage metrics
        self.metrics["system_cpu_usage"] = Gauge(
            "virtualization-mcp_system_cpu_usage_percent", "System CPU usage percentage"
        )

        self.metrics["system_memory_usage"] = Gauge(
            "virtualization-mcp_system_memory_usage_bytes", "System memory usage in bytes"
        )

        self.metrics["system_disk_usage"] = Gauge(
            "virtualization-mcp_system_disk_usage_bytes",
            "System disk usage in bytes",
            ["mount_point"],
        )

    def start_metrics_server(self) -> None:
        """Start the Prometheus metrics server."""
        try:
            start_http_server(self.metrics_port)
            logger.info(f"Metrics server started on port {self.metrics_port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")

    def record_api_request(self, endpoint: str, method: str, status_code: int) -> None:
        """Record an API request.

        Args:
            endpoint: The API endpoint that was called
            method: The HTTP method used (GET, POST, etc.)
            status_code: The HTTP status code returned
        """
        self.metrics["api_requests_total"].labels(
            endpoint=endpoint, method=method.upper(), status=status_code
        ).inc()

    def record_error(self, error_type: str) -> None:
        """Record an error.

        Args:
            error_type: The type of error that occurred
        """
        self.metrics["errors_total"].labels(type=error_type).inc()

    def update_vm_metrics(self, vm_name: str, cpu_usage: float, memory_usage: int) -> None:
        """Update VM-specific metrics.

        Args:
            vm_name: Name of the virtual machine
            cpu_usage: CPU usage percentage (0-100)
            memory_usage: Memory usage in bytes
        """
        self.metrics["vm_cpu_usage"].labels(vm_name=vm_name).set(cpu_usage)
        self.metrics["vm_memory_usage"].labels(vm_name=vm_name).set(memory_usage)

    def update_system_metrics(
        self, cpu_usage: float, memory_usage: int, disk_usage: dict[str, int]
    ) -> None:
        """Update system-wide metrics.

        Args:
            cpu_usage: System CPU usage percentage (0-100)
            memory_usage: System memory usage in bytes
            disk_usage: Dictionary mapping mount points to disk usage in bytes
        """
        self.metrics["system_cpu_usage"].set(cpu_usage)
        self.metrics["system_memory_usage"].set(memory_usage)

        # Update disk usage for each mount point
        for mount_point, usage in disk_usage.items():
            self.metrics["system_disk_usage"].labels(mount_point=mount_point).set(usage)

    def get_metrics(self) -> bytes:
        """Get the current metrics in Prometheus format.

        Returns:
            bytes: The metrics in Prometheus text format
        """
        return generate_latest()


# Create a singleton instance
metrics_manager = MetricsManager()

# Export the tool functions
start_metrics_server = metrics_manager.start_metrics_server
record_api_request = metrics_manager.record_api_request
record_error = metrics_manager.record_error
update_vm_metrics = metrics_manager.update_vm_metrics
update_system_metrics = metrics_manager.update_system_metrics
get_metrics = metrics_manager.get_metrics

# Export the metrics manager for advanced usage
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
