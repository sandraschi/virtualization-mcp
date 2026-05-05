import asyncio
import json
import logging
import os
import sys
import tempfile
import threading
import time
import urllib.request
import warnings
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    try:
        import google.generativeai as genai
    except ImportError:
        genai = None  # type: ignore[assignment]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("virtualization_backend")

# Add src directory to sys.path to import virtualization_mcp
current_dir = os.path.dirname(os.path.abspath(__file__))
# Map from: webapp/backend/app/main.py -> repo root and src
_repo_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
project_root = os.path.join(_repo_root, "src")
if os.path.exists(project_root) and project_root not in sys.path:
    sys.path.insert(0, project_root)
else:
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)
    project_root = _repo_root
# Assets folders for reuse (sandbox installers, VBox ISOs/OVA)
ASSETS_SANDBOX = os.path.join(_repo_root, "assets", "sandbox")
ASSETS_VBOX = os.path.join(_repo_root, "assets", "vbox")

# API key storage (user-set via Settings UI, overrides .env)
KEYS_FILE = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "virtualization-mcp", "keys.json")
os.makedirs(os.path.dirname(KEYS_FILE), exist_ok=True)

# MCP and service manager set at startup in lifespan
mcp = None
service_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mcp, service_manager
    logger.info("Virtualization Backend Starting...")
    from virtualization_mcp.services.service_manager import service_manager as sm

    # Initialize service_manager first so /api/v1/vms and /api/v1/host/info work even if MCP fails
    try:
        sm.initialize_services()
        service_manager = sm
        logger.info("Service manager initialized (VMs, host info available)")
    except Exception as e:
        logger.error("Service manager init failed: %s", e, exc_info=True)
        service_manager = None

    # Then try MCP server for tools
    try:
        from virtualization_mcp.all_tools_server import start_mcp_server

        mcp = start_mcp_server()
        if mcp:
            logger.info("MCP Server: %s", mcp.name)
    except Exception as e:
        logger.error("MCP server init failed: %s", e, exc_info=True)
        mcp = None

    yield
    logger.info("Virtualization Backend Stopping...")


# Registry Path
REGISTRY_PATH = "D:/Dev/repos/mcp-central-docs/operations/webapp-registry.json"

# Initialize Gemini (optional)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
chat_model = None
if genai and GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    chat_model = genai.GenerativeModel("gemini-1.5-flash")
elif not genai:
    logger.warning("google-generativeai not installed. Chat will be disabled.")
elif not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY not found; chat will be in limited mode.")

app = FastAPI(title="Virtualization MCP Backend", lifespan=lifespan)

# CORS Configuration (frontend dev: 10700; backend: 10701)
origins = os.getenv("CORS_ORIGINS", "http://localhost:10700,http://127.0.0.1:10700,http://localhost:10760").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Full dev setup: winget package IDs + optional download-and-run (max automatic)
SANDBOX_DEV_SETUP_TOOLS = {
    "python": "Python.Python.3.12",
    "git": "Git.Git",
    "node": "OpenJS.NodeJS.LTS",
    "just": "Casey.Just",
    "vscode": "Microsoft.VisualStudioCode",
    "notepad++": "Notepad++.Notepad++",
    "uv": "astral-sh.uv",
    "windsurf": "Codeium.Windsurf",
    "cursor": "Anysphere.Cursor",
    "antigravity": "Google.Antigravity",
}
# Claude Desktop: no winget; download and run installer
SANDBOX_DEV_SETUP_DOWNLOAD = {
    "claude_desktop": ("https://downloads.claude.ai/releases/win32/ClaudeSetup.exe", "ClaudeSetup.exe"),
}
# OpenClaw (npm), OpenFang (install.ps1), RoboFang (git + pip -e) - optional post-steps
ROBOFANG_REPO = "https://github.com/sandraschi/robofang"


