"""
Sandbox management for virtual machines.

This module provides functionality for creating and managing isolated testing environments (sandboxes)
for virtual machines, including snapshot management, network isolation, and resource constraints.
"""

import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from typing import Any

from ....vbox.vm_operations import VMOperations


class VMSandboxManager:
    """
    Manager for VM sandbox environments.

    Provides functionality for creating isolated testing environments with features like:
    - Temporary VM clones
    - Network isolation
    - Resource constraints
    - Automated cleanup
    - Snapshot management
    """

    def __init__(self, vm_operations: VMOperations, hypervisor: str = "virtualbox"):
        """
        Initialize the sandbox manager.

        Args:
            vm_operations: VM operations instance
            hypervisor: Hypervisor type ('virtualbox' or 'hyperv')
        """
        self.vm_operations = vm_operations
        self.hypervisor = hypervisor
        self.active_sandboxes: dict[str, dict[str, Any]] = {}

        # Setup sandbox base directory
        self.sandbox_dir = os.path.join(tempfile.gettempdir(), "virtualization-mcp_sandboxes")
        os.makedirs(self.sandbox_dir, exist_ok=True)

    def create_sandbox(
        self,
        source_vm: str,
        name: str = None,
        network_isolated: bool = True,
        resource_limits: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new sandboxed VM environment.

        API Endpoint: POST /sandbox/create

        Args:
            source_vm: Name of the base VM to clone
            name: Optional name for the sandbox (auto-generated if None)
            network_isolated: If True, isolates the sandbox from the host network
            resource_limits: Dictionary of resource limits (CPU, memory, etc.)

        Returns:
            Dictionary with sandbox details

        Example:
            ```python
            # Create a sandbox with network isolation
            sandbox = sandbox_mgr.create_sandbox(
                "base-vm",
                name="test-env-1",
                network_isolated=True,
                resource_limits={"cpus": 2, "memory_mb": 2048}
            )
            ```
        """
        # Generate a unique name if not provided
        if not name:
            name = f"sandbox-{str(uuid.uuid4())[:8]}"

        # Create a temporary directory for this sandbox
        sandbox_path = os.path.join(self.sandbox_dir, name)
        os.makedirs(sandbox_path, exist_ok=True)

        # Clone the VM
        try:
            # For VirtualBox
            if self.hypervisor == "virtualbox":
                self._clone_vm_virtualbox(source_vm, name, sandbox_path)
            # For Hyper-V
            else:
                self._clone_vm_hyperv(source_vm, name, sandbox_path)

            # Apply network isolation if requested
            if network_isolated:
                self._isolate_network(name)

            # Apply resource limits if specified
            if resource_limits:
                self._apply_resource_limits(name, resource_limits)

            # Store sandbox info
            sandbox_info = {
                "id": str(uuid.uuid4()),
                "name": name,
                "source_vm": source_vm,
                "path": sandbox_path,
                "created_at": time.time(),
                "network_isolated": network_isolated,
                "resource_limits": resource_limits or {},
                "status": "created",
            }

            self.active_sandboxes[name] = sandbox_info
            return sandbox_info

        except Exception as e:
            # Cleanup on failure
            if os.path.exists(sandbox_path):
                shutil.rmtree(sandbox_path, ignore_errors=True)
            raise RuntimeError(f"Failed to create sandbox: {str(e)}") from e

    def destroy_sandbox(self, name: str, force: bool = False) -> dict[str, Any]:
        """
        Destroy a sandbox and clean up its resources.

        API Endpoint: DELETE /sandbox/{name}

        Args:
            name: Name of the sandbox to destroy
            force: If True, force destroy even if VM is running

        Returns:
            Dictionary with operation status
        """
        if name not in self.active_sandboxes:
            raise ValueError(f"Sandbox '{name}' not found")

        sandbox = self.active_sandboxes[name]

        try:
            # Stop the VM if it's running
            if self.vm_operations.is_vm_running(name):
                if force:
                    self.vm_operations.stop_vm(name, force=True)
                else:
                    raise RuntimeError("VM is running. Use force=True to stop it.")

            # Unregister and delete the VM
            if self.hypervisor == "virtualbox":
                self._delete_vm_virtualbox(name)
            else:
                self._delete_vm_hyperv(name)

            # Remove sandbox directory
            if os.path.exists(sandbox["path"]):
                shutil.rmtree(sandbox["path"])

            # Remove from active sandboxes
            del self.active_sandboxes[name]

            return {
                "status": "success",
                "sandbox": name,
                "message": "Sandbox destroyed successfully",
            }

        except Exception as e:
            raise RuntimeError(f"Failed to destroy sandbox: {str(e)}") from e

    def list_sandboxes(self) -> list[dict[str, Any]]:
        """
        List all active sandboxes.

        API Endpoint: GET /sandbox

        Returns:
            List of sandbox information dictionaries
        """
        return list(self.active_sandboxes.values())

    def _clone_vm_virtualbox(
        self, source_vm: str, clone_name: str, target_path: str
    ) -> dict[str, Any]:
        """
        Clone a VM in VirtualBox using VBoxManage.

        Args:
            source_vm: Name of the source VM
            clone_name: Name for the new clone
            target_path: Path where the clone should be stored

        Returns:
            Dictionary with clone operation results
        """
        import subprocess

        try:
            # Clone the VM
            clone_cmd = [
                "VBoxManage",
                "clonevm",
                source_vm,
                "--name",
                clone_name,
                "--register",
                "--basefolder",
                target_path,
                "--mode",
                "machine",
                "--options",
                "KeepAllMACs,KeepNATMACs",
                "--snapshot",
                "current",
                "--type",
                "normal",
            ]

            # Execute clone command
            subprocess.run(clone_cmd, check=True, capture_output=True, text=True)

            # Get VM info
            info_cmd = ["VBoxManage", "showvminfo", "--machinereadable", clone_name]
            result = subprocess.run(info_cmd, capture_output=True, text=True, check=True)

            # Parse VM info
            vm_info = {}
            for line in result.stdout.splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    vm_info[key] = value.strip('"')

            return {
                "status": "success",
                "vm_name": clone_name,
                "uuid": vm_info.get("UUID"),
                "path": target_path,
                "memory": vm_info.get("memory"),
                "cpus": vm_info.get("cpus"),
            }

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone VM: {e.stderr}") from e
        except Exception as e:
            raise RuntimeError(f"Error during VM cloning: {str(e)}") from e

    def _clone_vm_hyperv(self, source_vm: str, clone_name: str, target_path: str) -> dict[str, Any]:
        """
        Clone a VM in Hyper-V using PowerShell.

        Args:
            source_vm: Name of the source VM
            clone_name: Name for the new clone
            target_path: Path where the clone should be stored

        Returns:
            Dictionary with clone operation results
        """
        import subprocess

        try:
            # Create the export script
            # Escape backslashes for PowerShell
            escaped_path = str(target_path).replace("\\", "\\\\")

            script_lines = [
                "$ErrorActionPreference = 'Stop'",
                f"$sourceVM = Get-VM -Name '{source_vm}' -ErrorAction Stop",
                f"$clonePath = '{escaped_path}'",
                f"$cloneName = '{clone_name}'",
                "",
                "# Create a snapshot for cloning",
                '$snapshot = $sourceVM | New-VMSnapshot -Name "TemporarySnapshot_$([Guid]::NewGuid().ToString())" -ErrorAction Stop',
                "",
                "try {",
                "    # Export the VM",
                "    $exportPath = Join-Path $clonePath 'export'",
                "    Export-VMSnapshot -VMSnapshot $snapshot -Path $exportPath -ErrorAction Stop",
                "",
                "    # Import the VM with a new name",
                '    $importedVM = Import-VM -Path "$exportPath\\*.exp" -Copy -GenerateNewId '
                + "-VirtualMachinePath $clonePath -VhdDestinationPath $clonePath -ErrorAction Stop",
                "    $importedVM | Rename-VM -NewName $cloneName -ErrorAction Stop",
                "",
                "    # Get VM info",
                "    $vmInfo = Get-VM -Name $cloneName -ErrorAction Stop | "
                + "Select-Object Name, Id, State, CPUUsage, MemoryAssigned, Status | "
                + "ConvertTo-Json -Depth 10 -Compress",
                "    return $vmInfo",
                "} finally {",
                "    # Clean up the temporary snapshot",
                "    $snapshot | Remove-VMSnapshot -Confirm:$false -ErrorAction SilentlyContinue",
                "}",
            ]
            export_script = "\n".join(script_lines)

            # Execute the script
            result = subprocess.run(
                ["powershell", "-Command", export_script],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse the result
            vm_info = json.loads(result.stdout)

            return {
                "status": "success",
                "vm_name": clone_name,
                "vm_id": vm_info.get("Id"),
                "state": vm_info.get("State"),
                "path": target_path,
                "memory_mb": vm_info.get("MemoryAssigned") / (1024 * 1024),  # Convert bytes to MB
                "cpu_cores": vm_info.get("CPUUsage"),
            }

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone VM in Hyper-V: {e.stderr}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("Failed to parse VM information from Hyper-V") from e
        except Exception as e:
            raise RuntimeError(f"Error during Hyper-V VM cloning: {str(e)}") from e

    def _isolate_network(self, vm_name: str) -> None:
        """
        Isolate VM network from host and other VMs.

        Args:
            vm_name: Name of the VM to isolate
        """
        if self.hypervisor == "virtualbox":
            self._isolate_network_virtualbox(vm_name)
        else:
            self._isolate_network_hyperv(vm_name)

    def _isolate_network_virtualbox(self, vm_name: str) -> None:
        """Isolate network for VirtualBox VM."""
        try:
            # Create an internal network for this VM
            internal_net_name = f"vboxnet_{vm_name}"

            # Create a host-only network
            subprocess.run(["VBoxManage", "hostonlyif", "create"], check=True, capture_output=True)

            # Add a host-only adapter
            subprocess.run(
                [
                    "VBoxManage",
                    "modifyvm",
                    vm_name,
                    "--nic1",
                    "hostonly",
                    "--hostonlyadapter1",
                    internal_net_name,
                ],
                check=True,
                capture_output=True,
            )

            # Disable DHCP server
            subprocess.run(
                ["VBoxManage", "dhcpserver", "remove", "--netname", internal_net_name],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to isolate network in VirtualBox: {e.stderr}") from e

    def _isolate_network_hyperv(self, vm_name: str) -> None:
        """Isolate network for Hyper-V VM."""
        try:
            # Create a private virtual switch
            switch_name = f"vswitch_{vm_name}"

            script = f"""
            $ErrorActionPreference = 'Stop'
            $switch = Get-VMSwitch -Name '{switch_name}' -ErrorAction SilentlyContinue
            if (-not $switch) {{
                New-VMSwitch -Name '{switch_name}' -SwitchType Private -ErrorAction Stop
            }}
            Get-VM -Name '{vm_name}' | Get-VMNetworkAdapter | Connect-VMNetworkAdapter -SwitchName '{switch_name}'
            """

            subprocess.run(["powershell", "-Command", script], check=True, capture_output=True)

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to isolate network in Hyper-V: {e.stderr}") from e

    def _apply_resource_limits(self, vm_name: str, limits: dict[str, Any]) -> None:
        """
        Apply resource limits to a VM.

        Args:
            vm_name: Name of the VM
            limits: Dictionary of resource limits (cpu, memory_mb, etc.)
        """
        if self.hypervisor == "virtualbox":
            self._apply_limits_virtualbox(vm_name, limits)
        else:
            self._apply_limits_hyperv(vm_name, limits)

    def _apply_limits_virtualbox(self, vm_name: str, limits: dict[str, Any]) -> None:
        """Apply resource limits to a VirtualBox VM."""
        try:
            # Set CPU count if specified
            if "cpus" in limits:
                subprocess.run(
                    ["VBoxManage", "modifyvm", vm_name, "--cpus", str(limits["cpus"])],
                    check=True,
                    capture_output=True,
                )

            # Set memory limit if specified
            if "memory_mb" in limits:
                subprocess.run(
                    ["VBoxManage", "modifyvm", vm_name, "--memory", str(limits["memory_mb"])],
                    check=True,
                    capture_output=True,
                )

            # Set CPU execution cap if specified (1-100%)
            if "cpu_cap" in limits:
                cap = max(1, min(100, int(limits["cpu_cap"])))
                subprocess.run(
                    ["VBoxManage", "modifyvm", vm_name, "--cpuexecutioncap", str(cap)],
                    check=True,
                    capture_output=True,
                )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to apply resource limits in VirtualBox: {e.stderr}") from e

    def _apply_limits_hyperv(self, vm_name: str, limits: dict[str, Any]) -> None:
        """Apply resource limits to a Hyper-V VM."""
        try:
            script = ["$ErrorActionPreference = 'Stop'"]

            # Set CPU count if specified
            if "cpus" in limits:
                script.append(f"Set-VMProcessor -VMName '{vm_name}' -Count {limits['cpus']}")

            # Set memory limit if specified
            if "memory_mb" in limits:
                memory_bytes = int(limits["memory_mb"]) * 1024 * 1024  # Convert MB to bytes
                script.append(
                    f"Set-VMMemory -VMName '{vm_name}' -DynamicMemoryEnabled $false -StartupBytes {memory_bytes}"
                )

            # Set CPU limit if specified (percentage of host CPU)
            if "cpu_cap" in limits:
                # Convert percentage to relative weight (1-10000)
                weight = int((limits["cpu_cap"] / 100.0) * 10000)
                script.append(
                    f"Set-VMProcessor -VMName '{vm_name}' -Maximum ${{env:NUMBER_OF_PROCESSORS}} -Reserve 10 -MaximumCountPerNumaNode ${{env:NUMBER_OF_PROCESSORS}} -MaximumCountPerNumaSocket ${{env:NUMBER_OF_PROCESSORS}} -RelativeWeight {weight}"
                )

            # Execute the script if we have any commands
            if len(script) > 1:
                subprocess.run(
                    ["powershell", "-Command", ";".join(script)], check=True, capture_output=True
                )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to apply resource limits in Hyper-V: {e.stderr}") from e

    def _delete_vm_virtualbox(self, vm_name: str) -> None:
        """
        Delete a VM in VirtualBox.

        Args:
            vm_name: Name of the VM to delete
        """
        try:
            # Power off the VM if it's running
            subprocess.run(
                ["VBoxManage", "controlvm", vm_name, "poweroff"],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )

            # Unregister and delete the VM
            subprocess.run(
                ["VBoxManage", "unregistervm", vm_name, "--delete"], check=True, capture_output=True
            )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to delete VM in VirtualBox: {e.stderr}") from e

    def _delete_vm_hyperv(self, vm_name: str) -> None:
        """
        Delete a VM in Hyper-V.

        Args:
            vm_name: Name of the VM to delete
        """
        try:
            # Stop the VM if it's running
            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    f"Stop-VM -Name '{vm_name}' -Force -ErrorAction SilentlyContinue",
                ],
                check=False,
            )

            # Remove the VM and its storage
            script = f"""
            $ErrorActionPreference = 'Stop'
            $vm = Get-VM -Name '{vm_name}' -ErrorAction Stop
            $vm | Remove-VM -Force -Confirm:$false
            """

            subprocess.run(["powershell", "-Command", script], check=True, capture_output=True)

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to delete VM in Hyper-V: {e.stderr}") from e
