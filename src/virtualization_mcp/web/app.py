"""
FastAPI app for virtualization-mcp webapp.

Used by webapp/start.ps1 when running:
  uvicorn virtualization_mcp.web.app:app --host 127.0.0.1 --port 10701

Adds repo root to path and delegates to webapp backend.
"""

import sys
from pathlib import Path

# Repo root: src/virtualization_mcp/web/app.py -> go up 4 levels to repo root
_repo_root = Path(__file__).resolve().parent.parent.parent.parent
if _repo_root.exists() and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from webapp.backend.app.main import app  # noqa: E402

__all__ = ["app"]
