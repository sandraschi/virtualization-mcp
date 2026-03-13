"""
Hyper-V Manager service implementation for virtualization-mcp.
"""

import asyncio
import json
import logging
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
            await self._run_ps(
                "Get-VM -ErrorAction SilentlyContinue | Select-Object Name | ConvertTo-Json"
            )
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

    async def start_vm(self, name: str) -> dict[str, Any]:
        """Start a Hyper-V VM."""
        try:
            await self._run_ps(f"Start-VM -Name '{name}'")
            return {"status": "success", "message": f"Hyper-V VM {name} started"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def stop_vm(self, name: str, force: bool = False) -> dict[str, Any]:
        """Stop a Hyper-V VM."""
        try:
            flag = "-TurnOff" if force else "-Force"
            await self._run_ps(f"Stop-VM -Name '{name}' {flag}")
            return {"status": "success", "message": f"Hyper-V VM {name} stopped"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def pause_vm(self, name: str) -> dict[str, Any]:
        """Suspend/Pause a Hyper-V VM."""
        try:
            await self._run_ps(f"Suspend-VM -Name '{name}'")
            return {"status": "success", "message": f"Hyper-V VM {name} paused"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def resume_vm(self, name: str) -> dict[str, Any]:
        """Resume a Hyper-V VM."""
        try:
            await self._run_ps(f"Resume-VM -Name '{name}'")
            return {"status": "success", "message": f"Hyper-V VM {name} resumed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

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
