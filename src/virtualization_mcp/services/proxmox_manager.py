"""Proxmox VE REST API client.

Proxmox VE is an open-source virtualization platform (KVM + LXC) with a
battle-tested REST API. This client wraps the API calls needed to manage
VMs (QEMU) remotely — list, create, start, stop, snapshots.

Configuration is via env vars, config file, or direct params:

    PROXMOX_HOST=<hostname-or-ip>
    PROXMOX_USER=<user@realm>     (default: root@pam)
    PROXMOX_PASSWORD=<password>
    PROXMOX_VERIFY_SSL=0          (default: 0, self-signed certs are normal)
    PROXMOX_NODE=<nodename>       (optional, autodetected if not set)
"""

import json
import logging
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class ProxmoxError(Exception):
    """Proxmox API error."""


class ProxmoxManager:
    """HTTP(S) client for the Proxmox VE REST API.

    Uses the ticket-based auth: POST /api2/json/access/ticket with
    username + password, then reuses the ticket cookie + CSRF token
    for subsequent requests.
    """

    def __init__(
        self,
        host: str | None = None,
        user: str | None = None,
        password: str | None = None,
        verify_ssl: bool = False,
        node: str | None = None,
    ):
        self.host = host or os.environ.get("PROXMOX_HOST", "")
        self.user = user or os.environ.get("PROXMOX_USER", "root@pam")
        self.password = password or os.environ.get("PROXMOX_PASSWORD", "")
        self.verify_ssl = verify_ssl or os.environ.get("PROXMOX_VERIFY_SSL", "0").lower() in ("1", "true", "yes")
        self._node = node or os.environ.get("PROXMOX_NODE", "")
        self._ticket: str | None = None
        self._csrf: str | None = None
        self._autodetected_node: str | None = None

    def _ensure_configured(self) -> None:
        if not self.host:
            raise ProxmoxError(
                "Proxmox host not configured. Set PROXMOX_HOST env var or pass host= to the constructor."
            )
        if not self.password:
            raise ProxmoxError(
                "Proxmox password not configured. Set PROXMOX_PASSWORD env var or pass password= to the constructor."
            )

    def _api_url(self, path: str) -> str:
        base = self.host.rstrip("/")
        if not base.startswith("http"):
            base = f"https://{base}"
        return f"{base}/api2/json/{path.lstrip('/')}"

    def _request(self, method: str, path: str, data: dict | None = None) -> dict[str, Any]:
        import base64 as _b64

        url = self._api_url(path)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        body = None

        if self._ticket:
            headers["Cookie"] = f"PVEAuthCookie={self._ticket}"
            headers["CSRFPreventionToken"] = self._csrf or ""
            if data:
                body = "&".join(f"{k}={_b64.urlsafe_b64encode(str(v).encode()).decode()}" for k, v in data.items())

        req = Request(url, data=body.encode() if body else None, headers=headers, method=method)
        try:
            resp = urlopen(req, timeout=30)
            result = json.loads(resp.read().decode())
            if result.get("data") is not None:
                return result["data"]
            return result
        except HTTPError as e:
            body = e.read().decode()
            raise ProxmoxError(f"Proxmox API error {e.code}: {body}") from e
        except URLError as e:
            raise ProxmoxError(f"Proxmox connection failed: {e.reason}") from e

    def authenticate(self) -> None:
        """Obtain a ticket from the Proxmox API."""
        import urllib.parse as _up

        self._ensure_configured()
        data = _up.urlencode({"username": self.user, "password": self.password}).encode()
        url = self._api_url("access/ticket")
        req = Request(url, data=data, method="POST")
        try:
            resp = urlopen(req, timeout=15)
            result = json.loads(resp.read().decode())
            ticket_data = result["data"]
            self._ticket = ticket_data["ticket"]
            self._csrf = ticket_data["CSRFPreventionToken"]
            logger.info("Authenticated to Proxmox at %s as %s", self.host, self.user)
        except HTTPError as e:
            raise ProxmoxError(f"Proxmox auth failed: {e.code} {e.read().decode()}") from e
        except URLError as e:
            raise ProxmoxError(f"Proxmox unreachable: {e.reason}") from e

    @property
    def node(self) -> str:
        if self._node:
            return self._node
        if self._autodetected_node:
            return self._autodetected_node
        nodes = self._request("GET", "nodes")
        if not nodes:
            raise ProxmoxError("No Proxmox nodes found in cluster")
        self._autodetected_node = nodes[0]["node"]
        logger.info("Autodetected Proxmox node: %s", self._autodetected_node)
        return self._autodetected_node

    # -- VM operations --

    def list_vms(self) -> list[dict[str, Any]]:
        """List all QEMU VMs on the node."""
        self.authenticate()
        vms = self._request("GET", f"nodes/{self.node}/qemu")
        result = []
        for vm in vms:
            result.append(
                {
                    "name": vm.get("name", ""),
                    "vmid": str(vm.get("vmid", "")),
                    "status": vm.get("status", "unknown"),
                    "mem": vm.get("mem", 0),
                    "cpus": vm.get("cpus", 0),
                    "disk": vm.get("disk", 0),
                    "uptime": vm.get("uptime", 0),
                    "provider": "proxmox",
                }
            )
        return result

    def get_vm_status(self, vmid: str) -> dict[str, Any]:
        """Get detailed status for a single VM."""
        self.authenticate()
        return self._request("GET", f"nodes/{self.node}/qemu/{vmid}/status/current")

    def start_vm(self, vmid: str) -> dict[str, Any]:
        """Start a VM."""
        self.authenticate()
        return self._request("POST", f"nodes/{self.node}/qemu/{vmid}/status/start")

    def stop_vm(self, vmid: str) -> dict[str, Any]:
        """Stop a VM (hard shutdown)."""
        self.authenticate()
        return self._request("POST", f"nodes/{self.node}/qemu/{vmid}/status/stop")

    def shutdown_vm(self, vmid: str) -> dict[str, Any]:
        """Send ACPI shutdown to a VM."""
        self.authenticate()
        return self._request("POST", f"nodes/{self.node}/qemu/{vmid}/status/shutdown")

    def create_vm(
        self,
        name: str,
        vmid: int | None = None,
        memory: int = 2048,
        cores: int = 2,
        disk_size: str = "32G",
        iso: str | None = None,
        net_bridge: str = "vmbr0",
    ) -> dict[str, Any]:
        """Create a new QEMU VM."""
        self.authenticate()
        params: dict[str, Any] = {
            "name": name,
            "memory": memory,
            "cores": cores,
            "net0": f"virtio,bridge={net_bridge}",
        }
        if vmid is not None:
            params["vmid"] = vmid
        if disk_size:
            params["virtio0"] = f"{disk_size},format=qcow2"
        if iso:
            params["ide2"] = f"{iso},media=cdrom"
        return self._request("POST", f"nodes/{self.node}/qemu", params)

    def delete_vm(self, vmid: str) -> dict[str, Any]:
        """Delete a VM (must be stopped first)."""
        self.authenticate()
        return self._request("DELETE", f"nodes/{self.node}/qemu/{vmid}")

    def create_snapshot(self, vmid: str, name: str, description: str = "") -> dict[str, Any]:
        """Create a VM snapshot."""
        self.authenticate()
        params = {"snapname": name}
        if description:
            params["description"] = description
        return self._request("POST", f"nodes/{self.node}/qemu/{vmid}/snapshot", params)

    def list_snapshots(self, vmid: str) -> list[dict[str, Any]]:
        """List all snapshots for a VM."""
        self.authenticate()
        return self._request("GET", f"nodes/{self.node}/qemu/{vmid}/snapshot")

    def delete_snapshot(self, vmid: str, name: str) -> dict[str, Any]:
        """Delete a VM snapshot."""
        self.authenticate()
        return self._request("DELETE", f"nodes/{self.node}/qemu/{vmid}/snapshot/{name}")

    # -- Node / cluster info --

    def node_status(self) -> dict[str, Any]:
        """Get node status (CPU, memory, disk)."""
        self.authenticate()
        return self._request("GET", f"nodes/{self.node}/status")

    def cluster_resources(self) -> list[dict[str, Any]]:
        """List all resources across the cluster."""
        self.authenticate()
        return self._request("GET", "cluster/resources")
