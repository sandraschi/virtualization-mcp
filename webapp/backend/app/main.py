from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import sys
import subprocess
import tempfile
import asyncio
from contextlib import asynccontextmanager
import logging
import json
from typing import List, Optional, Any, Dict

import warnings
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

        mcp = await start_mcp_server()
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
            "Python.Python.3.12", "Git.Git", "OpenJS.NodeJS.LTS", "Casey.Just",
            "Microsoft.VisualStudioCode", "Notepad++.Notepad++", "astral-sh.uv",
            "Codeium.Windsurf", "Anysphere.Cursor", "Google.Antigravity",
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
    return f'''# Setup-DevSandbox.ps1 - Full dev stack in Windows Sandbox (virtualization-mcp)
# Automatic: Python, Node, pip, uv/uvx, Git, VS Code, Just, Notepad++, Windsurf, Cursor, Antigravity, Claude Desktop, OpenClaw, OpenFang, RoboFang. Optional: host Ollama.
# Requires in C:\\Assets: DesktopAppInstaller_Dependencies.zip, Microsoft.DesktopAppInstaller_*.msixbundle

$assetRoot = "C:\\Assets"
if (-not (Test-Path $assetRoot)) {{
    Write-Host "Assets folder not found at $assetRoot." -ForegroundColor Red
    exit 1
}}
Set-Location $assetRoot

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

# 3) Refresh PATH for winget
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
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
'''


def _build_sandbox_xml_dev_setup(host_folder: str, memory_mb: int = 4096, vgpu: bool = True, networking: bool = True) -> str:
    import xml.sax.saxutils as sax
    host_escaped = sax.escape(host_folder)
    cmd_escaped = sax.escape(f'powershell -ExecutionPolicy Bypass -File C:\\Assets\\Setup-DevSandbox.ps1')
    return f"""<Configuration>
<VGpu>{"Enable" if vgpu else "Disable"}</VGpu>
<Networking>{"Enable" if networking else "Disable"}</Networking>
<MemoryInMB>{memory_mb}</MemoryInMB>
<MappedFolders>
<MappedFolder>
<HostFolder>{host_escaped}</HostFolder>
<SandboxFolder>C:\\Assets</SandboxFolder>
<ReadOnly>false</ReadOnly>
</MappedFolder>
</MappedFolders>
<LogonCommand>
<Command>{cmd_escaped}</Command>
</LogonCommand>
</Configuration>"""


# Models
class SandboxLaunchRequest(BaseModel):
    name: str
    config_xml: str
    full_dev_setup: Optional[bool] = None
    assets_folder: Optional[str] = None
    dev_tools: Optional[List[str]] = None
    memory_in_mb: Optional[int] = 4096
    vgpu: Optional[bool] = True
    networking: Optional[bool] = True
    airgap: Optional[bool] = None  # if True: networking disabled (OpenClaw 100% safe, no egress)
    use_host_ollama: Optional[bool] = None  # if True: set OLLAMA_HOST to host gateway so sandbox can use host Ollama


class VMCreateRequest(BaseModel):
    name: str
    template: str = "ubuntu-dev"
    memory_mb: Optional[int] = None
    disk_gb: Optional[int] = None
    iso_path: Optional[str] = None  # optional ISO from assets/vbox for first-boot install


class AttachIsoRequest(BaseModel):
    iso_path: str


class VMSnapshotRequest(BaseModel):
    snapshot_name: str
    description: str = ""


class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}


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


# FastMCP 3.1 prompts and skills (for webapp page)
PROMPTS_META = [
    {
        "name": "virtualization_expert",
        "description": "Load instructions for acting as a virtualization expert using this MCP server's tools (VMs, snapshots, storage, networking).",
        "arguments": [{"name": "focus", "default": "general", "description": "Focus area: general, lifecycle, storage, or network"}],
    },
]


def _get_skills_dir():
    try:
        import virtualization_mcp
        from pathlib import Path
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
        vbox_vms = await asyncio.to_thread(
            service_manager.vm_service.list_vms, details=True
        )
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
        "message": None if available else "VirtualBox not detected. Install VirtualBox and ensure VBoxManage is in PATH, or open VirtualBox once.",
    }


