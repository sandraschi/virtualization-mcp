"""
System Information and Utility Tools

This module contains system-level tools for getting VirtualBox information
and performing basic system operations.
"""

import asyncio
import logging
import platform
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


async def get_system_info() -> dict[str, Any]:
    """
    Get system information including host OS, Python version, and VirtualBox version.

    Returns:
        Dictionary containing system information
    """
    try:
        # Get VirtualBox version
        vbox_version = await _get_vbox_version()

        # Get system information
        system_info = {
            "status": "success",
            "system": {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "virtualbox_version": vbox_version.get("version")
                if vbox_version.get("status") == "success"
                else "Unknown",
            },
        }

        return system_info

    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {"status": "error", "message": f"Failed to get system information: {str(e)}"}


async def get_vbox_info() -> dict[str, Any]:
    """
    Get detailed VirtualBox information.

    Returns:
        Dictionary containing VirtualBox information
    """
    try:
        # Get VirtualBox version
        vbox_version = await _get_vbox_version()
        if vbox_version["status"] != "success":
            return vbox_version

        # Get system properties
        system_props = await _get_system_properties()

        # Get host information
        host_info = await _get_host_info()

        # Get all registered VMs
        vms = await _list_vms()

        return {
            "status": "success",
            "virtualbox": {
                "version": vbox_version,
                "system_properties": system_props,
                "host_info": host_info,
                "vm_count": len(vms.get("vms", [])),
                "vms": vms.get("vms", []),
            },
        }

    except Exception as e:
        logger.error(f"Error getting VirtualBox info: {e}")
        return {"status": "error", "message": f"Failed to get VirtualBox information: {str(e)}"}


async def check_vbox_installation() -> dict[str, Any]:
    """
    Check if VirtualBox is installed and accessible.

    Returns:
        Dictionary with installation status and details
    """
    try:
        # Check if VBoxManage is in PATH
        cmd = ["VBoxManage", "--version"]

        result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return {
                "status": "error",
                "installed": False,
                "message": "VBoxManage not found. Is VirtualBox installed and in PATH?",
            }

        # Get version details
        version_output = result.stdout.strip()
        version_parts = version_output.split("r")

        return {
            "status": "success",
            "installed": True,
            "version": {
                "full": version_output,
                "version": version_parts[0],
                "revision": version_parts[1] if len(version_parts) > 1 else "",
                "vboxmanage_path": "VBoxManage",  # This is the command, not the path
            },
            "message": "VirtualBox is installed and accessible",
        }

    except Exception as e:
        logger.error(f"Error checking VirtualBox installation: {e}")
        return {
            "status": "error",
            "installed": False,
            "message": f"Error checking VirtualBox installation: {str(e)}",
        }


async def list_ostypes() -> dict[str, Any]:
    """
    List all supported guest OS types.

    Returns:
        Dictionary containing the list of supported OS types
    """
    try:
        cmd = ["VBoxManage", "list", "ostypes", "--long"]

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, check=True
        )

        ostypes = []
        current_os = {}

        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                if current_os:
                    ostypes.append(current_os)
                    current_os = {}
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                current_os[key] = value

        if current_os:  # Add the last OS type
            ostypes.append(current_os)

        return {"status": "success", "ostypes": ostypes}

    except subprocess.CalledProcessError as e:
        logger.error(f"Error listing OS types: {e}")
        return {"status": "error", "message": f"Failed to list OS types: {e.stderr}"}


async def list_extpacks() -> dict[str, Any]:
    """
    List all installed VirtualBox extension packs.

    Returns:
        Dictionary containing the list of installed extension packs
    """
    try:
        cmd = ["VBoxManage", "list", "extpacks", "--long"]

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, check=True
        )

        extpacks = []
        current_pack = {}

        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                if current_pack:
                    extpacks.append(current_pack)
                    current_pack = {}
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Handle special cases
                if key == "Pack no.":
                    if current_pack:  # Save previous pack if exists
                        extpacks.append(current_pack)
                    current_pack = {"id": value}
                else:
                    current_pack[key] = value

        if current_pack:  # Add the last extension pack
            extpacks.append(current_pack)

        return {"status": "success", "extpacks": extpacks}

    except subprocess.CalledProcessError as e:
        logger.error(f"Error listing extension packs: {e}")
        return {"status": "error", "message": f"Failed to list extension packs: {e.stderr}"}