def _get_dev_setup_script(tools: list[str], use_host_ollama: bool = False) -> str:
    """Generate PowerShell script: winget + pip upgrade + optional Claude/OpenClaw/OpenFang/RoboFang + optional OLLAMA_HOST to host. As automatic as possible."""
    winget_ids = []
    has_python = False
    do_claude_desktop = False
    do_openclaw = False
    do_openfang = False
    do_robofang = False
    for t in tools:
        t_lower = t.strip().lower().replace(" ", "").replace("-", "_")
        if t_lower in SANDBOX_DEV_SETUP_TOOLS:
            winget_ids.append(SANDBOX_DEV_SETUP_TOOLS[t_lower])
            if t_lower == "python":
                has_python = True
        elif t_lower in ("claude_desktop", "claudesktop", "claudedesktop"):
            do_claude_desktop = True
        elif t_lower == "openclaw":
            do_openclaw = True
        elif t_lower == "openfang":
            do_openfang = True
        elif t_lower == "robofang":
            do_robofang = True
    if not winget_ids and not any((do_claude_desktop, do_openclaw, do_openfang, do_robofang)):
        winget_ids = [
            "Python.Python.3.12",
            "Git.Git",
            "OpenJS.NodeJS.LTS",
            "Casey.Just",
            "Microsoft.VisualStudioCode",
            "Notepad++.Notepad++",
            "astral-sh.uv",
            "Codeium.Windsurf",
            "Anysphere.Cursor",
            "Google.Antigravity",
        ]
        has_python = True

    winget_blocks = "\n".join(
        f'$wingetArgs = @("install", "-e", "--id", "{wid}", "--accept-package-agreements", "--accept-source-agreements")\n& winget @wingetArgs\nif ($LASTEXITCODE -ne 0) {{ Write-Host "winget {wid} failed." -ForegroundColor Red; exit 1 }}'
        for wid in winget_ids
    )
    pip_block = ""
    if has_python or "Python.Python.3.12" in winget_ids:
        pip_block = """
# 5) Upgrade pip (mod cons)
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "Upgrading pip..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { Write-Host "pip upgrade failed." -ForegroundColor Red; exit 1 }
}
"""
    claude_block = ""
    if do_claude_desktop:
        url, name = SANDBOX_DEV_SETUP_DOWNLOAD["claude_desktop"]
        claude_block = f"""
# 6) Claude Desktop (download and run installer; no winget)
Write-Host "Downloading Claude Desktop..." -ForegroundColor Yellow
$claudeExe = Join-Path $env:TEMP "{name}"
try {{
    Invoke-WebRequest -Uri "{url}" -OutFile $claudeExe -UseBasicParsing
    Write-Host "Installing Claude Desktop..." -ForegroundColor Yellow
    Start-Process -FilePath $claudeExe -Wait
}} catch {{ Write-Host "Claude Desktop: $($_.Exception.Message)" -ForegroundColor Yellow }}
"""
    openclaw_block = ""
    if do_openclaw:
        openclaw_block = """
# 7) OpenClaw (npm global)
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "Installing OpenClaw..." -ForegroundColor Yellow
    npm install -g openclaw@latest
    if ($LASTEXITCODE -ne 0) { Write-Host "OpenClaw install failed." -ForegroundColor Yellow }
}
"""
    openfang_block = ""
    if do_openfang:
        openfang_block = """
# 8) OpenFang (official install script)
Write-Host "Installing OpenFang..." -ForegroundColor Yellow
try {
    irm https://openfang.sh/install.ps1 | iex
} catch { Write-Host "OpenFang: $($_.Exception.Message)" -ForegroundColor Yellow }
"""
    robofang_block = ""
    if do_robofang:
        robofang_block = f"""
# 9) RoboFang (git clone + pip install -e .)
$codeRoot = Join-Path $assetRoot "code"
New-Item -ItemType Directory -Path $codeRoot -Force | Out-Null
Set-Location $codeRoot
if (-not (Test-Path "robofang")) {{
    Write-Host "Cloning RoboFang..." -ForegroundColor Yellow
    git clone {ROBOFANG_REPO}
    if ($LASTEXITCODE -ne 0) {{ Write-Host "RoboFang clone failed." -ForegroundColor Red; exit 1 }}
}}
Set-Location (Join-Path $codeRoot "robofang")
Write-Host "Installing RoboFang (pip install -e .)..." -ForegroundColor Yellow
python -m pip install -e .
if ($LASTEXITCODE -ne 0) {{ Write-Host "RoboFang pip install failed." -ForegroundColor Red; exit 1 }}
Set-Location $assetRoot
"""
    ollama_block = ""
    if use_host_ollama:
        ollama_block = r"""
# 10) Use host Ollama (default gateway = host from sandbox)
$gw = (Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue | Select-Object -First 1).NextHop
if ($gw) {
    $env:OLLAMA_HOST = "http://$gw:11434"
    [Environment]::SetEnvironmentVariable("OLLAMA_HOST", $env:OLLAMA_HOST, "User")
    Write-Host "OLLAMA_HOST set to $env:OLLAMA_HOST (host Ollama)" -ForegroundColor Cyan
}
"""
    return f"""# Setup-DevSandbox.ps1 - Full dev stack in Windows Sandbox (virtualization-mcp)
# Automatic: Python, Node, pip, uv/uvx, Git, VS Code, Just, Notepad++, Windsurf, Cursor, Antigravity, Claude Desktop, OpenClaw, OpenFang, RoboFang. Optional: host Ollama.
# Requires in C:\\Assets: DesktopAppInstaller_Dependencies.zip, Microsoft.DesktopAppInstaller_*.msixbundle

# Wait for mapped folder + network to stabilize
Write-Host "Waiting for environment to initialize..." -ForegroundColor Cyan
Start-Sleep 5

$assetRoot = "C:\\Assets"
if (-not (Test-Path $assetRoot)) {{
    Write-Host "Assets folder not found at $assetRoot." -ForegroundColor Red
    exit 1
}}
Set-Location $assetRoot

# Start transcript for full logging
$logPath = "$env:USERPROFILE\\Desktop\\dev-setup-ps.log"
Start-Transcript -Path $logPath -Append

# 1) Dependencies from zip
$depsZip = Get-ChildItem -File | Where-Object {{ $_.Name -eq "DesktopAppInstaller_Dependencies.zip" }} | Select-Object -First 1
if ($depsZip) {{
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    $depsDir = Join-Path $assetRoot "deps"
    if (Test-Path $depsDir) {{ Remove-Item -Recurse -Force $depsDir }}
    Expand-Archive -Path $depsZip.FullName -DestinationPath $depsDir -Force
    Get-ChildItem -Path $depsDir -Filter "*.msix" -Recurse | Sort-Object Name | ForEach-Object {{
        try {{ Add-AppxPackage -Path $_.FullName }} catch {{ Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red; exit 1 }}
    }}
}}

# 2) App Installer (winget) bundle
$bundle = Get-ChildItem -File | Where-Object {{ $_.Name -like "*.msixbundle" }} | Select-Object -First 1
if (-not $bundle) {{ Write-Host "No .msixbundle in $assetRoot." -ForegroundColor Red; exit 1 }}
try {{ Add-AppxPackage -Path $bundle.FullName }} catch {{ Write-Host $_.Exception.Message -ForegroundColor Red; exit 1 }}

# 3) Refresh PATH for winget (check WindowsApps dir explicitly)
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
$wingetDirs = @("$env:LOCALAPPDATA\\Microsoft\\WindowsApps", "$env:ProgramFiles\\winget")
foreach ($dir in $wingetDirs) {{
    if (Test-Path $dir -and $env:Path -notlike "*$dir*") {{
        $env:Path = "$dir;$env:Path"
    }}
}}
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {{
    Write-Host "winget not found. Open a NEW PowerShell and run this script again." -ForegroundColor Red
    exit 1
}}

# 4) Dev stack via winget (Python, Node, uv, Git, VS Code, Just, Notepad++, Windsurf, Cursor, Antigravity)
Write-Host "Installing dev tools via winget..." -ForegroundColor Yellow
{winget_blocks}
{pip_block}
{claude_block}
{openclaw_block}
{openfang_block}
{robofang_block}
{ollama_block}
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
Write-Host "Full dev setup complete." -ForegroundColor Green
Stop-Transcript
"""


def _build_sandbox_xml_dev_setup(
    host_folder: str, memory_mb: int = 4096, vgpu: bool = True, networking: bool = True
) -> str:
    """WSB: map assets/sandbox to C:\\Assets, run Run-DevSetup.cmd at logon.

    Microsoft samples put MappedFolders before LogonCommand. Using a .cmd launcher
    (rather than calling powershell -File directly) adds a startup delay for the
    mapped folder to stabilize and captures all output to Desktop/dev-setup.log.
    """
    import xml.sax.saxutils as sax

    host_escaped = sax.escape(host_folder)
    cmd_escaped = sax.escape(r"C:\Assets\Run-DevSetup.cmd")
    return f"""<Configuration>
<MappedFolders>
<MappedFolder>
<HostFolder>{host_escaped}</HostFolder>
<SandboxFolder>C:\\Assets</SandboxFolder>
<ReadOnly>false</ReadOnly>
</MappedFolder>
</MappedFolders>
<VGpu>{"Enable" if vgpu else "Disable"}</VGpu>
<Networking>{"Enable" if networking else "Disable"}</Networking>
<MemoryInMB>{memory_mb}</MemoryInMB>
<LogonCommand>
<Command>{cmd_escaped}</Command>
</LogonCommand>
</Configuration>"""


