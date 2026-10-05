"""Tests for skill-first chat surface + agentic chat loop (fleet chat SSOT).

Covers GET /skill/{name}, GET /api/v1/skills, the allowlist gate in
_exec_agent_tool, and POST /api/llm/chat-agent with a stubbed model turn
(no Ollama needed - deterministic).
"""

import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "webapp", "backend", "app"))


@pytest.fixture(scope="module")
def client():
    import main as webapp

    yield TestClient(webapp.app)


class TestSkillSurface:
    def test_skill_raw(self, client):
        r = client.get("/skill/virtualization-expert")
        assert r.status_code == 200
        assert "Virtualization expert" in r.text
        assert "vm_management" in r.text

    def test_skill_unknown(self, client):
        r = client.get("/skill/does-not-exist")
        assert r.status_code == 200
        assert r.text.strip('"') == "not found"

    def test_skill_traversal_blocked(self, client):
        # Starlette normalizes ".." out of the path (framework 404) or the
        # fixed allowlist rejects it ("not found"). Either way no file leaks.
        r = client.get("/skill/..%2F..%2Fpyproject")
        assert r.status_code in (200, 404)
        assert "Virtualization expert" not in r.text
        assert "requires-python" not in r.text

    def test_skills_list(self, client):
        r = client.get("/api/v1/skills")
        assert r.status_code == 200
        ids = [s.get("id") for s in r.json().get("skills", [])]
        assert "virtualization-expert" in ids


class TestAgentAllowlist:
    def test_unknown_tool_rejected(self, client):
        import asyncio

        import main as webapp

        result = asyncio.run(webapp._exec_agent_tool("delete_everything", {}))
        assert result["success"] is False
        assert "unknown tool" in result["error"]

    def test_destructive_action_not_exposed(self, client):
        import main as webapp

        actions = {tool for tool, _, _ in webapp._AGENT_TOOLMAP.values()}
        assert "delete" not in {a for _, a, _ in webapp._AGENT_TOOLMAP.values()}
        # every mapped action is read-only
        readonly = {
            "list",
            "info",
            "host_info",
            "vbox_version",
            "list_disks",
            "list_networks",
            "win_sandbox_status",
        }
        assert {a for _, a, _ in webapp._AGENT_TOOLMAP.values()} <= readonly
        assert actions  # non-empty allowlist


class TestChatAgent:
    def test_plain_reply_no_tools(self, client):
        import main as webapp

        async def fake_turn(session, model, system, messages, with_tools=True):
            assert "virtualization" in system.lower()
            return {"content": "2 VMs, both off.", "tool_calls": []}

        with (
            patch.object(webapp, "_prefetch_vm_inventory", new=AsyncMock(return_value=None)),
            patch.object(webapp, "_ollama_agent_turn", side_effect=fake_turn),
        ):
            r = client.post(
                "/api/llm/chat-agent",
                json={"messages": [{"role": "user", "content": "how many VMs?"}]},
            )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["reply"] == "2 VMs, both off."
        assert data["trace"] == []

    def test_tool_leak_restated(self, client):
        import main as webapp

        async def fake_turn(session, model, system, messages, with_tools=True):
            if with_tools:
                return {"content": '{"vms": []}', "tool_calls": []}
            return {"content": "No VMs found.", "tool_calls": []}

        with (
            patch.object(webapp, "_prefetch_vm_inventory", new=AsyncMock(return_value=None)),
            patch.object(webapp, "_ollama_agent_turn", side_effect=fake_turn),
        ):
            r = client.post(
                "/api/llm/chat-agent",
                json={"messages": [{"role": "user", "content": "how many VMs?"}]},
            )
        assert r.status_code == 200
        assert r.json()["reply"] == "No VMs found."
