"""
Tests for exceptions module to boost coverage from 80% to 100%.

All exception types need to be tested for instantiation and error messages.
"""

import pytest


class TestVirtualizationMCPExceptions:
    """Test all exception classes."""

    def test_virtualization_mcp_error(self):
        """Test base VMError."""
        from virtualization_mcp.exceptions import VMError

        error = VMError("test error")
        assert str(error) == "test error"
        assert isinstance(error, Exception)

    def test_vbox_error(self):
        """Test VMError (replaces old VBoxError)."""
        from virtualization_mcp.exceptions import VMError

        error = VMError("VBox error occurred")
        assert "VBox error occurred" in str(error)

    def test_vm_not_found_error(self):
        """Test VMNotFoundError exception."""
        from virtualization_mcp.exceptions import VMNotFoundError

        error = VMNotFoundError("test-vm")
        assert "test-vm" in str(error)

    def test_vm_already_exists_error(self):
        """Test VMError with 'already exists' message (no dedicated class)."""
        from virtualization_mcp.exceptions import VMError

        error = VMError("VM 'existing-vm' already exists")
        assert "existing-vm" in str(error)

    def test_invalid_state_error(self):
        """Test InvalidStateError exception."""
        from virtualization_mcp.exceptions import InvalidStateError

        error = InvalidStateError(operation="start", current_state="running")
        assert "in state" in str(error).lower()
        assert "running" in str(error)

    def test_invalid_configuration_error(self):
        """Test ConfigurationError (replaces old InvalidConfigurationError)."""
        from virtualization_mcp.exceptions import ConfigurationError

        error = ConfigurationError("Invalid config")
        assert "config" in str(error).lower()

    def test_snapshot_error(self):
        """Test SnapshotError exception."""
        from virtualization_mcp.exceptions import SnapshotError

        error = SnapshotError(operation="create", error="Snapshot operation failed")
        assert "snapshot" in str(error).lower()

    def test_network_error(self):
        """Test NetworkError exception."""
        from virtualization_mcp.exceptions import NetworkError

        error = NetworkError(operation="config", error="Network configuration failed")
        assert "network" in str(error).lower()

    def test_storage_error(self):
        """Test StorageError exception."""
        from virtualization_mcp.exceptions import StorageError

        error = StorageError(operation="attach", error="Storage operation failed")
        assert "storage" in str(error).lower()

    def test_timeout_error(self):
        """Test OperationTimedOut (replaces old TimeoutError)."""
        from virtualization_mcp.exceptions import OperationTimedOut

        error = OperationTimedOut(operation="start", timeout=30)
        assert "timed out" in str(error).lower()

    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        from virtualization_mcp.exceptions import AuthenticationError

        error = AuthenticationError("Authentication failed")
        assert "authentication" in str(error).lower()

    def test_authorization_error(self):
        """Test AuthorizationError exception."""
        from virtualization_mcp.exceptions import AuthorizationError

        error = AuthorizationError("Not authorized")
        assert "authorized" in str(error).lower()

    def test_validation_error(self):
        """Test ValidationError exception."""
        from virtualization_mcp.exceptions import ValidationError

        error = ValidationError("Validation failed")
        assert "validation" in str(error).lower()

    def test_rate_limit_error(self):
        """Test RateLimitExceeded (replaces old RateLimitError)."""
        from virtualization_mcp.exceptions import RateLimitExceeded

        error = RateLimitExceeded("Rate limit exceeded")
        assert "rate limit" in str(error).lower()

    def test_service_unavailable_error(self):
        """Test ServiceUnavailable (replaces old ServiceUnavailableError)."""
        from virtualization_mcp.exceptions import ServiceUnavailable

        error = ServiceUnavailable(service_name="TestService", reason="Service is unavailable")
        assert "unavailable" in str(error).lower()

    def test_resource_exhausted_error(self):
        """Test ResourceExhaustedError exception."""
        from virtualization_mcp.exceptions import ResourceExhaustedError

        error = ResourceExhaustedError(resource="memory", limit="8GB")
        assert "limit exceeded" in str(error).lower()
        assert "memory" in str(error).lower()
        assert "8gb" in str(error).lower()

    def test_configuration_error(self):
        """Test ConfigurationError exception."""
        from virtualization_mcp.exceptions import ConfigurationError

        error = ConfigurationError("Configuration error")
        assert "configuration" in str(error).lower()

    def test_vm_manager_error(self):
        """Test VMManagerError exception."""
        from virtualization_mcp.exceptions import VMManagerError

        error = VMManagerError(operation="create", error="failed")
        assert "failed to create" in str(error).lower()


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_base(self):
        """Test all custom exceptions inherit from VMError."""
        from virtualization_mcp.exceptions import (
            AuthenticationError,
            NetworkError,
            SnapshotError,
            StorageError,
            ValidationError,
            VMError,
            VMNotFoundError,
        )

        assert issubclass(VMNotFoundError, VMError)
        assert issubclass(SnapshotError, VMError)
        assert issubclass(NetworkError, VMError)
        assert issubclass(StorageError, VMError)
        assert issubclass(ValidationError, VMError)
        assert issubclass(AuthenticationError, VMError)

    def test_exceptions_can_be_raised(self):
        """Test exceptions can be raised and caught."""
        from virtualization_mcp.exceptions import VMError

        with pytest.raises(VMError) as exc_info:
            raise VMError("Test error")

        assert "Test error" in str(exc_info.value)

    def test_exception_with_custom_message(self):
        """Test exception with formatted message."""
        from virtualization_mcp.exceptions import VMNotFoundError

        vm_name = "my-test-vm"
        with pytest.raises(VMNotFoundError) as exc_info:
            raise VMNotFoundError(vm_name)

        assert vm_name in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
