"""
VM Operations - Virtual Machine lifecycle management

Handles create, start, stop, delete, and configuration operations
using a compatibility layer that works with both VirtualBox Python API
and VBoxManage command-line tool.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

from .compat_adapter import VBoxManager, VBoxManagerError

logger = logging.getLogger(__name__)


class VMOperations:
    """
    High-level VM lifecycle operations

    Provides Austrian dev efficiency with comprehensive VM management
    including template-based creation, state management, and configuration.
    """

    def __init__(self, manager: VBoxManager, templates_path: str | Path | None = None):
        """
        Initialize VM operations with compatibility layer

        Args:
            manager: VBoxManager instance (from compat_adapter)
            templates_path: Path to VM templates YAML file or directory
        """
        self.manager = manager

        # Handle templates path resolution
        if templates_path is None:
            # Default to config directory in the package
            self.templates_path = Path(__file__).parent.parent.parent / "config" / "vm_templates.yaml"
        else:
            self.templates_path = Path(templates_path)

        self._templates = None
        logger.debug(f"VMOperations initialized with templates path: {self.templates_path}")

    @property
    def templates(self) -> dict[str, Any]:
        """Load and cache VM templates"""
        if self._templates is None:
            self._templates = self._load_templates()
        return self._templates

    def _load_templates(self) -> dict[str, Any]:
        """Load VM templates from YAML file"""
        try:
            if self.templates_path.exists():
                with open(self.templates_path) as f:
                    data = yaml.safe_load(f)
                    return data.get("templates", {})
            else:
                logger.warning(f"Templates file not found: {self.templates_path}")
                return self._get_default_templates()
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            return self._get_default_templates()

    def _get_default_templates(self) -> dict[str, Any]:
        """Return default VM templates if file loading fails"""
        return {
            "ubuntu-dev": {
                "os_type": "Ubuntu_64",
                "memory_mb": 4096,
                "disk_gb": 25,
                "cpus": 2,
                "network": "NAT",
                "description": "Ubuntu development environment",
            },
            "minimal-linux": {
                "os_type": "Ubuntu_64",
                "memory_mb": 1024,
                "disk_gb": 10,
                "cpus": 1,
                "network": "NAT",
                "description": "Minimal Linux for quick tests",
            },
            "win11-pro": {
                "os_type": "Windows11_64",
                "memory_mb": 8192,
                "disk_gb": 80,
                "cpus": 4,
                "network": "NAT",
                "description": "Windows 11 Pro - attach ISO, install once, export to OVA in assets/vbox for reuse",
            },
        }

    def create_vm(
        self,
        name: str,
        template: str = "ubuntu-dev",
        memory_mb: int | None = None,
        disk_gb: int | None = None,
        cpus: int | None = None,
        custom_settings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create new VM from template with optional overrides

        Args:
            name: VM name
            template: Template name from config
            memory_mb: Override template memory
            disk_gb: Override template disk size
            custom_settings: Additional custom settings

        Returns:
            Dict with creation result and VM info
        """
        try:
            logger.debug("Starting VM creation: name='%s', template='%s'", name, template)

            # Validate VM name
            if not self.manager.validate_vm_name(name):
                logger.warning("Rejected invalid VM name: '%s'", name)
                raise VBoxManagerError(f"Invalid VM name: '{name}'")

            logger.debug("Name validation passed for '%s'", name)

            # Check if VM already exists
            if self.manager.vm_exists(name):
                logger.warning("VM '%s' already exists, aborting creation", name)
                raise VBoxManagerError(f"VM '{name}' already exists")

            # Get template configuration
            if template not in self.templates:
                logger.warning("Template '%s' not found, available: %s", template, list(self.templates.keys()))
                raise VBoxManagerError(f"Template '{template}' not found. Available: {list(self.templates.keys())}")

            template_config = self.templates[template].copy()

            # Apply overrides
            if memory_mb:
                logger.debug("Overriding template memory: %d -> %d MB", template_config.get("memory_mb"), memory_mb)
                template_config["memory_mb"] = memory_mb
            if disk_gb:
                logger.debug("Overriding template disk: %d -> %d GB", template_config.get("disk_gb"), disk_gb)
                template_config["disk_gb"] = disk_gb
            if cpus:
                logger.debug("Overriding template cpus: %d -> %d", template_config.get("cpus", 1), cpus)
                template_config["cpus"] = cpus
            if custom_settings:
                logger.debug("Applying custom settings: %s", custom_settings)
                template_config.update(custom_settings)

            logger.info(
                "Creating VM '%s' from template '%s': os=%s, mem=%dMB, disk=%dGB, cpus=%d, net=%s",
                name,
                template,
                template_config["os_type"],
                template_config["memory_mb"],
                template_config.get("disk_gb", 0),
                template_config.get("cpus", 1),
                template_config.get("network", "NAT"),
            )

            # Create VM
            import subprocess as _sub

            vbox = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
            _sub.run(
                [vbox, "createvm", "--name", name, "--ostype", template_config["os_type"], "--register"],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            logger.debug("VM '%s' registered with VBox", name)

            # Configure memory + network + boot order in one modifyvm call
            boot_opts = ["--boot1", "dvd", "--boot2", "disk"]
            _sub.run(
                [vbox, "modifyvm", name, "--memory", str(template_config["memory_mb"]), *boot_opts],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )

            # Configure network
            network_type = template_config.get("network", "NAT")
            _sub.run(
                [vbox, "modifyvm", name, "--nic1", network_type.lower()],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )

            # Create and attach disk if specified
            if template_config.get("disk_gb"):
                logger.debug("Creating disk for '%s': %d GB", name, template_config["disk_gb"])
                disk_path = self._create_disk(name, template_config["disk_gb"])
                self._attach_disk(name, disk_path)

            # Apply additional settings
            self._apply_vm_settings(name, template_config)

            # Get final VM info (vbox_compat lowercases keys, so check both)
            vm_info = self.manager.get_vm_info(name)
            vm_state = vm_info.get("vmstate") or vm_info.get("VMState", "unknown")
            logger.debug("VM '%s' info retrieved: state=%s", name, vm_state)

            result = {
                "success": True,
                "vm_name": name,
                "template": template,
                "configuration": template_config,
                "vm_info": vm_info,
                "message": f"VM '{name}' created successfully from template '{template}'",
            }

            logger.info(
                "Successfully created VM '%s' (os=%s, mem=%dMB, disk=%dGB)",
                name,
                template_config["os_type"],
                template_config["memory_mb"],
                template_config.get("disk_gb", 0),
            )
            return result

        except VBoxManagerError as e:
            logger.error("Failed to create VM '%s' from template '%s': %s", name, template, e)
            logger.debug("Log path for diagnostics: %s", getattr(self.manager, "log_path", "N/A"))
            self._cleanup_failed_vm(name)
            raise
        except Exception as e:
            logger.error("Unexpected error creating VM '%s' from template '%s': %s", name, template, e)
            logger.debug("Log path for diagnostics: %s", getattr(self.manager, "log_path", "N/A"))
            self._cleanup_failed_vm(name)
            raise VBoxManagerError(f"Failed to create VM: {e!s}") from e

    def _create_disk(self, vm_name: str, size_gb: int) -> str:
        """Create virtual disk in the VM's folder."""
        import os as _os

        home = _os.path.expanduser("~")
        vbox_folder = _os.path.join(home, "VirtualBox VMs", vm_name)
        _os.makedirs(vbox_folder, exist_ok=True)
        disk_path = _os.path.join(vbox_folder, f"{vm_name}.vdi")
        size_mb = size_gb * 1024

        import subprocess as _sub

        vbox = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
        _sub.run(
            [vbox, "createhd", "--filename", disk_path, "--size", str(size_mb), "--format", "VDI"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        return disk_path

    def _attach_disk(self, vm_name: str, disk_path: str) -> None:
        """Attach disk to VM via SATA controller."""
        import subprocess as _sub

        vbox = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
        # Add SATA controller (ignore error if exists)
        _sub.run(
            [vbox, "storagectl", vm_name, "--name", "SATA", "--add", "sata", "--controller", "IntelAHCI"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        # Attach disk
        _sub.run(
            [
                vbox,
                "storageattach",
                vm_name,
                "--storagectl",
                "SATA",
                "--port",
                "0",
                "--device",
                "0",
                "--type",
                "hdd",
                "--medium",
                disk_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )

    def _apply_vm_settings(self, vm_name: str, config: dict[str, Any]) -> None:
        """Apply additional VM settings from template."""
        import subprocess as _sub

        vbox = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"

        # Enable ACPI, IOAPIC, VT-x, CPU count, VMSVGA, VRAM, clipboard
        cpus = config.get("cpus", 1)
        _sub.run(
            [
                vbox,
                "modifyvm",
                vm_name,
                "--acpi",
                "on",
                "--ioapic",
                "on",
                "--hwvirtex",
                "on",
                "--cpus",
                str(cpus),
                "--graphicscontroller",
                "vmsvga",
                "--vram",
                "128",
                "--clipboard",
                "bidirectional",
                "--draganddrop",
                "bidirectional",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Enable 3D acceleration separately (may fail)
        _sub.run([vbox, "modifyvm", vm_name, "--accelerate3d", "on"], capture_output=True, text=True, timeout=15)

    def start_vm(self, name: str, headless: bool = True) -> dict[str, Any]:
        """
        Start virtual machine

        Args:
            name: VM name
            headless: Start without GUI (default for testing)

        Returns:
            Dict with start result
        """
        try:
            if not self.manager.vm_exists(name):
                raise VBoxManagerError(f"VM '{name}' not found")

            current_state = self.manager.get_vm_state(name)
            if current_state == "running":
                return {
                    "success": True,
                    "vm_name": name,
                    "message": f"VM '{name}' already running",
                    "state": "running",
                }

            start_type = "headless" if headless else "gui"
            logger.info(f"Starting VM '{name}' in {start_type} mode")

            self.manager.run_command(["startvm", name, "--type", start_type])

            return {
                "success": True,
                "vm_name": name,
                "message": f"VM '{name}' started successfully",
                "mode": start_type,
                "state": "running",
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to start VM '{name}': {e}")
            raise

    def stop_vm(self, name: str, force: bool = False) -> dict[str, Any]:
        """
        Stop virtual machine

        Args:
            name: VM name
            force: Force stop (power off) vs graceful shutdown

        Returns:
            Dict with stop result
        """
        try:
            if not self.manager.vm_exists(name):
                raise VBoxManagerError(f"VM '{name}' not found")

            current_state = self.manager.get_vm_state(name)
            if current_state != "running":
                return {
                    "success": True,
                    "vm_name": name,
                    "message": f"VM '{name}' already stopped",
                    "state": current_state,
                }

            stop_type = "poweroff" if force else "acpipowerbutton"
            logger.info(f"Stopping VM '{name}' with {stop_type}")

            self.manager.run_command(["controlvm", name, stop_type])

            return {
                "success": True,
                "vm_name": name,
                "message": f"VM '{name}' stopped successfully",
                "method": "forced" if force else "graceful",
                "state": "poweroff",
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to stop VM '{name}': {e}")
            raise

    def delete_vm(self, name: str, delete_disk: bool = True) -> dict[str, Any]:
        """
        Delete virtual machine

        Args:
            name: VM name
            delete_disk: Also delete VM disk files

        Returns:
            Dict with deletion result
        """
        try:
            if not self.manager.vm_exists(name):
                raise VBoxManagerError(f"VM '{name}' not found")

            # Stop VM if running
            current_state = self.manager.get_vm_state(name)
            if current_state == "running":
                logger.info(f"Stopping running VM '{name}' before deletion")
                self.stop_vm(name, force=True)

            # Unregister and delete
            cmd = ["unregistervm", name]
            if delete_disk:
                cmd.append("--delete")

            logger.info(f"Deleting VM '{name}' (delete_disk={delete_disk})")
            self.manager.run_command(cmd)

            return {
                "success": True,
                "vm_name": name,
                "message": f"VM '{name}' deleted successfully",
                "disk_deleted": delete_disk,
            }

        except VBoxManagerError as e:
            logger.error(f"Failed to delete VM '{name}': {e}")
            raise

    def _cleanup_failed_vm(self, name: str) -> None:
        """Clean up VM after failed creation"""
        try:
            if self.manager.vm_exists(name):
                logger.info(f"Cleaning up failed VM '{name}'")
                self.delete_vm(name, delete_disk=True)
        except Exception as e:
            logger.warning(f"Failed to cleanup VM '{name}': {e}")

    def list_vms(self, details: bool = False) -> dict[str, Any]:
        """
        List all registered VMs.

        Args:
            details: If True, include more detail per VM (uses manager's verbose listing).

        Returns:
            Dict with "success", "vms" (list), and on error "error".
        """
        try:
            vms = self.manager.list_vms(verbose=details)
            return {"success": True, "vms": vms}
        except VBoxManagerError as e:
            logger.debug(f"list_vms failed: {e}")
            return {"success": False, "error": str(e), "vms": []}

    def attach_iso(self, vm_name: str, iso_path: str, port: int = 1, device: int = 0) -> dict[str, Any]:
        """Attach an ISO to the VM's optical drive via VBoxManage."""
        import subprocess as _sub

        vbox = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
        try:
            # Add IDE controller (ignore error if already exists)
            _sub.run(
                [vbox, "storagectl", vm_name, "--name", "IDE", "--add", "ide"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            # Attach the ISO
            r = _sub.run(
                [
                    vbox,
                    "storageattach",
                    vm_name,
                    "--storagectl",
                    "IDE",
                    "--port",
                    str(port),
                    "--device",
                    str(device),
                    "--type",
                    "dvddrive",
                    "--medium",
                    iso_path,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if r.returncode != 0:
                raise VBoxManagerError(r.stderr.strip() or f"VBoxManage exit code {r.returncode}")
            return {"success": True, "message": f"ISO attached: {iso_path}"}
        except Exception as e:
            logger.error("Failed to attach ISO to %s: %s", vm_name, e)
            return {"success": False, "error": str(e)}

    def configure_network(
        self,
        name: str,
        adapter: int = 1,
        mode: str = "nat",
        host_only_if: str | None = None,
        bridged_if: str | None = None,
        intnet_name: str | None = None,
        port_forwarding: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Configure a VM network adapter.

        Args:
            name: VM name
            adapter: NIC number (1-4)
            mode: nat, bridged, hostonly, intnet, natnetwork, none
            host_only_if: Host-only interface name (for hostonly mode)
            bridged_if: Bridged adapter name (for bridged mode)
            intnet_name: Internal network name (for intnet mode)
            port_forwarding: List of rules [{name, protocol, host_port, guest_port}]

        Returns:
            Dict with success/error
        """
        try:
            import subprocess as _sub

            vbox = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
            nic = f"--nic{adapter}"
            cmd = [vbox, "modifyvm", name, nic, mode.upper()]
            _sub.run(cmd, capture_output=True, text=True, timeout=30, check=True)

            # Mode-specific settings
            if mode == "hostonly" and host_only_if:
                _sub.run(
                    [vbox, "modifyvm", name, f"--hostonlyadapter{adapter}", host_only_if],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            elif mode == "bridged" and bridged_if:
                _sub.run(
                    [vbox, "modifyvm", name, f"--bridgeadapter{adapter}", bridged_if],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            elif mode == "intnet" and intnet_name:
                _sub.run(
                    [vbox, "modifyvm", name, f"--intnet{adapter}", intnet_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

            # Port forwarding rules (NAT only)
            if mode == "nat" and port_forwarding:
                for rule in port_forwarding:
                    rname = rule.get("name", f"rule{adapter}")
                    proto = rule.get("protocol", "tcp")
                    hport = rule.get("host_port", 8080)
                    gport = rule.get("guest_port", 80)
                    _sub.run(
                        [vbox, "controlvm", name, "natpf1", rname, f"{proto},,{hport},,{gport}"],
                        capture_output=True,
                        text=True,
                        timeout=15,
                    )

            logger.info("Network configured for %s: nic%d=%s", name, adapter, mode)
            return {"success": True, "adapter": adapter, "mode": mode}
        except Exception as e:
            logger.error("Failed to configure network for %s: %s", name, e)
            return {"success": False, "error": str(e)}

    def get_network_config(self, name: str) -> dict[str, Any]:
        """Get all network adapter configurations for a VM.

        Args:
            name: VM name

        Returns:
            Dict with adapters list and port forwarding rules
        """
        try:
            import re
            import subprocess as _sub

            vbox = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
            r = _sub.run(
                [vbox, "showvminfo", name, "--machinereadable"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if r.returncode != 0:
                return {"success": False, "error": r.stderr.strip() or "VM not found"}

            adapters = []
            port_rules = []
            for line in r.stdout.splitlines():
                # NIC types: nic1="nat", nic2="bridged", etc.
                m = re.match(r'^nic(\d+)="([^"]+)"', line)
                if m:
                    adapters.append({"adapter": int(m.group(1)), "mode": m.group(2).lower()})
                # NAT forwarding rules
                m2 = re.match(r'^Forwarding\(\d+\)="([^"]+)"', line)
                if m2:
                    # Format: "rule_name,tcp,,host_port,,guest_port"
                    parts = m2.group(1).split(",")
                    if len(parts) >= 5:
                        port_rules.append(
                            {
                                "name": parts[0],
                                "protocol": parts[1],
                                "host_port": int(parts[3]) if parts[3].isdigit() else parts[3],
                                "guest_port": int(parts[5])
                                if len(parts) > 5 and parts[5].isdigit()
                                else parts[5]
                                if len(parts) > 5
                                else "",
                            }
                        )

            return {
                "success": True,
                "vm_name": name,
                "adapters": sorted(adapters, key=lambda a: a["adapter"]),
                "port_forwarding": port_rules,
            }
        except Exception as e:
            logger.error("Failed to get network config for %s: %s", name, e)
            return {"success": False, "error": str(e)}

    def list_templates(self) -> list[dict[str, Any]]:
        """Get list of available VM templates"""
        return [
            {
                "name": name,
                "description": config.get("description", "No description"),
                "os_type": config.get("os_type", "Unknown"),
                "memory_mb": config.get("memory_mb", 0),
                "disk_gb": config.get("disk_gb", 0),
                "config": config,
            }
            for name, config in self.templates.items()
        ]
