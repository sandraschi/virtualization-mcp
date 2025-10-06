"""
System Settings Manager for VMs.

This module provides functionality to manage system-level settings for virtual machines.
"""
import logging
import os
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, HTTPException, status

from ...plugins.base import BasePlugin
from ...plugins import register_plugin

logger = logging.getLogger(__name__)

class ChipsetType(str, Enum):
    """Supported chipset types with compatibility notes:
    - ICH9: Modern chipset with better performance (default)
    - PIIX3: Legacy chipset for older OSes
    """
    ICH9 = "ICH9"  # Default for modern OSes
    PIIX3 = "PIIX3"  # Legacy

class FirmwareType(str, Enum):
    """Supported firmware types with architecture notes:
    - BIOS: Legacy BIOS (default for compatibility)
    - EFI: UEFI firmware (recommended for modern OSes)
    - EFI32/EFI64: Architecture-specific UEFI
    - EFIDUAL: Dual-architecture UEFI (32/64-bit)
    """
    EFI = "EFI"  # Default UEFI (auto-detects architecture)
    BIOS = "BIOS"  # Legacy BIOS
    EFI32 = "EFI32"  # 32-bit UEFI
    EFI64 = "EFI64"  # 64-bit UEFI
    EFIDUAL = "EFIDUAL"  # Dual-architecture UEFI

class CPUProfile(str, Enum):
    """CPU profile presets for different use cases."""
    DESKTOP = "desktop"  # Balanced performance for general use
    SERVER = "server"    # Optimized for server workloads
    HIGH_PERF = "high_perf"  # Maximum performance
    COMPATIBILITY = "compat"  # Maximum compatibility
    CUSTOM = "custom"  # Manual configuration

class RTCUseUTC(str, Enum):
    """RTC time standard settings."""
    UTC = "UTC"  # Use UTC (recommended for Linux guests)
    LOCAL = "local"  # Use host local time (Windows default)

class SystemSettings(BaseModel):
    """System settings for a VM with optimized defaults.
    
    Key settings:
    - memory_size_mb: Total RAM in MB (default: 4GB)
    - cpu_count: Number of vCPUs (default: 2)
    - cpu_profile: Performance profile (default: DESKTOP)
    - firmware: UEFI/BIOS (default: EFI for modern OSes)
    - virtualization: Hardware acceleration settings
    - boot: Boot configuration
    - time: Time and timezone settings
    """
    # Memory and CPU
    memory_size_mb: int = Field(
        8192,  # 8GB default for Windows 11
        ge=4096,  # Windows 11 minimum is 4GB
        le=262144,  # 256GB max
        description="Memory in MB (Windows 11 requires min 4GB, 8GB+ recommended)"
    )
    cpu_count: int = Field(
        4,  # 4 vCPUs default for better performance
        ge=2,  # Windows 11 requires at least 2 cores
        le=os.cpu_count() or 64,
        description="Number of virtual CPUs (Windows 11 requires min 2 cores, 4+ recommended)"
    )
    cpu_profile: CPUProfile = CPUProfile.DESKTOP
    cpu_hotplug: bool = True
    
    # Hardware
    chipset: ChipsetType = ChipsetType.ICH9
    firmware: FirmwareType = FirmwareType.EFI
    
    # Virtualization features
    acpi: bool = True
    io_apic: bool = True
    pae: bool = True  # Required for >4GB RAM on 32-bit guests
    nested_paging: bool = True
    vtx_vpid: bool = True  # VPID for better performance
    vtx_ux: bool = False  # Unrestricted guest (Intel VT-x only)
    
    # Boot configuration
    boot_order: List[str] = Field(
        ["disk", "dvd", "net"],
        description="Boot order (disk, dvd, net, none, floppy)"
    )
    efi_nvram: Optional[str] = None  # Path to NVRAM file for EFI
    secure_boot: bool = True  # Enable UEFI secure boot
    
    # Time settings
    rtc_use_utc: RTCUseUTC = RTCUseUTC.UTC
    time_offset: timedelta = Field(
        timedelta(),
        description="Time offset from host (positive or negative)"
    )
    time_sync: str = Field(
        "host",
        description="Time sync mode: 'host', 'guest', or 'none'"
    )
    
    # Advanced settings
    properties: Dict[str, Any] = Field(
        default_factory=lambda: {
            "chipset": {
                "firmware_architecture": "x86_64",  # or "i386"
                "pointing_device": "usb-tablet",  # or "ps2-mouse", "usb-mouse"
                "keyboard_controller": "ps2",  # or "usb"
            },
            "cpu": {
                "execution_cap": 100,  # 100% of host CPU
                "hw_virt": True,  # Hardware virtualization
                "nested_hw_virt": False,  # Nested virtualization
            },
            "debug": {
                "gdb_enabled": False,
                "gdb_port": 1234,
            }
        }
    )

@register_plugin("system_settings")
class SystemSettingsManager(BasePlugin):
    """Manages system-level settings for virtual machines."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the System Settings Manager."""
        super().__init__(config)
        self.router = APIRouter(prefix="/system", tags=["system"])
        self.setup_routes()
    
    def setup_routes(self):
        """Set up API routes for system settings."""
        self.router.add_api_route(
            "/{vm_name}",
            self.get_system_settings,
            methods=["GET"],
            response_model=SystemSettings
        )
        self.router.add_api_route(
            "/{vm_name}",
            self.update_system_settings,
            methods=["PUT"],
            response_model=SystemSettings
        )
        self.router.add_api_route(
            "/{vm_name}/boot-order",
            self.get_boot_order,
            methods=["GET"],
            response_model=List[str]
        )
        self.router.add_api_route(
            "/{vm_name}/boot-order",
            self.set_boot_order,
            methods=["PUT"],
            response_model=List[str]
        )
    
    async def get_system_settings(self, vm_name: str) -> SystemSettings:
        """Get system settings for a VM."""
        # Implementation would query the actual VM's system settings
        return SystemSettings()
    
    async def update_system_settings(
        self,
        vm_name: str,
        settings: SystemSettings
    ) -> SystemSettings:
        """Update system settings for a VM."""
        # Implementation would update the actual VM's system settings
        return settings
    
    async def get_boot_order(self, vm_name: str) -> List[str]:
        """Get the boot order for a VM."""
        # Implementation would query the actual VM's boot order
        return ["disk", "dvd", "net", "none"]
    
    async def set_boot_order(
        self,
        vm_name: str,
        boot_order: List[str]
    ) -> List[str]:
        """Set the boot order for a VM."""
        # Implementation would update the actual VM's boot order
        return boot_order