async def get_host_info() -> dict[str, Any]:
    """
    Get information about the host system's resources.

    Returns:
        Dictionary containing host system information
    """
    try:
        # Get system properties which include host info
        system_props = await _get_system_properties()

        # Get additional host info
        host_info = await _get_host_info()

        # Get CPU info
        cpu_info = await _get_cpu_info()

        # Get memory info
        memory_info = await _get_memory_info()

        return {
            "status": "success",
            "host": {**host_info, **cpu_info, **memory_info, "system_properties": system_props},
        }

    except Exception as e:
        logger.error(f"Error getting host info: {e}")
        return {"status": "error", "message": f"Failed to get host information: {str(e)}"}


# Public functions


def get_vbox_version() -> dict[str, Any]:
    """
    Get VirtualBox version information.

    Returns:
        Dictionary containing VirtualBox version information
    """
    return asyncio.run(_get_vbox_version())


# Helper functions


async def _get_vbox_version() -> dict[str, Any]:
    """Get VirtualBox version information."""
    try:
        cmd = ["VBoxManage", "--version"]

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, check=True
        )

        version_output = result.stdout.strip()
        version_parts = version_output.split("r")

        return {
            "status": "success",
            "version": {
                "full": version_output,
                "version": version_parts[0],
                "revision": version_parts[1] if len(version_parts) > 1 else "",
            },
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting VirtualBox version: {e}")
        return {"status": "error", "message": f"Failed to get VirtualBox version: {e.stderr}"}


async def _get_system_properties() -> dict[str, Any]:
    """Get VirtualBox system properties."""
    try:
        cmd = ["VBoxManage", "list", "systemproperties"]

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, check=True
        )

        props = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                props[key.strip()] = value.strip()

        return props

    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting system properties: {e}")
        return {"error": f"Failed to get system properties: {e.stderr}"}


async def _get_host_info() -> dict[str, Any]:
    """Get host information."""
    try:
        cmd = ["VBoxManage", "list", "hostinfo"]

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, check=True
        )

        info = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                info[key.strip()] = value.strip()

        return info

    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting host info: {e}")
        return {"error": f"Failed to get host info: {e.stderr}"}


async def _list_vms() -> dict[str, Any]:
    """List all registered VMs."""
    try:
        from ..vm.vm_tools import list_vms

        return await list_vms()
    except Exception as e:
        logger.error(f"Error listing VMs: {e}")
        return {"vms": [], "error": f"Failed to list VMs: {str(e)}"}


async def _get_cpu_info() -> dict[str, Any]:
    """Get CPU information."""
    try:
        if platform.system() == "Windows":
            return _get_windows_cpu_info()
        elif platform.system() == "Linux":
            return await _get_linux_cpu_info()
        elif platform.system() == "Darwin":
            return await _get_macos_cpu_info()
        else:
            return {"cpu_info": "Unsupported platform"}
    except Exception as e:
        logger.error(f"Error getting CPU info: {e}")
        return {"cpu_info": f"Error: {str(e)}"}


def _get_windows_cpu_info() -> dict[str, Any]:
    """Get CPU information on Windows."""
    import wmi

    try:
        c = wmi.WMI()
        cpu = c.Win32_Processor()[0]

        return {
            "cpu_info": {
                "name": cpu.Name.strip(),
                "cores": cpu.NumberOfCores,
                "logical_processors": cpu.NumberOfLogicalProcessors,
                "max_clock_speed": f"{cpu.MaxClockSpeed} MHz",
                "architecture": _get_architecture(cpu.AddressWidth),
                "virtualization_enabled": cpu.VirtualizationFirmwareEnabled
                if hasattr(cpu, "VirtualizationFirmwareEnabled")
                else None,
            }
        }
    except Exception as e:
        logger.error(f"Error getting Windows CPU info: {e}")
        return {"cpu_info": f"Error: {str(e)}"}


async def _get_linux_cpu_info() -> dict[str, Any]:
    """Get CPU information on Linux."""
    try:
        # Get CPU info from /proc/cpuinfo
        with open("/proc/cpuinfo") as f:
            cpuinfo = f.read()

        info = {}
        for line in cpuinfo.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                info[key.strip()] = value.strip()

        # Get CPU flags to check for virtualization support
        flags = info.get("flags", "").split()

        return {
            "cpu_info": {
                "model_name": info.get("model name", "Unknown"),
                "vendor_id": info.get("vendor_id", "Unknown"),
                "cpu_cores": info.get("cpu cores", "1"),
                "siblings": info.get("siblings", "1"),
                "virtualization_support": "vmx" in flags or "svm" in flags,
                "flags": flags,
            }
        }
    except Exception as e:
        logger.error(f"Error getting Linux CPU info: {e}")
        return {"cpu_info": f"Error: {str(e)}"}


