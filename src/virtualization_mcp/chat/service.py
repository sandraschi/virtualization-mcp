# virtualization_mcp/chat/service.py
"""Chat service for virtualization-mcp backend."""

import json as _json  # noqa: F401 - used in ask() nested try/except
import os  # noqa: F401 - used in _load_keys, _get_skills_dir, etc.
import urllib.request as _req  # noqa: F401 - used in ask() for LLM HTTP calls
from typing import Any

from .memory import ChatMemory  # noqa: F401 - used in __init__


# ---------------------------------------------------------------------------
# Core service implementation.
# ---------------------------------------------------------------------------
class ChatService:
    """Encapsulates chat handling, provider dispatch and persistent memory.

    The service is instantiated once at application start‑up and reused for all
    incoming ``/api/v1/chat`` requests.
    """

    def __init__(self, db_path: str = "chat_memory.db", limit: int = 40):
        self.memory = ChatMemory(db_path=db_path, limit=limit)
        self._settings_cache: dict[str, Any] | None = None
        self._provider_order = ["lmstudio", "deepseek", "openai", "anthropic", "ollama"]

    # ---------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------
    def _load_settings(self) -> dict[str, Any]:
        if self._settings_cache is None:
            self._settings_cache = self._load_llm_settings()
        return self._settings_cache

    def _load_llm_settings(self) -> dict[str, Any]:
        return {"endpoint": os.environ.get("OLLAMA_HOST", "http://localhost:11434"), "model": "gemma4:e4b"}

    def _build_system_prompt(self, personality: str | None) -> str:
        base = "You are the SOTA Virtualization Assistant. You help manage VMs, Sandboxes, and the MCP Fleet."
        personality_instructions = {
            "professional": "",
            "pirate": "You speak like a pirate captain, using nautical terms and humor.",
            "sarcastic": "You respond with dry sarcasm and witty remarks.",
            "mentor": "You act as a supportive mentor, explaining patiently and encouraging the user.",
        }
        instr = personality_instructions.get(personality or "professional", "")
        if instr:
            base += f"\n\n{instr}"
        # Load optional skill content (virtualization‑expert) if present.
        try:
            skills_dir = self._get_skills_dir()
            if skills_dir:
                expert_path = os.path.join(skills_dir, "virtualization-expert", "SKILL.md")
                if os.path.isfile(expert_path):
                    with open(expert_path, encoding="utf-8") as f:
                        skill_content = f.read()
                    if skill_content.startswith("---"):
                        end = skill_content.find("---", 3)
                        if end != -1:
                            skill_content = skill_content[end + 3 :].strip()
                    base += f"\n\nUse the following skill guidelines when helping the user:\n{skill_content}"
        except Exception:
            pass
        return base

    def _get_skills_dir(self) -> str | None:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        candidate = os.path.join(repo_root, "skills")
        return candidate if os.path.isdir(candidate) else None

    def _build_messages(self, request: Any) -> list[dict[str, str]]:
        system_prompt = self._build_system_prompt(request.personality)
        session_id = request.session_id or "default"
        history = self.memory.get_messages(session_id)
        messages = [{"role": h["role"], "content": h["content"]} for h in history]
        messages.insert(0, {"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": request.message})
        return messages

    def _load_keys(self) -> dict[str, str]:
        keys_file = os.environ.get("VIRTUALIZATION_KEYS_FILE", "")
        if keys_file and os.path.isfile(keys_file):
            try:
                with open(keys_file) as f:
                    return _json.load(f)
            except Exception:
                pass
        return {}

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    async def ask(self, request: Any) -> dict[str, Any]:
        """Process a chat request and return a dictionary compatible with the
        original endpoint response.
        """
        try:
            settings = self._load_settings()
            endpoint = settings.get("endpoint", "http://localhost:11434").rstrip("/")
            preferred_model = request.model or settings.get("model", "gemma4:e4b")
            messages = self._build_messages(request)
            session_id = request.session_id or "default"

            for provider in self._provider_order:
                # Ollama provider
                if provider == "ollama":
                    try:
                        # discover available models
                        try:
                            avail_req = _req.urlopen(f"{endpoint}/api/tags", timeout=3)
                            avail_data = _json.loads(avail_req.read())
                            models = [m["name"] for m in avail_data.get("models", [])]
                        except Exception:
                            models = []
                        _preferred = preferred_model
                        if _preferred not in models and models:
                            for fallback in (
                                "gemma4:e4b",
                                "gemma4:e2b",
                                "llama3.2:3b",
                                "llama3.2:1b",
                                "llama3.1:latest",
                                "qwen2.5-coder:latest",
                            ):
                                if fallback in models:
                                    _preferred = fallback
                                    break
                            else:
                                _preferred = models[0]
                        payload = _json.dumps(
                            {
                                "model": _preferred,
                                "messages": messages,
                                "stream": False,
                            }
                        ).encode()
                        oreq = _req.Request(
                            f"{endpoint}/api/chat",
                            data=payload,
                            headers={"Content-Type": "application/json"},
                        )
                        with _req.urlopen(oreq, timeout=120) as r:
                            data = _json.loads(r.read())
                        reply = data.get("message", {}).get("content", "")
                        if reply:
                            self.memory.append(session_id, "assistant", reply)
                            return {"reply": reply, "provider": f"ollama ({_preferred})"}
                    except Exception:
                        continue

                # OpenAI compatible provider
                if provider == "openai":
                    try:
                        keys = self._load_keys()
                        api_key = keys.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY", "")
                        headers = {"Content-Type": "application/json"}
                        if api_key:
                            headers["Authorization"] = f"Bearer {api_key}"
                        openai_url = endpoint.rstrip("/")
                        if not openai_url.endswith("/chat/completions"):
                            if not openai_url.endswith("/v1"):
                                openai_url += "/v1"
                            openai_url += "/chat/completions"
                        payload = _json.dumps(
                            {
                                "model": preferred_model or "gpt-4o-mini",
                                "messages": messages,
                                "max_tokens": 1024,
                                "stream": False,
                            }
                        ).encode()
                        oreq = _req.Request(openai_url, data=payload, headers=headers)
                        with _req.urlopen(oreq, timeout=60) as r:
                            data = _json.loads(r.read())
                        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        if reply:
                            self.memory.append(session_id, "assistant", reply)
                            return {"reply": reply, "provider": f"openai compatible ({preferred_model})"}
                    except Exception:
                        continue

                # DeepSeek provider
                if provider == "deepseek":
                    try:
                        keys = self._load_keys()
                        api_key = keys.get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")
                        if not api_key:
                            return {
                                "reply": "DeepSeek API Key is missing. Please set it in Settings.",
                                "provider": None,
                            }
                        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
                        url = endpoint.rstrip("/")
                        if not url.endswith("/chat/completions"):
                            if not url.endswith("/v1"):
                                url += "/v1"
                            url += "/chat/completions"
                        payload = _json.dumps(
                            {
                                "model": preferred_model or "deepseek-v4-flash",
                                "messages": messages,
                                "max_tokens": 1024,
                            }
                        ).encode()
                        oreq = _req.Request(url, data=payload, headers=headers)
                        with _req.urlopen(oreq, timeout=60) as r:
                            data = _json.loads(r.read())
                        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        if reply:
                            self.memory.append(session_id, "assistant", reply)
                            return {"reply": reply, "provider": f"deepseek ({preferred_model})"}
                    except Exception:
                        continue

                # Anthropic provider
                if provider == "anthropic":
                    try:
                        keys = self._load_keys()
                        api_key = keys.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")
                        if not api_key:
                            return {"reply": "Anthropic API Key missing.", "provider": None}
                        headers = {
                            "Content-Type": "application/json",
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01",
                        }
                        url = endpoint.rstrip("/") + "/v1/messages"
                        payload = _json.dumps(
                            {
                                "model": preferred_model or "claude-3-opus-20240229",
                                "messages": messages,
                                "max_tokens": 1024,
                            }
                        ).encode()
                        oreq = _req.Request(url, data=payload, headers=headers)
                        with _req.urlopen(oreq, timeout=60) as r:
                            data = _json.loads(r.read())
                        reply = data.get("content", [{}])[0].get("text", "")
                        if reply:
                            self.memory.append(session_id, "assistant", reply)
                            return {"reply": reply, "provider": f"anthropic ({preferred_model})"}
                    except Exception:
                        continue

                # LM Studio provider (OpenAI compatible)
                if provider == "lmstudio":
                    try:
                        headers = {"Content-Type": "application/json"}
                        lm_url = endpoint.rstrip("/") + "/v1/chat/completions"
                        payload = _json.dumps(
                            {
                                "model": preferred_model or "gpt-4o-mini",
                                "messages": messages,
                                "max_tokens": 1024,
                                "stream": False,
                            }
                        ).encode()
                        oreq = _req.Request(lm_url, data=payload, headers=headers)
                        with _req.urlopen(oreq, timeout=60) as r:
                            data = _json.loads(r.read())
                        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        if reply:
                            self.memory.append(session_id, "assistant", reply)
                            return {"reply": reply, "provider": f"lmstudio ({preferred_model})"}
                    except Exception:
                        continue

            # Fallback echo provider
            echo_reply = f"Echo: {request.message}"
            self.memory.append(session_id, "assistant", echo_reply)
            return {"reply": echo_reply, "provider": "echo"}
        except Exception as e:
            return {"success": False, "ok": False, "error": str(e)}
