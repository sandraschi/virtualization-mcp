# ruff: noqa: S105,S110,S310,S602,B904,F821,RUF005,F841,S104
# ^ intentional: S105(password defaults), S110(cleanup excepts),
#   S310(LLM/ISO URL fetch), S602(start fleet app),
#   B904(HTTPException re-raises), F821(C# string literal),
#   RUF005(list concat readability)

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
from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from virtualization_mcp.chat import ChatService

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
CONSUMER_SANDBOX_FILES = (
    "Setup-ConsumerSandbox.ps1",
    "Run-Consumer.cmd",
    "Show-ConsumerLog.ps1",
    os.path.join("lib", "Winget-Bootstrap.ps1"),
)
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


# Registry Path (optional — may not exist in PyInstaller or on other machines)
REGISTRY_PATH = os.environ.get("REGISTRY_PATH", "") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "..",
    "..",
    "mcp-central-docs",
    "operations",
    "webapp-registry.json",
)
if not os.path.exists(REGISTRY_PATH):
    REGISTRY_PATH = ""

# Initialize Gemini (optional)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
chat_model = None
if genai and GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    chat_model = genai.GenerativeModel("gemini-3.5-flash")
elif not genai:
    logger.warning("google-generativeai not installed. Chat will be disabled.")
elif not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY not found; chat will be in limited mode.")

app = FastAPI(title="Virtualization MCP Backend", lifespan=lifespan)
chat_service = ChatService()