async def _get_macos_cpu_info() -> dict[str, Any]:
    """Get CPU information on macOS."""
    try:
        # Get CPU brand string
        cmd = ["sysctl", "-n", "machdep.cpu.brand_string"]
        result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)
        brand = result.stdout.strip()

        # Get CPU features
        cmd = ["sysctl", "-a", "machdep.cpu.features"]
        result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)
        features = result.stdout.split(":", 1)[1].strip().lower().split()

        # Get CPU core count
        cmd = ["sysctl", "-n", "hw.ncpu"]
        result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)
        cores = result.stdout.strip()

        return {
            "cpu_info": {
                "brand": brand,
                "cores": cores,
                "virtualization_support": "vmx" in features,
                "features": features,
            }
        }
    except Exception as e:
        logger.error(f"Error getting macOS CPU info: {e}")
        return {"cpu_info": f"Error: {str(e)}"}


async def _get_memory_info() -> dict[str, Any]:
    """Get memory information."""
    try:
        if platform.system() == "Windows":
            return _get_windows_memory_info()
        elif platform.system() in ["Linux", "Darwin"]:
            return await _get_unix_memory_info()
        else:
            return {"memory_info": "Unsupported platform"}
    except Exception as e:
        logger.error(f"Error getting memory info: {e}")
        return {"memory_info": f"Error: {str(e)}"}


def _get_windows_memory_info() -> dict[str, Any]:
    """Get memory information on Windows."""
    import ctypes

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    memoryStatus = MEMORYSTATUSEX()
    memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memoryStatus))

    total_phys = memoryStatus.ullTotalPhys / (1024**3)  # Convert to GB
    avail_phys = memoryStatus.ullAvailPhys / (1024**3)  # Convert to GB

    return {
        "memory_info": {
            "total_physical_gb": round(total_phys, 2),
            "available_physical_gb": round(avail_phys, 2),
            "used_physical_gb": round(total_phys - avail_phys, 2),
            "memory_load_percent": memoryStatus.dwMemoryLoad,
        }
    }


async def _get_unix_memory_info() -> dict[str, Any]:
    """Get memory information on Linux/macOS."""
    try:
        if platform.system() == "Linux":
            with open("/proc/meminfo") as f:
                meminfo = {}
                for line in f:
                    key, value = line.split(":")
                    meminfo[key.strip()] = value.strip()

            total = int(meminfo["MemTotal"].split()[0]) / 1024  # Convert to MB
            free = int(meminfo["MemFree"].split()[0]) / 1024
            available = int(meminfo["MemAvailable"].split()[0]) / 1024

            return {
                "memory_info": {
                    "total_mb": round(total, 2),
                    "free_mb": round(free, 2),
                    "available_mb": round(available, 2),
                    "used_mb": round(total - available, 2),
                    "used_percent": round(((total - available) / total) * 100, 2),
                }
            }
        else:  # macOS
            cmd = ["vm_stat"]
            result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)

            # Parse vm_stat output
            vm_stats = {}
            for line in result.stdout.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    vm_stats[key.strip()] = int(value.strip(" ."))

            # Get page size
            cmd = ["pagesize"]
            result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)
            page_size = int(result.stdout.strip())

            # Calculate memory usage
            free_memory = vm_stats.get("Pages free", 0) * page_size / (1024**2)  # MB
            active_memory = vm_stats.get("Pages active", 0) * page_size / (1024**2)
            inactive_memory = vm_stats.get("Pages inactive", 0) * page_size / (1024**2)
            wired_memory = vm_stats.get("Pages wired down", 0) * page_size / (1024**2)

            used_memory = active_memory + inactive_memory + wired_memory
            total_memory = free_memory + used_memory

            return {
                "memory_info": {
                    "total_mb": round(total_memory, 2),
                    "free_mb": round(free_memory, 2),
                    "used_mb": round(used_memory, 2),
                    "active_mb": round(active_memory, 2),
                    "inactive_mb": round(inactive_memory, 2),
                    "wired_mb": round(wired_memory, 2),
                }
            }

    except Exception as e:
        logger.error(f"Error getting Unix memory info: {e}")
        return {"memory_info": f"Error: {str(e)}"}


def _get_architecture(bits: int) -> str:
    """Convert address width to architecture name."""
    return {32: "x86", 64: "x86_64", 128: "aarch64"}.get(bits, f"Unknown ({bits}-bit)")
