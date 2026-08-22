"""Unit tests for Prefab UI tools, ResourceGuard, and Cloud-Init ISO generator."""


from unittest.mock import MagicMock, patch

import pytest

from virtualization_mcp.services.cloud_init import create_cloud_init_iso, generate_cloud_init_config
from virtualization_mcp.tools.ui.prefab_tools import (
    show_hypervisor_health_card,
    show_sandbox_status_card,
    show_vm_card,
)
from virtualization_mcp.utils.resource_guard import ResourceGuard, ResourceQuotaExceededError


@pytest.mark.asyncio
async def test_prefab_vm_card():
    res = await show_vm_card("test-ubuntu")
    assert res.get("type") == "prefab_card"
    assert "data" in res


@pytest.mark.asyncio
async def test_prefab_hypervisor_health_card():
    res = await show_hypervisor_health_card()
    assert res.get("type") == "prefab_card"
    assert "host_metrics" in res.get("data", {})


@pytest.mark.asyncio
async def test_prefab_sandbox_status_card():
    res = await show_sandbox_status_card()
    assert res.get("type") == "prefab_card"
    assert "backends" in res.get("data", {})


def test_resource_guard_status():
    status = ResourceGuard.get_system_resource_status()
    assert "total_ram_mb" in status
    assert "ram_used_percent" in status


def test_resource_guard_quota_check():
    mock_mem = MagicMock()
    mock_mem.percent = 50.0
    mock_mem.available = 16 * 1024 * 1024 * 1024
    with patch("psutil.virtual_memory", return_value=mock_mem):
        # Safe request
        res = ResourceGuard.check_resource_quota(requested_memory_mb=128)
        assert res["safe"] is True

        # Oversized request
        with pytest.raises(ResourceQuotaExceededError):
            ResourceGuard.check_resource_quota(requested_memory_mb=99999999)


def test_cloud_init_generator():
    user_data, meta_data = generate_cloud_init_config(
        hostname="test-vm",
        username="devuser",
        ssh_public_key="ssh-rsa AAAAB3NzaC1yc2E...",
        run_commands=["echo 123"],
    )
    assert "test-vm" in user_data
    assert "devuser" in user_data
    assert "ssh-rsa" in user_data
    assert "echo 123" in user_data
    assert "instance-id: test-vm-init" in meta_data


def test_create_cloud_init_iso(tmp_path):
    iso_target = tmp_path / "seed.iso"
    res = create_cloud_init_iso(
        output_iso_path=str(iso_target),
        hostname="test-iso-host",
        username="admin",
    )
    assert res["success"] is True
