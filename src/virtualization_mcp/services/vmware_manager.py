"""
VMware Workstation Pro manager for virtualization-mcp.

Single source of truth for VMware ``vmrun.exe`` operations, mirroring
``services/hyperv_manager.py``. Phase 2 covers suspend/pause/reset,
snapshots, clone, and guest IP in addition to phase 1 probe + list/get/start/stop.

VMware Workstation Pro is free for all use since Broadcom Nov 2024, and it
is the only Windows hypervisor where macOS guests are practical
(community Unlocker + smc.version="0" + darwin guestOS). macOS guests are
Apple-EULA-grey and Unlocker is unofficial - this manager only drives
vmrun, it never downloads Unlocker or macOS images.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _default_vmrun_candidates() -> list[Path]:
    candidates: list[Path] = []
    env = os.environ.get("VMWARE_VMRUN_PATH")
    if env:
        candidates.append(Path(env))
    candidates += [
        Path(r"C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"),
        Path(r"C:\Program Files\VMware\VMware Workstation\vmrun.exe"),
        Path("/usr/bin/vmrun"),
        Path("/usr/local/bin/vmrun"),
    ]
    which = shutil.which("vmrun")
    if which:
        candidates.append(Path(which))
    return candidates


def find_vmrun(vmrun_path: str | Path | None = None) -> Path | None:
    """Resolve vmrun.exe, explicit path first then well-known locations."""
    if vmrun_path:
        p = Path(vmrun_path)
        if p.exists():
            return p.resolve()
        logger.warning("Specified vmrun path does not exist: %s", vmrun_path)
    for cand in _default_vmrun_candidates():
        try:
            if cand.exists():
                return cand.resolve()
        except OSError:
            continue
    return None


def default_inventory_dir() -> Path:
    env = os.environ.get("VMWARE_INVENTORY_DIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / "Documents" / "Virtual Machines"


class VmwareManager:
    """Manages VMware Workstation Pro VMs via ``vmrun``."""

    def __init__(self, vmrun_path: str | Path | None = None) -> None:
        self.vmrun_path: Path | None = find_vmrun(vmrun_path)
        self._available: bool | None = None

    def is_available(self) -> bool:
        """Sync probe: vmrun exists and answers ``-T ws list``."""
        if self._available is not None:
            return self._available
        if self.vmrun_path is None:
            self._available = False
            return False
        try:
            import subprocess

            out = subprocess.run(
                [str(self.vmrun_path), "-T", "ws", "list"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            self._available = out.returncode == 0 and "Total running VMs" in (out.stdout or "")
        except Exception as e:
            logger.warning("VMware vmrun probe failed: %s", e)
            self._available = False
        return self._available

    async def _run_vmrun(self, *args: str, timeout: int = 60) -> str:
        if self.vmrun_path is None:
            raise RuntimeError(
                "vmrun not found. Install VMware Workstation Pro (free) "
                "or set VMWARE_VMRUN_PATH."
            )
        proc = await asyncio.create_subprocess_exec(
            str(self.vmrun_path),
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            proc.kill()
            raise RuntimeError(f"vmrun timed out after {timeout}s: {' '.join(args)}") from None
        if proc.returncode != 0:
            err = (stderr or b"").decode(errors="replace").strip()
            raise RuntimeError(f"vmrun {' '.join(args)} failed: {err or proc.returncode}")
        return (stdout or b"").decode(errors="replace")

    @staticmethod
    def parse_list_output(stdout: str) -> list[str]:
        """Parse ``vmrun list`` into .vmx paths (first line is count header)."""
        lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
        if not lines or not lines[0].lower().startswith("total running vms"):
            return []
        return [ln for ln in lines[1:] if ln.lower().endswith(".vmx")]

    @staticmethod
    def parse_vmx(path: str | Path) -> dict[str, str]:
        """Parse a .vmx file into a flat dict (quoted values unquoted)."""
        result: dict[str, str] = {}
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return result
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip().strip('"')
            value = value.strip().strip('"')
            result[key] = value
        return result

    def scan_inventory(self) -> list[dict[str, Any]]:
        """Scan the inventory dir for .vmx files (registered or not)."""
        base = default_inventory_dir()
        if not base.is_dir():
            return []
        found: list[dict[str, Any]] = []
        for vmx in sorted(base.rglob("*.vmx")):
            meta = self.parse_vmx(vmx)
            found.append(
                {
                    "name": meta.get("displayName", vmx.parent.name),
                    "vmx_path": str(vmx),
                    "guest_os": meta.get("guestOS", "unknown"),
                    "memory_mb": int(meta.get("memsize", "0") or 0),
                    "cpus": int(meta.get("numvcpus", "0") or 0),
                    "provider": "vmware",
                }
            )
        return found

    async def list_vms(self) -> list[dict[str, Any]]:
        """List running VMs via vmrun, enriched with .vmx metadata."""
        stdout = await self._run_vmrun("-T", "ws", "list")
        running = set(self.parse_list_output(stdout))
        inventory = {entry["vmx_path"]: entry for entry in self.scan_inventory()}
        vms: list[dict[str, Any]] = []
        for vmx_path in sorted(running):
            meta = inventory.get(vmx_path) or (
                {"name": Path(vmx_path).parent.name, "guest_os": "unknown", "provider": "vmware"}
            )
            vms.append({**meta, "vmx_path": vmx_path, "state": "running"})
        for vmx_path, meta in sorted(inventory.items()):
            if vmx_path not in running:
                vms.append({**meta, "state": "stopped"})
        return vms

    async def get_vm(self, vmx_path: str) -> dict[str, Any] | None:
        """Get detail for one VM by .vmx path."""
        meta = self.parse_vmx(vmx_path)
        if not meta and not Path(vmx_path).exists():
            return None
        try:
            stdout = await self._run_vmrun("-T", "ws", "list")
            running = set(self.parse_list_output(stdout))
        except Exception:
            running = set()
        return {
            "name": meta.get("displayName", Path(vmx_path).parent.name),
            "vmx_path": vmx_path,
            "state": "running" if vmx_path in running else "stopped",
            "guest_os": meta.get("guestOS", "unknown"),
            "memory_mb": int(meta.get("memsize", "0") or 0),
            "cpus": int(meta.get("numvcpus", "0") or 0),
            "firmware": meta.get("firmware", "bios"),
            "provider": "vmware",
        }

    async def start_vm(self, vmx_path: str, gui: bool = False) -> dict[str, Any]:
        """Start a VM (nogui by default, gui=True opens Workstation UI)."""
        mode = "gui" if gui else "nogui"
        await self._run_vmrun("-T", "ws", "start", vmx_path, mode, timeout=120)
        return {"status": "success", "message": f"VMware VM started: {vmx_path}"}

    async def stop_vm(self, vmx_path: str, hard: bool = False) -> dict[str, Any]:
        """Stop a VM (soft guest shutdown default, hard = power off)."""
        mode = "hard" if hard else "soft"
        await self._run_vmrun("-T", "ws", "stop", vmx_path, mode, timeout=120)
        return {"status": "success", "message": f"VMware VM stopped: {vmx_path}"}

    async def reset_vm(self, vmx_path: str) -> dict[str, Any]:
        """Reset (power-cycle) a VM."""
        await self._run_vmrun("-T", "ws", "reset", vmx_path, timeout=120)
        return {"status": "success", "message": f"VMware VM reset: {vmx_path}"}

    async def suspend_vm(self, vmx_path: str) -> dict[str, Any]:
        """Suspend a VM to disk (fast resume, keeps RAM state)."""
        await self._run_vmrun("-T", "ws", "suspend", vmx_path, timeout=180)
        return {"status": "success", "message": f"VMware VM suspended: {vmx_path}"}

    async def pause_vm(self, vmx_path: str) -> dict[str, Any]:
        """Pause a VM (freeze CPU, RAM stays resident)."""
        await self._run_vmrun("-T", "ws", "pause", vmx_path)
        return {"status": "success", "message": f"VMware VM paused: {vmx_path}"}

    async def unpause_vm(self, vmx_path: str) -> dict[str, Any]:
        """Resume a paused VM."""
        await self._run_vmrun("-T", "ws", "unpause", vmx_path)
        return {"status": "success", "message": f"VMware VM unpaused: {vmx_path}"}

    # -- Snapshots --

    @staticmethod
    def parse_snapshot_list(stdout: str) -> list[str]:
        """Parse ``vmrun listSnapshots`` (one name per line, header-free)."""
        return [ln.strip() for ln in stdout.splitlines() if ln.strip()]

    async def list_snapshots(self, vmx_path: str) -> list[dict[str, Any]]:
        """List snapshots for a VM."""
        stdout = await self._run_vmrun("-T", "ws", "listSnapshots", vmx_path)
        return [{"name": n, "vmx_path": vmx_path} for n in self.parse_snapshot_list(stdout)]

    async def create_snapshot(self, vmx_path: str, name: str) -> dict[str, Any]:
        """Create a named snapshot."""
        if not name or not name.strip():
            raise ValueError("snapshot name is required")
        await self._run_vmrun("-T", "ws", "snapshot", vmx_path, name.strip(), timeout=180)
        return {"status": "success", "message": f"Snapshot '{name.strip()}' created for {vmx_path}"}

    async def revert_snapshot(self, vmx_path: str, name: str) -> dict[str, Any]:
        """Revert to a named snapshot."""
        await self._run_vmrun("-T", "ws", "revertToSnapshot", vmx_path, name, timeout=180)
        return {"status": "success", "message": f"VM {vmx_path} reverted to '{name}'"}

    async def delete_snapshot(self, vmx_path: str, name: str) -> dict[str, Any]:
        """Delete a named snapshot."""
        await self._run_vmrun("-T", "ws", "deleteSnapshot", vmx_path, name, timeout=180)
        return {"status": "success", "message": f"Snapshot '{name}' deleted from {vmx_path}"}

    # -- Clone + guest ops (slow-path, best-effort on Goliath) --

    async def clone_vm(self, src_vmx: str, dst_vmx: str, full: bool = True) -> dict[str, Any]:
        """Clone a VM (full clone default; linked when full=False)."""
        clone_type = "full" if full else "linked"
        await self._run_vmrun("-T", "ws", "clone", src_vmx, dst_vmx, clone_type, timeout=600)
        return {"status": "success", "message": f"Cloned {src_vmx} -> {dst_vmx} ({clone_type})"}

    async def get_guest_ip(self, vmx_path: str) -> dict[str, Any]:
        """Get the guest IP via VMware Tools (requires Tools in guest)."""
        stdout = await self._run_vmrun("-T", "ws", "getGuestIPAddress", vmx_path, timeout=60)
        ip = stdout.strip().splitlines()[-1].strip() if stdout.strip() else ""
        return {"status": "success", "vmx_path": vmx_path, "ip": ip}

    async def get_version(self) -> str | None:
        """Best-effort Workstation version string for host_info cards."""
        if self.vmrun_path is None:
            return None
        try:
            proc = await asyncio.create_subprocess_exec(
                str(self.vmrun_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
            first = (stdout or b"").decode(errors="replace").splitlines()
            return first[0].strip() if first else None
        except Exception:
            return None
