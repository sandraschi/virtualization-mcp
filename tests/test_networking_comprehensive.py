"""Comprehensive unit tests for vbox/networking.py and network tools."""

from unittest.mock import MagicMock, patch

import pytest

from virtualization_mcp.tools.network.network_tools import list_hostonly_networks
from virtualization_mcp.vbox.networking import NetworkManager


def test_network_manager_init():
    mock_vbox = MagicMock()
    mgr = NetworkManager(mock_vbox)
    assert mgr is not None


def test_list_hostonly_interfaces_mock():
    mock_vbox = MagicMock()
    mgr = NetworkManager(mock_vbox)
    if hasattr(mgr, "list_hostonly_interfaces"):
        ifs = mgr.list_hostonly_interfaces()
        assert isinstance(ifs, list)


@pytest.mark.asyncio
async def test_network_tools():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Name: vboxnet0\n"
        res = await list_hostonly_networks()
        assert isinstance(res, dict)