@app.post("/api/v1/vbox/launch")
async def vbox_launch():
    """Try to launch the VirtualBox GUI. Helps ensure the VirtualBox service is running."""
    import shutil
    import platform
    vbox_exe = None
    if platform.system() == "Windows":
        for path in [
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Oracle", "VirtualBox", "VirtualBox.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Oracle", "VirtualBox", "VirtualBox.exe"),
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
            await asyncio.create_subprocess_exec("open", *args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
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
        info_result = await asyncio.to_thread(
            service_manager.vm_service.get_system_info
        )
        return info_result
    except Exception as e:
        logger.error(f"Error fetching system info: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/sandbox/dev-setup-script")
async def get_dev_setup_script(tools: Optional[str] = None, use_host_ollama: Optional[bool] = None):
    """Return PowerShell script for full dev setup in Sandbox. Query: tools (comma-separated), use_host_ollama (true/false)."""
    tool_list = [t.strip() for t in (tools or "").split(",") if t.strip()] if tools else list(SANDBOX_DEV_SETUP_TOOLS.keys())
    script = _get_dev_setup_script(tool_list, use_host_ollama=bool(use_host_ollama))
    return {"script": script, "tools": tool_list}


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
                f.write(_get_dev_setup_script(
                    request.dev_tools or list(SANDBOX_DEV_SETUP_TOOLS.keys()),
                    use_host_ollama=use_host_ollama,
                ))
            config_xml = _build_sandbox_xml_dev_setup(
                assets_folder,
                memory_mb=request.memory_in_mb or 4096,
                vgpu=request.vgpu if request.vgpu is not None else True,
                networking=networking,
            )
        else:
            config_xml = request.config_xml

        with tempfile.NamedTemporaryFile(suffix=".wsb", delete=False, mode="w", encoding="utf-8") as tmp:
            tmp.write(config_xml)
            tmp_path = tmp.name

        logger.info(f"Launching sandbox with config: {tmp_path}")
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
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception as e:
        logger.error(f"Error reading registry: {e}")
        return {"webapps": []}


@app.post("/api/v1/chat")
async def chat_interaction(request: ChatRequest):
    """Handle AI chat interactions using Gemini."""
    if not chat_model:
        return {"reply": "Gemini backend is not configured. Please set GOOGLE_API_KEY."}

    try:
        # Convert history format if needed (GenAI uses different format)
        # Simplified for now: just send the message
        # In a real SOTA app, we would inject fleet context here
        prefix = "Context: You are the SOTA Virtualization Assistant. You help manage VMs, Sandboxes, and the MCP Fleet.\n"
        response = await asyncio.to_thread(
            chat_model.generate_content, f"{prefix}{request.message}"
        )
        return {"reply": response.text}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"reply": f"Sorry, I encountered an error: {str(e)}"}


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
            info = await asyncio.to_thread(
                service_manager.vm_service.vbox_manager.get_vm_info, name
            )
            state = info.get("VMState", "").lower()

            if state == "running":
                result = await asyncio.to_thread(
                    service_manager.vm_service.vbox_manager.pause_vm, name
                )
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
            result = await asyncio.to_thread(
                service_manager.vm_service.vbox_manager.resume_vm, name
            )
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
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                # If it's not a VBox VM, or VBox fails, check if we can do something for Hyper-V
                # Hyper-V doesn't have a direct "screenshot" CLI as easily as VBox
                raise Exception(stderr.decode())

            from fastapi.responses import FileResponse

            return FileResponse(tmp_path, media_type="image/png")
        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            logger.error(f"Error taking snapshot for VM {name}: {e}")
            raise HTTPException(
                status_code=501,
                detail=(
                    f"Screenshot capture is under construction for this VM/provider: {str(e)}"
                ),
            ) from e

    except Exception as e:
        logger.error(f"Error in screenshot helper: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10761, reload=True)
