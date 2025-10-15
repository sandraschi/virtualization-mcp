"""Monitoring plugin for virtualization-mcp."""

import asyncio
from datetime import datetime
from typing import Any

from prometheus_client import Counter, Gauge, start_http_server

from virtualization_mcp.server_v2.plugins import register_plugin
from virtualization_mcp.server_v2.plugins.base import BasePlugin


@register_plugin("monitoring")
class MonitoringPlugin(BasePlugin):
    """Monitoring plugin that provides metrics and health checks."""

    def __init__(self, config: dict[str, Any]):
        """Initialize the monitoring plugin."""
        super().__init__(config)
        self.metrics_port = config.get("metrics_port", 8001)
        self.metrics = {}
        self.setup_metrics()

    def setup_metrics(self) -> None:
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

    def setup_routes(self) -> None:
        """Set up API routes for monitoring."""

        @self.router.get("/health")
        async def health_check() -> dict[str, Any]:
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
            }

        @self.router.get("/metrics")
        async def get_metrics() -> dict[str, Any]:
            """Get current metrics."""
            return {
                "vm_count": self.metrics["vm_count"]._value.get(),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def startup(self) -> None:
        """Start the metrics server."""
        await super().startup()
        # Start Prometheus metrics server in a separate thread
        import threading

        self.metrics_thread = threading.Thread(target=start_http_server, args=(self.metrics_port,))
        self.metrics_thread.daemon = True
        self.metrics_thread.start()

        # Start background task to update metrics
        self.update_task = asyncio.create_task(self.update_metrics_loop())

    async def shutdown(self) -> None:
        """Clean up resources."""
        await super().shutdown()
        if hasattr(self, "update_task"):
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass

    async def update_metrics_loop(self) -> None:
        """Background task to update metrics."""
        while True:
            try:
                await self.update_metrics()
                await asyncio.sleep(30)  # Update every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.metrics["errors_total"].labels(type="metrics_update").inc()
                import logging

                logging.error(f"Error updating metrics: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error

    async def update_metrics(self) -> None:
        """Update all metrics."""
        try:
            # Get VM list (this would use the actual VM manager in a real implementation)
            vms = []  # await self.vm_manager.list_vms()

            # Update VM count
            self.metrics["vm_count"].set(len(vms))

            # Update per-VM metrics
            for vm in vms:
                # In a real implementation, we would get these from the VM manager
                vm_name = vm.get("name", "unknown")
                self.metrics["vm_cpu_usage"].labels(vm_name=vm_name).set(vm.get("cpu_usage", 0))
                self.metrics["vm_memory_usage"].labels(vm_name=vm_name).set(
                    vm.get("memory_usage", 0)
                )

        except Exception:
            self.metrics["errors_total"].labels(type="metrics_update").inc()
            raise
