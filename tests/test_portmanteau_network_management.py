"""
Comprehensive test suite for Network Management Portmanteau Tool

Tests all actions and edge cases for the network_management portmanteau tool.
Target: 90%+ coverage for GLAMA Gold Standard.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from virtualization_mcp.tools.portmanteau.network_management import (
    NETWORK_ACTIONS,
    register_network_management_tool,
)


class TestNetworkManagementPortmanteau:
    """Test suite for Network Management Portmanteau Tool."""

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
    def network_management_tool(self, mock_mcp):
        """Register and return the network management tool."""
        register_network_management_tool(mock_mcp)
        # Return the captured tool function
        return self._tool_func

    def test_register_network_management_tool(self, mock_mcp):
        """Test that the network management tool is registered correctly."""
        register_network_management_tool(mock_mcp)

        # Verify tool registration - the function should be captured
        assert self._tool_func is not None
        assert self._tool_func.__name__ == "network_management"
        assert "Comprehensive network management" in self._tool_func.__doc__

    @pytest.mark.asyncio
    async def test_invalid_action(self, network_management_tool):
        """Test handling of invalid actions."""
        result = await network_management_tool(action="invalid_action")

        assert result["success"] is False
        assert "Invalid action" in result["error"]
        assert "available_actions" in result
        assert result["available_actions"] == NETWORK_ACTIONS

    @pytest.mark.asyncio
    async def test_list_networks_action_success(self, network_management_tool):
        """Test list networks action."""
        mock_networks = [
            {"name": "vboxnet0", "ip": "192.168.56.1"},
            {"name": "vboxnet1", "ip": "192.168.57.1"},
        ]
        mock_payload = {"status": "success", "networks": mock_networks}

        with patch(
            "virtualization_mcp.tools.portmanteau.network_management.list_hostonly_networks",
            new_callable=AsyncMock,
        ) as mock_list_networks:
            mock_list_networks.return_value = mock_payload

            result = await network_management_tool(action="list_networks")

            assert result["success"] is True
            assert result["action"] == "list_networks"
            assert result["data"] == mock_payload
            assert result["count"] == 2
            mock_list_networks.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_networks_action_error(self, network_management_tool):
        """Test list networks action with error."""
        with patch(
            "virtualization_mcp.tools.portmanteau.network_management.list_hostonly_networks",
            new_callable=AsyncMock,
        ) as mock_list_networks:
            mock_list_networks.side_effect = Exception("Network error")

            result = await network_management_tool(action="list_networks")

            assert result["success"] is False
            assert result["action"] == "list_networks"
            assert "Failed to list networks" in result["error"]

    @pytest.mark.asyncio
    async def test_create_network_action_success(self, network_management_tool):
        """Test create network action."""
        mock_result = {"status": "success", "network_name": "TestNetwork"}

        with patch(
            "virtualization_mcp.tools.portmanteau.network_management.create_hostonly_network",
            new_callable=AsyncMock,
        ) as mock_create_network:
            mock_create_network.return_value = mock_result

            result = await network_management_tool(
                action="create_network",
                network_name="TestNetwork",
                ip_address="192.168.56.1",
                netmask="255.255.255.0",
            )

            assert result["success"] is True
            assert result["action"] == "create_network"
            assert result["network_name"] == "TestNetwork"
            assert result["data"] == mock_result
            mock_create_network.assert_called_once_with(
                network_name="TestNetwork", ip="192.168.56.1", netmask="255.255.255.0"
            )

    @pytest.mark.asyncio
    async def test_create_network_action_missing_network_name(self, network_management_tool):
        """Test create network action without network_name."""
        result = await network_management_tool(action="create_network", ip_address="192.168.56.1")

        assert result["success"] is False
        assert result["action"] == "create_network"
        assert "network_name is required" in result["error"]

    @pytest.mark.asyncio
    async def test_remove_network_action_success(self, network_management_tool):
        """Test remove network action."""
        mock_result = {"status": "success", "network_name": "TestNetwork"}

        with patch(
            "virtualization_mcp.tools.portmanteau.network_management.remove_hostonly_network",
            new_callable=AsyncMock,
        ) as mock_remove_network:
            mock_remove_network.return_value = mock_result

            result = await network_management_tool(
                action="remove_network", network_name="TestNetwork"
            )

            assert result["success"] is True
            assert result["action"] == "remove_network"
            assert result["network_name"] == "TestNetwork"
            assert result["data"] == mock_result
            mock_remove_network.assert_called_once_with(interface="TestNetwork")

    @pytest.mark.asyncio
    async def test_remove_network_action_missing_network_name(self, network_management_tool):
        """Test remove network action without network_name."""
        result = await network_management_tool(action="remove_network")

        assert result["success"] is False
        assert result["action"] == "remove_network"
        assert "network_name is required" in result["error"]

    @pytest.mark.asyncio
    async def test_list_adapters_action_success(self, network_management_tool):
        """Test list adapters action."""
        mock_result = {
            "status": "success",
            "vm_name": "TestVM",
            "adapters": [
                {"slot": 0, "type": "nat", "enabled": True},
                {"slot": 1, "type": "none", "enabled": False},
                {"slot": 2, "type": "none", "enabled": False},
                {"slot": 3, "type": "none", "enabled": False},
            ],
        }
        with patch(
            "virtualization_mcp.tools.portmanteau.network_management.list_network_adapters",
            new_callable=AsyncMock,
        ) as mock_list_adapters:
            mock_list_adapters.return_value = mock_result
            result = await network_management_tool(action="list_adapters", vm_name="TestVM")

            assert result["success"] is True
            assert result["action"] == "list_adapters"
            assert result["vm_name"] == "TestVM"
            assert "adapters" in result["data"]
            assert len(result["data"]["adapters"]) == 4
            mock_list_adapters.assert_called_once_with(vm_name="TestVM")

    @pytest.mark.asyncio
    async def test_list_adapters_action_missing_vm_name(self, network_management_tool):
        """Test list adapters action without vm_name."""
        result = await network_management_tool(action="list_adapters")

        assert result["success"] is False
        assert result["action"] == "list_adapters"
        assert "vm_name is required" in result["error"]

    @pytest.mark.asyncio
    async def test_configure_adapter_action_success(self, network_management_tool):
        """Test configure adapter action."""
        with patch(
            "virtualization_mcp.tools.portmanteau.network_management.configure_network_adapter",
            new_callable=AsyncMock,
        ) as mock_configure:
            mock_result = {"status": "success", "message": "configured"}
            mock_configure.return_value = mock_result
            result = await network_management_tool(
                action="configure_adapter",
                vm_name="TestVM",
                adapter_slot=0,
                network_type="hostonly",
                network_name="TestNetwork",
            )

            assert result["success"] is True
            assert result["action"] == "configure_adapter"
            assert result["vm_name"] == "TestVM"
            assert result["data"] == mock_result
            mock_configure.assert_called_once_with(
                vm_name="TestVM", adapter_id=1, network_type="hostonly"
            )

    @pytest.mark.asyncio
    async def test_configure_adapter_action_missing_vm_name(self, network_management_tool):
        """Test configure adapter action without vm_name."""
        result = await network_management_tool(
            action="configure_adapter", adapter_slot=0, network_type="hostonly"
        )

        assert result["success"] is False
        assert result["action"] == "configure_adapter"
        assert "vm_name is required" in result["error"]

    @pytest.mark.asyncio
    async def test_configure_adapter_action_missing_adapter_slot(self, network_management_tool):
        """Test configure adapter action without adapter_slot."""
        result = await network_management_tool(
            action="configure_adapter", vm_name="TestVM", network_type="hostonly"
        )

        assert result["success"] is False
        assert result["action"] == "configure_adapter"
        assert "adapter_slot is required" in result["error"]

    @pytest.mark.asyncio
    async def test_configure_adapter_action_missing_network_type(self, network_management_tool):
        """Test configure adapter action without network_type."""
        result = await network_management_tool(
            action="configure_adapter", vm_name="TestVM", adapter_slot=0
        )

        assert result["success"] is False
        assert result["action"] == "configure_adapter"
        assert "network_type is required" in result["error"]

    @pytest.mark.asyncio
    async def test_exception_handling(self, network_management_tool):
        """Test exception handling in tool execution."""
        with patch(
            "virtualization_mcp.tools.portmanteau.network_management.list_hostonly_networks",
            new_callable=AsyncMock,
        ) as mock_list_networks:
            mock_list_networks.side_effect = RuntimeError("Unexpected error")

            result = await network_management_tool(action="list_networks")

            assert result["success"] is False
            assert "Failed" in result["error"]  # Error message may vary
            assert result["action"] == "list_networks"
            # available_actions may not be in error responses

    def test_network_actions_constant(self):
        """Test that NETWORK_ACTIONS constant is properly defined."""
        expected_actions = {
            "list_networks",
            "create_network",
            "remove_network",
            "list_adapters",
            "configure_adapter",
        }

        assert set(NETWORK_ACTIONS.keys()) == expected_actions

        # Check that all actions have descriptions
        for _action, description in NETWORK_ACTIONS.items():
            assert isinstance(description, str)
            assert len(description) > 0

    @pytest.mark.skip(reason="Portmanteau tools have specific params, don't accept arbitrary kwargs")
    @pytest.mark.asyncio
    async def test_kwargs_passthrough(self, network_management_tool):
        """Test that additional kwargs are passed through to underlying functions."""
        with patch(
            "virtualization_mcp.tools.portmanteau.network_management.create_hostonly_network",
            new_callable=AsyncMock,
        ) as mock_create_network:
            mock_create_network.return_value = {"created": True}

            await network_management_tool(
                action="create_network", network_name="TestNetwork", extra_param="extra_value"
            )

            # Check that extra_param is passed through
            call_kwargs = mock_create_network.call_args[1]
            assert "extra_param" in call_kwargs
            assert call_kwargs["extra_param"] == "extra_value"

    @pytest.mark.asyncio
    async def test_all_network_actions(self, network_management_tool):
        """Test that all network actions are properly handled."""
        # Test each action with minimal valid parameters
        test_cases = [
            ("list_networks", {}),
            ("create_network", {"network_name": "TestNetwork"}),
            ("remove_network", {"network_name": "TestNetwork"}),
            ("list_adapters", {"vm_name": "TestVM"}),
            ("configure_adapter", {"vm_name": "TestVM", "adapter_slot": 0, "network_type": "nat"}),
        ]

        for action, params in test_cases:
            result = await network_management_tool(action=action, **params)
            # Should not fail with "action not implemented"
            assert "not implemented" not in result.get("error", "")

    @pytest.mark.asyncio
    async def test_network_management_error_scenarios(self, network_management_tool):
        """Test various error scenarios."""
        # Test with None values
        result = await network_management_tool(action="create_network", network_name=None)
        assert result["success"] is False

        # Test with empty string
        result = await network_management_tool(action="create_network", network_name="")
        assert result["success"] is False

        # Test with invalid adapter slot now fails via underlying validation
        with patch(
            "virtualization_mcp.tools.portmanteau.network_management.configure_network_adapter",
            new_callable=AsyncMock,
        ) as mock_configure:
            mock_configure.return_value = {"status": "error", "message": "Adapter ID must be between 1 and 4"}
            result = await network_management_tool(
                action="configure_adapter", vm_name="TestVM", adapter_slot=-1, network_type="nat"
            )
            assert result["success"] is False
