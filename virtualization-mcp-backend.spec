# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for virtualization-mcp backend sidecar (fleet pattern)."""

from PyInstaller.utils.hooks import copy_metadata

datas = [
    ("src/virtualization_mcp", "virtualization_mcp"),
    ("webapp/backend", "webapp/backend"),
]
for pkg in (
    "fastmcp",
    "fastapi",
    "uvicorn",
    "pydantic",
    "starlette",
    "httpx",
    "prefab-ui",
):
    datas += copy_metadata(pkg)

hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.httptools_impl",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.websockets_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "webapp.backend.app.main",
    "virtualization_mcp.all_tools_server",
    "virtualization_mcp.config",
    "virtualization_mcp.tools.register_tools",
    "virtualization_mcp.vbox",
    "virtualization_mcp.services",
    "virtualization_mcp.prompts",
    "virtualization_mcp.skills",
    "docker",
    "prometheus_client",
    "prefab_ui",
    "rich",
    "loguru",
    "_strptime",
]

a = Analysis(
    ["run_server.py"],
    pathex=["src", "."],
    binaries=[],
    
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pandas", "scipy", "torch", "tensorflow"],
    noarchive=True,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    
    name="virtualization-mcp-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
)








