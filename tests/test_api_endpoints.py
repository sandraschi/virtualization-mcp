"""
FastAPI endpoint tests for virtualization-mcp web backend.

Tests all REST API endpoints using FastAPI TestClient with mocked service layer.
Does NOT require VirtualBox to be installed (CI-safe).
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add webapp backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "webapp", "backend", "app"))


@pytest.fixture(scope="module", autouse=True)
def mock_network():
    """Mock all network calls that could hang (Ollama, LM Studio, GitHub API, socket)."""
    with (
        patch("urllib.request.urlopen") as mock_urlopen,
        patch("urllib.request.build_opener"),
        patch("socket.create_connection") as mock_socket,
    ):
        from unittest.mock import MagicMock as _M
        mock_resp = _M()
        mock_resp.read.return_value = b'{"version":"0.0.0"}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp
        mock_socket.side_effect = ConnectionRefusedError()
        yield


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient with mocked service_manager."""
    import main as webapp
    webapp.service_manager = MagicMock()
    webapp.service_manager.vm_service = MagicMock()
    webapp.ASSETS_VBOX = os.path.join(os.path.dirname(__file__), "..", "assets", "vbox")
    os.makedirs(os.path.dirname(webapp.KEYS_FILE), exist_ok=True)
    yield TestClient(webapp.app)


class TestHealth:
    """Basic health checks."""

    def test_health(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"

    def test_host_info(self, client):
        r = client.get("/api/v1/host/info")
        assert r.status_code == 200

    def test_vbox_status(self, client):
        r = client.get("/api/v1/vbox/status")
        assert r.status_code == 200


class TestVMs:
    """VM listing and CRUD endpoints."""

    def test_list_vms(self, client):
        from main import service_manager
        from unittest.mock import AsyncMock
        service_manager.vm_service.list_vms.return_value = {"success": True, "vms": []}
        service_manager.vm_service.hyperv_manager = MagicMock()
        service_manager.vm_service.hyperv_manager.list_vms = AsyncMock(return_value=[])
        r = client.get("/api/v1/vms")
        assert r.status_code == 200

    def test_create_vm(self, client):
        from main import service_manager
        service_manager.vm_service.create_vm.return_value = {
            "status": "success", "name": "test-vm1", "vm_id": "abc"
        }
        r = client.post("/api/v1/vms", json={"name": "test-vm1", "template": "ubuntu-dev"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "test-vm1"

    def test_create_vm_hyperv(self, client):
        from main import service_manager
        from unittest.mock import AsyncMock
        service_manager.vm_service.hyperv_manager = MagicMock()
        service_manager.vm_service.hyperv_manager.create_vm = AsyncMock(
            return_value={"status": "success", "vm_name": "hv-vm"}
        )
        r = client.post("/api/v1/vms", json={"name": "hv-vm", "provider": "hyperv"})
        assert r.status_code == 200
        data = r.json()
        assert data.get("vm_name") == "hv-vm" or data.get("status") == "success"

    def test_delete_vm(self, client):
        from main import service_manager
        service_manager.vm_service.delete_vm.return_value = {"status": "success", "message": "Deleted"}
        r = client.delete("/api/v1/vms/test-vm1")
        assert r.status_code == 200

    def test_start_vm(self, client):
        from main import service_manager
        service_manager.vm_service.start_vm.return_value = {"status": "success"}
        r = client.post("/api/v1/vms/test-vm1/start")
        assert r.status_code == 200

    def test_stop_vm(self, client):
        from main import service_manager
        service_manager.vm_service.stop_vm.return_value = {"status": "success"}
        r = client.post("/api/v1/vms/test-vm1/stop")
        assert r.status_code == 200


class TestSnapshots:
    """Snapshot endpoints."""

    def test_create_snapshot(self, client):
        from main import service_manager
        service_manager.vm_service.create_snapshot.return_value = {"status": "success"}
        r = client.post("/api/v1/vms/test-vm1/snapshot", json={"snapshot_name": "snap1"})
        assert r.status_code == 200

    def test_list_snapshots(self, client):
        from main import service_manager
        service_manager.vm_service.list_snapshots.return_value = {
            "status": "success", "snapshots": [{"name": "snap1"}]
        }
        r = client.get("/api/v1/vms/test-vm1/snapshots")
        assert r.status_code == 200
        data = r.json()
        assert "snapshots" in data


class TestISO:
    """ISO download pipeline endpoints."""

    def test_iso_candidates(self, client):
        r = client.get("/api/v1/iso/candidates")
        assert r.status_code == 200
        data = r.json()
        assert "categories" in data or "candidates" in data

    def test_iso_download_start(self, client):
        r = client.post("/api/v1/iso/download", json={"url": "https://example.com/test.iso"})
        assert r.status_code == 200
        data = r.json()
        assert "task_id" in data


class TestSettings:
    """Settings endpoints."""

    def test_llm_providers(self, client):
        r = client.get("/api/v1/settings/llm/providers")
        assert r.status_code == 200
        data = r.json()
        assert "ollama" in data
        assert "lm_studio" in data

    def test_api_keys_get(self, client):
        r = client.get("/api/v1/settings/keys")
        assert r.status_code == 200
        data = r.json()
        assert "keys" in data

    def test_api_keys_set(self, client):
        r = client.post("/api/v1/settings/keys", json={"keys": {"TEST_KEY": "sk-test123"}})
        assert r.status_code == 200
        data = r.json()
        assert data.get("saved") is True

    def test_dashboard(self, client):
        r = client.get("/api/v1/dashboard")
        assert r.status_code == 200
        data = r.json()
        assert "host" in data


class TestSandbox:
    """Sandbox endpoints."""

    def test_sandbox_status(self, client):
        r = client.get("/api/v1/sandbox/status")
        assert r.status_code == 200
        data = r.json()
        assert "running" in data


class TestFleet:
    """Fleet app discovery and installer endpoints."""

    def test_apps_list(self, client):
        r = client.get("/api/v1/apps")
        assert r.status_code == 200
        data = r.json()
        assert "webapps" in data

    def test_apps_health(self, client):
        r = client.get("/api/v1/apps/check")
        assert r.status_code == 200
        data = r.json()
        assert "statuses" in data

    def test_fleet_install_script(self, client):
        r = client.post("/api/v1/fleet/install-script", json={"repos": ["virtualization-mcp"]})
        assert r.status_code == 200
        data = r.json()
        assert "script" in data


class TestAssets:
    """Assets endpoints."""

    def test_assets_paths(self, client):
        r = client.get("/api/v1/assets/paths")
        assert r.status_code == 200
        data = r.json()
        assert "assets_vbox" in data

    def test_assets_vbox(self, client):
        r = client.get("/api/v1/assets/vbox")
        assert r.status_code == 200
        data = r.json()
        assert "files" in data


class TestChat:
    """Chat endpoint (tests the route exists, not actual LLM call)."""

    def test_chat_endpoint(self, client):
        r = client.post("/api/v1/chat", json={"message": "hello"})
        # Should return either a reply or a "no provider" message
        assert r.status_code == 200
        data = r.json()
        assert "reply" in data
