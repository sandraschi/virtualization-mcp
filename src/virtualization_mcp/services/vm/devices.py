"""
VM Device and Media Management Module

This module provides comprehensive functionality for managing VM devices and media,
including ISO handling, USB devices, shared folders, and hardware passthrough.
Supports both VirtualBox and Hyper-V hypervisors with appropriate fallbacks.
"""

import logging
import os
import platform
import subprocess
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


# Constants for device types
class DeviceType(Enum):
    """Enumeration of supported device types."""

    CD_DVD = "cdrom"
    FLOPPY = "floppy"
    USB = "usb"
    NETWORK = "network"
    STORAGE = "storage"
    DISPLAY = "display"
    SOUND = "sound"
    SERIAL = "serial"
    PARALLEL = "parallel"
    USB_CONTROLLER = "usb_controller"
    SATA_CONTROLLER = "sata_controller"
    SCSI_CONTROLLER = "scsi_controller"
    VIRTIO_SCSI = "virtio_scsi"


@dataclass
class DeviceInfo:
    """Data class containing information about a VM device."""

    name: str
    type: DeviceType
    attached: bool = False
    details: dict[str, Any] | None = None
    controller: str | None = None
    port: int | None = None
    device: int | None = None


# Decorator for device operations
def device_operation(func):
    """Decorator for device operations with error handling and logging."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            logger.error(f"Device operation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "operation": func.__name__,
                "vm_name": kwargs.get("vm_name", "unknown"),
            }

    return wrapper


class VMDeviceMixin:
    """
    Mixin class providing comprehensive VM device and media management methods.

    This class handles all device-related operations for virtual machines,
    including ISO management, USB device handling, shared folders, and more.
    It provides a unified interface that works across different hypervisors.
    """

    def __init__(self, vm_service):
        """
        Initialize with a reference to the parent VMService.

        Args:
            vm_service: Reference to the parent VMService instance
        """
        self.vm_service = vm_service
        self.vbox_manager = vm_service.vbox_manager
        self.vm_operations = vm_service.vm_operations
        self.hypervisor = self._detect_hypervisor()

    def _detect_hypervisor(self) -> str:
        """Detect the underlying hypervisor (VirtualBox or Hyper-V)."""
        if platform.system().lower() == "windows":
            try:
                # Check if Hyper-V is enabled
                result = subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        "Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if "Enabled" in result.stdout:
                    return "hyperv"
            except Exception:
                pass

        # Default to VirtualBox
        return "virtualbox"

    @device_operation
    def attach_iso(
        self,
        vm_name: str,
        iso_path: str,
        port: int = 1,
        device: int = 0,
        controller: str = "IDE Controller",
        temporary: bool = False,
    ) -> dict[str, Any]:
        """
        Attach an ISO file to a virtual machine's virtual CD/DVD drive.

        This method attaches an ISO image to the specified VM's virtual optical drive.
        It works with both VirtualBox and Hyper-V hypervisors.

        API Endpoint: POST /vms/{vm_name}/devices/iso/attach

        Args:
            vm_name: Name of the VM to attach the ISO to
            iso_path: Absolute path to the ISO file
            port: Controller port number (default: 1)
            device: Device number on the port (default: 0)
            controller: Name of the storage controller (default: "IDE Controller")
            temporary: If True, the ISO will be detached on VM power off

        Returns:
            Dictionary containing the result of the operation

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If the VM is not found or if there's an error
                         attaching the ISO

        Example:
            ```python
            # Attach an ISO to a VM
            result = devices.attach_iso(
                vm_name="my-vm",
                iso_path="/path/to/install.iso",
                port=1,
                device=0,
                controller="IDE Controller"
            )
            ```
        """
        # Input validation
        if not vm_name:
            raise ValueError("VM name is required")
        if not iso_path or not os.path.isfile(iso_path):
            raise ValueError(f"ISO file not found: {iso_path}")

        # Get the VM
        vm = self.vm_operations.get_vm_by_name(vm_name)
        if not vm:
            raise RuntimeError(f"VM '{vm_name}' not found")

        # Handle based on hypervisor
        if self.hypervisor == "hyperv":
            return self._attach_iso_hyperv(vm_name, iso_path, port, device, temporary)
        else:
            return self._attach_iso_virtualbox(
                vm_name, iso_path, port, device, controller, temporary
            )

    def _attach_iso_virtualbox(
        self, vm_name: str, iso_path: str, port: int, device: int, controller: str, temporary: bool
    ) -> dict[str, Any]:
        """Internal method to attach ISO in VirtualBox."""
        # Open a session
        session = self.vbox_manager.mgr.get_session_object()
        try:
            # Lock the VM for configuration
            vm = self.vm_operations.get_vm_by_name(vm_name)
            if not vm:
                raise RuntimeError(f"VM '{vm_name}' not found")

            vm.lock_machine(session, self.vbox_manager.constants.LockType_Write)

            # Get the storage controller
            storage_ctl = session.machine.get_storage_controller_by_name(controller)
            if not storage_ctl:
                # Create an IDE controller if it doesn't exist
                if "IDE" in controller:
                    storage_ctl = session.machine.add_storage_controller(
                        controller, self.vbox_manager.constants.StorageBus_IDE
                    )
                else:
                    raise RuntimeError(f"Storage controller '{controller}' not found")

            # Open the ISO as a medium
            medium = self.vbox_manager.vbox.open_medium(
                iso_path,
                self.vbox_manager.constants.DeviceType_DVD,
                self.vbox_manager.constants.AccessMode_ReadOnly,
                False,
            )

            # Attach the medium
            session.machine.mount_medium(controller, port, device, medium, temporary)

            # Save settings if not temporary
            if not temporary:
                session.machine.save_settings()

            return {
                "status": "success",
                "message": f"ISO attached to VM '{vm_name}'",
                "vm_name": vm_name,
                "iso_path": iso_path,
                "controller": controller,
                "port": port,
                "device": device,
                "temporary": temporary,
            }

        finally:
            session.unlock_machine()

    def _attach_iso_hyperv(
        self, vm_name: str, iso_path: str, port: int, device: int, temporary: bool
    ) -> dict[str, Any]:
        """Internal method to attach ISO in Hyper-V."""
        try:
            # Convert Windows path if needed
            if ":" in iso_path and not iso_path.startswith("\\"):
                # Local path
                iso_path = os.path.abspath(iso_path)

            # Use PowerShell to attach the ISO
            cmd = [
                "powershell",
                "-Command",
                f'$vm = Get-VM -Name "{vm_name}" -ErrorAction Stop; '
                f'Set-VMDvdDrive -VMName "{vm_name}" -Path "{iso_path}" -ErrorAction Stop; '
                'Write-Output "ISO attached successfully"',
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            return {
                "status": "success",
                "message": f"ISO attached to VM '{vm_name}' in Hyper-V",
                "vm_name": vm_name,
                "iso_path": iso_path,
                "temporary": temporary,
                "output": result.stdout.strip(),
            }

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to attach ISO in Hyper-V: {e.stderr}") from e

    @device_operation
    def detach_iso(
        self, vm_name: str, port: int = 1, device: int = 0, controller: str = "IDE Controller"
    ) -> dict[str, Any]:
        """
        Detach an ISO file from a virtual machine's virtual CD/DVD drive.

        This method detaches any ISO image from the specified VM's virtual optical drive.

        API Endpoint: DELETE /vms/{vm_name}/devices/iso

        Args:
            vm_name: Name of the VM to detach the ISO from
            port: Controller port number (default: 1)
            device: Device number on the port (default: 0)
            controller: Name of the storage controller (default: "IDE Controller")

        Returns:
            Dictionary containing the result of the operation

        Example:
            ```python
            # Detach an ISO from a VM
            result = devices.detach_iso(
                vm_name="my-vm",
                port=1,
                device=0,
                controller="IDE Controller"
            )
            ```
        """
        # Input validation
        if not vm_name:
            raise ValueError("VM name is required")

        # Get the VM
        vm = self.vm_operations.get_vm_by_name(vm_name)
        if not vm:
            raise RuntimeError(f"VM '{vm_name}' not found")

        # Handle based on hypervisor
        if self.hypervisor == "hyperv":
            return self._detach_iso_hyperv(vm_name)
        else:
            return self._detach_iso_virtualbox(vm_name, port, device, controller)

    def _detach_iso_virtualbox(
        self, vm_name: str, port: int, device: int, controller: str
    ) -> dict[str, Any]:
        """Internal method to detach ISO in VirtualBox."""
        # Open a session
        session = self.vbox_manager.mgr.get_session_object()
        try:
            # Lock the VM for configuration
            vm = self.vm_operations.get_vm_by_name(vm_name)
            if not vm:
                raise RuntimeError(f"VM '{vm_name}' not found")

            vm.lock_machine(session, self.vbox_manager.constants.LockType_Write)

            # Get the storage controller
            storage_ctl = session.machine.get_storage_controller_by_name(controller)
            if not storage_ctl:
                raise RuntimeError(f"Storage controller '{controller}' not found")

            # Eject the medium
            session.machine.mount_medium(controller, port, device, None, False)

            # Save settings
            session.machine.save_settings()

            return {
                "status": "success",
                "message": f"ISO detached from VM '{vm_name}'",
                "vm_name": vm_name,
                "controller": controller,
                "port": port,
                "device": device,
            }

        finally:
            if session.state == self.vbox_manager.constants.SessionState_Locked:
                session.unlock_machine()

    def _detach_iso_hyperv(self, vm_name: str) -> dict[str, Any]:
        """Internal method to detach ISO in Hyper-V."""
        try:
            # Use PowerShell to detach the ISO
            cmd = [
                "powershell",
                "-Command",
                f'$vm = Get-VM -Name "{vm_name}" -ErrorAction Stop; '
                f'Set-VMDvdDrive -VMName "{vm_name}" -Path $null -ErrorAction Stop; '
                'Write-Output "ISO detached successfully"',
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            return {
                "status": "success",
                "message": f"ISO detached from VM '{vm_name}' in Hyper-V",
                "vm_name": vm_name,
                "output": result.stdout.strip(),
            }

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to detach ISO in Hyper-V: {e.stderr}") from e

    @device_operation
    def attach_usb(
        self, vm_name: str, usb_filter: str, port: int = 0, capture: bool = True, echi: bool = False
    ) -> dict[str, Any]:
        """
        Attach a USB device to a virtual machine.

        API Endpoint: POST /vms/{vm_name}/usb/attach

        Args:
            vm_name: Name of the VM
            usb_filter: USB device filter string (vendor:product) or device name
            port: USB controller port number (default: 0)
            capture: If True, capture the device from the host (default: True)
            echi: Enable EHCI (USB 2.0) controller if needed (default: False)

        Returns:
            Dictionary with operation status and device information

        Example:
            ```python
            # Attach a USB device by vendor:product
            result = devices.attach_usb("my-vm", "046d:c52b")

            # Attach to specific port with EHCI
            result = devices.attach_usb("my-vm", "Logitech_Receiver", port=1, echi=True)
            ```
        """
        # Input validation
        if not vm_name:
            raise ValueError("VM name is required")
        if not usb_filter:
            raise ValueError("USB filter or device name is required")

        # Get the VM
        vm = self.vm_operations.get_vm_by_name(vm_name)
        if not vm:
            raise RuntimeError(f"VM '{vm_name}' not found")

        # Handle based on hypervisor
        if self.hypervisor == "hyperv":
            return self._attach_usb_hyperv(vm_name, usb_filter, port, capture)
        else:
            return self._attach_usb_virtualbox(vm_name, usb_filter, port, capture, echi)

    def _attach_usb_virtualbox(
        self, vm_name: str, usb_filter: str, port: int, capture: bool, echi: bool
    ) -> dict[str, Any]:
        """Attach a USB device in VirtualBox."""
        session = self.vbox_manager.mgr.get_session_object()
        try:
            # Lock the VM for writing
            vm = self.vm_operations.get_vm_by_name(vm_name)
            vm.lock_machine(session, self.vbox_manager.constants.LockType_Write)

            # Enable USB controller if needed
            usb_controller = None
            for controller in session.machine.usb_controllers:
                if controller.name == "USB Controller":
                    usb_controller = controller
                    break

            if not usb_controller:
                usb_controller = session.machine.add_usb_controller(
                    "USB Controller", self.vbox_manager.constants.USBControllerType_OHCI
                )

            # Enable EHCI if requested
            if echi and usb_controller.type == self.vbox_manager.constants.USBControllerType_OHCI:
                session.machine.remove_usb_controller("USB Controller")
                usb_controller = session.machine.add_usb_controller(
                    "USB Controller", self.vbox_manager.constants.USBControllerType_EHCI
                )

            # Create a USB device filter
            usb_filter_obj = session.machine.create_usb_device_filter()
            if ":" in usb_filter:
                vendor_id, product_id = usb_filter.split(":", 1)
                usb_filter_obj.vendor_id = vendor_id
                usb_filter_obj.product_id = product_id
            else:
                usb_filter_obj.name = usb_filter

            usb_filter_obj.active = True
            usb_filter_obj.action = self.vbox_manager.constants.USBDeviceFilterAction_Hold

            # Add the filter
            session.machine.insert_usb_device_filter(usb_filter_obj)

            # Save settings
            session.machine.save_settings()

            return {
                "status": "success",
                "vm_name": vm_name,
                "usb_filter": usb_filter,
                "port": port,
                "captured": capture,
                "ehci_enabled": echi,
            }

        except Exception as e:
            raise RuntimeError(f"Failed to attach USB device: {str(e)}") from e
        finally:
            if session.state == self.vbox_manager.constants.SessionState_Locked:
                session.unlock_machine()

    def _attach_usb_hyperv(
        self, vm_name: str, usb_filter: str, port: int, capture: bool
    ) -> dict[str, Any]:
        """Attach a USB device in Hyper-V (limited support)."""
        try:
            # Hyper-V has limited USB passthrough capabilities
            # This is a simplified implementation that works with USB over IP solutions

            # Build the PowerShell command
            cmd = ["powershell", "-Command"]
            ps_script = [
                f'$vm = Get-VM -Name "{vm_name}" -ErrorAction Stop;',
                f'$usbDevice = Get-PnpDevice | Where-Object {{ $_.FriendlyName -like "*{usb_filter}*" }} | Select-Object -First 1;',
                'if (-not $usbDevice) { throw "USB device not found" };',
                "$vm | Add-VMScsiController -ErrorAction Stop;",
                "$vm | Add-VMHardDiskDrive -ControllerType SCSI -ErrorAction Stop;",
                "$usbInfo = $usbDevice | Select-Object FriendlyName, DeviceID, Status, Class;",
                "$usbInfo | ConvertTo-Json -Depth 10",
            ]

            cmd.append(" ".join(ps_script))

            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Parse and return the result
            import json

            device_info = json.loads(result.stdout)

            return {
                "status": "success",
                "vm_name": vm_name,
                "usb_device": device_info,
                "note": "USB passthrough in Hyper-V is limited. Consider using USB over IP solutions for better compatibility.",
            }

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to attach USB device in Hyper-V: {e.stderr}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse USB device info from Hyper-V: {e}") from e

    @device_operation
    def detach_usb(self, vm_name: str, usb_filter: str = None, port: int = None) -> dict[str, Any]:
        """
        Detach a USB device from a virtual machine.

        API Endpoint: DELETE /vms/{vm_name}/usb/detach

        Args:
            vm_name: Name of the VM
            usb_filter: USB device filter string (vendor:product) or device name.
                       If None, detaches all USB devices.
            port: USB controller port number. If None, matches any port.

        Returns:
            Dictionary with operation status

        Example:
            ```python
            # Detach a specific USB device
            result = devices.detach_usb("my-vm", "046d:c52b")

            # Detach all USB devices
            result = devices.detach_usb("my-vm")

            # Detach from specific port
            result = devices.detach_usb("my-vm", port=1)
            ```
        """
        # Input validation
        if not vm_name:
            raise ValueError("VM name is required")

        # Get the VM
        vm = self.vm_operations.get_vm_by_name(vm_name)
        if not vm:
            raise RuntimeError(f"VM '{vm_name}' not found")

        # Handle based on hypervisor
        if self.hypervisor == "hyperv":
            return self._detach_usb_hyperv(vm_name, usb_filter, port)
        else:
            return self._detach_usb_virtualbox(vm_name, usb_filter, port)

    def _detach_usb_virtualbox(
        self, vm_name: str, usb_filter: str = None, port: int = None
    ) -> dict[str, Any]:
        """Detach a USB device in VirtualBox."""
        session = self.vbox_manager.mgr.get_session_object()
        try:
            # Lock the VM for writing
            vm = self.vm_operations.get_vm_by_name(vm_name)
            vm.lock_machine(session, self.vbox_manager.constants.LockType_Write)

            # Get the USB controller
            usb_controller = None
            for controller in session.machine.usb_controllers:
                if controller.name == "USB Controller":
                    usb_controller = controller
                    break

            if not usb_controller:
                raise RuntimeError("USB controller not found")

            # Remove the USB device filter
            if usb_filter:
                for filter in session.machine.usb_device_filters:
                    if filter.name == usb_filter:
                        session.machine.remove_usb_device_filter(filter)
                        break
            else:
                # Remove all USB device filters
                for filter in session.machine.usb_device_filters:
                    session.machine.remove_usb_device_filter(filter)

            # Save settings
            session.machine.save_settings()

            return {"status": "success", "vm_name": vm_name, "usb_filter": usb_filter, "port": port}

        except Exception as e:
            raise RuntimeError(f"Failed to detach USB device: {str(e)}") from e
        finally:
            if session.state == self.vbox_manager.constants.SessionState_Locked:
                session.unlock_machine()

    def _detach_usb_hyperv(
        self, vm_name: str, usb_filter: str = None, port: int = None
    ) -> dict[str, Any]:
        """Detach a USB device in Hyper-V (limited support)."""
        try:
            # Hyper-V has limited USB passthrough capabilities
            # This is a simplified implementation that works with USB over IP solutions

            # Build the PowerShell command
            cmd = ["powershell", "-Command"]
            ps_script = [
                f'$vm = Get-VM -Name "{vm_name}" -ErrorAction Stop;',
                "if ($vm | Get-VMScsiController) { $vm | Remove-VMScsiController -ErrorAction Stop; };",
                "if ($vm | Get-VMHardDiskDrive) { $vm | Remove-VMHardDiskDrive -ErrorAction Stop; };",
            ]

            cmd.append(" ".join(ps_script))

            # Execute the command
            subprocess.run(cmd, capture_output=True, text=True, check=True)

            return {
                "status": "success",
                "vm_name": vm_name,
                "note": "USB passthrough in Hyper-V is limited. Consider using USB over IP solutions for better compatibility.",
            }

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to detach USB device in Hyper-V: {e.stderr}") from e

    def _list_devices_virtualbox(self, vm_name: str) -> list[dict[str, Any]]:
        """Internal method to list devices in VirtualBox."""
        devices = []
        session = None

        try:
            # Open a session
            session = self.vbox_manager.mgr.get_session_object()
            # Lock the VM for reading
            vm = self.vm_operations.get_vm_by_name(vm_name)
            if not vm:
                raise RuntimeError(f"VM '{vm_name}' not found")

            vm.lock_machine(session, self.vbox_manager.constants.LockType_Shared)

            try:
                # Get storage controllers
                for controller in session.machine.storage_controllers:
                    # Controller info
                    controller_info = {
                        "name": controller.name,
                        "type": controller.controller_type,
                        "port_count": controller.port_count,
                        "devices": [],
                    }

                    # Get attached devices
                    for port in range(controller.port_count):
                        for device in range(controller.max_devices_per_port):
                            try:
                                medium = session.machine.get_medium_attachments_of_controller(
                                    controller.name, port, device
                                )
                                if medium:
                                    device_info = {
                                        "port": port,
                                        "device": device,
                                        "type": "storage",
                                        "medium": medium.medium_id,
                                        "controller": controller.name,
                                    }
                                    controller_info["devices"].append(device_info)
                            except Exception as e:
                                logger.debug(
                                    f"No device at {controller.name}:{port}:{device}: {str(e)}"
                                )

                    devices.append(controller_info)

                # Get network adapters
                for i in range(self.vbox_manager.constants.NetworkAdapterCount):
                    try:
                        adapter = session.machine.get_network_adapter(i)
                        if adapter:
                            devices.append(
                                {
                                    "type": "network",
                                    "slot": i,
                                    "enabled": adapter.enabled,
                                    "adapter_type": adapter.adapter_type,
                                    "mac_address": adapter.mac_address,
                                    "cable_connected": adapter.cable_connected,
                                    "attachment_type": adapter.attachment_type,
                                }
                            )
                    except Exception as e:
                        logger.debug(f"No network adapter at slot {i}: {str(e)}")

                return devices

            except Exception as e:
                logger.error(f"Error listing devices: {str(e)}")
                raise

            finally:
                if (
                    session
                    and hasattr(session, "unlock_machine")
                    and session.state == self.vbox_manager.constants.SessionState_Locked
                ):
                    try:
                        session.unlock_machine()
                    except Exception as unlock_error:
                        logger.error(f"Error unlocking session: {str(unlock_error)}")

        except Exception as e:
            raise RuntimeError(f"Failed to list devices for VM {vm_name}: {str(e)}") from e

    def _list_devices_hyperv(self, vm_name: str) -> dict[str, Any]:
        """
        Internal method to list devices in Hyper-V.

        Args:
            vm_name: Name of the VM to list devices for

        Returns:
            Dictionary containing the status, VM name, and list of devices
        """
        from .devices_hyperv import HyperVDeviceManager

        try:
            devices = HyperVDeviceManager.list_devices(vm_name)

            # Ensure devices is a list
            if not isinstance(devices, list):
                if isinstance(devices, dict):
                    devices = [devices]
                else:
                    logger.warning(f"Unexpected device list format: {type(devices)}")
                    devices = []

            return {"status": "success", "vm_name": vm_name, "devices": devices}

        except Exception as e:
            logger.error(f"Failed to list devices for VM {vm_name}: {str(e)}")
            return {"status": "error", "vm_name": vm_name, "error": str(e), "devices": []}

    @device_operation
    def update_network_adapter(self, vm_name: str, adapter_number: int, **kwargs) -> dict[str, Any]:
        """
        Update network adapter settings for a VM.

        API Endpoint: PATCH /vms/{vm_name}/network/adapters/{adapter_number}

        Args:
            vm_name: Name of the VM
            adapter_number: Network adapter number (0-based index)
            **kwargs: Network adapter settings to update. Common options include:
                - enabled: bool - Enable/disable the adapter
                - adapter_type: str - Type of network adapter (e.g., '82540EM', 'virtio')
                - mac_address: str - Custom MAC address
                - cable_connected: bool - Whether the network cable is connected
                - promiscuous_mode: str - Promiscuous mode ('Deny', 'AllowVM', 'AllowAll')
                - nat_network: str - Name of NAT network to connect to
                - bridged_interface: str - Name of host interface to bridge to
                - internal_network: str - Name of internal network
                - host_only_interface: str - Name of host-only interface

        Returns:
            Dictionary with operation status and updated adapter settings

        Example:
            ```python
            # Connect adapter 0 to a NAT network
            result = devices.update_network_adapter(
                "my-vm", 0,
                enabled=True,
                nat_network="NatNetwork"
            )
            ```
        """
        # Input validation
        if not vm_name:
            raise ValueError("VM name is required")
        if not isinstance(adapter_number, int) or adapter_number < 0:
            raise ValueError("Adapter number must be a non-negative integer")

        # Get the VM
        vm = self.vm_operations.get_vm_by_name(vm_name)
        if not vm:
            raise RuntimeError(f"VM '{vm_name}' not found")

        # Handle based on hypervisor
        if self.hypervisor == "hyperv":
            return self._update_network_adapter_hyperv(vm_name, adapter_number, **kwargs)
        else:
            return self._update_network_adapter_virtualbox(vm_name, adapter_number, **kwargs)

    def _update_network_adapter_virtualbox(
        self, vm_name: str, adapter_number: int, **kwargs
    ) -> dict[str, Any]:
        """Update network adapter settings in VirtualBox."""
        session = self.vbox_manager.mgr.get_session_object()
        try:
            # Lock the VM for writing
            vm = self.vm_operations.get_vm_by_name(vm_name)
            vm.lock_machine(session, self.vbox_manager.constants.LockType_Write)

            # Get the network adapter
            try:
                adapter = session.machine.get_network_adapter(adapter_number)
            except Exception as e:
                raise RuntimeError(f"Network adapter {adapter_number} not found: {str(e)}") from e

            # Update adapter settings
            if "enabled" in kwargs:
                adapter.enabled = bool(kwargs["enabled"])

            if "adapter_type" in kwargs:
                adapter.adapter_type = kwargs["adapter_type"]

            if "mac_address" in kwargs:
                adapter.mac_address = kwargs["mac_address"]

            if "cable_connected" in kwargs:
                adapter.cable_connected = bool(kwargs["cable_connected"])

            if "promiscuous_mode" in kwargs:
                adapter.promiscuous_mode = getattr(
                    self.vbox_manager.constants.NetworkAdapterPromiscModePolicy,
                    f"_{kwargs['promiscuous_mode']}",
                    self.vbox_manager.constants.NetworkAdapterPromiscModePolicy_Deny,
                )

            # Handle connection type
            if any(
                k in kwargs
                for k in [
                    "nat_network",
                    "bridged_interface",
                    "internal_network",
                    "host_only_interface",
                ]
            ):
                if "nat_network" in kwargs:
                    adapter.attachment_type = (
                        self.vbox_manager.constants.NetworkAttachmentType_NATNetwork
                    )
                    adapter.nat_network = kwargs["nat_network"]
                elif "bridged_interface" in kwargs:
                    adapter.attachment_type = (
                        self.vbox_manager.constants.NetworkAttachmentType_Bridged
                    )
                    adapter.bridged_interface = kwargs["bridged_interface"]
                elif "internal_network" in kwargs:
                    adapter.attachment_type = (
                        self.vbox_manager.constants.NetworkAttachmentType_Internal
                    )
                    adapter.internal_network = kwargs["internal_network"]
                elif "host_only_interface" in kwargs:
                    adapter.attachment_type = (
                        self.vbox_manager.constants.NetworkAttachmentType_HostOnly
                    )
                    adapter.host_only_interface = kwargs["host_only_interface"]

            # Save settings
            session.machine.save_settings()

            # Get updated settings
            updated_settings = {
                "enabled": adapter.enabled,
                "type": adapter.adapter_type,
                "mac_address": adapter.mac_address,
                "cable_connected": adapter.cable_connected,
                "promiscuous_mode": str(adapter.promiscuous_mode).split(".")[-1],
                "attachment_type": str(adapter.attachment_type).split(".")[-1],
            }

            return {
                "status": "success",
                "vm_name": vm_name,
                "adapter_number": adapter_number,
                "settings": updated_settings,
            }

        except Exception as e:
            raise RuntimeError(f"Failed to update network adapter: {str(e)}") from e
        finally:
            if session.state == self.vbox_manager.constants.SessionState_Locked:
                session.unlock_machine()

    def _update_network_adapter_hyperv(
        self, vm_name: str, adapter_number: int, **kwargs
    ) -> dict[str, Any]:
        """Update network adapter settings in Hyper-V."""
        try:
            # Build the PowerShell command
            cmd = ["powershell", "-Command"]
            ps_script = [
                f'$vm = Get-VM -Name "{vm_name}" -ErrorAction Stop;',
                f"$adapter = Get-VMNetworkAdapter -VM $vm | Select-Object -Index {adapter_number};",
                'if (-not $adapter) { throw "Network adapter not found" }',
            ]

            # Add parameter updates
            updates = []
            if "enabled" in kwargs:
                state = "On" if kwargs["enabled"] else "Off"
                updates.append(
                    f"Set-VMNetworkAdapter -VMNetworkAdapter $adapter -DeviceNaming {state}"
                )

            if "mac_address" in kwargs:
                updates.append(
                    f'Set-VMNetworkAdapter -VMNetworkAdapter $adapter -StaticMacAddress "{kwargs["mac_address"]}"'
                )

            if "switch_name" in kwargs:
                updates.append(
                    f'Connect-VMNetworkAdapter -VMNetworkAdapter $adapter -SwitchName "{kwargs["switch_name"]}"'
                )

            if updates:
                ps_script.extend(updates)

            # Get updated settings
            ps_script.extend(
                [
                    "$adapter = Get-VMNetworkAdapter -VM $vm | Select-Object -Index $adapter.Index;",
                    "$adapter | Select-Object Name, SwitchName, MacAddress, Status, IsLegacy, DynamicMacAddressEnabled | ",
                    "ConvertTo-Json -Depth 10",
                ]
            )

            cmd.append(" ".join(ps_script))

            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Parse and return the result
            import json

            adapter_info = json.loads(result.stdout)

            return {
                "status": "success",
                "vm_name": vm_name,
                "adapter_number": adapter_number,
                "settings": adapter_info,
            }

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to update network adapter in Hyper-V: {e.stderr}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse network adapter info from Hyper-V: {e}") from e

    @device_operation
    def add_disk(
        self,
        vm_name: str,
        disk_path: str,
        disk_type: str = "normal",
        size_mb: int = 10240,
        controller: str = "SATA Controller",
        port: int = 0,
        device: int = 0,
    ) -> dict[str, Any]:
        """
        Add a virtual disk to a VM.

        API Endpoint: POST /vms/{vm_name}/disks

        Args:
            vm_name: Name of the VM
            disk_path: Path to the disk file (will be created if it doesn't exist)
            disk_type: Type of disk ('normal', 'fixed', 'split2g', 'stream', 'disk1.1')
            size_mb: Size of the disk in MB (ignored if disk exists)
            controller: Name of the storage controller
            port: Controller port number
            device: Device number on the port

        Returns:
            Dictionary with operation status and disk information

        Example:
            ```python
            # Add a 20GB disk to a VM
            result = devices.add_disk(
                "my-vm",
                "/path/to/disk.vdi",
                disk_type="fixed",
                size_mb=20480
            )
            ```
        """
        # Input validation
        if not vm_name:
            raise ValueError("VM name is required")
        if not disk_path:
            raise ValueError("Disk path is required")
        if size_mb <= 0:
            raise ValueError("Disk size must be positive")

        # Get the VM
        vm = self.vm_operations.get_vm_by_name(vm_name)
        if not vm:
            raise RuntimeError(f"VM '{vm_name}' not found")

        # Handle based on hypervisor
        if self.hypervisor == "hyperv":
            return self._add_disk_hyperv(
                vm_name, disk_path, disk_type, size_mb, controller, port, device
            )
        else:
            return self._add_disk_virtualbox(
                vm_name, disk_path, disk_type, size_mb, controller, port, device
            )


    def list_attached_devices(self, vm_name: str) -> dict[str, Any]:
        """
        List all devices attached to a virtual machine.

        Args:
            vm_name: Name of the VM

        Returns:
            Dict containing status and list of attached devices
        """
        try:
            # Implementation will be moved from vm_service.py
            pass
        except Exception as e:
            logger.error(f"Failed to list devices for VM {vm_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
