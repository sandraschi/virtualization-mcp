"""
Type definitions for VM services.

This module contains all the data models and type definitions used throughout
the VM services package.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, TypedDict


# VM State Enums
class VMState(str, Enum):
    """Virtual machine states."""

    POWERED_OFF = "PoweredOff"
    RUNNING = "Running"
    PAUSED = "Paused"
    SAVED = "Saved"
    ABORTED = "Aborted"
    STARTING = "Starting"
    STOPPING = "Stopping"
    UNKNOWN = "Unknown"


class VMPowerState(str, Enum):
    """VM power states for lifecycle operations."""

    ON = "on"
    OFF = "off"
    PAUSED = "paused"
    SAVED = "saved"


# Device Types
class DeviceType(str, Enum):
    """Types of devices that can be attached to VMs."""

    USB = "usb"
    STORAGE = "storage"
    NETWORK = "network"
    AUDIO = "audio"
    VIDEO = "video"
    SERIAL = "serial"
    PARALLEL = "parallel"


@dataclass
class USBDeviceFilter:
    """USB device filter for device passthrough."""

    name: str | None = None
    vendor_id: str | None = None
    product_id: str | None = None
    revision: str | None = None
    manufacturer: str | None = None
    product: str | None = None
    serial_number: str | None = None
    active: bool = True


# Storage Types
class StorageControllerType(str, Enum):
    """Storage controller types supported by VirtualBox."""

    IDE = "IDE"
    SATA = "SATA"
    SCSI = "SCSI"
    SAS = "SAS"
    USB = "USB"
    PCIE = "PCIe"
    VIRTIO_SCSI = "VirtioSCSI"
    PIIX3 = "PIIX3"
    PIIX4 = "PIIX4"
    ICH6 = "ICH6"
    AHCI = "AHCI"
    LSILOGIC = "LsiLogic"
    BUSLOGIC = "BusLogic"


class StorageBus(str, Enum):
    """Storage bus types."""

    IDE = "IDE"
    SATA = "SATA"
    SCSI = "SCSI"
    FLOPPY = "Floppy"
    SAS = "SAS"
    USB = "USB"
    PCIE = "PCIe"
    VIRTIO = "VirtIO"


@dataclass
class StorageMedium:
    """Storage medium definition."""

    path: str
    format_: str = "VDI"  # VDI, VMDK, VHD, etc.
    type_: str = "normal"  # normal, writethrough, immutable, etc.
    size_mb: int | None = None


# Network Types (re-export from network module)
class NetworkAttachmentType(str, Enum):
    """Network attachment types."""

    NAT = "nat"
    NAT_NETWORK = "natnetwork"
    BRIDGED = "bridged"
    HOST_ONLY = "hostonly"
    INTERNAL = "internal"
    GENERIC = "generic"
    NONE = "none"


# Operation Result Types
class VMOperationResult(TypedDict, total=False):
    """Standard response format for VM operations."""

    status: Literal["success", "error"]
    vm_name: str
    message: str
    error: str | None
    details: dict[str, Any]


class DeviceOperationResult(TypedDict, total=False):
    """Standard response format for device operations."""

    status: Literal["success", "error"]
    vm_name: str
    device_type: DeviceType
    message: str
    error: str | None
    device_info: dict[str, Any] | None


class StorageOperationResult(TypedDict, total=False):
    """Standard response format for storage operations."""

    status: Literal["success", "error"]
    vm_name: str
    controller_name: str | None
    message: str
    error: str | None
    storage_info: dict[str, Any] | None
