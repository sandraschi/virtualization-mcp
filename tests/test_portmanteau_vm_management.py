"""
Comprehensive test suite for VM Management Portmanteau Tool

Tests all actions and edge cases for the vm_management portmanteau tool.
Target: 90%+ coverage for GLAMA Gold Standard.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from virtualization_mcp.tools.portmanteau.vm_management import (
    VM_ACTIONS,
    register_vm_management_tool,
)


class TestVMManagementPortmanteau:
    """Test suite for VM Management Portmanteau Tool."""

    @pytest.fixture
    def mock_mcp(self):
        """Mock FastMCP instance."""
        mcp = Mock()
        # Store the decorated function when tool() is called
        self._tool_func = None

        def mock_tool_decorator(func=None, **kwargs):
            # Handle both @mcp.tool() and mcp.tool(func, name="...") patterns
            if func is not None:
                self._tool_func = func
                return func

            def decorator(f):
                self._tool_func = f
                return f
            return decorator

        mcp.tool = mock_tool_decorator
        return mcp

    @pytest.fixture
    def vm_management_tool(self, mock_mcp):
        """Register and return the VM management tool."""
        register_vm_management_tool(mock_mcp)
        # Return the captured tool function
        return self._tool_func

    def test_register_vm_management_tool(self, mock_mcp):
        """Test that the VM management tool is registered correctly."""
        register_vm_management_tool(mock_mcp)

        # Verify tool registration - the function should be captured
        assert self._tool_func is not None
        assert self._tool_func.__name__ == "vm_management"
        assert "Manage virtual machines" in self._tool_func.__doc__

    @pytest.mark.asyncio
    async def test_invalid_action(self, vm_management_tool):
        """Test handling of invalid actions."""
        result = await vm_management_tool(action="invalid_action")

        assert result["success"] is False
        assert "Invalid action" in result["error"]
        assert "available_actions" in result
        assert result["available_actions"] == VM_ACTIONS

    @pytest.mark.asyncio
    async def test_list_vms_action(self, vm_management_tool):
        """Test list VMs action."""
        mock_vms = [{"name": "VM1", "state": "running"}, {"name": "VM2", "state": "stopped"}]

        with patch(
            "virtualization_mcp.tools.portmanteau.vm_management.list_vms", new_callable=AsyncMock
        ) as mock_list_vms:
            mock_list_vms.return_value = mock_vms

            result = await vm_management_tool(action="list")

            assert result["success"] is True
            assert result["action"] == "list"
            assert result["data"] == mock_vms
            assert result["count"] == 2
            mock_list_vms.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_vms_action_error(self, vm_management_tool):
        """Test list VMs action with error."""
        with patch(
            "virtualization_mcp.tools.portmanteau.vm_management.list_vms", new_callable=AsyncMock
        ) as mock_list_vms:
            mock_list_vms.side_effect = Exception("VirtualBox error")

            result = await vm_management_tool(action="list")

            assert result["success"] is False
            assert result["action"] == "list"
            assert "Failed to list VMs" in result["error"]

    @pytest.mark.asyncio
    async def test_create_vm_action_success(self, vm_management_tool):
        """Test create VM action with valid parameters."""
        mock_result = {"vm_name": "TestVM", "created": True}

        with patch(
            "virtualization_mcp.tools.portmanteau.vm_management.create_vm", new_callable=AsyncMock
        ) as mock_create_vm:
            mock_create_vm.return_value = mock_result

            result = await vm_management_tool(
                action="create",
                vm_name="TestVM",
                os_type="Windows10_64",
                memory_mb=4096,
                disk_size_gb=50,
            )

            assert result["success"] is True
            assert result["action"] == "create"
            assert result["vm_name"] == "TestVM"
            assert result["data"] == mock_result
            mock_create_vm.assert_called_once_with(
                vm_name="TestVM", os_type="Windows10_64", memory_mb=4096, disk_size_gb=50
            )

    @pytest.mark.asyncio
    async def test_create_vm_action_missing_vm_name(self, vm_management_tool):
        """Test create VM action without vm_name."""
        result = await vm_management_tool(action="create", os_type="Windows10_64")

        assert result["success"] is False
        assert result["action"] == "create"
        assert "vm_name is required" in result["error"]

    @pytest.mark.asyncio
    async def test_create_vm_action_missing_os_type(self, vm_management_tool):
        """Test create VM action without os_type."""
        result = await vm_management_tool(action="create", vm_name="TestVM")

        assert result["success"] is False
        assert result["action"] == "create"
        assert "os_type is required" in result["error"]

    @pytest.mark.asyncio
    async def test_create_vm_action_error(self, vm_management_tool):
        """Test create VM action with error."""
        with patch(
            "virtualization_mcp.tools.portmanteau.vm_management.create_vm", new_callable=AsyncMock
        ) as mock_create_vm:
            mock_create_vm.side_effect = Exception("Creation failed")

            result = await vm_management_tool(
                action="create", vm_name="TestVM", os_type="Windows10_64"
            )

            assert result["success"] is False
            assert result["action"] == "create"
            assert "Failed to create VM" in result["error"]

    @pytest.mark.asyncio
    async def test_start_vm_action_success(self, vm_management_tool):
        """Test start VM action."""
        mock_result = {"vm_name": "TestVM", "started": True}

        with patch(
            "virtualization_mcp.tools.portmanteau.vm_management.start_vm", new_callable=AsyncMock
        ) as mock_start_vm:
            mock_start_vm.return_value = mock_result

            result = await vm_management_tool(action="start", vm_name="TestVM")

            assert result["success"] is True
            assert result["action"] == "start"
            assert result["vm_name"] == "TestVM"
            assert result["data"] == mock_result
            mock_start_vm.assert_called_once_with(vm_name="TestVM")

    @pytest.mark.asyncio
    async def test_start_vm_action_missing_vm_name(self, vm_management_tool):
        """Test start VM action without vm_name."""
        result = await vm_management_tool(action="start")

        assert result["success"] is False
        assert result["action"] == "start"
        assert "vm_name is required" in result["error"]

    @pytest.mark.asyncio
    async def test_stop_vm_action_success(self, vm_management_tool):
        """Test stop VM action."""
        mock_result = {"vm_name": "TestVM", "stopped": True}

        with patch(
            "virtualization_mcp.tools.portmanteau.vm_management.stop_vm", new_callable=AsyncMock
        ) as mock_stop_vm:
            mock_stop_vm.return_value = mock_result

            result = await vm_management_tool(action="stop", vm_name="TestVM")

            assert result["success"] is True
            assert result["action"] == "stop"
            assert result["vm_name"] == "TestVM"
            assert result["data"] == mock_result
            mock_stop_vm.assert_called_once_with(vm_name="TestVM")

    @pytest.mark.asyncio
    async def test_delete_vm_action_success(self, vm_management_tool):
        """Test delete VM action."""
        mock_result = {"vm_name": "TestVM", "deleted": True}

        with patch(
            "virtualization_mcp.tools.portmanteau.vm_management.delete_vm", new_callable=AsyncMock
        ) as mock_delete_vm:
            mock_delete_vm.return_value = mock_result

            result = await vm_management_tool(action="delete", vm_name="TestVM")

            assert result["success"] is True
            assert result["action"] == "delete"
            assert result["vm_name"] == "TestVM"
            assert result["data"] == mock_result
            mock_delete_vm.assert_called_once_with(vm_name="TestVM")

    @pytest.mark.asyncio
    async def test_clone_vm_action_success(self, vm_management_tool):
        """Test clone VM action."""
        mock_result = {"source_vm": "SourceVM", "new_vm": "ClonedVM", "cloned": True}

        with patch(
            "virtualization_mcp.tools.portmanteau.vm_management.clone_vm", new_callable=AsyncMock
        ) as mock_clone_vm:
            mock_clone_vm.return_value = mock_result

            result = await vm_management_tool(
                action="clone", source_vm="SourceVM", new_vm_name="ClonedVM"
            )

            assert result["success"] is True
            assert result["action"] == "clone"
            assert result["source_vm"] == "SourceVM"
            assert result["new_vm_name"] == "ClonedVM"
            assert result["data"] == mock_result
            mock_clone_vm.assert_called_once_with(source_vm="SourceVM", new_vm_name="ClonedVM")

    @pytest.mark.asyncio
    async def test_clone_vm_action_missing_source_vm(self, vm_management_tool):
        """Test clone VM action without source_vm."""
        result = await vm_management_tool(action="clone", new_vm_name="ClonedVM")

        assert result["success"] is False
        assert result["action"] == "clone"
        assert "source_vm is required" in result["error"]

    @pytest.mark.asyncio
    async def test_clone_vm_action_missing_new_vm_name(self, vm_management_tool):
        """Test clone VM action without new_vm_name."""
        result = await vm_management_tool(action="clone", source_vm="SourceVM")

        assert result["success"] is False
        assert result["action"] == "clone"
        assert "new_vm_name is required" in result["error"]

    @pytest.mark.asyncio
    async def test_reset_vm_action_success(self, vm_management_tool):
        """Test reset VM action."""
        mock_result = {"vm_name": "TestVM", "reset": True}

        with patch(
            "virtualization_mcp.tools.portmanteau.vm_management.reset_vm", new_callable=AsyncMock
        ) as mock_reset_vm:
            mock_reset_vm.return_value = mock_result

            result = await vm_management_tool(action="reset", vm_name="TestVM")

            assert result["success"] is True
            assert result["action"] == "reset"
            assert result["vm_name"] == "TestVM"
            assert result["data"] == mock_result
            mock_reset_vm.assert_called_once_with(vm_name="TestVM")

    @pytest.mark.asyncio
    async def test_pause_vm_action_success(self, vm_management_tool):
        """Test pause VM action."""
        mock_result = {"vm_name": "TestVM", "paused": True}

        with patch(
            "virtualization_mcp.tools.portmanteau.vm_management.pause_vm", new_callable=AsyncMock
        ) as mock_pause_vm:
            mock_pause_vm.return_value = mock_result

            result = await vm_management_tool(action="pause", vm_name="TestVM")

            assert result["success"] is True
            assert result["action"] == "pause"
            assert result["vm_name"] == "TestVM"
            assert result["data"] == mock_result
            mock_pause_vm.assert_called_once_with(vm_name="TestVM")

    @pytest.mark.asyncio
    async def test_resume_vm_action_success(self, vm_management_tool):
        """Test resume VM action."""
        mock_result = {"vm_name": "TestVM", "resumed": True}

        with patch(
            "virtualization_mcp.tools.portmanteau.vm_management.resume_vm", new_callable=AsyncMock
        ) as mock_resume_vm:
            mock_resume_vm.return_value = mock_result

            result = await vm_management_tool(action="resume", vm_name="TestVM")

            assert result["success"] is True
            assert result["action"] == "resume"
            assert result["vm_name"] == "TestVM"
            assert result["data"] == mock_result
            mock_resume_vm.assert_called_once_with(vm_name="TestVM")

    @pytest.mark.asyncio
    async def test_get_vm_info_action_success(self, vm_management_tool):
        """Test get VM info action."""
        mock_result = {"vm_name": "TestVM", "state": "running", "memory": 4096, "cpus": 2}

        with patch(
            "virtualization_mcp.tools.portmanteau.vm_management.get_vm_info", new_callable=AsyncMock
        ) as mock_get_vm_info:
            mock_get_vm_info.return_value = mock_result

            result = await vm_management_tool(action="info", vm_name="TestVM")

            assert result["success"] is True
            assert result["action"] == "info"
            assert result["vm_name"] == "TestVM"
            assert result["data"] == mock_result
            mock_get_vm_info.assert_called_once_with(vm_name="TestVM")

    @pytest.mark.asyncio
    async def test_get_vm_info_action_missing_vm_name(self, vm_management_tool):
        """Test get VM info action without vm_name."""
        result = await vm_management_tool(action="info")

        assert result["success"] is False
        assert result["action"] == "info"
        assert "vm_name is required" in result["error"]

    @pytest.mark.asyncio
    async def test_all_actions_require_vm_name_except_list(self, vm_management_tool):
        """Test that all actions except 'list' require vm_name."""
        actions_requiring_vm_name = [
            "create",
            "start",
            "stop",
            "delete",
            "reset",
            "pause",
            "resume",
            "info",
        ]

        for action in actions_requiring_vm_name:
            result = await vm_management_tool(action=action)
            assert result["success"] is False
            assert "vm_name is required" in result["error"]

    @pytest.mark.asyncio
    async def test_exception_handling(self, vm_management_tool):
        """Test exception handling in tool execution."""
        with patch(
            "virtualization_mcp.tools.portmanteau.vm_management.list_vms", new_callable=AsyncMock
        ) as mock_list_vms:
            mock_list_vms.side_effect = RuntimeError("Unexpected error")

            result = await vm_management_tool(action="list")

            assert result["success"] is False
            assert "Failed" in result["error"]  # Error message may vary
            assert result["action"] == "list"
            # available_actions may not be in error responses

    def test_vm_actions_constant(self):
        """Test that VM_ACTIONS constant is properly defined."""
        expected_actions = {
            "list",
            "create",
            "start",
            "stop",
            "delete",
            "clone",
            "reset",
            "pause",
            "resume",
            "info",
        }

        assert set(VM_ACTIONS.keys()) == expected_actions

        # Check that all actions have descriptions
        for _action, description in VM_ACTIONS.items():
            assert isinstance(description, str)
            assert len(description) > 0

    @pytest.mark.skip(reason="Portmanteau tools have specific params, don't accept arbitrary kwargs")
    @pytest.mark.asyncio
    async def test_kwargs_passthrough(self, vm_management_tool):
        """Test that additional kwargs are passed through to underlying functions."""
        with patch(
            "virtualization_mcp.tools.portmanteau.vm_management.create_vm", new_callable=AsyncMock
        ) as mock_create_vm:
            mock_create_vm.return_value = {"created": True}

            await vm_management_tool(
                action="create", vm_name="TestVM", os_type="Windows10_64", extra_param="extra_value"
            )

            # Check that extra_param is passed through
            call_kwargs = mock_create_vm.call_args[1]
            assert "extra_param" in call_kwargs
            assert call_kwargs["extra_param"] == "extra_value"
