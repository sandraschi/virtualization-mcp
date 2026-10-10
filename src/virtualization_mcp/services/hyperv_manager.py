"""
Hyper-V Manager service implementation for virtualization-mcp.

Single source of truth for Hyper-V PowerShell operations. Used by:
- webapp REST (vm_service.hyperv_manager)
- MCP tools (tools/vm/hyperv_tools.py delegates here)

Covers VMConnect console, checkpoints, VMSwitch networking, and ISO media,
per https://learn.microsoft.com/en-gb/windows-server/virtualization/hyper-v/virtual-machine-connection
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class HyperVVM(BaseModel):
    name: str
    state: str
    status: str
    uptime: str
    memory_usage: int | None = None
    cpu_usage: int | None = None
    provider: str = "hyperv"


def _q(value: str) -> str:
    """Quote a PowerShell single-quoted string safely ('' escapes ')."""
    return str(value).replace("'", "''")


class HyperVManager:
    """Manages Hyper-V virtual machines using PowerShell."""

    def __init__(self):
        self._check_available = None

    async def is_available(self) -> bool:
        """Check if Hyper-V is available and accessible."""
        if self._check_available is not None:
            return self._check_available

        try:
            # Try a simple Get-VM command
            await self._run_ps("Get-VM -ErrorAction SilentlyContinue | Select-Object Name | ConvertTo-Json")
            self._check_available = True
            return True
        except Exception as e:
            logger.warning(f"Hyper-V not available or no permissions: {e}")
            self._check_available = False
            return False

    async def list_vms(self) -> list[dict[str, Any]]:
        """List all Hyper-V virtual machines."""
        if not await self.is_available():
            return []

        try:
            cmd = "Get-VM | Select-Object Name, State, Status, Uptime, MemoryAssigned, CPUUsage | ConvertTo-Json"
            stdout = await self._run_ps(cmd)

            if not stdout:
                return []

            data = json.loads(stdout)
            if isinstance(data, dict):
                data = [data]

            vms = []
            for item in data:
                # Map PowerShell states to our standard states
                ps_state = str(item.get("State", "Off"))
                state = self._map_state(ps_state)

                vms.append(
                    {
                        "name": item.get("Name"),
                        "state": state,
                        "status": item.get("Status", ""),
                        "uptime": str(item.get("Uptime", "")),
                        "memory_mb": int(item.get("MemoryAssigned", 0)) // (1024 * 1024),
                        "cpus": 0,  # Get-VM doesn't show CPU count directly in simple select
                        "provider": "hyperv",
                        "os_type": "Windows/Other",
                    }
                )
            return vms
        except Exception as e:
            logger.error(f"Error listing Hyper-V VMs: {e}")
            return []

    async def get_vm(self, name: str) -> dict[str, Any] | None:
        """Get detailed info for one Hyper-V VM."""
        try:
            safe = _q(name)
            cmd = (
                f"Get-VM -Name '{safe}' -ErrorAction Stop | "
                "Select-Object Name, State, Status, Uptime, MemoryAssigned, "
                "ProcessorCount, Generation, Path, Version, "
                "AutomaticStartAction, AutomaticStopAction | ConvertTo-Json"
            )
            stdout = await self._run_ps(cmd)
            if not stdout:
                return None
            item = json.loads(stdout)
            if isinstance(item, list):
                item = item[0] if item else None
            if not item:
                return None
            return {
                "name": item.get("Name"),
                "state": self._map_state(str(item.get("State", "Off"))),
                "status": str(item.get("Status", "")),
                "uptime": str(item.get("Uptime", "")),
                "memory_mb": int(item.get("MemoryAssigned", 0)) // (1024 * 1024),
                "cpus": int(item.get("ProcessorCount", 0) or 0),
                "generation": int(item.get("Generation", 2) or 2),
                "path": str(item.get("Path", "")),
                "version": str(item.get("Version", "")),
                "provider": "hyperv",
                "os_type": "Windows/Other",
            }
        except Exception as e:
            logger.error(f"Error getting Hyper-V VM {name}: {e}")
            return None

    async def create_vm(
        self, name: str, memory_mb: int = 2048, disk_gb: int = 25, generation: int = 2
    ) -> dict[str, Any]:
        """Create a new Hyper-V VM."""
        try:
            safe = _q(name)
            vhd_path = f"C:\\VMs\\{name}\\{name}.vhdx"
            boot_device_param = "-BootDevice VHD" if generation == 1 else ""
            ps = (
                f"New-Item -ItemType Directory -Path 'C:\\VMs\\{safe}' -Force | Out-Null; "
                f"New-VM -Name '{safe}' -MemoryStartupBytes {int(memory_mb)}MB {boot_device_param} "
                f"-NewVHDPath '{vhd_path}' -NewVHDSizeBytes {int(disk_gb)}GB "
                f"-Generation {int(generation)}"
            )
            await self._run_ps(ps)
            return {"status": "success", "vm_name": name, "message": f"Hyper-V VM {name} created"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def delete_vm(self, name: str, delete_vhd: bool = True) -> dict[str, Any]:
        """Delete a Hyper-V VM, optionally removing its VHDX folder."""
        try:
            safe = _q(name)
            ps = (
                f"Stop-VM -Name '{safe}' -TurnOff -ErrorAction SilentlyContinue; "
                f"Remove-VM -Name '{safe}' -Force -ErrorAction Stop"
            )
            await self._run_ps(ps)
            if delete_vhd:
                folder = f"C:\\VMs\\{name}"
                try:
                    if os.path.isdir(folder):
                        import shutil

                        shutil.rmtree(folder, ignore_errors=True)
                except Exception as e:
                    logger.warning(f"Could not remove VHD folder {folder}: {e}")
            return {"status": "success", "vm_name": name, "message": f"Hyper-V VM {name} deleted"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def start_vm(self, name: str) -> dict[str, Any]:
        """Start a Hyper-V VM."""
        try:
            await self._run_ps(f"Start-VM -Name '{_q(name)}'")
            return {"status": "success", "message": f"Hyper-V VM {name} started"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def stop_vm(self, name: str, force: bool = False) -> dict[str, Any]:
        """Stop a Hyper-V VM."""
        try:
            flag = "-TurnOff" if force else "-Force"
            await self._run_ps(f"Stop-VM -Name '{_q(name)}' {flag}")
            return {"status": "success", "message": f"Hyper-V VM {name} stopped"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def pause_vm(self, name: str) -> dict[str, Any]:
        """Suspend/Pause a Hyper-V VM."""
        try:
            await self._run_ps(f"Suspend-VM -Name '{_q(name)}'")
            return {"status": "success", "message": f"Hyper-V VM {name} paused"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def resume_vm(self, name: str) -> dict[str, Any]:
        """Resume a Hyper-V VM."""
        try:
            await self._run_ps(f"Resume-VM -Name '{_q(name)}'")
            return {"status": "success", "message": f"Hyper-V VM {name} resumed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # -- Checkpoints (VMConnect Action > Checkpoint) --

    async def list_checkpoints(self, name: str) -> list[dict[str, Any]]:
        """List checkpoints (snapshots) for a Hyper-V VM."""
        try:
            cmd = (
                f"Get-VMSnapshot -VMName '{_q(name)}' -ErrorAction SilentlyContinue | "
                "Select-Object Name, SnapshotType, CreationTime, Id | ConvertTo-Json"
            )
            stdout = await self._run_ps(cmd)
            if not stdout:
                return []
            data = json.loads(stdout)
            if isinstance(data, dict):
                data = [data]
            return [
                {
                    "name": item.get("Name"),
                    "type": str(item.get("SnapshotType", "")),
                    "creation_time": str(item.get("CreationTime", "")),
                    "id": str(item.get("Id", "")),
                }
                for item in data
            ]
        except Exception as e:
            logger.error(f"Error listing checkpoints for {name}: {e}")
            return []

    async def create_checkpoint(self, name: str, checkpoint_name: str) -> dict[str, Any]:
        """Create a named checkpoint for a Hyper-V VM."""
        try:
            await self._run_ps(f"Checkpoint-VM -Name '{_q(name)}' -SnapshotName '{_q(checkpoint_name)}'")
            return {"status": "success", "message": f"Checkpoint {checkpoint_name} created for {name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def restore_checkpoint(self, name: str, checkpoint_name: str) -> dict[str, Any]:
        """Restore a Hyper-V VM to a named checkpoint."""
        try:
            await self._run_ps(f"Restore-VMSnapshot -Name '{_q(checkpoint_name)}' -VMName '{_q(name)}' -Confirm:$false")
            return {"status": "success", "message": f"VM {name} restored to {checkpoint_name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def remove_checkpoint(self, name: str, checkpoint_name: str) -> dict[str, Any]:
        """Delete a named checkpoint."""
        try:
            await self._run_ps(f"Remove-VMSnapshot -Name '{_q(checkpoint_name)}' -VMName '{_q(name)}' -Confirm:$false")
            return {"status": "success", "message": f"Checkpoint {checkpoint_name} removed from {name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # -- Networking (VMSwitch) --

    async def list_switches(self) -> list[dict[str, Any]]:
        """List Hyper-V virtual switches."""
        try:
            cmd = "Get-VMSwitch | Select-Object Name, SwitchType, NetAdapterInterfaceDescription | ConvertTo-Json"
            stdout = await self._run_ps(cmd)
            if not stdout:
                return []
            data = json.loads(stdout)
            if isinstance(data, dict):
                data = [data]
            return [
                {
                    "name": item.get("Name"),
                    "type": str(item.get("SwitchType", "")),
                    "adapter": str(item.get("NetAdapterInterfaceDescription", "")),
                }
                for item in data
            ]
        except Exception as e:
            logger.error(f"Error listing VMSwitches: {e}")
            return []

    async def create_switch(self, switch_name: str, switch_type: str = "Internal") -> dict[str, Any]:
        """Create a Hyper-V virtual switch (External/Internal/Private)."""
        try:
            st = switch_type if switch_type in ("External", "Internal", "Private") else "Internal"
            await self._run_ps(f"New-VMSwitch -Name '{_q(switch_name)}' -SwitchType {st}")
            return {"status": "success", "message": f"Switch {switch_name} ({st}) created"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def connect_network(self, name: str, switch_name: str) -> dict[str, Any]:
        """Connect a VM's network adapter to a virtual switch."""
        try:
            await self._run_ps(f"Connect-VMNetworkAdapter -VMName '{_q(name)}' -SwitchName '{_q(switch_name)}'")
            return {"status": "success", "message": f"VM {name} connected to {switch_name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # -- Media (VMConnect Media > DVD image) --

    async def attach_iso(self, name: str, iso_path: str) -> dict[str, Any]:
        """Attach an ISO to a VM's DVD drive (adds one if missing)."""
        try:
            norm = os.path.normpath(os.path.abspath(iso_path))
            if not os.path.isfile(norm):
                return {"status": "error", "message": f"ISO not found: {norm}"}
            safe_iso = norm.replace("'", "''")
            ps = (
                f"$dvd = Get-VMDvdDrive -VMName '{_q(name)}' -ErrorAction SilentlyContinue | Select-Object -First 1; "
                f"if (-not $dvd) {{ Add-VMDvdDrive -VMName '{_q(name)}' -Path '{safe_iso}' }} "
                f"else {{ Set-VMDvdDrive -VMName '{_q(name)}' -Path '{safe_iso}' }}"
            )
            await self._run_ps(ps)
            return {"status": "success", "message": f"ISO attached to {name}: {norm}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def detach_iso(self, name: str) -> dict[str, Any]:
        """Detach any ISO from a VM's DVD drive."""
        try:
            await self._run_ps(f"Set-VMDvdDrive -VMName '{_q(name)}' -Path $null")
            return {"status": "success", "message": f"ISO detached from {name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # -- Console (VMConnect) + Enhanced Session Mode --

    async def get_enhanced_session(self) -> dict[str, Any]:
        """Get host Enhanced Session Mode setting (USB/clipboard/resolution)."""
        try:
            stdout = await self._run_ps("Get-VMHost | Select-Object EnableEnhancedSessionMode | ConvertTo-Json")
            data = json.loads(stdout) if stdout else {}
            if isinstance(data, list):
                data = data[0] if data else {}
            return {"status": "success", "enabled": bool(data.get("EnableEnhancedSessionMode", False))}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def set_enhanced_session(self, enabled: bool = True) -> dict[str, Any]:
        """Enable/disable host Enhanced Session Mode."""
        try:
            flag = "$true" if enabled else "$false"
            await self._run_ps(f"Set-VMHost -EnableEnhancedSessionMode {flag}")
            return {"status": "success", "enabled": enabled}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def connect_command(self, name: str, server: str = "localhost") -> dict[str, Any]:
        """Return the VMConnect command for a VM (VMConnect.exe Server VM [/edit]).

        The web backend best-effort launches it server-side too; clients that
        run remotely should run the returned command locally.
        """
        safe_server = _q(server)
        safe_name = _q(name)
        return {
            "status": "success",
            "vm_name": name,
            "server": server,
            "command": f"vmconnect.exe {server} {name}",
            "edit_command": f"VMConnect.exe {server} {name} /edit",
            "ps_launch": (f"Start-Process vmconnect.exe -ArgumentList '{safe_server}','{safe_name}'"),
        }

    async def launch_console(self, name: str, server: str = "localhost") -> dict[str, Any]:
        """Best-effort launch VMConnect on the host running this service."""
        if sys.platform != "win32":
            return self.connect_command(name, server)
        try:
            subprocess.Popen(
                ["vmconnect.exe", server, name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            result = self.connect_command(name, server)
            result["launched"] = True
            return result
        except Exception as e:
            result = self.connect_command(name, server)
            result["launched"] = False
            result["error"] = str(e)
            return result

    async def _run_ps(self, command: str) -> str:
        """Run a PowerShell command."""
        # Use pwsh if available, fallback to powershell
        shell = "pwsh"
        try:
            process = await asyncio.create_subprocess_exec(
                shell,
                "-Command",
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            shell = "powershell"
            process = await asyncio.create_subprocess_exec(
                shell,
                "-Command",
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            raise RuntimeError(f"PowerShell error: {error_msg}")

        return stdout.decode().strip()

    def _map_state(self, ps_state: str) -> str:
        """Map Hyper-V state string to common VM state."""
        mapping = {
            "Running": "running",
            "Off": "poweroff",
            "Paused": "paused",
            "Saved": "saved",
            "Starting": "starting",
            "Stopping": "stopping",
        }
        return mapping.get(ps_state, ps_state.lower())


# Singleton instance
hyperv_manager = HyperVManager()
