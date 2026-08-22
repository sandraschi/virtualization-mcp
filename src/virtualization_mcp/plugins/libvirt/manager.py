"""
Libvirt/KVM Provider Plugin for virtualization-mcp.

Provides libvirt/KVM domain management capabilities on Linux and WSL2 hosts.
"""

import logging
import shutil
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


class LibvirtManager:
    """Manager for libvirt / QEMU / KVM domains."""

    def __init__(self) -> None:
        self.virsh_path = shutil.which("virsh")

    def is_available(self) -> bool:
        """Return True if virsh CLI tool is installed and accessible."""
        return self.virsh_path is not None

    def list_domains(self) -> list[dict[str, Any]]:
        """List active and inactive libvirt virtual machine domains.

        Returns:
            List of dicts containing domain ID, name, and state.
        """
        if not self.is_available():
            logger.warning("virsh CLI tool not available on this host.")
            return []

        try:
            res = subprocess.run(
                [self.virsh_path, "list", "--all"],
                check=True,
                capture_output=True,
                text=True,
            )
            domains = []
            lines = res.stdout.strip().splitlines()
            for line in lines[2:]:  # Skip header lines
                parts = line.strip().split()
                if len(parts) >= 2:
                    dom_id = parts[0]
                    name = parts[1]
                    state = " ".join(parts[2:]) if len(parts) > 2 else "unknown"
                    domains.append({"id": dom_id, "name": name, "state": state})
            return domains
        except Exception as e:
            logger.error(f"Error listing libvirt domains: {e}")
            return []

    def start_domain(self, domain_name: str) -> dict[str, Any]:
        """Start a libvirt domain.

        Args:
            domain_name: Domain name or UUID.

        Returns:
            Operation result status dict.
        """
        if not self.is_available():
            return {"status": "error", "message": "virsh tool not available"}

        try:
            res = subprocess.run(
                [self.virsh_path, "start", domain_name],
                check=True,
                capture_output=True,
                text=True,
            )
            return {"status": "success", "domain": domain_name, "output": res.stdout.strip()}
        except Exception as e:
            return {"status": "error", "domain": domain_name, "message": str(e)}

    def stop_domain(self, domain_name: str) -> dict[str, Any]:
        """Shutdown a libvirt domain gracefully.

        Args:
            domain_name: Domain name or UUID.

        Returns:
            Operation result status dict.
        """
        if not self.is_available():
            return {"status": "error", "message": "virsh tool not available"}

        try:
            res = subprocess.run(
                [self.virsh_path, "shutdown", domain_name],
                check=True,
                capture_output=True,
                text=True,
            )
            return {"status": "success", "domain": domain_name, "output": res.stdout.strip()}
        except Exception as e:
            return {"status": "error", "domain": domain_name, "message": str(e)}