# CORS Configuration (frontend dev: 10700; backend: 10701; Tauri: tauri://localhost)
origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:10700,http://127.0.0.1:10700,http://goliath:10700,http://localhost:10760,http://goliath:10760,tauri://localhost,http://tauri.localhost,https://tauri.localhost",
).split(",")
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
# Claude Desktop: use MSIX for silent/headless install
SANDBOX_DEV_SETUP_DOWNLOAD = {
    "claude_desktop": ("https://claude.ai/api/desktop/win32/x64/msix/latest/redirect", "Claude.msix"),
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
        f'$wingetArgs = @("install", "-e", "--id", "{wid}", "--source", "winget", "--accept-package-agreements", "--accept-source-agreements")\n& winget @wingetArgs\nif ($LASTEXITCODE -ne 0) {{ Write-Host "winget {wid} failed." -ForegroundColor Red; exit 1 }}'
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
    Write-Host "Downloading Claude Desktop (MSIX)..." -ForegroundColor Yellow
$claudeMsix = Join-Path $env:TEMP "{name}"
try {{
    Invoke-WebRequest -Uri "{url}" -OutFile $claudeMsix -UseBasicParsing
    Write-Host "Installing Claude Desktop (headless MSIX)..." -ForegroundColor Yellow
    Add-AppxPackage -Path $claudeMsix -ErrorAction Stop
    Write-Host "Claude Desktop installed." -ForegroundColor Green
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
    return """# Setup-DevSandbox.ps1 - Full dev stack in Windows Sandbox (virtualization-mcp)
# Automatic: Python, Node, pip, uv/uvx, Git, VS Code, Just, Notepad++, Windsurf, Cursor, Antigravity, Claude Desktop, OpenClaw, OpenFang, RoboFang. Optional: host Ollama.
# Downloads winget from GitHub if not present, then installs dev tools via winget.

# Wait for mapped folder + network to stabilize
Write-Host "Waiting for environment to initialize..." -ForegroundColor Cyan
Start-Sleep 5

$logPath = "$env:USERPROFILE\\Desktop\\dev-setup-ps.log"
Start-Transcript -Path $logPath -Append

# 1) Check if winget already available
$haveWinget = $false
try {
    $null = (Get-Command winget -ErrorAction Stop)
    $haveWinget = $true
} catch {}

if (-not $haveWinget) {
    Write-Host "winget not found. Installing App Installer from GitHub..." -ForegroundColor Yellow

    $work = Join-Path $env:TEMP ('winget-bootstrap-' + [Guid]::NewGuid().ToString('N'))
    $null = New-Item -ItemType Directory -Path $work -Force

    $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/microsoft/winget-cli/releases/latest' -UseBasicParsing

    # Download deps zip
    $depsAsset = $null
    foreach ($a in $release.assets) { if ($a.name -eq 'DesktopAppInstaller_Dependencies.zip') { $depsAsset = $a; break } }
    if ($depsAsset) {
        Write-Host "Downloading dependencies (93 MB)..." -ForegroundColor Yellow
        $depsPath = Join-Path $work $depsAsset.name
        Invoke-WebRequest -Uri $depsAsset.browser_download_url -OutFile $depsPath -UseBasicParsing
        $depsDir = Join-Path $work 'deps'
        Expand-Archive -Path $depsPath -DestinationPath $depsDir -Force
        Get-ChildItem -Path $depsDir -Include '*.appx','*.msix','*.msixbundle' -Recurse | Sort-Object Name | ForEach-Object {
            try { Add-AppxPackage -Path $_.FullName -ErrorAction Stop } catch { Write-Host "  Skip: $($_.Name)" -ForegroundColor Yellow }
        }
    }

    # Download and install App Installer bundle
    foreach ($a in $release.assets) {
        if ($a.name -like 'Microsoft.DesktopAppInstaller_*.msixbundle') {
            Write-Host "Downloading App Installer..." -ForegroundColor Yellow
            $bundlePath = Join-Path $work $a.name
            Invoke-WebRequest -Uri $a.browser_download_url -OutFile $bundlePath -UseBasicParsing
            Add-AppxPackage -Path $bundlePath
            break
        }
    }

    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    $wingetDirs = @("$env:LOCALAPPDATA\\Microsoft\\WindowsApps", "$env:ProgramFiles\\winget")
    foreach ($dir in $wingetDirs) {
        if (Test-Path $dir -and $env:Path -notlike "*$dir*") { $env:Path = "$dir;$env:Path" }
    }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "winget still not found after install." -ForegroundColor Red
        exit 1
    }
    Write-Host "winget installed successfully." -ForegroundColor Green
}

# 2) Dev stack via winget
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


def _build_sandbox_xml_consumer(
    host_folder: str,
    memory_mb: int = 8192,
    vgpu: bool = True,
    networking: bool = True,
    install_claude_desktop: bool = False,
) -> str:
    """WSB: nearly-naked install test — winget bootstrap only, optional Claude MSIX fixture."""
    import xml.sax.saxutils as sax

    host_escaped = sax.escape(host_folder)
    if install_claude_desktop:
        cmd_raw = r'cmd.exe /c "set CONSUMER_INSTALL_CLAUDE=1&& C:\Assets\Run-Consumer.cmd"'
    else:
        cmd_raw = r"C:\Assets\Run-Consumer.cmd"
    cmd_escaped = sax.escape(cmd_raw)
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
    consumer_setup: bool | None = None  # nearly naked: winget bootstrap only; optional Claude fixture
    consumer_install_claude: bool | None = None
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
    provider: str = "virtualbox"  # "virtualbox" or "hyperv"
    network_mode: str | None = None  # nat, bridged, hostonly, intnet (default from template)
    unattended: bool | None = None  # if True, inject autoinstall/autounattend


class AttachIsoRequest(BaseModel):
    iso_path: str


class VMSnapshotRequest(BaseModel):
    snapshot_name: str
    description: str = ""


class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = []
    model: str | None = None
    personality: str | None = None


class RefinePromptRequest(BaseModel):
    prompt: str
    model: str | None = None


class VrdeRequest(BaseModel):
    enabled: bool = True
    port: int | None = None


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = {}


# ── Template / Network / Unattended Models ─────────────────────────────────


class TemplateUpdateRequest(BaseModel):
    name: str  # new template name (rename key)
    config: dict[str, Any]  # full template config


class VmNetworkRequest(BaseModel):
    adapter: int = 1
    mode: str = "nat"  # nat, bridged, hostonly, intnet, natnetwork, none
    host_only_if: str | None = None
    bridged_if: str | None = None
    intnet_name: str | None = None
    port_forwarding: list[dict[str, Any]] | None = None


class VmPortForwardRequest(BaseModel):
    name: str = "rule1"
    protocol: str = "tcp"  # tcp or udp
    host_port: int
    guest_port: int


class UnattendedRequest(BaseModel):
    os_type: str = "ubuntu"  # ubuntu or windows
    hostname: str = "vm"
    username: str = "user"
    password: str = "password"
    timezone: str = "Europe/Vienna"
    dev_tools: list[str] | None = None  # dev tool keys (python, git, node, etc.)
    use_host_ollama: bool = False  # set OLLAMA_HOST to host gateway


# ── Template Storage ─────────────────────────────────────────────────────


TEMPLATES_FILE = os.path.join(os.path.dirname(KEYS_FILE), "templates.json")


def _load_templates() -> dict[str, Any]:
    """Load user-created VM templates from JSON."""
    try:
        if os.path.isfile(TEMPLATES_FILE):
            with open(TEMPLATES_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_templates(data: dict[str, Any]) -> None:
    """Save user-created VM templates to JSON."""
    os.makedirs(os.path.dirname(TEMPLATES_FILE), exist_ok=True)
    with open(TEMPLATES_FILE, "w") as f:
        json.dump(data, f, indent=2)


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
    """Check default Ollama and LM Studio endpoints, and check API keys for cloud providers."""
    ollama, lm = await asyncio.gather(
        _check_ollama("http://localhost:11434"),
        _check_lm_studio("http://localhost:1234"),
        return_exceptions=True,
    )
    if isinstance(ollama, Exception):
        ollama = {"available": False, "error": str(ollama), "models": []}
    if isinstance(lm, Exception):
        lm = {"available": False, "error": str(lm), "models": []}

    saved_keys = _load_keys()

    def has_key(name: str) -> bool:
        return bool(saved_keys.get(name) or os.environ.get(name))

    openai = {
        "available": has_key("OPENAI_API_KEY"),
        "version": "Cloud API",
        "models": [{"name": "gpt-4o-mini", "size": ""}, {"name": "gpt-4o", "size": ""}],
    }
    deepseek = {
        "available": has_key("DEEPSEEK_API_KEY"),
        "version": "DeepSeek API",
        "models": [{"name": "deepseek-v4-flash", "size": ""}, {"name": "deepseek-v4-pro", "size": ""}],
    }
    anthropic = {
        "available": has_key("ANTHROPIC_API_KEY"),
        "version": "Anthropic API",
        "models": [{"name": "claude-3-5-sonnet-latest", "size": ""}, {"name": "claude-3-5-haiku-latest", "size": ""}],
    }
    gemini = {
        "available": has_key("GOOGLE_API_KEY"),
        "version": "Gemini API",
        "models": [{"name": "gemini-3.5-flash", "size": ""}, {"name": "gemini-1.5-pro", "size": ""}],
    }

    return {
        "ollama": ollama,
        "lm_studio": lm,
        "openai": openai,
        "deepseek": deepseek,
        "anthropic": anthropic,
        "gemini": gemini,
    }


@app.get("/api/v1/settings/llm/models")
async def llm_models(endpoint: str = "", provider: str = ""):
    """List models from a specific LLM provider endpoint."""
    if not provider:
        if "api.openai.com" in endpoint or "openai" in endpoint:
            provider = "openai"
        elif "deepseek" in endpoint:
            provider = "deepseek"
        elif "anthropic" in endpoint:
            provider = "anthropic"
        elif "googleapis.com" in endpoint:
            provider = "gemini"
        else:
            provider = "ollama" if "11434" in endpoint else "lm_studio"

    if provider == "openai":
        return {
            "available": True,
            "version": "Cloud API",
            "models": [{"name": "gpt-4o-mini", "size": ""}, {"name": "gpt-4o", "size": ""}],
        }
    if provider == "deepseek":
        return {
            "available": True,
            "version": "DeepSeek API",
            "models": [{"name": "deepseek-v4-flash", "size": ""}, {"name": "deepseek-v4-pro", "size": ""}],
        }
    if provider == "anthropic":
        return {
            "available": True,
            "version": "Anthropic API",
            "models": [
                {"name": "claude-3-5-sonnet-latest", "size": ""},
                {"name": "claude-3-5-haiku-latest", "size": ""},
            ],
        }
    if provider == "gemini":
        return {
            "available": True,
            "version": "Gemini API",
            "models": [{"name": "gemini-3.5-flash", "size": ""}, {"name": "gemini-1.5-pro", "size": ""}],
        }
    if provider == "ollama":
        return await _check_ollama(endpoint or "http://localhost:11434")
    return await _check_lm_studio(endpoint or "http://localhost:1234")


# ── Local LLM Settings, Logs, and Help ─────────────────────────────────────────

LLM_SETTINGS_FILE = os.path.join(os.path.dirname(KEYS_FILE), "llm_settings.json")


class LlmSettingsRequest(BaseModel):
    provider: str = "ollama"
    endpoint: str = "http://localhost:11434"
    model: str = "gemma4:e4b"
    gpu_accel: bool = True


def _load_llm_settings() -> dict[str, Any]:
    """Load saved LLM settings from llm_settings.json."""
    try:
        if os.path.isfile(LLM_SETTINGS_FILE):
            with open(LLM_SETTINGS_FILE, encoding="utf-8") as f:
                data = json.load(f)
                provider = data.get("provider", "ollama")
                endpoint = data.get("endpoint", "")

                # Auto-correct mismatched default ports
                if provider == "lm_studio" and "11434" in endpoint:
                    data["endpoint"] = endpoint.replace("11434", "1234")
                elif provider == "ollama" and "1234" in endpoint:
                    data["endpoint"] = endpoint.replace("1234", "11434")
                elif provider == "openai" and ("1234" in endpoint or "11434" in endpoint or not endpoint):
                    data["endpoint"] = "https://api.openai.com/v1"
                elif provider == "deepseek" and ("1234" in endpoint or "11434" in endpoint or not endpoint):
                    data["endpoint"] = "https://api.deepseek.com/v1"
                elif provider == "anthropic" and ("1234" in endpoint or "11434" in endpoint or not endpoint):
                    data["endpoint"] = "https://api.anthropic.com/v1"
                elif provider == "gemini" and ("1234" in endpoint or "11434" in endpoint or not endpoint):
                    data["endpoint"] = "https://generativelanguage.googleapis.com"
                elif not endpoint:
                    if provider == "ollama":
                        data["endpoint"] = "http://localhost:11434"
                    elif provider == "lm_studio":
                        data["endpoint"] = "http://localhost:1234"

                return data
    except Exception:
        pass
    return {
        "provider": "ollama",
        "endpoint": "http://localhost:11434",
        "model": "gemma4:e4b",
        "gpu_accel": True,
    }


def _save_llm_settings(settings: dict[str, Any]) -> None:
    """Save LLM settings to llm_settings.json."""
    os.makedirs(os.path.dirname(LLM_SETTINGS_FILE), exist_ok=True)
    with open(LLM_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


@app.get("/api/v1/settings/llm")
async def get_llm_settings():
    """Get the saved LLM configuration."""
    return _load_llm_settings()


@app.post("/api/v1/settings/llm")
async def set_llm_settings(request: LlmSettingsRequest):
    """Save LLM configuration."""
    data = request.dict()
    provider = data.get("provider", "ollama")
    endpoint = data.get("endpoint", "")

    # Auto-correct mismatched default ports on save
    if provider == "lm_studio" and "11434" in endpoint:
        data["endpoint"] = endpoint.replace("11434", "1234")
    elif provider == "ollama" and "1234" in endpoint:
        data["endpoint"] = endpoint.replace("1234", "11434")
    elif provider == "openai" and ("1234" in endpoint or "11434" in endpoint or not endpoint):
        data["endpoint"] = "https://api.openai.com/v1"
    elif provider == "deepseek" and ("1234" in endpoint or "11434" in endpoint or not endpoint):
        data["endpoint"] = "https://api.deepseek.com/v1"
    elif provider == "anthropic" and ("1234" in endpoint or "11434" in endpoint or not endpoint):
        data["endpoint"] = "https://api.anthropic.com/v1"
    elif provider == "gemini" and ("1234" in endpoint or "11434" in endpoint or not endpoint):
        data["endpoint"] = "https://generativelanguage.googleapis.com"

    _save_llm_settings(data)
    return {"success": True, "settings": data}


@app.get("/api/v1/logs")
async def get_logs(file: str = "", limit: int = 200, level: str = "all", search: str = ""):
    """Read application logs with search and level filters."""
    logs_dir = os.path.join(_repo_root, "logs")
    if not os.path.exists(logs_dir):
        return {"files": [], "current_file": "", "lines": [], "error": "Logs directory not found"}

    files = [f for f in os.listdir(logs_dir) if f.endswith(".log")]
    files.sort()

    if not files:
        return {"files": [], "current_file": "", "lines": []}

    if not file or file not in files:
        if "virtualization-mcp.log" in files:
            file = "virtualization-mcp.log"
        else:
            file = files[-1]

    file_path = os.path.join(logs_dir, file)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=400, detail="Log file does not exist")

    matching_lines = []
    search_lower = search.lower().strip() if search else ""
    level_upper = level.upper().strip() if level and level != "all" else ""

    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()

        for line in reversed(all_lines):
            line_strip = line.strip()
            if not line_strip:
                continue

            if level_upper and level_upper not in line_strip.upper():
                continue

            if search_lower and search_lower not in line_strip.lower():
                continue

            matching_lines.append(line_strip)
            if len(matching_lines) >= limit:
                break

        matching_lines.reverse()
    except Exception as e:
        logger.error("Error reading log file %s: %s", file, e)
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {
        "files": files,
        "current_file": file,
        "lines": matching_lines,
    }


@app.get("/api/v1/help")
async def get_help():
    """Return FAQ and troubleshooting documentation."""
    return {
        "faqs": [
            {
                "question": "How do I launch a Windows Sandbox?",
                "answer": "Navigate to the 'Windows Sandbox' page, select your configuration preset, and click 'Launch Sandbox'. The backend will generate a temporary .wsb configuration file and execute it.",
                "category": "Sandbox",
            },
            {
                "question": "Can I run VirtualBox VMs headlessly?",
                "answer": "Yes. Start/stop controls on the VirtualBox page manage VMs in headless or standard GUI mode depending on global VirtualBox settings.",
                "category": "VirtualBox",
            },
            {
                "question": "Why does creating Hyper-V VMs fail?",
                "answer": "This is usually caused by insufficient permissions to manage Hyper-V. Ensure the virtualization backend is running with Administrator privileges, or that your user account is in the 'Hyper-V Administrators' local group.",
                "category": "Hyper-V",
            },
            {
                "question": "How do I configure a local LLM?",
                "answer": "Install Ollama or LM Studio, download/pull a model (e.g. gemma4:e4b, llama3.2), and update the Endpoint and Model fields on the Settings page.",
                "category": "Local LLM",
            },
            {
                "question": "What is the purpose of the MCP Server?",
                "answer": "The Model Context Protocol (MCP) server allows Claude Desktop or other AI clients to inspect, query, and run tools on your virtualization fleet automatically.",
                "category": "MCP Infrastructure",
            },
        ],
        "troubleshooting": [
            {
                "issue": "VirtualBox VM fails to start",
                "fix": "Ensure that hardware virtualization (VT-x/AMD-V) is enabled in your host system's BIOS, and close Hyper-V if it causes compatibility conflicts.",
            },
            {
                "issue": "Ollama connection refused",
                "fix": "Ensure the Ollama service is running (`ollama serve`). If running inside a VM or container, ensure it listens on `0.0.0.0` instead of `127.0.0.1` and that firewall ports are open.",
            },
            {
                "issue": "Hyper-V VM creation fails (Permission Denied)",
                "fix": "Hyper-V commands require elevated permissions. Run the backend server as Administrator, or add your user account to the local 'Hyper-V Administrators' group by running 'Add-LocalGroupMember -Group \"Hyper-V Administrators\" -Member $env:USERNAME' in an elevated PowerShell prompt and then log out/in.",
            },
        ],
        "system_info": {
            "docs_link": "https://github.com/sandraschi/virtualization-mcp",
            "version": "1.0.0",
            "mcp_version": "FastMCP 3.1",
        },
    }


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

# ISO categories loaded from external JSON (editable, extensible), fallback to empty list
ISO_CATEGORIES_FILE = os.path.join(_repo_root, "config", "iso_categories.json")
ISO_CATEGORIES: list[dict[str, Any]] = []


def _load_iso_categories() -> list[dict[str, Any]]:
    """Load ISO categories from config/iso_categories.json, with cache."""
    try:
        if os.path.isfile(ISO_CATEGORIES_FILE):
            with open(ISO_CATEGORIES_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning("Failed to load %s: %s", ISO_CATEGORIES_FILE, e)
    return []


def _get_iso_categories() -> list[dict[str, Any]]:
    """Return ISO categories, reloaded on each call so edits take effect without restart."""
    # Reload from JSON on every call
    return _load_iso_categories()


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


def _derive_filename(url: str, fallback: str = "download.iso") -> str:
    """Extract a reasonable filename from a download URL.

    Handles fwlink-style redirect URLs that produce empty basenames.
    """
    # Try to get basename from the path portion of the URL
    from urllib.parse import urlparse

    parsed = urlparse(url)
    base = os.path.basename(parsed.path)
    if base and base.lower().endswith(".iso"):
        return base
    # Try the query-param-stripped URL
    base = os.path.basename(url.split("?")[0])
    if base and len(base) > 4:  # at least ".iso" length
        return base
    # Extract from Content-Disposition hint in the URL
    for segment in url.split("/"):
        if segment.lower().endswith(".iso"):
            return segment
    return fallback


@app.get("/api/v1/iso/candidates")
async def iso_candidates():
    """List downloadable ISO candidates from config/iso_categories.json (reloaded on each call).

    Edit config/iso_categories.json and refresh to see changes immediately.
    """
    cats = _get_iso_categories()
    return {"categories": cats, "assets_vbox": ASSETS_VBOX, "config_file": ISO_CATEGORIES_FILE}


@app.post("/api/v1/iso/download")
async def iso_download(request: IsoDownloadRequest):
    """Start downloading an ISO to assets/vbox in the background."""
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    filename = request.filename or _derive_filename(url)
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


# ── Template CRUD ─────────────────────────────────────────────────────────


@app.get("/api/v1/templates")
async def get_templates():
    """List all VM templates (built-in + user-defined)."""
    user_templates = _load_templates()
    # Get built-in templates from VM operations
    builtin = []
    if service_manager and hasattr(service_manager.vm_service, "vbox_operations"):
        try:
            builtin_raw = await asyncio.to_thread(service_manager.vm_service.vbox_operations.list_templates)
            if builtin_raw:
                builtin = [
                    {
                        "name": t["name"],
                        "config": t["config"],
                        "builtin": True,
                        **{k: v for k, v in t.items() if k != "config"},
                    }
                    for t in builtin_raw
                ]
        except Exception as e:
            logger.warning("Could not load built-in templates: %s", e)
    user_list = [
        {
            "name": name,
            "config": cfg,
            "builtin": False,
            "description": cfg.get("description", ""),
            "os_type": cfg.get("os_type", ""),
            "memory_mb": cfg.get("memory_mb", 0),
            "disk_gb": cfg.get("disk_gb", 0),
        }
        for name, cfg in user_templates.items()
    ]
    return {"templates": builtin + user_list}


@app.post("/api/v1/templates")
async def create_template(request: TemplateUpdateRequest):
    """Create or overwrite a user-defined VM template."""
    data = _load_templates()
    data[request.name] = request.config
    _save_templates(data)
    return {"success": True, "name": request.name, "template": request.config}


@app.put("/api/v1/templates/{template_name}")
async def update_template(template_name: str, request: TemplateUpdateRequest):
    """Update an existing user-defined template."""
    data = _load_templates()
    if template_name not in data:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    del data[template_name]
    data[request.name] = request.config
    _save_templates(data)
    return {"success": True, "name": request.name, "template": request.config}


@app.delete("/api/v1/templates/{template_name}")
async def delete_template(template_name: str):
    """Delete a user-defined template."""
    data = _load_templates()
    if template_name in data:
        del data[template_name]
        _save_templates(data)
    return {"success": True, "deleted": template_name}


# ── VM Network Configuration ──────────────────────────────────────────────


@app.get("/api/v1/vms/{name}/network")
async def get_vm_network(name: str):
    """Get network adapter configuration for a VM."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")
    ops = getattr(service_manager.vm_service, "vbox_operations", None)
    if not ops or not hasattr(ops, "get_network_config"):
        raise HTTPException(status_code=501, detail="Network config not available")
    try:
        result = await asyncio.to_thread(ops.get_network_config, name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/vms/{name}/network")
async def set_vm_network(name: str, request: VmNetworkRequest):
    """Configure a VM network adapter."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")
    ops = getattr(service_manager.vm_service, "vbox_operations", None)
    if not ops or not hasattr(ops, "configure_network"):
        raise HTTPException(status_code=501, detail="Network config not available")
    try:
        result = await asyncio.to_thread(
            ops.configure_network,
            name,
            adapter=request.adapter,
            mode=request.mode,
            host_only_if=request.host_only_if,
            bridged_if=request.bridged_if,
            intnet_name=request.intnet_name,
            port_forwarding=request.port_forwarding,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/vms/{name}/network/port-forwarding")
async def add_port_forwarding(name: str, request: VmPortForwardRequest):
    """Add a NAT port forwarding rule to a VM."""
    import subprocess as _sub

    vbox = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
    try:
        r = _sub.run(
            [
                vbox,
                "controlvm",
                name,
                "natpf1",
                request.name,
                f"{request.protocol},,{request.host_port},,{request.guest_port}",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode != 0:
            raise HTTPException(status_code=400, detail=r.stderr.strip())
        return {"success": True, "rule": request.name, "host_port": request.host_port, "guest_port": request.guest_port}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/v1/vms/{name}/network/port-forwarding/{rule_name}")
async def remove_port_forwarding(name: str, rule_name: str):
    """Remove a NAT port forwarding rule."""
    import subprocess as _sub

    vbox = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
    try:
        r = _sub.run(
            [vbox, "controlvm", name, "natpf1", "delete", rule_name],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode != 0:
            raise HTTPException(status_code=400, detail=r.stderr.strip())
        return {"success": True, "deleted": rule_name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ── VM Unattended Install ─────────────────────────────────────────────────


def _generate_ubuntu_autoinstall(hostname: str, username: str, password: str, timezone: str) -> str:
    """Generate Ubuntu autoinstall.yaml content."""
    return f"""#cloud-config
autoinstall:
  version: 1
  identity:
    hostname: {hostname}
    username: {username}
    password: "$6$rounds=4096$placeholder$0"
  ssh:
    install-server: true
    allow-pw: true
    authorized-keys: []
  storage:
    layout:
      name: lvm
  packages:
    - curl
    - git
    - htop
    - net-tools
    - openssh-server
    - python3
    - python3-pip
    - vim
  late-commands:
    - echo 'ubuntu-server-setup' | sudo tee /etc/motd
  user-data:
    timezone: {timezone}
  network:
    version: 2
    ethernets:
      enp0s3:
        dhcp4: true
"""


def _generate_autounattend(
    hostname: str,
    username: str,
    password: str,
    timezone: str,
    dev_tools: list[str] | None = None,
    use_host_ollama: bool = False,
) -> str:
    """Generate Windows autounattend.xml content.

    If dev_tools is provided, injects a FirstLogonCommand that installs
    the selected dev tooling via winget + pip + npm.
    """
    dev_script = _generate_win_dev_setup_ps1(username, dev_tools, use_host_ollama)
    first_logon = ""
    if dev_script:
        escaped = dev_script.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        first_logon = f"""
            <FirstLogonCommands>
                <SynchronousCommand wcm:action="add">
                    <CommandLine>powershell -ExecutionPolicy Bypass -Command "{escaped}"</CommandLine>
                    <Description>Dev Environment Setup</Description>
                    <Order>1</Order>
                    <RequiresUserInput>false</RequiresUserInput>
                </SynchronousCommand>
            </FirstLogonCommands>"""

    return f"""<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
    <settings pass="windowsPE">
        <component name="Microsoft-Windows-International-Core-WinPE" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35">
            <SetupUILanguage>
                <UILanguage>en-US</UILanguage>
            </SetupUILanguage>
            <InputLocale>en-US</InputLocale>
            <SystemLocale>en-US</SystemLocale>
            <UILanguage>en-US</UILanguage>
            <UserLocale>en-US</UserLocale>
        </component>
        <component name="Microsoft-Windows-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35">
            <UserData>
                <ProductKey>
                    <Key>VK7JG-NPHTM-C97JM-9MPGT-3V66T</Key>
                </ProductKey>
                <AcceptEula>true</AcceptEula>
                <FullName>{username}</FullName>
                <Organization>Dev</Organization>
            </UserData>
        </component>
    </settings>
    <settings pass="oobeSystem">
        <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35">
            <UserAccounts>
                <LocalAccounts>
                    <LocalAccount wcm:action="add">
                        <Password>
                            <Value>{password}</Value>
                            <PlainText>true</PlainText>
                        </Password>
                        <DisplayName>{username}</DisplayName>
                        <Name>{username}</Name>
                        <Group>Administrators</Group>
                    </LocalAccount>
                </LocalAccounts>
            </UserAccounts>
            <AutoLogon>
                <Password>
                    <Value>{password}</Value>
                    <PlainText>true</PlainText>
                </Password>
                <Enabled>true</Enabled>
                <LogonCount>1</LogonCount>
                <Username>{username}</Username>
            </AutoLogon>
            <OEMInformation>
                <Manufacturer>Sandra's Virtualization MCP</Manufacturer>
                <Model>Automated VM</Model>
            </OEMInformation>
            <TimeZone>{timezone}</TimeZone>
            {first_logon}
        </component>
    </settings>
</unattend>
"""


def _generate_win_dev_setup_ps1(
    username: str = "user",
    tools: list[str] | None = None,
    use_host_ollama: bool = False,
) -> str:
    """Generate a PowerShell script to install dev tools in a Windows VM.

    Runs winget installs silently, then pip/npm setup. Uses the same tool IDs
    as the Sandbox dev setup.
    """
    if not tools:
        return ""

    tool_map = {
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

    winget_ids = [tool_map[t] for t in tools if t in tool_map]
    has_python = "python" in tools
    has_claude = any(t in ("claude_desktop", "claudesktop", "claudedesktop") for t in tools)

    lines = [
        "# Dev Environment Setup (generated by virtualization-mcp)",
        '$logFile = "$env:USERPROFILE\\Desktop\\dev-setup.log"',
        "Start-Transcript -Path $logFile -Append",
        "Write-Host '--- Dev Environment Setup ---' -ForegroundColor Cyan",
    ]

    for wid in winget_ids:
        lines.append(
            f'Write-Host "Installing {wid}..." -ForegroundColor Yellow; '
            f"& winget install -e --id {wid} --source winget --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null"
        )

    if has_python:
        lines.append(
            'Write-Host "Upgrading pip..." -ForegroundColor Yellow; python -m pip install --upgrade pip 2>&1 | Out-Null'
        )

    if has_claude:
        lines.append(
            'Write-Host "Downloading Claude Desktop..." -ForegroundColor Yellow; '
            '$msix = "$env:TEMP\\Claude.msix"; '
            'Invoke-WebRequest -Uri "https://claude.ai/api/desktop/win32/x64/msix/latest/redirect" -OutFile $msix -UseBasicParsing; '
            "Add-AppxPackage -Path $msix -ErrorAction SilentlyContinue"
        )

    if use_host_ollama:
        lines.append(
            '$gw = (Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue | Select-Object -First 1).NextHop; '
            "if ($gw) { "
            '$env:OLLAMA_HOST = "http://$gw`:11434"; '
            '[Environment]::SetEnvironmentVariable("OLLAMA_HOST", $env:OLLAMA_HOST, "User") '
            "}"
        )

    lines.append("Write-Host 'Dev setup complete!' -ForegroundColor Green")
    lines.append("Stop-Transcript")
    return "; ".join(lines)


UNATTENDED_DIR = os.path.join(_repo_root, "assets", "unattended")


@app.post("/api/v1/vms/{name}/unattended")
async def setup_unattended_install(name: str, request: UnattendedRequest):
    """Generate unattended install answer file for a VM.

    For Ubuntu: generates autoinstall.yaml and creates a cloud-init ISO
    (secondary attach, boot order maintains dvd first).
    For Windows: generates autounattend.xml and injects into a response ISO.
    """
    os.makedirs(UNATTENDED_DIR, exist_ok=True)
    os_type = (request.os_type or "ubuntu").lower()

    try:
        if os_type == "ubuntu":
            content = _generate_ubuntu_autoinstall(
                request.hostname, request.username, request.password, request.timezone
            )
            dest = os.path.join(UNATTENDED_DIR, f"{name}-autoinstall.yaml")
            with open(dest, "w") as f:
                f.write(content)
            _make_cloudinit_iso(name, dest)
            return {
                "success": True,
                "os_type": "ubuntu",
                "file": dest,
                "message": "Cloud-init ISO generated. Attach it as the secondary drive after the main ISO.",
            }
        elif os_type == "windows":
            content = _generate_autounattend(
                request.hostname,
                request.username,
                request.password,
                request.timezone,
                dev_tools=request.dev_tools,
                use_host_ollama=request.use_host_ollama,
            )
            dest = os.path.join(UNATTENDED_DIR, f"{name}-autounattend.xml")
            with open(dest, "w") as f:
                f.write(content)
            msg = "autounattend.xml generated."
            if request.dev_tools:
                msg += f" Dev tools ({len(request.dev_tools)} selected) will install on first login."
            return {
                "success": True,
                "os_type": "windows",
                "file": dest,
                "message": msg,
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported OS type: {os_type}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def _make_cloudinit_iso(vm_name: str, userdata_path: str) -> str:
    """Create a cloud-init ISO with meta-data and user-data for VBox attachment."""
    import subprocess as _sub

    iso_dir = os.path.join(UNATTENDED_DIR, f"{vm_name}-cidata")
    os.makedirs(iso_dir, exist_ok=True)
    meta_path = os.path.join(iso_dir, "meta-data")
    with open(meta_path, "w") as f:
        f.write(f"instance-id: {vm_name}-autoinstall\nlocal-hostname: {vm_name}\n")
    userdata_dest = os.path.join(iso_dir, "user-data")
    import shutil

    shutil.copy2(userdata_path, userdata_dest)
    iso_out = os.path.join(UNATTENDED_DIR, f"{vm_name}-cidata.iso")
    mkisofs = shutil.which("mkisofs") or shutil.which("genisoimage") or shutil.which("xorrisofs")
    if mkisofs:
        _sub.run(
            [mkisofs, "-output", iso_out, "-volid", "cidata", "-joliet", "-rock", iso_dir],
            capture_output=True,
            text=True,
            timeout=30,
        )
    else:
        # Fallback: write script for manual ISO creation
        logger.warning("No mkisofs found; user-data written to %s for manual ISO creation", userdata_dest)
        return userdata_dest
    return iso_out


@app.get("/api/v1/vms/{name}/unattended")
async def get_unattended_config(name: str):
    """Get the unattended install config for a VM (if generated)."""
    for fname in (f"{name}-autoinstall.yaml", f"{name}-autounattend.xml"):
        path = os.path.join(UNATTENDED_DIR, fname)
        if os.path.isfile(path):
            with open(path) as f:
                return {"exists": True, "file": fname, "content": f.read()}
    return {"exists": False, "message": "No unattended config found for this VM"}


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
    """Return WSB XML for download or UI preview. preset=dev-infra, consumer, or full-dev."""
    p = (preset or "dev-infra").lower().strip()
    mem = int(memory_in_mb) if memory_in_mb else 8192
    if p == "dev-infra":
        folder = (assets_folder or "").strip() or ASSETS_SANDBOX
        if not os.path.isdir(folder):
            raise HTTPException(status_code=400, detail=f"Assets folder does not exist: {folder}")
        for required in (
            "Setup-DevInfraSandbox.ps1",
            "Run-DevInfra.cmd",
            "Show-DevInfraLog.ps1",
            os.path.join("lib", "Winget-Bootstrap.ps1"),
        ):
            rp = os.path.join(folder, required)
            if not os.path.isfile(rp):
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing {required} in {folder}. Use virtualization-mcp assets/sandbox.",
                )
        xml = _build_sandbox_xml_dev_infra(folder, memory_mb=mem, vgpu=vgpu, networking=networking)
        return {"xml": xml, "preset": p, "assets_folder": folder, "filename": "DevInfra.wsb"}
    if p == "consumer":
        folder = (assets_folder or "").strip() or ASSETS_SANDBOX
        if not os.path.isdir(folder):
            raise HTTPException(status_code=400, detail=f"Assets folder does not exist: {folder}")
        for required in CONSUMER_SANDBOX_FILES:
            rp = os.path.join(folder, required)
            if not os.path.isfile(rp):
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing {required} in {folder}. Use virtualization-mcp assets/sandbox.",
                )
        xml = _build_sandbox_xml_consumer(folder, memory_mb=mem, vgpu=vgpu, networking=networking)
        return {"xml": xml, "preset": p, "assets_folder": folder, "filename": "Consumer.wsb"}
    if p == "full-dev":
        folder = (assets_folder or "").strip()
        if not folder or not os.path.isdir(folder):
            raise HTTPException(
                status_code=400,
                detail="full-dev requires assets_folder query parameter (existing host directory with offline winget assets).",
            )
        xml = _build_sandbox_xml_dev_setup(folder, memory_mb=mem, vgpu=vgpu, networking=networking)
        return {"xml": xml, "preset": p, "assets_folder": folder, "filename": "FullDev.wsb"}
    raise HTTPException(status_code=400, detail="Unknown preset (use dev-infra, consumer, or full-dev).")


@app.get("/api/v1/sandbox/status")
async def sandbox_status():
    """Check if Windows Sandbox is currently running."""
    running = False
    import subprocess as _sub

    try:
        r = _sub.run(
            ["tasklist", "/FI", "IMAGENAME eq WindowsSandbox.exe", "/NH", "/FO", "CSV"],
            capture_output=True,
            text=True,
            timeout=5,
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
                    "@echo off\r\n"
                    'set "LOG=%USERPROFILE%\\Desktop\\dev-setup.log"\r\n'
                    'echo [%DATE% %TIME%] Run-DevSetup.cmd starting > "%LOG%"\r\n'
                    'if exist "C:\\Assets\\Run-DevSetup.cmd" ( echo [%DATE% %TIME%] C:\\Assets mapped OK >> "%LOG%" ) else ( echo [%DATE% %TIME%] C:\\Assets NOT MAPPED >> "%LOG%" )\r\n'
                    'dir "C:\\Assets" >> "%LOG%" 2>&1\r\n'
                    'echo [%DATE% %TIME%] Waiting 5s... >> "%LOG%"\r\n'
                    "ping -n 6 127.0.0.1 > nul\r\n"
                    'if exist "C:\\Assets\\Setup-DevSandbox.ps1" (\r\n'
                    '    echo [%DATE% %TIME%] Starting Setup-DevSandbox.ps1 >> "%LOG%"\r\n'
                    '    powershell -ExecutionPolicy Bypass -File "C:\\Assets\\Setup-DevSandbox.ps1" >> "%LOG%" 2>&1\r\n'
                    '    echo [%DATE% %TIME%] Exit code %ERRORLEVEL% >> "%LOG%"\r\n'
                    ") else (\r\n"
                    '    echo [%DATE% %TIME%] ERROR: Setup-DevSandbox.ps1 NOT FOUND >> "%LOG%"\r\n'
                    ")\r\n"
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
            for required in (
                "Setup-DevInfraSandbox.ps1",
                "Run-DevInfra.cmd",
                "Show-DevInfraLog.ps1",
                os.path.join("lib", "Winget-Bootstrap.ps1"),
            ):
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
        elif getattr(request, "consumer_setup", None):
            raw = getattr(request, "assets_folder", None) or ""
            host_folder = raw.strip() if isinstance(raw, str) else ""
            if not host_folder:
                host_folder = ASSETS_SANDBOX
            if not os.path.isdir(host_folder):
                raise HTTPException(status_code=400, detail=f"Assets folder does not exist: {host_folder}")
            for required in CONSUMER_SANDBOX_FILES:
                rp = os.path.join(host_folder, required)
                if not os.path.isfile(rp):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing {required} in {host_folder}",
                    )
            mem = request.memory_in_mb if request.memory_in_mb is not None else 8192
            net = request.networking if request.networking is not None else True
            vg = request.vgpu if request.vgpu is not None else True
            install_claude = bool(getattr(request, "consumer_install_claude", None))
            config_xml = _build_sandbox_xml_consumer(
                host_folder,
                memory_mb=mem,
                vgpu=vg,
                networking=net,
                install_claude_desktop=install_claude,
            )
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


@app.get("/api/v1/apps/check")
async def check_apps_health():
    """Check which registered apps are actually running by pinging their ports."""
    import socket as _socket

    if not os.path.exists(REGISTRY_PATH):
        return {"statuses": {}}
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry = json.load(f)
    statuses = {}
    for app in registry.get("webapps", []):
        port = app.get("port")
        app_id = app.get("id", "")
        if not port:
            statuses[app_id] = "unknown"
            continue
        try:
            with _socket.create_connection(("127.0.0.1", port), timeout=1):
                statuses[app_id] = "running"
        except (ConnectionRefusedError, OSError):
            statuses[app_id] = "stopped"
        except Exception:
            statuses[app_id] = "unknown"
    return {"statuses": statuses}


@app.post("/api/v1/apps/{app_id}/start")
async def start_fleet_app(app_id: str):
    """Start a fleet app by running its start command."""
    import subprocess as _sub

    if not os.path.exists(REGISTRY_PATH):
        raise HTTPException(status_code=500, detail="Registry not found")
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry = json.load(f)
    for app in registry.get("webapps", []):
        if app.get("id") == app_id:
            repo = app.get("repo_path", "")
            cmd = app.get("start_command", "")
            if not cmd:
                raise HTTPException(status_code=400, detail="No start command configured")
            try:
                # Run in background
                _sub.Popen(
                    cmd,
                    cwd=repo if os.path.isdir(repo) else None,
                    shell=True,
                    creationflags=_sub.CREATE_NEW_CONSOLE,
                )
                return {"status": "started", "app_id": app_id}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=404, detail=f"App '{app_id}' not found in registry")


# ── Fleet Installer ────────────────────────────────────────────────────────────


class FleetInstallRequest(BaseModel):
    repos: list[str]  # repo IDs from the registry
    install_dir: str = "C:\\Fleet"  # where to clone
    setup_venv: bool = True
    setup_npm: bool = True


@app.post("/api/v1/fleet/install-script")
async def fleet_install_script(request: FleetInstallRequest):
    """Generate a PowerShell script that clones and installs selected fleet repos."""
    if not os.path.exists(REGISTRY_PATH):
        raise HTTPException(status_code=500, detail="Registry not found")

    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry = json.load(f)

    webapps = registry.get("webapps", [])
    selected = [w for w in webapps if w.get("id") in request.repos]

    lines = [
        "# Fleet Install Script (generated by virtualization-mcp)",
        "# Run this in PowerShell as Admin inside your VM or sandbox.",
        "",
        f"$fleetDir = '{request.install_dir}'",
        "Write-Host '=== Fleet Install ===' -ForegroundColor Cyan",
        "Write-Host ('Installing ' + " + str(len(selected)) + " + ' repos to ' + $fleetDir)",
        "",
        "if (-not (Test-Path $fleetDir)) { New-Item -ItemType Directory -Path $fleetDir -Force | Out-Null }",
        "Set-Location $fleetDir",
        "",
    ]

    for app in selected:
        repo_path = app.get("repo_path", "")
        repo_id = app.get("id", "unknown")
        label = app.get("label", repo_id)
        start_cmd = app.get("start_command", "")

        # Extract GitHub URL from repo_path or use generic
        gh_url = f"https://github.com/sandraschi/{repo_id}.git"

        lines += [
            "",
            f"# === {label} ===",
            f"Write-Host 'Cloning {label}...' -ForegroundColor Yellow",
            f"if (-not (Test-Path '{repo_id}')) {{",
            f"    git clone {gh_url}",
            "} else {",
            "    Write-Host '  Already exists, pulling...' -ForegroundColor Gray",
            f"    Set-Location '{repo_id}'",
            "    git pull",
            "    Set-Location $fleetDir",
            "}",
            f"Set-Location '{repo_id}'",
        ]

        # Detect and setup
        lines += [
            "# Python venv setup",
            "if (Test-Path 'requirements.txt') {",
            "    Write-Host '  Installing Python deps...' -ForegroundColor Yellow",
            "    pip install -r requirements.txt 2>&1 | Out-Null",
            "}",
            "if (Test-Path 'pyproject.toml') {",
            "    Write-Host '  Installing Python package...' -ForegroundColor Yellow",
            "    pip install -e . 2>&1 | Out-Null",
            "}",
            "# npm setup",
            "if (Test-Path 'package.json') {",
            "    Write-Host '  Installing npm deps...' -ForegroundColor Yellow",
            "    npm install 2>&1 | Out-Null",
            "}",
            "Set-Location $fleetDir",
        ]

    lines += [
        "",
        "Write-Host '=== Fleet install complete ===' -ForegroundColor Green",
        "Write-Host ('Repos installed in: ' + $fleetDir) -ForegroundColor Cyan",
    ]

    script = "\n".join(lines)
    return {"script": script, "repos": selected, "install_dir": request.install_dir}


_COLD_INSTALL_MANIFEST = os.path.join(
    _repo_root, "..", "mcp-central-docs", "scripts", "fleet-cold-install-manifest.json"
)
_COLD_INSTALL_MANIFEST = os.path.normpath(_COLD_INSTALL_MANIFEST)
_STDIO_SMOKE_SCRIPT = os.path.normpath(
    os.path.join(_repo_root, "..", "mcp-central-docs", "scripts", "stdio_mcp_smoke.py")
)
_SANDBOX_RUNS_ROOT = os.path.normpath(os.path.join(_repo_root, "..", "_sandbox_runs"))


class FleetInstallMcpbRequest(BaseModel):
    repo: str
    releases_url: str = ""
    asset_name: str = ""
    run_dir: str = ""


class FleetStdioSmokeRequest(BaseModel):
    command: str
    args: list[str] = []
    timeout_sec: float = 12.0
    env: dict[str, str] = {}
    cwd: str = ""


class FleetInstallRunRequest(BaseModel):
    script: str
    run_dir: str = ""
    label: str = "install"


def _load_cold_install_entry(repo: str) -> dict[str, Any] | None:
    if not os.path.isfile(_COLD_INSTALL_MANIFEST):
        return None
    with open(_COLD_INSTALL_MANIFEST, encoding="utf-8-sig") as f:
        rows = json.load(f)
    for row in rows:
        if row.get("repo") == repo:
            return row
    return None


def _github_latest_mcpb_asset(owner: str, repo: str, asset_hint: str = "") -> dict[str, Any]:
    api = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    headers = {"User-Agent": "virtualization-mcp-fleet-install"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(api, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as resp:
        release = json.loads(resp.read().decode())
    asset = None
    for a in release.get("assets") or []:
        name = a.get("name") or ""
        if name.endswith(".mcpb") and (not asset_hint or name == asset_hint):
            asset = a
            break
    if not asset:
        for a in release.get("assets") or []:
            if (a.get("name") or "").endswith(".mcpb"):
                asset = a
                break
    if not asset:
        return {"ok": False, "error": "No .mcpb asset on latest release"}
    return {
        "ok": True,
        "asset_name": asset.get("name"),
        "download_url": asset.get("browser_download_url"),
        "release_tag": release.get("tag_name"),
    }


def _build_mcpb_install_script(download_url: str, asset_name: str, repo: str) -> str:
    return "\n".join(
        [
            "# Fleet mcpb install (generated by virtualization-mcp)",
            f"# Repo: {repo}",
            "$ErrorActionPreference = 'Stop'",
            "$pkgDir = Join-Path $env:USERPROFILE 'Downloads\\fleet-mcpb'",
            "if (-not (Test-Path $pkgDir)) { New-Item -ItemType Directory -Path $pkgDir -Force | Out-Null }",
            f"$asset = '{asset_name}'",
            "$out = Join-Path $pkgDir $asset",
            f"Write-Host 'Downloading {asset_name}...' -ForegroundColor Cyan",
            f"Invoke-WebRequest -Uri '{download_url}' -OutFile $out -UseBasicParsing",
            "if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {",
            "  Write-Host 'npx missing - install Node.js LTS first' -ForegroundColor Red",
            "  exit 1",
            "}",
            "Write-Host 'Running mcpb install...' -ForegroundColor Yellow",
            "npx --yes @anthropic-ai/mcpb@latest install $out",
            "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }",
            "Write-Host 'mcpb install complete' -ForegroundColor Green",
        ]
    )


@app.post("/api/v1/fleet/install-mcpb")
async def fleet_install_mcpb(request: FleetInstallMcpbRequest):
    """Download latest .mcpb and generate sandbox/host install script."""
    entry = _load_cold_install_entry(request.repo)
    owner = (entry or {}).get("githubOwner") or "sandraschi"
    gh_repo = (entry or {}).get("githubRepo") or request.repo
    asset_hint = request.asset_name or (entry or {}).get("mcpbAssetName") or ""
    releases_url = request.releases_url or (entry or {}).get("mcpbReleasesUrl") or ""

    asset_info = await asyncio.to_thread(_github_latest_mcpb_asset, owner, gh_repo, asset_hint)
    if not asset_info.get("ok"):
        return {
            "success": False,
            "repo": request.repo,
            "error": asset_info.get("error", "mcpb asset lookup failed"),
            "releases_url": releases_url or f"https://github.com/{owner}/{gh_repo}/releases",
        }

    script = _build_mcpb_install_script(
        asset_info["download_url"],
        asset_info["asset_name"],
        request.repo,
    )
    run_dir = request.run_dir or os.path.join(
        _SANDBOX_RUNS_ROOT, __import__("datetime").datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    )
    os.makedirs(run_dir, exist_ok=True)
    script_path = os.path.join(run_dir, f"{request.repo}-mcpb-install.ps1")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    return {
        "success": True,
        "repo": request.repo,
        "asset_name": asset_info["asset_name"],
        "release_tag": asset_info.get("release_tag"),
        "script": script,
        "script_path": script_path,
        "run_dir": run_dir,
        "hint": "Run script inside consumer sandbox (C:\\Assets mapped) or on host for smoke prep",
    }


@app.post("/api/v1/fleet/stdio-smoke")
async def fleet_stdio_smoke(request: FleetStdioSmokeRequest):
    """Run MCP stdio initialize smoke (host execution)."""
    import subprocess as _sub

    if not os.path.isfile(_STDIO_SMOKE_SCRIPT):
        raise HTTPException(status_code=500, detail=f"Smoke script missing: {_STDIO_SMOKE_SCRIPT}")

    cmd = [
        sys.executable,
        _STDIO_SMOKE_SCRIPT,
        "--timeout",
        str(request.timeout_sec),
    ]
    if request.cwd:
        cmd.extend(["--cwd", request.cwd])
    for key, value in (request.env or {}).items():
        cmd.extend(["--env", f"{key}={value}"])
    cmd.extend(["--", request.command, *request.args])
    try:
        proc = await asyncio.to_thread(
            _sub.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=max(30, int(request.timeout_sec) + 10),
        )
        payload: dict[str, Any] = {}
        if proc.stdout.strip():
            try:
                payload = json.loads(proc.stdout)
            except json.JSONDecodeError:
                payload = {"ok": False, "error": "Invalid JSON from smoke helper", "log": proc.stdout[-2000:]}
        ok = proc.returncode == 0 and bool(payload.get("ok"))
        return {
            "success": ok,
            "ok": ok,
            "command": request.command,
            "args": request.args,
            "returncode": proc.returncode,
            "result": payload,
            "stderr": (proc.stderr or "")[-1000:],
        }
    except Exception as e:
        return {"success": False, "ok": False, "error": str(e)}


@app.post("/api/v1/fleet/install-run")
async def fleet_install_run(request: FleetInstallRunRequest):
    """Persist install script to sandbox runs folder for mapped-folder execution."""
    run_dir = request.run_dir or os.path.join(
        _SANDBOX_RUNS_ROOT, __import__("datetime").datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    )
    os.makedirs(run_dir, exist_ok=True)
    safe_label = "".join(c if c.isalnum() or c in "-_" else "-" for c in request.label)
    script_path = os.path.join(run_dir, f"{safe_label}.ps1")
    # No personality handling needed for install-run; original logic retained.
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(request.script)
    log_path = os.path.join(run_dir, f"{safe_label}.log")
    return {
        "success": True,
        "script_path": script_path,
        "log_path": log_path,
        "run_dir": run_dir,
        "hint": "Copy script into consumer sandbox mapped folder and run via Run-Consumer extension or manual PS",
    }


@app.post("/api/v1/chat")
async def chat_interaction(request: ChatRequest):
    """Handle AI chat using local LLM (Ollama/LM Studio) or Gemini fallback."""
    return await chat_service.ask(request)
    import json as _json
    import urllib.request as _req

    settings = _load_llm_settings()
    provider = settings.get("provider", "ollama")
    endpoint = settings.get("endpoint", "http://localhost:11434").rstrip("/")
    preferred_model = request.model or settings.get("model", "gemma4:e4b")

    # Load base system prompt or skill content
    system_prompt = "You are the SOTA Virtualization Assistant. You help manage VMs, Sandboxes, and the MCP Fleet."

    # Personality handling
    personality = getattr(request, "personality", None) or "professional"
    personality_instructions = {
        "professional": "",
        "pirate": "You speak like a pirate captain, using nautical terms and humor.",
        "sarcastic": "You respond with dry sarcasm and witty remarks.",
        "mentor": "You act as a supportive mentor, explaining patiently and encouraging the user.",
    }
    instr = personality_instructions.get(personality, "")
    if instr:
        system_prompt += f"\n\n{instr}"
    else:
        logger.warning("Unknown personality %s, defaulting to professional", personality)

    # Try to load the virtualization-expert skill to augment the prompt
    try:
        skills_dir = _get_skills_dir()
        if skills_dir:
            expert_skill_path = os.path.join(skills_dir, "virtualization-expert", "SKILL.md")
            if os.path.isfile(expert_skill_path):
                with open(expert_skill_path, encoding="utf-8") as f:
                    skill_content = f.read()
                # Strip YAML frontmatter if present
                if skill_content.startswith("---"):
                    end_fm = skill_content.find("---", 3)
                    if end_fm != -1:
                        skill_content = skill_content[end_fm + 3 :].strip()
                system_prompt += "\n\nUse the following skill guidelines when helping the user:\n" + skill_content
    except Exception as e:
        logger.warning("Could not load virtualization-expert skill for chat prompt: %s", e)

    # Build messages list for LLM payload
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": request.message}]
    reply = ""

    if provider == "ollama":
        try:
            # Probe available models to pick one that exists
            ollama_endpoint = endpoint
            # Auto-correct mismatched default port
            if "1234" in ollama_endpoint:
                ollama_endpoint = ollama_endpoint.replace("1234", "11434")

            try:
                _avail_req = _req.urlopen(f"{ollama_endpoint}/api/tags", timeout=3)
                _avail_data = _json.loads(_avail_req.read())
                _models = [m["name"] for m in _avail_data.get("models", [])]
            except Exception:
                if ollama_endpoint != "http://localhost:11434":
                    try:
                        ollama_endpoint = "http://localhost:11434"
                        _avail_req = _req.urlopen(f"{ollama_endpoint}/api/tags", timeout=3)
                        _avail_data = _json.loads(_avail_req.read())
                        _models = [m["name"] for m in _avail_data.get("models", [])]
                    except Exception:
                        _models = []
                else:
                    _models = []
        except Exception:
            _models = []

        _preferred = preferred_model
        if _preferred not in _models and _models:
            for _fallback in (
                "gemma4:e4b",
                "gemma4:e2b",
                "llama3.2:3b",
                "llama3.2:1b",
                "llama3.1:latest",
                "qwen2.5-coder:latest",
            ):
                if _fallback in _models:
                    _preferred = _fallback
                    break
            else:
                _preferred = _models[0]
        try:
            ollama_payload = _json.dumps(
                {
                    "model": _preferred,
                    "messages": messages,
                    "stream": False,
                }
            ).encode()
            oreq = _req.Request(
                f"{ollama_endpoint}/api/chat",
                data=ollama_payload,
                headers={"Content-Type": "application/json"},
            )
            with _req.urlopen(oreq, timeout=120) as r:
                data = _json.loads(r.read())
                reply = data.get("message", {}).get("content", "")
                if reply:
                    return {"reply": reply, "provider": f"ollama ({_preferred})"}
        except Exception:
            pass

    if provider == "openai":
        try:
            saved_keys = _load_keys()
            api_key = saved_keys.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")

            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            openai_url = endpoint.rstrip("/")
            if not openai_url.endswith("/chat/completions"):
                if not openai_url.endswith("/v1"):
                    openai_url += "/v1"
                openai_url += "/chat/completions"

            openai_payload = _json.dumps(
                {
                    "model": preferred_model or "gpt-4o-mini",
                    "messages": messages,
                    "max_tokens": 1024,
                    "stream": False,
                }
            ).encode()

            oreq = _req.Request(
                openai_url,
                data=openai_payload,
                headers=headers,
            )
            with _req.urlopen(oreq, timeout=60) as r:
                data = _json.loads(r.read())
                reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if reply:
                    return {"reply": reply, "provider": f"openai compatible ({preferred_model})"}
        except Exception as e:
            logger.error("OpenAI compatible chat error: %s", e)

    if provider == "deepseek":
        try:
            saved_keys = _load_keys()
            api_key = saved_keys.get("DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_API_KEY", "")
            if not api_key:
                return {"reply": "DeepSeek API Key is missing. Please set it in Settings.", "provider": None}

            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

            url = endpoint.rstrip("/")
            if not url.endswith("/chat/completions"):
                if not url.endswith("/v1"):
                    url += "/v1"
                url += "/chat/completions"

            deepseek_payload = _json.dumps(
                {
                    "model": preferred_model or "deepseek-v4-flash",
                    "messages": messages,
                    "max_tokens": 1024,
                    "stream": False,
                }
            ).encode()

            oreq = _req.Request(
                url,
                data=deepseek_payload,
                headers=headers,
            )
            with _req.urlopen(oreq, timeout=60) as r:
                data = _json.loads(r.read())
                reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if reply:
                    return {"reply": reply, "provider": f"deepseek ({preferred_model or 'deepseek-v4-flash'})"}
        except Exception as e:
            logger.error("DeepSeek chat error: %s", e)
            return {"reply": f"DeepSeek API Error: {e}", "provider": None}

    if provider == "anthropic":
        try:
            saved_keys = _load_keys()
            api_key = saved_keys.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                return {"reply": "Anthropic API Key is missing. Please set it in Settings.", "provider": None}

            headers = {"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"}

            anthropic_payload = _json.dumps(
                {
                    "model": preferred_model or "claude-3-5-sonnet-latest",
                    "messages": [{"role": "user", "content": prefix + request.message}],
                    "max_tokens": 1024,
                }
            ).encode()

            url = endpoint.rstrip("/")
            if "api.anthropic.com" in url and not url.endswith("/v1/messages"):
                if not url.endswith("/v1"):
                    url += "/v1"
                url += "/messages"
            elif not url.endswith("/messages") and "api.anthropic.com" not in url:
                pass
            else:
                url = "https://api.anthropic.com/v1/messages"

            oreq = _req.Request(
                url,
                data=anthropic_payload,
                headers=headers,
            )
            with _req.urlopen(oreq, timeout=60) as r:
                data = _json.loads(r.read())
                reply = data.get("content", [{}])[0].get("text", "")
                if reply:
                    return {"reply": reply, "provider": f"anthropic ({preferred_model or 'claude-3-5-sonnet-latest'})"}
        except Exception as e:
            logger.error("Anthropic chat error: %s", e)
            return {"reply": f"Anthropic API Error: {e}", "provider": None}

    if provider == "gemini":
        try:
            saved_keys = _load_keys()
            api_key = saved_keys.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
            if not api_key:
                return {"reply": "Google API Key is missing. Please set it in Settings.", "provider": None}

            model_name = preferred_model or "gemini-3.5-flash"
            if genai:
                try:
                    genai.configure(api_key=api_key)
                    gmodel = genai.GenerativeModel(model_name)
                    response = await asyncio.to_thread(gmodel.generate_content, prefix + request.message)
                    return {"reply": response.text, "provider": f"gemini ({model_name})"}
                except Exception as sdk_e:
                    logger.warning("Gemini SDK call failed, falling back to direct HTTP: %s", sdk_e)

            # Fallback to direct HTTP POST if SDK not available or failed
            headers = {"Content-Type": "application/json"}
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload = _json.dumps({"contents": [{"parts": [{"text": prefix + request.message}]}]}).encode()

            oreq = _req.Request(url, data=payload, headers=headers)
            with _req.urlopen(oreq, timeout=60) as r:
                data = _json.loads(r.read())
                reply = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if reply:
                    return {"reply": reply, "provider": f"gemini ({model_name})"}
        except Exception as e:
            logger.error("Gemini chat error: %s", e)
            return {"reply": f"Gemini API Error: {e}", "provider": None}

    if provider == "lm_studio" or not reply:
        try:
            lm_endpoint = endpoint if provider == "lm_studio" else "http://localhost:1234"
            # Auto-correct mismatched default port
            if provider == "lm_studio" and "11434" in lm_endpoint:
                lm_endpoint = lm_endpoint.replace("11434", "1234")

            lm_payload = _json.dumps(
                {
                    "model": preferred_model,
                    "messages": [{"role": "user", "content": prefix + request.message}],
                    "max_tokens": 1024,
                    "stream": False,
                }
            ).encode()
            lreq = _req.Request(
                f"{lm_endpoint}/v1/chat/completions",
                data=lm_payload,
                headers={"Content-Type": "application/json"},
            )
            try:
                with _req.urlopen(lreq, timeout=60) as r:
                    data = _json.loads(r.read())
                    reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if reply:
                        return {"reply": reply, "provider": f"lm_studio ({preferred_model})"}
            except Exception as inner_e:
                # If custom failed and is not default, try fallback to default LM Studio port
                if lm_endpoint != "http://localhost:1234":
                    logger.warning("LM Studio custom endpoint failed, trying default: %s", inner_e)
                    lreq_fallback = _req.Request(
                        "http://localhost:1234/v1/chat/completions",
                        data=lm_payload,
                        headers={"Content-Type": "application/json"},
                    )
                    with _req.urlopen(lreq_fallback, timeout=30) as r:
                        data = _json.loads(r.read())
                        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        if reply:
                            return {"reply": reply, "provider": f"lm_studio default ({preferred_model})"}
                raise inner_e
        except Exception as e:
            logger.error("LM Studio chat error: %s", e)

    # Fallback: Gemini (if configured via legacy/fallback path)
    if chat_model:
        try:
            response = await asyncio.to_thread(chat_model.generate_content, prefix + request.message)
            return {"reply": response.text, "provider": "gemini"}
        except Exception as e:
            logger.error("Gemini chat error: %s", e)

    return {
        "reply": f"No LLM provider available at {endpoint}. Start Ollama (`ollama serve`), LM Studio, or set GOOGLE_API_KEY.",
        "provider": None,
    }


@app.post("/api/v1/chat/refine")
async def refine_prompt(request: RefinePromptRequest):
    """Refine a virtualization prompt using the active LLM."""
    if not request.prompt.strip():
        return {"refined": ""}

    refine_instruction = (
        "You are a prompt engineering assistant. Your task is to rewrite the user's input prompt to be "
        "clear, precise, and optimized for an AI virtualization assistant that controls VirtualBox and Hyper-V. "
        "Make it detailed, specifying parameter options (like RAM, CPUs) if implied or suggested by best practices, "
        "while keeping the core intent exactly the same. Do not output anything other than the raw refined prompt itself. "
        "Do not include intro/outro comments, explanations, formatting code blocks, or conversational text. Just return the refined prompt.\n\n"
        f"User Prompt: {request.prompt}\n\n"
        "Refined Prompt:"
    )

    chat_req = ChatRequest(message=refine_instruction, history=[], model=request.model)

    res = await chat_interaction(chat_req)
    refined = res.get("reply", "").strip()

    # Clean up markdown ticks if some LLMs append them
    if refined.startswith("```") and refined.endswith("```"):
        lines = refined.split("\n")
        if len(lines) > 2:
            refined = "\n".join(lines[1:-1]).strip()
        else:
            refined = refined.replace("```", "").strip()
    elif refined.startswith('"') and refined.endswith('"'):
        refined = refined[1:-1].strip()

    return {"refined": refined}


@app.post("/api/v1/vms")
async def create_vm(request: VMCreateRequest):
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")
    try:
        if request.provider == "hyperv":
            if not hasattr(service_manager.vm_service, "hyperv_manager"):
                raise HTTPException(status_code=503, detail="Hyper-V not available")
            result = await service_manager.vm_service.hyperv_manager.create_vm(
                name=request.name,
                memory_mb=request.memory_mb or 2048,
                disk_gb=request.disk_gb or 25,
            )
        else:
            result = await asyncio.to_thread(
                service_manager.vm_service.create_vm,
                name=request.name,
                template=request.template,
                memory_mb=request.memory_mb,
                disk_gb=request.disk_gb,
                cpus=request.cpus,
            )
            # Apply network override if specified
            if request.network_mode and result.get("success", True):
                ops = getattr(service_manager.vm_service, "vbox_operations", None)
                if ops and hasattr(ops, "configure_network"):
                    await asyncio.to_thread(ops.configure_network, request.name, mode=request.network_mode)
                    result["network_mode"] = request.network_mode
            if request.iso_path:
                raw = request.iso_path.strip()
                logger.debug("ISO path raw: %r", raw)
                norm = os.path.normpath(os.path.abspath(raw))
                logger.debug("ISO path norm: %r", norm)
                logger.debug("ISO exists: isfile=%s exists=%s", os.path.isfile(norm), os.path.exists(norm))
                if os.path.isfile(norm):
                    await asyncio.to_thread(
                        service_manager.vm_service.attach_iso,
                        vm_name=request.name,
                        iso_path=norm,
                    )
                    result["iso_attached"] = norm
                else:
                    logger.warning("ISO path not found, skipping: %r", norm)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating VM {request.name}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


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


@app.get("/api/v1/vms/{name}/snapshots")
async def list_vm_snapshots(name: str):
    """List all snapshots for a VM."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")
    try:
        result = await asyncio.to_thread(service_manager.vm_service.list_snapshots, name)
        return result
    except Exception as e:
        logger.error(f"Error listing snapshots for VM {name}: {e}")
        return {"status": "error", "snapshots": [], "error": str(e)}


@app.post("/api/v1/vms/{name}/restore")
async def restore_vm_snapshot(name: str, request: VMSnapshotRequest):
    """Restore a VM snapshot."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")
    try:
        result = await asyncio.to_thread(service_manager.vm_service.restore_snapshot, name, request.snapshot_name)
        return result
    except Exception as e:
        logger.error(f"Error restoring snapshot for VM {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/vms/{name}/delete-snapshot")
async def delete_vm_snapshot(name: str, request: VMSnapshotRequest):
    """Delete a VM snapshot."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")
    try:
        result = await asyncio.to_thread(service_manager.vm_service.delete_snapshot, name, request.snapshot_name)
        return result
    except Exception as e:
        logger.error(f"Error deleting snapshot for VM {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/v1/vms/{name}")
async def delete_vm(name: str):
    """Delete a VM (VirtualBox)."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")
    try:
        result = await asyncio.to_thread(service_manager.vm_service.delete_vm, name)
        return result
    except Exception as e:
        logger.error(f"Error deleting VM {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/vms/{name}/move-desktop")
async def move_vm_to_desktop(name: str, desktop: int = 2):
    """Move a running VM's window to a specific Windows virtual desktop."""
    import subprocess as _sub

    ps_script = f'''
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class VBoxWindow {{
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [ComImport, Guid("aa509086-5ca9-4c6c-95c2-4cb0f5c7b5e2"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    public interface IVirtualDesktopManager {{
        void IsWindowOnCurrentVirtualDesktop(IntPtr topLevelWindow, out bool onCurrentDesktop);
        void GetWindowDesktopId(IntPtr topLevelWindow, out Guid desktopId);
        void MoveWindowToDesktop(IntPtr topLevelWindow, ref Guid desktopId);
    }}

    public static void MoveToDesktop(string vmName, int targetDesktop) {{
        IntPtr hwnd = FindWindow(null, vmName);
        if (hwnd == IntPtr.Zero) {{
            hwnd = FindWindow("Qt5QWindowIcon", vmName);
        }}
        if (hwnd == IntPtr.Zero) {{
            hwnd = FindWindow("VBoxWindow", vmName);
        }}
        if (hwnd == IntPtr.Zero)
            throw new Exception("Window not found for: " + vmName);

        ShowWindow(hwnd, 1);
        SetForegroundWindow(hwnd);
        System.Threading.Thread.Sleep(200);

        Type mgrType = Type.GetTypeFromCLSID(new Guid("aa509086-5ca9-4c6c-95c2-4cb0f5c7b5e2"));
        var mgr = (IVirtualDesktopManager)Activator.CreateInstance(mgrType);

        Guid desktopId;
        mgr.GetWindowDesktopId(hwnd, out desktopId);

        int currentDesktop = 1;
        try {{ currentDesktop = int.Parse(Environment.GetCommandLineArgs().Skip(1).First() ?? "1"); }} catch {{ }}

        int diff = targetDesktop - currentDesktop;
        string direction = diff > 0 ? "{{RIGHT}}" : "{{LEFT}}";
        int times = Math.Abs(diff);

        for (int i = 0; i < times; i++) {{
            System.Windows.Forms.SendKeys.SendWait("^%{direction}");
            System.Threading.Thread.Sleep(100);
        }}
    }}
}}
"@ -ReferencedAssemblies System.Windows.Forms
[VBoxWindow]::MoveToDesktop("{name}", {desktop})
'''
    try:
        r = _sub.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            return {"status": "success", "message": f"Moved {name} to desktop {desktop}"}
        else:
            return {"status": "error", "message": r.stderr.strip() or r.stdout.strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/v1/vms/{vm_name}/attach-iso")
async def attach_iso_to_vm(vm_name: str, request: AttachIsoRequest):
    """Attach an ISO to a VM (e.g. path from assets/vbox)."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")
    iso_path = (request.iso_path or "").strip()
    logger.debug("Attach ISO raw path: %r", iso_path)
    norm = os.path.normpath(os.path.abspath(iso_path))
    logger.debug("Attach ISO norm path: %r", norm)
    logger.debug("Attach ISO exists: isfile=%s exists=%s", os.path.isfile(norm), os.path.exists(norm))
    if not norm or not os.path.isfile(norm):
        raise HTTPException(status_code=400, detail=f"iso_path must be an existing file: {norm}")
    try:
        result = await asyncio.to_thread(
            service_manager.vm_service.attach_iso,
            vm_name=vm_name,
            iso_path=norm,
        )
        return result
    except Exception as e:
        logger.error(f"Error attaching ISO to {vm_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/vms/{name}/screenshot")
async def get_vm_screenshot(name: str):
    """Capture a screenshot of a running VM's screen."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="VM Service not available")
    import subprocess as _sub

    vbox = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        r = _sub.run([vbox, "controlvm", name, "screenshotpng", tmp_path], capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            raise Exception(r.stderr.strip())
        from fastapi.responses import FileResponse

        return FileResponse(tmp_path, media_type="image/png")
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=501, detail=str(e))


@app.post("/api/v1/vms/{name}/vrde")
async def set_vm_vrde(name: str, request: VrdeRequest):
    """Enable or disable VRDE (remote desktop) for a VM."""
    import subprocess as _sub

    vbox = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
    enable = "on" if request.enabled else "off"
    port_arg = ["--vrdeport", str(request.port)] if request.port else []
    try:
        cmd = [vbox, "modifyvm", name, "--vrde", enable] + port_arg
        r = _sub.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise HTTPException(status_code=400, detail=r.stderr.strip())
        show_cmd = [vbox, "showvminfo", name, "--machinereadable"]
        r2 = _sub.run(show_cmd, capture_output=True, text=True, timeout=30)
        port = "3389"
        for line in r2.stdout.splitlines():
            if line.startswith("vrdeport="):
                port = line.split("=", 1)[1].strip('"')
                break
        return {"status": "success", "vrde": request.enabled, "port": port}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/vms/{name}/vrde")
async def get_vm_vrde(name: str):
    """Get VRDE status and port for a VM."""
    import subprocess as _sub

    vbox = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
    try:
        cmd = [vbox, "showvminfo", name, "--machinereadable"]
        r = _sub.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise HTTPException(status_code=404, detail=f"VM '{name}' not found")
        vrde = "false"
        port = "3389"
        for line in r.stdout.splitlines():
            if line.startswith("vrde="):
                vrde = line.split("=", 1)[1].strip('"').lower()
            elif line.startswith("vrdeport="):
                port = line.split("=", 1)[1].strip('"')
        return {"vrde": vrde in ("on", "true"), "port": int(port)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/vms/{name}/rdp")
async def download_vm_rdp(name: str):
    """Download an .rdp file for connecting to the VM via Remote Desktop."""
    import subprocess as _sub

    vbox = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
    try:
        cmd = [vbox, "showvminfo", name, "--machinereadable"]
        r = _sub.run(cmd, capture_output=True, text=True, timeout=30)
        port = "3389"
        for line in r.stdout.splitlines():
            if line.startswith("vrdeport="):
                port = line.split("=", 1)[1].strip('"')
                break
        rdp = f"full address:s:127.0.0.1:{port}\nprompt for credentials:i:1\nusername:s:user\nscreen mode id:i:2\nsession bpp:i:32\nconnection type:i:2\nnetworkautodetect:i:1\n"
        from fastapi.responses import PlainTextResponse

        return PlainTextResponse(
            content=rdp,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{name}.rdp"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/api/v1/vms/{name}/vnc")
async def vm_vnc_websocket(websocket: WebSocket, name: str):
    """WebSocket proxy: browser (noVNC) -> VM VRDP server."""
    import subprocess as _sub

    await websocket.accept()
    vbox = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
    port = 3389
    try:
        r = _sub.run([vbox, "showvminfo", name, "--machinereadable"], capture_output=True, text=True, timeout=15)
        for line in r.stdout.splitlines():
            if line.startswith("vrdeport="):
                port = int(line.split("=", 1)[1].strip('"'))
                break
    except Exception:
        pass
    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
    except ConnectionRefusedError:
        await websocket.send_text("ERROR: VRDE not running")
        await websocket.close()
        return
    except Exception as e:
        await websocket.send_text(f"ERROR: {e}")
        await websocket.close()
        return

    async def ws_to_tcp():
        try:
            while True:
                data = await websocket.receive_bytes()
                writer.write(data)
                await writer.drain()
        except Exception:
            pass
        finally:
            try:
                writer.close()
            except Exception:
                pass

    async def tcp_to_ws():
        try:
            while True:
                data = await reader.read(65536)
                if not data:
                    break
                await websocket.send_bytes(data)
        except Exception:
            pass
        finally:
            try:
                writer.close()
            except Exception:
                pass

    await asyncio.gather(ws_to_tcp(), tcp_to_ws())


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10761, reload=True)