def _build_sandbox_xml_dev_infra(
    host_folder: str, memory_mb: int = 8192, vgpu: bool = True, networking: bool = True
) -> str:
    """WSB: map assets/sandbox to C:\\Assets, run Run-DevInfra.cmd at logon (cmd + short delay + powershell setup).

    Microsoft samples put MappedFolders before LogonCommand; LogonCommand is executed by cmd.exe — a small .cmd
    launcher is more reliable than calling powershell -File on a mapped .ps1 immediately at logon.
    """
    import xml.sax.saxutils as sax

    host_escaped = sax.escape(host_folder)
    cmd_escaped = sax.escape(r"C:\Assets\Run-DevInfra.cmd")
    return f"""<Configuration>
<MappedFolders>
<MappedFolder>
<HostFolder>{host_escaped}</HostFolder>
<SandboxFolder>C:\\Assets</SandboxFolder>
<ReadOnly>false</ReadOnly>
</MappedFolder>
</MappedFolders>
<VGpu>{"Enable" if vgpu else "Disable"}</VGpu>
<Networking>{"Enable" if networking else "Disable"}</Networking>
<MemoryInMB>{memory_mb}</MemoryInMB>
<LogonCommand>
<Command>{cmd_escaped}</Command>
</LogonCommand>
</Configuration>"""


# Models
class SandboxLaunchRequest(BaseModel):
    name: str
    config_xml: str
    full_dev_setup: bool | None = None
    dev_infra_setup: bool | None = None  # maps assets/sandbox, runs Setup-DevInfraSandbox.ps1 (no offline msix zip)
    assets_folder: str | None = None
    dev_tools: list[str] | None = None
    memory_in_mb: int | None = 4096
    vgpu: bool | None = True
    networking: bool | None = True
    airgap: bool | None = None  # if True: networking disabled (OpenClaw 100% safe, no egress)
    use_host_ollama: bool | None = None  # if True: set OLLAMA_HOST to host gateway so sandbox can use host Ollama


class VMCreateRequest(BaseModel):
    name: str
    template: str = "ubuntu-dev"
    memory_mb: int | None = None
    disk_gb: int | None = None
    cpus: int | None = None
    iso_path: str | None = None  # optional ISO from assets/vbox for first-boot install


class AttachIsoRequest(BaseModel):
    iso_path: str


class VMSnapshotRequest(BaseModel):
    snapshot_name: str
    description: str = ""


class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = []
    model: str | None = None


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = {}


# API Endpoints
@app.get("/health")
async def health_root():
    """Simple health for start.ps1 wait."""
    return {"status": "ok"}


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "mcp_connected": mcp is not None,
        "service_manager": service_manager is not None,
    }


@app.get("/api/v1/dashboard")
async def dashboard():
    """Aggregated dashboard data: host info, VMs, VBox status, sandbox."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service not available")
    try:
        host_info = await asyncio.to_thread(service_manager.vm_service.get_system_info)
        vbox_status = {"version": host_info.get("virtualbox", {}).get("version", "")} if host_info else {}
        # Get VMs
        vms = []
        try:
            vms_result = await asyncio.to_thread(service_manager.vm_service.list_vms, details=False)
            vms = (
                vms_result
                if isinstance(vms_result, list)
                else vms_result.get("vms", [])
                if isinstance(vms_result, dict)
                else []
            )
        except Exception:
            pass
        running = sum(1 for v in vms if v.get("state") == "running")
        stopped = sum(1 for v in vms if v.get("state") == "poweroff")
        paused = sum(1 for v in vms if v.get("state") == "paused")
        return {
            "host": host_info or {},
            "vms": {"total": len(vms), "running": running, "stopped": stopped, "paused": paused, "list": vms[:10]},
            "virtualbox": vbox_status or {},
        }
    except Exception as e:
        logger.error("Dashboard aggregation error: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


# ── API Key Management ─────────────────────────────────────────────────────────


def _load_keys() -> dict[str, str]:
    """Load saved API keys from keys.json."""
    try:
        if os.path.isfile(KEYS_FILE):
            with open(KEYS_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_keys(keys: dict[str, str]) -> None:
    """Save API keys to keys.json."""
    os.makedirs(os.path.dirname(KEYS_FILE), exist_ok=True)
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)


def _mask_key(key: str) -> str:
    """Return masked key showing first 8 + last 4 chars."""
    if len(key) < 16:
        return key[:4] + "..." + key[-4:] if len(key) > 8 else "****"
    return key[:8] + "..." + key[-4:]


KEY_DEFINITIONS = [
    {"id": "DEEPSEEK_API_KEY", "label": "DeepSeek", "link": "https://platform.deepseek.com/api_keys"},
    {"id": "ANTHROPIC_API_KEY", "label": "Anthropic (Claude)", "link": "https://console.anthropic.com/settings/keys"},
    {"id": "GOOGLE_API_KEY", "label": "Google (Gemini)", "link": "https://aistudio.google.com/app/apikey"},
    {"id": "OPENAI_API_KEY", "label": "OpenAI", "link": "https://platform.openai.com/api-keys"},
]


class ApiKeysRequest(BaseModel):
    keys: dict[str, str]  # full key values to save


class ApiKeysResponse(BaseModel):
    keys: dict[str, str]  # masked key values for display


@app.get("/api/v1/settings/keys")
async def get_api_keys():
    """Return masked API keys for display."""
    saved = _load_keys()
    masked = {}
    for kd in KEY_DEFINITIONS:
        kid = kd["id"]
        val = saved.get(kid) or os.environ.get(kid, "")
        masked[kid] = _mask_key(val) if val else ""
    return {"keys": masked, "definitions": KEY_DEFINITIONS}


@app.post("/api/v1/settings/keys")
async def set_api_keys(request: ApiKeysRequest):
    """Save API keys. Also sets them in os.environ for the current process."""
    current = _load_keys()
    for kid, val in request.keys.items():
        if val:
            current[kid] = val
            os.environ[kid] = val  # live update for this process
        else:
            current.pop(kid, None)
            os.environ.pop(kid, None)
    _save_keys(current)
    # Return masked
    masked = {k: _mask_key(v) if v else "" for k, v in current.items()}
    return {"keys": masked, "definitions": KEY_DEFINITIONS, "saved": True}


# ── LLM Provider Discovery ────────────────────────────────────────────────────


async def _check_ollama(endpoint: str) -> dict:
    """Check if Ollama is reachable and return its version + models."""
    import json as _json

    try:
        import urllib.request as _req

        r = _req.urlopen(f"{endpoint}/api/version", timeout=3)
        version_data = _json.loads(r.read())
        r2 = _req.urlopen(f"{endpoint}/api/tags", timeout=5)
        tags_data = _json.loads(r2.read())
        models = [{"name": m["name"], "size": m.get("size", 0)} for m in tags_data.get("models", [])]
        return {"available": True, "version": version_data.get("version", ""), "models": models}
    except Exception as e:
        return {"available": False, "error": str(e), "models": []}


async def _check_lm_studio(endpoint: str) -> dict:
    """Check if LM Studio is reachable and return its loaded models."""
    import json as _json

    try:
        import urllib.request as _req

        r = _req.urlopen(f"{endpoint}/v1/models", timeout=3)
        data = _json.loads(r.read())
        models = [{"name": m["id"], "size": m.get("owned_by", "")} for m in data.get("data", [])]
        return {"available": True, "version": "LM Studio", "models": models}
    except Exception as e:
        return {"available": False, "error": str(e), "models": []}


@app.get("/api/v1/settings/llm/providers")
async def llm_providers():
    """Check default Ollama and LM Studio endpoints, return what's available."""
    ollama, lm = await asyncio.gather(
        _check_ollama("http://localhost:11434"),
        _check_lm_studio("http://localhost:1234"),
        return_exceptions=True,
    )
    if isinstance(ollama, Exception):
        ollama = {"available": False, "error": str(ollama), "models": []}
    if isinstance(lm, Exception):
        lm = {"available": False, "error": str(lm), "models": []}
    return {"ollama": ollama, "lm_studio": lm}


