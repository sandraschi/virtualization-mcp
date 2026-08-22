"""
Resource Guard Safety Utility for virtualization-mcp.

Monitors physical host memory and CPU utilization to prevent host resource exhaustion
when creating or powering on virtual machines.
"""

import logging
from typing import Any

import psutil

from virtualization_mcp.exceptions import VirtualizationMCPError

logger = logging.getLogger(__name__)

# Safety thresholds
MAX_MEMORY_PERCENT_THRESHOLD = 95.0  # Max host RAM usage % before blocking launch


class ResourceQuotaExceededError(VirtualizationMCPError):
    """Raised when host system resources are insufficient to launch or create a VM."""

    pass


class ResourceGuard:
    """Monitors host resources and enforces memory/CPU safety guards."""

    @staticmethod
    def get_system_resource_status() -> dict[str, Any]:
        """Return host system CPU, RAM, and swap memory statistics."""
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=None)
        return {
            "total_ram_mb": round(mem.total / (1024 * 1024), 2),
            "available_ram_mb": round(mem.available / (1024 * 1024), 2),
            "ram_used_percent": mem.percent,
            "cpu_used_percent": cpu_percent,
            "cpu_count": psutil.cpu_count(logical=True),
        }

    @classmethod
    def check_resource_quota(cls, requested_memory_mb: int = 0, max_threshold_percent: float = 95.0) -> dict[str, Any]:
        """Check whether requesting `requested_memory_mb` is safe given current host load.

        Args:
            requested_memory_mb: RAM requested for the new/powered-on VM in MB.
            max_threshold_percent: Host memory usage limit percentage (default 95.0%).

        Returns:
            dict containing success status and current metrics.

        Raises:
            ResourceQuotaExceededError: If physical RAM usage is above max_threshold_percent.
        """
        status = cls.get_system_resource_status()
        current_percent = status["ram_used_percent"]
        available_mb = status["available_ram_mb"]

        if current_percent >= max_threshold_percent:
            msg = (
                f"Host RAM utilization is critical ({current_percent}% >= {max_threshold_percent}% limit). "
                "Operation blocked to prevent host freeze."
            )
            logger.error(msg)
            raise ResourceQuotaExceededError(msg)

        if requested_memory_mb > 0 and requested_memory_mb > available_mb:
            msg = (
                f"Requested memory ({requested_memory_mb} MB) exceeds currently available host RAM "
                f"({available_mb:.0f} MB)."
            )
            logger.error(msg)
            raise ResourceQuotaExceededError(msg)

        return {
            "safe": True,
            "current_ram_used_percent": current_percent,
            "available_ram_mb": available_mb,
        }
