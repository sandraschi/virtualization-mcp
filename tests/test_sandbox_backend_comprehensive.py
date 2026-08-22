"""Comprehensive unit tests for sandbox_backend.py."""

from unittest.mock import patch

import pytest

from virtualization_mcp.tools.sandbox.sandbox_backend import execute_code


def test_sandbox_backend_import():
    assert callable(execute_code)


@pytest.mark.asyncio
async def test_sandbox_backend_run_mock():
    with patch("virtualization_mcp.tools.sandbox.sandbox_backend._get_client") as mock_client:
        mock_container = mock_client.return_value.containers.run.return_value
        mock_container.logs.return_value = b"Hello World\n"
        mock_container.wait.return_value = {"StatusCode": 0}

        res = execute_code(code="print('Hello World')", language="python")
        assert res.get("success") is True
        assert "output" in res