@app.get("/api/v1/settings/llm/models")
async def llm_models(endpoint: str = "", provider: str = ""):
    """List models from a specific LLM provider endpoint."""
    if not provider:
        provider = "ollama" if "11434" in endpoint else "lm_studio"
    if provider == "ollama":
        return await _check_ollama(endpoint or "http://localhost:11434")
    return await _check_lm_studio(endpoint or "http://localhost:1234")


@app.get("/api/v1/status")
async def status():
    """Debug: backend init state for tools, VMs, apps."""
    registry_ok = os.path.isfile(REGISTRY_PATH) if REGISTRY_PATH else False
    return {
        "mcp": mcp is not None,
        "service_manager": service_manager is not None,
        "registry_file": REGISTRY_PATH,
        "registry_exists": registry_ok,
    }


@app.get("/api/v1/assets/paths")
async def get_assets_paths():
    """Return repo assets folder paths for sandbox and VBox reuse."""
    return {
        "repo_root": _repo_root,
        "assets_sandbox": ASSETS_SANDBOX,
        "assets_vbox": ASSETS_VBOX,
    }


@app.get("/api/v1/assets/vbox")
async def list_vbox_assets():
    """List ISO/OVA/OVF files in repo assets/vbox for reuse."""
    if not os.path.isdir(ASSETS_VBOX):
        return {"files": [], "assets_path": ASSETS_VBOX}
    files = []
    for name in os.listdir(ASSETS_VBOX):
        lower = name.lower()
        if lower.endswith((".iso", ".ova", ".ovf")):
            path = os.path.join(ASSETS_VBOX, name)
            if os.path.isfile(path):
                files.append({"name": name, "path": path})
    files.sort(key=lambda x: x["name"])
    return {"files": files, "assets_path": ASSETS_VBOX}


# ── ISO Download Pipeline ──────────────────────────────────────────────────────
# In-memory download task tracker
_download_tasks: dict[str, dict[str, Any]] = {}
_download_lock = threading.Lock()

# Common Ubuntu releases (amd64 live-server)
ISO_CATEGORIES = [
    {
        "id": "ubuntu",
        "label": "Ubuntu",
        "items": [
            {
                "version": "24.04 LTS Server",
                "url": "https://releases.ubuntu.com/24.04/ubuntu-24.04.4-live-server-amd64.iso",
                "description": "Ubuntu Server 24.04 LTS — recommended for VMs",
                "size": "~2.6 GB",
            },
            {
                "version": "24.04 LTS Desktop",
                "url": "https://releases.ubuntu.com/24.04/ubuntu-24.04.4-desktop-amd64.iso",
                "description": "Ubuntu Desktop 24.04 LTS — full GUI",
                "size": "~5.7 GB",
            },
            {
                "version": "22.04 LTS Server",
                "url": "https://releases.ubuntu.com/22.04/ubuntu-22.04.5-live-server-amd64.iso",
                "description": "Ubuntu Server 22.04 LTS — stable, long support",
                "size": "~2.6 GB",
            },
            {
                "version": "22.04 LTS Desktop",
                "url": "https://releases.ubuntu.com/22.04/ubuntu-22.04.5-desktop-amd64.iso",
                "description": "Ubuntu Desktop 22.04 LTS",
                "size": "~4.6 GB",
            },
            {
                "version": "25.04 Server",
                "url": "https://releases.ubuntu.com/25.04/ubuntu-25.04-live-server-amd64.iso",
                "description": "Ubuntu Server 25.04 — latest release",
                "size": "~2.8 GB",
            },
        ],
    },
    {
        "id": "debian",
        "label": "Debian",
        "items": [
            {
                "version": "Debian 12 Bookworm",
                "url": "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-12.9.0-amd64-netinst.iso",
                "description": "Debian 12 netinstall — minimal, rock-solid",
                "size": "~700 MB",
            },
            {
                "version": "Debian 12 Live XFCE",
                "url": "https://cdimage.debian.org/debian-cd/current-live/amd64/iso-cd/debian-live-12.9.0-amd64-xfce.iso",
                "description": "Debian 12 with XFCE desktop",
                "size": "~3.1 GB",
            },
        ],
    },
    {
        "id": "windows",
        "label": "Windows",
        "items": [
            {
                "version": "Windows 11 24H2 (eval)",
                "url": "https://software-static.download.prss.microsoft.com/dbazure/988969d5-f34g-4e03-ac9d-1f9786c66751/26100.1742.240906-0331.ge_release_svc_refresh_CLIENTENTERPRISEEVAL_OEMRET_x64FRE_en-us.iso",
                "description": "Windows 11 Enterprise Evaluation — 90-day trial",
                "size": "~6.4 GB",
            },
            {
                "version": "Windows 10 22H2 (eval)",
                "url": "https://software-static.download.prss.microsoft.com/sg/download/888969d5-f34g-4e03-ac9d-1f9786c66751/19045.2006.220908-0225.22h2_release_svc_refresh_CLIENTENTERPRISEEVAL_OEMRET_x64FRE_en-us.iso",
                "description": "Windows 10 Enterprise Evaluation — 90-day trial",
                "size": "~5.8 GB",
            },
            {
                "version": "Windows Server 2025 (eval)",
                "url": "https://software-static.download.prss.microsoft.com/dbazure/888969d5-f34g-4e03-ac9d-1f9786c66749/26100.1742.240906-0331.ge_release_svc_refresh_SERVER_EVAL_x64FRE_en-us.iso",
                "description": "Windows Server 2025 Evaluation — 180-day trial",
                "size": "~6.0 GB",
            },
        ],
    },
    {
        "id": "utilities",
        "label": "Utilities",
        "items": [
            {
                "version": "GParted Live",
                "url": "https://downloads.sourceforge.net/gparted/gparted-live-1.6.0-1-amd64.iso",
                "description": "Partition manager — resize, repair, recover disks",
                "size": "~550 MB",
            },
            {
                "version": "SystemRescue 11",
                "url": "https://downloads.sourceforge.net/systemrescue/systemrescue-11.02-amd64.iso",
                "description": "System rescue toolkit — fsck, backup, network tools",
                "size": "~850 MB",
            },
            {
                "version": "Hiren's Boot CD PE",
                "url": "https://archive.org/download/hirens-boot-cd-pe-x64-2023/Hirens.Boot.CD.PE.x64.2023.iso",
                "description": "All-in-one diagnostics and recovery environment",
                "size": "~2.0 GB",
            },
            {
                "version": "Clonezilla Live",
                "url": "https://downloads.sourceforge.net/clonezilla/clonezilla-live-3.1.3-9-amd64.iso",
                "description": "Disk cloning and imaging — bare-metal backup",
                "size": "~450 MB",
            },
        ],
    },
    {
        "id": "safety",
        "label": "Safety Tools",
        "items": [
            {
                "version": "Kali Linux 2024",
                "url": "https://cdimage.kali.org/kali-2024.4/kali-linux-2024.4-installer-amd64.iso",
                "description": "Penetration testing and security auditing distro",
                "size": "~4.6 GB",
            },
            {
                "version": "Kali Linux Live (2024)",
                "url": "https://cdimage.kali.org/kali-2024.4/kali-linux-2024.4-live-amd64.iso",
                "description": "Kali live environment — no install needed",
                "size": "~4.2 GB",
            },
            {
                "version": "Security Onion 2",
                "url": "https://download.securityonion.net/file/securityonion/securityonion-2.4.110-20240805.iso",
                "description": "IDS/IPS, SIEM, and security monitoring platform",
                "size": "~9.0 GB",
            },
        ],
    },
]


