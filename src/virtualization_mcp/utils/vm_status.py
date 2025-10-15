"""
VM Status Utilities

This module provides utility functions for checking the status of VirtualBox VMs.
"""

# Import the VBoxManager only when needed to avoid circular imports
# We'll use a lazy import pattern to handle the dependency
_vbox_manager = None


def _get_vbox_manager():
    """Lazy import and return the VBoxManager instance."""
    global _vbox_manager
    if _vbox_manager is None:
        from ..vbox.manager import VBoxManager

        _vbox_manager = VBoxManager()
    return _vbox_manager


def is_vm_running(vm_name: str) -> bool:
    """Check if a VM is currently running.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if the VM is running, False otherwise
    """
    manager = _get_vbox_manager()
    try:
        vm = manager.get_vm(vm_name)
        return vm.is_running()
    except Exception:
        return False


def is_vm_paused(vm_name: str) -> bool:
    """Check if a VM is currently paused.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if the VM is paused, False otherwise
    """
    manager = _get_vbox_manager()
    try:
        vm = manager.get_vm(vm_name)
        return vm.is_paused()
    except Exception:
        return False


def is_vm_poweroff(vm_name: str) -> bool:
    """Check if a VM is powered off.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if the VM is powered off, False otherwise
    """
    return not is_vm_running(vm_name) and not is_vm_paused(vm_name)


def is_vm_saved(vm_name: str) -> bool:
    """Check if a VM is in a saved state.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if the VM is in a saved state, False otherwise
    """
    manager = _get_vbox_manager()
    try:
        vm = manager.get_vm(vm_name)
        return vm.is_saved()
    except Exception:
        return False


def is_vm_aborted(vm_name: str) -> bool:
    """Check if a VM is in an aborted state.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if the VM is aborted, False otherwise
    """
    manager = _get_vbox_manager()
    try:
        vm = manager.get_vm(vm_name)
        return vm.is_aborted()
    except Exception:
        return False


def is_vm_error(vm_name: str) -> bool:
    """Check if a VM is in an error state.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if the VM is in an error state, False otherwise
    """
    manager = _get_vbox_manager()
    try:
        vm = manager.get_vm(vm_name)
        return vm.is_error()
    except Exception:
        return True  # If we can't get the VM, consider it in an error state


def is_vm_starting(vm_name: str) -> bool:
    """Check if a VM is currently starting.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if the VM is starting, False otherwise
    """
    # This is a simplified implementation
    # In a real implementation, you might track starting state in the VM object
    # or use some other mechanism to detect a VM that's in the process of starting
    return False


def is_vm_stopping(vm_name: str) -> bool:
    """Check if a VM is currently stopping.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if the VM is stopping, False otherwise
    """
    # This is a simplified implementation
    # In a real implementation, you might track stopping state in the VM object
    # or use some other mechanism to detect a VM that's in the process of stopping
    return False


def is_vm_pausing(vm_name: str) -> bool:
    """Check if a VM is currently pausing.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if the VM is pausing, False otherwise
    """
    # This is a simplified implementation
    # In a real implementation, you might track pausing state in the VM object
    # or use some other mechanism to detect a VM that's in the process of pausing
    return False


def is_vm_teleporting(vm_name: str) -> bool:
    """Check if a VM is currently being teleported.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if the VM is being teleported, False otherwise
    """
    # This is a simplified implementation
    # In a real implementation, you would check the teleporting state
    return False


def is_vm_live_snapshotting(vm_name: str) -> bool:
    """Check if a live snapshot is currently being taken of the VM.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if a live snapshot is being taken, False otherwise
    """
    # This is a simplified implementation
    # In a real implementation, you would check the snapshotting state
    return False


def is_vm_deleting(vm_name: str) -> bool:
    """Check if a VM is currently being deleted.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if the VM is being deleted, False otherwise
    """
    # This is a simplified implementation
    # In a real implementation, you might track deletion state
    return False


def is_vm_importing(vm_name: str) -> bool:
    """Check if a VM is currently being imported.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if the VM is being imported, False otherwise
    """
    # This is a simplified implementation
    # In a real implementation, you might track import state
    return False


def is_vm_exporting(vm_name: str) -> bool:
    """Check if a VM is currently being exported.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if the VM is being exported, False otherwise
    """
    # This is a simplified implementation
    # In a real implementation, you might track export state
    return False


def is_vm_cloning(vm_name: str) -> bool:
    """Check if a VM is currently being cloned.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if the VM is being cloned, False otherwise
    """
    # This is a simplified implementation
    # In a real implementation, you might track clone state
    return False


def is_vm_resetting(vm_name: str) -> bool:
    """Check if a VM is currently being reset.

    Args:
        vm_name: Name of the VM to check

    Returns:
        bool: True if the VM is being reset, False otherwise
    """
    # This is a simplified implementation
    # In a real implementation, you might track reset state
    return False
