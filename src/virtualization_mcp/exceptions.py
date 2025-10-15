"""
Custom exceptions for the VirtualBox MCP server.
"""


class VMError(Exception):
    """Base exception for VM-related errors."""

    def __init__(self, message: str = "VM operation failed", details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(VMError):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation failed", details: dict = None):
        super().__init__(f"Validation error: {message}", details)


class RateLimitExceeded(VMError):
    """Raised when the rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message)


class ServiceUnavailable(VMError):
    """Raised when a required service is unavailable."""

    def __init__(self, service_name: str, reason: str = "Service unavailable"):
        message = f"{service_name} is unavailable: {reason}"
        super().__init__(message)


class VMManagerError(VMError):
    """Raised when there's an error in VM management operations."""

    def __init__(self, operation: str, error: str):
        super().__init__(f"Failed to {operation}: {error}")


class VMNotFoundError(VMError):
    """Raised when a VM is not found."""

    def __init__(self, vm_name: str):
        super().__init__(f"VM '{vm_name}' not found")


class SnapshotError(VMError):
    """Raised when there's an error with VM snapshots."""

    def __init__(self, operation: str, error: str):
        super().__init__(f"Snapshot {operation} failed: {error}")


class NetworkError(VMError):
    """Raised when there's a network-related error."""

    def __init__(self, operation: str, error: str):
        super().__init__(f"Network {operation} failed: {error}")


class StorageError(VMError):
    """Raised when there's a storage-related error."""

    def __init__(self, operation: str, error: str):
        super().__init__(f"Storage {operation} failed: {error}")


class ConfigurationError(VMError):
    """Raised when there's a configuration error."""

    def __init__(self, message: str):
        super().__init__(f"Configuration error: {message}")


class AuthenticationError(VMError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class AuthorizationError(VMError):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message)


class ResourceExhaustedError(VMError):
    """Raised when a resource limit is exceeded."""

    def __init__(self, resource: str, limit: str):
        super().__init__(f"{resource} limit exceeded: {limit}")


class TimeoutError(VMError):
    """Raised when an operation times out."""

    def __init__(self, operation: str, timeout: int):
        super().__init__(f"{operation} timed out after {timeout} seconds")


class InvalidStateError(VMError):
    """Raised when an operation is performed in an invalid state."""

    def __init__(self, operation: str, current_state: str, expected_states: list = None):
        message = f"Cannot {operation} in state '{current_state}'"
        if expected_states:
            message += f". Expected states: {', '.join(expected_states)}"
        super().__init__(message)
