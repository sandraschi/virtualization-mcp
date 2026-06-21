"""Entry point for PyInstaller-bundled web dashboard backend."""

import _strptime  # noqa: F401 -- PyInstaller must bundle this eagerly
import os
import sys

# In PyInstaller bundle, __file__ lives at extraction root
_extract_root = os.path.dirname(os.path.abspath(__file__))
_src = os.path.join(_extract_root, "src")
for _p in [_extract_root, _src]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Set CORS origins BEFORE importing the web backend so only ONE CORS middleware is configured
_tauri_port = os.environ.get("PORT", "10700")
os.environ.setdefault(
    "CORS_ORIGINS",
    f"http://127.0.0.1:{_tauri_port},http://localhost:{_tauri_port},"
    "tauri://localhost,http://tauri.localhost,https://tauri.localhost,null",
)

from webapp.backend.app.main import app  # noqa: E402


def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "10700"))

    import uvicorn

    uvicorn.run(app, host=host, port=port, lifespan="on", log_level="info", timeout_graceful_shutdown=2)


if __name__ == "__main__":
    main()