def _download_iso_worker(task_id: str, url: str, dest: str) -> None:
    """Download ISO in a background thread with progress tracking."""
    with _download_lock:
        if task_id in _download_tasks:
            _download_tasks[task_id]["status"] = "connecting"
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "virtualization-mcp/1.0"})
        with _download_lock:
            if task_id in _download_tasks:
                _download_tasks[task_id]["status"] = "downloading"
        # Follow redirects (Ubuntu releases use redirects)
        opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
        with opener.open(req, timeout=300) as response:
            total = int(response.headers.get("Content-Length", 0))
            chunk_size = 65536
            downloaded = 0
            with open(dest, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    with _download_lock:
                        if task_id in _download_tasks:
                            t = _download_tasks[task_id]
                            t["downloaded"] = downloaded
                            t["total"] = total
                            t["progress"] = round(downloaded / max(total, 1) * 100, 1)
                            t["human_size"] = _human_bytes(downloaded)
        with _download_lock:
            if task_id in _download_tasks:
                _download_tasks[task_id].update(status="completed", progress=100.0, file_path=dest)
    except Exception as e:
        logger.error("ISO download failed for %s: %s", url, e)
        with _download_lock:
            if task_id in _download_tasks:
                _download_tasks[task_id].update(status="failed", error=str(e))
        try:
            if os.path.exists(dest):
                os.remove(dest)
        except Exception:
            pass


def _human_bytes(n: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


class IsoDownloadRequest(BaseModel):
    url: str
    filename: str | None = None  # optional override, else derived from URL


@app.get("/api/v1/iso/candidates")
async def iso_candidates():
    """List downloadable Ubuntu ISO candidates."""
    return {"categories": ISO_CATEGORIES, "assets_vbox": ASSETS_VBOX}


@app.post("/api/v1/iso/download")
async def iso_download(request: IsoDownloadRequest):
    """Start downloading an ISO to assets/vbox in the background."""
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    filename = request.filename or os.path.basename(url.split("?")[0])
    if not filename.lower().endswith(".iso"):
        filename += ".iso"

    dest = os.path.join(ASSETS_VBOX, filename)
    task_id = f"dl_{int(time.time())}_{filename}"

    with _download_lock:
        _download_tasks[task_id] = {
            "task_id": task_id,
            "url": url,
            "filename": filename,
            "dest": dest,
            "status": "queued",
            "progress": 0.0,
            "downloaded": 0,
            "total": 0,
            "human_size": "0 B",
            "error": None,
            "file_path": None,
        }

    thread = threading.Thread(target=_download_iso_worker, args=(task_id, url, dest), daemon=True)
    thread.start()

    return {"task_id": task_id, "filename": filename, "dest": dest, "status": "starting"}


@app.get("/api/v1/iso/download/{task_id}")
async def iso_download_status(task_id: str):
    """Poll the status of an ISO download task."""
    with _download_lock:
        task = _download_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Download task not found")
    return task


@app.get("/api/v1/iso/downloads")
async def iso_downloads_list():
    """List all download tasks (active and completed)."""
    with _download_lock:
        tasks = list(_download_tasks.values())
    return {"tasks": tasks}


# FastMCP 3.1 prompts and skills (for webapp page)
PROMPTS_META = [
    {
        "name": "virtualization_expert",
        "description": "Load instructions for acting as a virtualization expert using this MCP server's tools (VMs, snapshots, storage, networking).",
        "arguments": [
            {
                "name": "focus",
                "default": "general",
                "description": "Focus area: general, lifecycle, storage, or network",
            }
        ],
    },
]


def _get_skills_dir():
    try:
        from pathlib import Path

        import virtualization_mcp

        return Path(virtualization_mcp.__file__).resolve().parent / "skills"
    except Exception:
        return None


@app.get("/api/v1/prompts")
async def list_prompts():
    """List FastMCP 3.1 prompts (metadata for webapp)."""
    return {"prompts": PROMPTS_META}


@app.get("/api/v1/skills")
async def list_skills():
    """List FastMCP 3.1 skills (bundled skill dirs with SKILL.md)."""
    skills_dir = _get_skills_dir()
    if not skills_dir or not skills_dir.is_dir():
        return {"skills": []}
    out = []
    for path in skills_dir.iterdir():
        if path.is_dir():
            skill_md = path / "SKILL.md"
            if skill_md.is_file():
                name = path.name.replace("-", " ").title()
                desc = ""
                try:
                    raw = skill_md.read_text(encoding="utf-8")
                    if raw.startswith("---"):
                        end = raw.find("---", 3)
                        if end != -1:
                            for line in raw[4:end].strip().splitlines():
                                if line.startswith("description:"):
                                    desc = line.split(":", 1)[1].strip().strip('"')
                                    break
                except Exception:
                    pass
                out.append({"id": path.name, "name": name, "description": desc or name})
    return {"skills": out}


@app.get("/api/v1/skills/{skill_id}")
async def get_skill_content(skill_id: str):
    """Return markdown content for a skill (FastMCP 3.1)."""
    skills_dir = _get_skills_dir()
    if not skills_dir or not skills_dir.is_dir():
        raise HTTPException(status_code=404, detail="Skills not available")
    safe_id = "".join(c for c in skill_id if c.isalnum() or c == "-")
    skill_path = skills_dir / safe_id / "SKILL.md"
    if not skill_path.is_file():
        raise HTTPException(status_code=404, detail="Skill not found")
    try:
        return {"id": safe_id, "content": skill_path.read_text(encoding="utf-8")}
    except Exception as e:
        logger.error("Error reading skill %s: %s", safe_id, e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/vms")
async def get_vms():
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")

    try:
        # Get VirtualBox VMs
        vbox_vms = await asyncio.to_thread(service_manager.vm_service.list_vms, details=True)
        vbox_list = vbox_vms.get("vms", [])
        for vm in vbox_list:
            vm["provider"] = "virtualbox"

        # Get Hyper-V VMs
        hyperv_list = []
        if hasattr(service_manager.vm_service, "hyperv_manager"):
            hyperv_list = await service_manager.vm_service.hyperv_manager.list_vms()

        return {"status": "success", "vms": vbox_list + hyperv_list}
    except Exception as e:
        logger.error(f"Error fetching VMs: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/vbox/status")
async def vbox_status():
    """Return whether VirtualBox is available (required for VMs, snapshots, networks)."""
    available = service_manager is not None
    return {
        "available": available,
        "message": None
        if available
        else "VirtualBox not detected. Install VirtualBox and ensure VBoxManage is in PATH, or open VirtualBox once.",
    }


@app.post("/api/v1/vbox/launch")
async def vbox_launch():
    """Try to launch the VirtualBox GUI. Helps ensure the VirtualBox service is running."""
    import platform
    import shutil

    vbox_exe = None
    if platform.system() == "Windows":
        for path in [
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Oracle", "VirtualBox", "VirtualBox.exe"),
            os.path.join(
                os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Oracle", "VirtualBox", "VirtualBox.exe"
            ),
        ]:
            if os.path.isfile(path):
                vbox_exe = path
                break
    elif shutil.which("VirtualBox"):
        vbox_exe = shutil.which("VirtualBox")
    elif os.path.isfile("/usr/bin/VirtualBox"):
        vbox_exe = "/usr/bin/VirtualBox"
    elif os.path.isdir("/Applications/VirtualBox.app"):
        vbox_exe = "open"
        args = ["/Applications/VirtualBox.app"]
    if not vbox_exe:
        return {"success": False, "message": "VirtualBox executable not found in standard locations."}
    try:
        if vbox_exe == "open":
            await asyncio.create_subprocess_exec(
                "open", *args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )
        else:
            kwargs = {"stdout": asyncio.subprocess.DEVNULL, "stderr": asyncio.subprocess.DEVNULL}
            if sys.platform == "win32":
                kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
            await asyncio.create_subprocess_exec(vbox_exe, **kwargs)
        return {"success": True, "message": "VirtualBox launch initiated."}
    except Exception as e:
        logger.error("vbox_launch error: %s", e)
        return {"success": False, "message": str(e)}


@app.get("/api/v1/host/info")
async def get_host_info():
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")

    try:
        info_result = await asyncio.to_thread(service_manager.vm_service.get_system_info)
        return info_result
    except Exception as e:
        logger.error(f"Error fetching system info: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/sandbox/dev-setup-script")
async def get_dev_setup_script(tools: str | None = None, use_host_ollama: bool | None = None):
    """Return PowerShell script for full dev setup in Sandbox. Query: tools (comma-separated), use_host_ollama (true/false)."""
    tool_list = (
        [t.strip() for t in (tools or "").split(",") if t.strip()] if tools else list(SANDBOX_DEV_SETUP_TOOLS.keys())
    )
    script = _get_dev_setup_script(tool_list, use_host_ollama=bool(use_host_ollama))
    return {"script": script, "tools": tool_list}


@app.get("/api/v1/sandbox/wsb-preview")
async def sandbox_wsb_preview(
    preset: str = "dev-infra",
    assets_folder: str | None = None,
    memory_in_mb: int = 8192,
    vgpu: bool = True,
    networking: bool = True,
):
    """Return WSB XML for download or UI preview. preset=dev-infra (default) or full-dev."""
    p = (preset or "dev-infra").lower().strip()
    mem = int(memory_in_mb) if memory_in_mb else 8192
    if p == "dev-infra":
        folder = (assets_folder or "").strip() or ASSETS_SANDBOX
        if not os.path.isdir(folder):
            raise HTTPException(status_code=400, detail=f"Assets folder does not exist: {folder}")
        for required in ("Setup-DevInfraSandbox.ps1", "Run-DevInfra.cmd", "Show-DevInfraLog.ps1"):
            rp = os.path.join(folder, required)
            if not os.path.isfile(rp):
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing {required} in {folder}. Use virtualization-mcp assets/sandbox.",
                )
        xml = _build_sandbox_xml_dev_infra(folder, memory_mb=mem, vgpu=vgpu, networking=networking)
        return {"xml": xml, "preset": p, "assets_folder": folder, "filename": "DevInfra.wsb"}
    if p == "full-dev":
        folder = (assets_folder or "").strip()
        if not folder or not os.path.isdir(folder):
            raise HTTPException(
                status_code=400,
                detail="full-dev requires assets_folder query parameter (existing host directory with offline winget assets).",
            )
        xml = _build_sandbox_xml_dev_setup(folder, memory_mb=mem, vgpu=vgpu, networking=networking)
        return {"xml": xml, "preset": p, "assets_folder": folder, "filename": "FullDev.wsb"}
    raise HTTPException(status_code=400, detail="Unknown preset (use dev-infra or full-dev).")


@app.get("/api/v1/sandbox/status")
async def sandbox_status():
    """Check if Windows Sandbox is currently running."""
    running = False
    import subprocess as _sub
    try:
        r = _sub.run(
            ["tasklist", "/FI", "IMAGENAME eq WindowsSandbox.exe", "/NH", "/FO", "CSV"],
            capture_output=True, text=True, timeout=5,
        )
        running = "WindowsSandbox.exe" in r.stdout
    except Exception:
        pass
    return {"running": running}


@app.post("/api/v1/sandbox/launch")
async def launch_sandbox(request: SandboxLaunchRequest):
    """Launch Windows Sandbox. Use config_xml for manual XML, or full_dev_setup + assets_folder for auto dev stack."""
    try:
        if getattr(request, "full_dev_setup", None) and getattr(request, "assets_folder", None):
            assets_folder = request.assets_folder.strip()
            if not os.path.isdir(assets_folder):
                raise HTTPException(status_code=400, detail=f"Assets folder does not exist: {assets_folder}")
            airgap = getattr(request, "airgap", None) or False
            use_host_ollama = getattr(request, "use_host_ollama", None) or False
            if airgap:
                networking = False
            elif use_host_ollama:
                networking = True
            else:
                networking = request.networking if request.networking is not None else True
            script_path = os.path.join(assets_folder, "Setup-DevSandbox.ps1")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(
                    _get_dev_setup_script(
                        request.dev_tools or list(SANDBOX_DEV_SETUP_TOOLS.keys()),
                        use_host_ollama=use_host_ollama,
                    )
                )
            # Write .cmd launcher (delay + log capture)
            cmd_path = os.path.join(assets_folder, "Run-DevSetup.cmd")
            with open(cmd_path, "w", encoding="utf-8") as f:
                f.write(
                    '@echo off\r\n'
                    'set "LOG=%USERPROFILE%\\Desktop\\dev-setup.log"\r\n'
                    'echo [%DATE% %TIME%] Run-DevSetup.cmd starting > "%LOG%"\r\n'
                    'if exist "C:\\Assets\\Run-DevSetup.cmd" ( echo [%DATE% %TIME%] C:\\Assets mapped OK >> "%LOG%" ) else ( echo [%DATE% %TIME%] C:\\Assets NOT MAPPED >> "%LOG%" )\r\n'
                    'dir "C:\\Assets" >> "%LOG%" 2>&1\r\n'
                    'echo [%DATE% %TIME%] Waiting 5s... >> "%LOG%"\r\n'
                    'ping -n 6 127.0.0.1 > nul\r\n'
                    'if exist "C:\\Assets\\Setup-DevSandbox.ps1" (\r\n'
                    '    echo [%DATE% %TIME%] Starting Setup-DevSandbox.ps1 >> "%LOG%"\r\n'
                    '    powershell -ExecutionPolicy Bypass -File "C:\\Assets\\Setup-DevSandbox.ps1" >> "%LOG%" 2>&1\r\n'
                    '    echo [%DATE% %TIME%] Exit code %ERRORLEVEL% >> "%LOG%"\r\n'
                    ') else (\r\n'
                    '    echo [%DATE% %TIME%] ERROR: Setup-DevSandbox.ps1 NOT FOUND >> "%LOG%"\r\n'
                    ')\r\n'
                    'echo @echo off > "%USERPROFILE%\\Desktop\\View Setup Log.cmd"\r\n'
                    'echo type "%LOG%" >> "%USERPROFILE%\\Desktop\\View Setup Log.cmd"\r\n'
                    'echo echo. >> "%USERPROFILE%\\Desktop\\View Setup Log.cmd"\r\n'
                    'echo pause >> "%USERPROFILE%\\Desktop\\View Setup Log.cmd"\r\n'
                    'start "" cmd.exe /c "title Dev Setup Log & powershell -NoExit -Command Get-Content -Wait \'%LOG%\'"\r\n'
                )
            config_xml = _build_sandbox_xml_dev_setup(
                assets_folder,
                memory_mb=request.memory_in_mb or 4096,
                vgpu=request.vgpu if request.vgpu is not None else True,
                networking=networking,
            )
        elif getattr(request, "dev_infra_setup", None):
            raw = getattr(request, "assets_folder", None) or ""
            host_folder = raw.strip() if isinstance(raw, str) else ""
            if not host_folder:
                host_folder = ASSETS_SANDBOX
            if not os.path.isdir(host_folder):
                raise HTTPException(status_code=400, detail=f"Assets folder does not exist: {host_folder}")
            for required in ("Setup-DevInfraSandbox.ps1", "Run-DevInfra.cmd", "Show-DevInfraLog.ps1"):
                rp = os.path.join(host_folder, required)
                if not os.path.isfile(rp):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing {required} in {host_folder}",
                    )
            mem = request.memory_in_mb if request.memory_in_mb is not None else 8192
            net = request.networking if request.networking is not None else True
            vg = request.vgpu if request.vgpu is not None else True
            config_xml = _build_sandbox_xml_dev_infra(host_folder, memory_mb=mem, vgpu=vg, networking=net)
        else:
            config_xml = request.config_xml

        with tempfile.NamedTemporaryFile(
            suffix=".wsb", delete=False, mode="w", encoding="utf-8", newline="\r\n"
        ) as tmp:
            tmp.write(config_xml)
            tmp_path = tmp.name

        logger.info("Launching sandbox with config: %s", tmp_path)
        wsb_exe = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32", "WindowsSandbox.exe")
        if os.path.isfile(wsb_exe):
            await asyncio.create_subprocess_exec(
                wsb_exe,
                tmp_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        else:
            await asyncio.create_subprocess_shell(
                f'start "" "{tmp_path}"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        return {
            "status": "success",
            "message": "Windows Sandbox launch initiated",
            "temp_file": tmp_path,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error launching sandbox: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/apps")
async def get_apps():
    """Get all webapps from the central registry."""
    if not os.path.exists(REGISTRY_PATH):
        logger.error(f"Registry not found at {REGISTRY_PATH}")
        return {"webapps": []}

    try:
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception as e:
        logger.error(f"Error reading registry: {e}")
        return {"webapps": []}


@app.post("/api/v1/chat")
async def chat_interaction(request: ChatRequest):
    """Handle AI chat using local LLM (Ollama/LM Studio) or Gemini fallback."""
    import json as _json
    import urllib.request as _req

    prefix = "You are the SOTA Virtualization Assistant. You help manage VMs, Sandboxes, and the MCP Fleet.\nUser: "

    # Try Ollama first
    try:
        ollama_payload = _json.dumps(
            {
                "model": request.model or "llama3.2",
                "messages": [{"role": "user", "content": prefix + request.message}],
                "stream": False,
            }
        ).encode()
        oreq = _req.Request(
            "http://localhost:11434/api/chat",
            data=ollama_payload,
            headers={"Content-Type": "application/json"},
        )
        with _req.urlopen(oreq, timeout=60) as r:
            data = _json.loads(r.read())
            reply = data.get("message", {}).get("content", "")
            if reply:
                return {"reply": reply, "provider": "ollama"}
    except Exception:
        pass

    # Fallback: LM Studio
    try:
        lm_payload = _json.dumps(
            {
                "messages": [{"role": "user", "content": prefix + request.message}],
                "max_tokens": 1024,
                "stream": False,
            }
        ).encode()
        lreq = _req.Request(
            "http://localhost:1234/v1/chat/completions",
            data=lm_payload,
            headers={"Content-Type": "application/json"},
        )
        with _req.urlopen(lreq, timeout=60) as r:
            data = _json.loads(r.read())
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if reply:
                return {"reply": reply, "provider": "lm_studio"}
    except Exception:
        pass

    # Fallback: Gemini (if configured)
    if chat_model:
        try:
            response = await asyncio.to_thread(chat_model.generate_content, prefix + request.message)
            return {"reply": response.text, "provider": "gemini"}
        except Exception as e:
            logger.error("Gemini chat error: %s", e)

    return {
        "reply": "No LLM provider available. Start Ollama (`ollama serve`), LM Studio, or set GOOGLE_API_KEY.",
        "provider": None,
    }


@app.post("/api/v1/vms/{name}/start")
async def start_vm(name: str, request: Request):
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")

    # Check if provider is specified in query or body
    provider = request.query_params.get("provider", "virtualbox")

    try:
        if provider == "hyperv":
            result = await service_manager.vm_service.hyperv_manager.start_vm(name)
        else:
            result = await asyncio.to_thread(service_manager.vm_service.start_vm, name)
        return result
    except Exception as e:
        logger.error(f"Error starting VM {name} ({provider}): {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/vms/{name}/stop")
async def stop_vm(name: str, request: Request):
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")

    provider = request.query_params.get("provider", "virtualbox")

    try:
        if provider == "hyperv":
            result = await service_manager.vm_service.hyperv_manager.stop_vm(name)
        else:
            result = await asyncio.to_thread(service_manager.vm_service.stop_vm, name)
        return result
    except Exception as e:
        logger.error(f"Error stopping VM {name} ({provider}): {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/vms/{name}/pause")
async def pause_vm(name: str, request: Request):
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")

    provider = request.query_params.get("provider", "virtualbox")

    try:
        if provider == "hyperv":
            result = await service_manager.vm_service.hyperv_manager.pause_vm(name)
        else:
            # Check current state first
            info = await asyncio.to_thread(service_manager.vm_service.vbox_manager.get_vm_info, name)
            state = info.get("VMState", "").lower()

            if state == "running":
                result = await asyncio.to_thread(service_manager.vm_service.vbox_manager.pause_vm, name)
                result = {
                    "status": "success",
                    "message": f"VM {name} paused",
                    "result": result,
                }
            else:
                result = {
                    "status": "error",
                    "message": f"VM {name} is in state {state}, cannot pause",
                }
        return result
    except Exception as e:
        logger.error(f"Error pausing VM {name} ({provider}): {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/vms/{name}/resume")
async def resume_vm(name: str, request: Request):
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")

    provider = request.query_params.get("provider", "virtualbox")

    try:
        if provider == "hyperv":
            result = await service_manager.vm_service.hyperv_manager.resume_vm(name)
        else:
            result = await asyncio.to_thread(service_manager.vm_service.vbox_manager.resume_vm, name)
            result = {
                "status": "success",
                "message": f"VM {name} resumed",
                "result": result,
            }
        return result
    except Exception as e:
        logger.error(f"Error resuming VM {name} ({provider}): {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/vms/{name}/snapshot")
async def create_snapshot(name: str, request: VMSnapshotRequest):
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")
    try:
        result = await asyncio.to_thread(
            service_manager.vm_service.create_snapshot,
            name,
            request.snapshot_name,
            request.description,
        )
        return result
    except Exception as e:
        logger.error(f"Error creating snapshot for VM {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/vms")
async def create_vm(request: VMCreateRequest):
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")
    try:
        result = await asyncio.to_thread(
            service_manager.vm_service.create_vm,
            name=request.name,
            template=request.template,
            memory_mb=request.memory_mb,
            disk_gb=request.disk_gb,
            cpus=request.cpus,
        )
        if request.iso_path and os.path.isfile(request.iso_path.strip()):
            await asyncio.to_thread(
                service_manager.vm_service.attach_iso,
                vm_name=request.name,
                iso_path=os.path.abspath(request.iso_path.strip()),
            )
            result["iso_attached"] = request.iso_path.strip()
        return result
    except Exception as e:
        logger.error(f"Error creating VM {request.name}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/vms/{vm_name}/attach-iso")
async def attach_iso_to_vm(vm_name: str, request: AttachIsoRequest):
    """Attach an ISO to a VM (e.g. path from assets/vbox)."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")
    iso_path = (request.iso_path or "").strip()
    if not iso_path or not os.path.isfile(iso_path):
        raise HTTPException(status_code=400, detail="iso_path must be an existing file")
    try:
        result = await asyncio.to_thread(
            service_manager.vm_service.attach_iso,
            vm_name=vm_name,
            iso_path=os.path.abspath(iso_path),
        )
        return result
    except Exception as e:
        logger.error(f"Error attaching ISO to {vm_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest):
    """Execute an MCP tool."""
    if not mcp:
        raise HTTPException(status_code=503, detail="MCP Server not available")

    try:
        # Note: Tool calling logic depends on FastMCP internal structure
        # This is a SOTA implementation detail
        result = await mcp.call_tool(request.name, request.arguments)
        return {"result": result}
    except Exception as e:
        logger.error(f"Tool call error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Mount MCP Server over HTTP (FastMCP feature)
async def _list_tools_impl():
    if not mcp:
        raise HTTPException(status_code=503, detail="MCP Server not available")
    try:
        raw = mcp.list_tools()
        if asyncio.iscoroutine(raw):
            raw = await raw
        if isinstance(raw, list):
            return [getattr(t, "name", t) if not isinstance(t, str) else t for t in raw]
        return [getattr(tool, "name", str(tool)) for tool in raw]
    except Exception as e:
        logger.error("list_tools error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/tools")
async def list_tools_alias():
    return await _list_tools_impl()


@app.get("/mcp/tools")
async def list_tools():
    return await _list_tools_impl()


@app.get("/api/v1/vms/{name}/screenshot")
async def get_vm_screenshot(name: str):
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")
    try:
        # Use VBoxManage to take a screenshot
        # VBoxManage controlvm <name> screenshotpng <filename>
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # We need to run this on the host
            process = await asyncio.create_subprocess_exec(
                "VBoxManage",
                "controlvm",
                name,
                "screenshotpng",
                tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _stdout, stderr = await process.communicate()

            if process.returncode != 0:
                # If it's not a VBox VM, or VBox fails, check if we can do something for Hyper-V
                # Hyper-V doesn't have a direct "screenshot" CLI as easily as VBox
                raise Exception(stderr.decode())

            from fastapi.responses import FileResponse

            return FileResponse(tmp_path, media_type="image/png")
        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            logger.debug("Screenshot failed for VM %s: %s", name, e)
            raise HTTPException(
                status_code=501,
                detail=(f"Screenshot capture is under construction for this VM/provider: {e!s}"),
            ) from e

    except Exception as e:
        logger.debug("Screenshot helper error for VM %s: %s", name, e)
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10761, reload=True)
