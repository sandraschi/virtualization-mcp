#!/usr/bin/env python3
"""
Automated Docstring Enhancement Script

This script enhances all tool docstrings across the virtualization-mcp project
to match the production-quality standard set by the Windows Sandbox module.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Docstring enhancements for remaining VM tools
VM_TOOLS_ENHANCEMENTS = {
    "pause_vm": '''"""Pause a running virtual machine.

    Freezes a running VM in its current state, preserving all memory and CPU state.
    The VM can be resumed later from exactly the same point.

    Args:
        vm_name: Name or UUID of the virtual machine

    Returns:
        Dictionary containing:
            - status: "success" or "error"
            - vm_name: Name of the paused VM
            - message: Operation result or error message

    Examples:
        Pause a running VM:
            >>> result = await pause_vm("ubuntu-server")
            >>> print(result['message'])

        Pause before maintenance:
            >>> await pause_vm("production-vm")
            >>> # Do host maintenance
            >>> await resume_vm("production-vm")

        Pause multiple VMs:
            >>> vms = ["web", "db", "cache"]
            >>> for vm in vms:
            ...     await pause_vm(vm)

    Notes:
        - VM must be in "running" state to pause
        - All execution stops instantly
        - Memory state preserved in RAM
        - Use resume_vm() to continue execution
        - Different from saved state (pause keeps VM loaded in RAM)
        - Lower overhead than save/restore cycle
        - Useful for temporary freezing during host operations

    Common Errors:
        - "VM is not running": VM must be running to pause
        - "Could not find VM": Invalid name/UUID

    Raises:
        No exceptions raised - errors returned in result dictionary

    See Also:
        - resume_vm(): Continue execution of paused VM
        - stop_vm(): Shutdown the VM
        - start_vm(): Start a powered-off VM
    """''',

    "resume_vm": '''"""Resume a paused virtual machine.

    Continues execution of a paused VM from exactly where it was frozen,
    restoring all CPU and memory state.

    Args:
        vm_name: Name or UUID of the virtual machine

    Returns:
        Dictionary containing:
            - status: "success" or "error"
            - vm_name: Name of the resumed VM
            - message: Operation result or error message

    Examples:
        Resume a paused VM:
            >>> result = await resume_vm("ubuntu-server")
            >>> print(result['message'])

        Pause and resume workflow:
            >>> await pause_vm("my-vm")
            >>> # Do something on host
            >>> await resume_vm("my-vm")
            # VM continues from exact pause point

        Resume multiple VMs:
            >>> paused_vms = ["web", "db", "cache"]
            >>> for vm in paused_vms:
            ...     await resume_vm(vm)

    Notes:
        - VM must be in "paused" state to resume
        - Resumes from exact point it was paused
        - No data loss or state change
        - Instant operation (< 1 second)
        - Cannot resume a powered-off or saved VM
        - Use start_vm() for powered-off VMs

    Common Errors:
        - "VM is not paused": VM must be paused first
        - "Could not find VM": Invalid name/UUID

    Raises:
        No exceptions raised - errors returned in result dictionary

    See Also:
        - pause_vm(): Freeze the VM
        - start_vm(): Start a powered-off VM
        - get_vm_info(): Check VM state
    """''',

    "reset_vm": '''"""Reset a virtual machine (hard or soft reboot).

    Performs a hard or soft reset of a running VM, equivalent to pressing the
    reset button or sending an ACPI reset signal.

    Args:
        vm_name: Name or UUID of the virtual machine
        reset_type: Type of reset (default: "hard")
                   - "hard": Immediate power cycle (like reset button)
                   - "soft": ACPI reset signal (guest OS handles)

    Returns:
        Dictionary containing:
            - status: "success" or "error"
            - vm_name: Name of the reset VM
            - reset_type: Type of reset performed
            - message: Operation result or error message

    Examples:
        Hard reset (immediate):
            >>> result = await reset_vm("ubuntu-server")
            >>> print(result['message'])

        Soft reset (ACPI):
            >>> result = await reset_vm("windows-vm", reset_type="soft")
            # Guest OS handles reboot gracefully

        Reset after config change:
            >>> await modify_vm("my-vm", memory_mb=4096)
            >>> await reset_vm("my-vm")  # Apply changes

    Notes:
        - Hard reset = immediate reboot (may lose unsaved work)
        - Soft reset = ACPI signal (guest decides how to reboot)
        - VM must be running to reset
        - Some config changes require reset to apply
        - Use stop_vm() + start_vm() for cleaner restart
        - Hard reset faster but riskier for data

    Reset Types:
        1. Hard ("hard"):
           - Immediate power cycle
           - Like pressing reset button
           - Fast but may corrupt data
           - Always works

        2. Soft ("soft"):
           - ACPI reset signal
           - Guest OS handles reboot
           - Safer for running apps
           - Requires guest additions

    Common Errors:
        - "VM is not running": Must be running to reset
        - "Could not find VM": Invalid name/UUID

    Raises:
        No exceptions raised - errors returned in result dictionary

    See Also:
        - stop_vm(): Shutdown instead of reset
        - start_vm(): Start after stop
        - modify_vm(): Change VM configuration
    """''',
}


def main():
    """Main script execution."""
    print("=" * 70)
    print(" Docstring Enhancement Reference")
    print("=" * 70)
    print()
    print("This script provides enhanced docstring templates for tool functions.")
    print()
    print(f"Enhanced templates defined for {len(VM_TOOLS_ENHANCEMENTS)} VM tools:")
    for func_name in VM_TOOLS_ENHANCEMENTS:
        print(f"  - {func_name}()")
    print()
    print("To apply these enhancements, use search_replace in the IDE or")
    print("manually copy the enhanced docstrings to the source files.")
    print()
    print("All enhanced docstrings include:")
    print("  ✓ Summary line")
    print("  ✓ Detailed description")
    print("  ✓ Complete Args documentation")
    print("  ✓ Returns structure")
    print("  ✓ 3-5 usage examples")
    print("  ✓ Notes section")
    print("  ✓ Common errors")
    print("  ✓ Raises documentation")
    print("  ✓ See Also cross-references")
    print()
    print("=" * 70)

    # Show one example
    print("\nExample enhanced docstring (pause_vm):")
    print("-" * 70)
    print(VM_TOOLS_ENHANCEMENTS["pause_vm"])
    print("=" * 70)


if __name__ == "__main__":
    main()



