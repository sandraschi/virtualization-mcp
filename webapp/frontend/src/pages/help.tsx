import {
  AlertTriangle,
  Book,
  Box,
  Bug,
  CheckCircle2,
  HelpCircle,
  LifeBuoy,
  Monitor,
  RefreshCw,
  Server,
  Terminal,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useState } from "react";

const tabs = [
  {
    id: "getting-started",
    label: "Getting Started",
    icon: Book,
    content: () => (
      <div className="space-y-8">
        <section>
          <h3 className="text-xl font-bold mb-3">Quick Start</h3>
          <div className="grid gap-4">
            {[
              {
                step: "1",
                title: "Install the app",
                desc: "Download the NSIS installer from GitHub Releases and run it. The installer includes both the desktop shell and Python backend in a single file.",
              },
              {
                step: "2",
                title: "Launch Virtualization MCP",
                desc: 'Start the app from the Start Menu or desktop shortcut. The backend starts automatically — wait about 20 seconds for the status badge to turn green ("Connected").',
              },
              {
                step: "3",
                title: "Check VirtualBox is detected",
                desc: "The Dashboard shows VirtualBox status. If it says 'VirtualBox not found', install VirtualBox 7+ and ensure VBoxManage.exe is on your PATH.",
              },
              {
                step: "4",
                title: "Explore the pages",
                desc: "Use the sidebar to navigate: VirtualBox (manage VMs), Windows Sandbox (launch sandboxes), Tools Console, AI Chat, Apps Hub, and Settings.",
              },
            ].map((item) => (
              <div
                key={item.step}
                className="flex gap-4 p-4 rounded-xl border border-border bg-card/40"
              >
                <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-sm shrink-0">
                  {item.step}
                </div>
                <div>
                  <h4 className="font-semibold">{item.title}</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    {item.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h3 className="text-xl font-bold mb-3">Requirements</h3>
          <div className="grid md:grid-cols-2 gap-3">
            {[
              {
                label: "Windows 11 Pro/Enterprise/Education",
                note: "Required for Hyper-V and Windows Sandbox",
              },
              {
                label: "VirtualBox 7+",
                note: "Required for VM management features. VBoxManage must be on PATH.",
              },
              {
                label: "Python 3.12+",
                note: "Only needed for development builds. The NSIS installer includes everything.",
              },
              {
                label: "WebView2 Runtime",
                note: "Included with Windows 11. Skip install for most systems.",
              },
            ].map((req) => (
              <div
                key={req.label}
                className="p-4 rounded-xl border border-border bg-card/40"
              >
                <div className="flex items-center gap-2 mb-1">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  <span className="font-semibold text-sm">{req.label}</span>
                </div>
                <p className="text-xs text-muted-foreground">{req.note}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    ),
  },
  {
    id: "virtualbox",
    label: "VirtualBox",
    icon: Server,
    content: () => (
      <div className="space-y-8">
        <section>
          <h3 className="text-xl font-bold mb-3">VM Lifecycle</h3>
          <div className="grid gap-3">
            {[
              {
                action: "List VMs",
                how: "Open the VirtualBox page. All registered VMs appear in a grid with their current state (Running / Powered Off / Saved).",
              },
              {
                action: "Create a VM",
                how: 'Click "Create VM", select a template (Ubuntu, Windows, etc.), configure CPU/RAM/disk, and submit. The VM is registered in VirtualBox with the specified settings.',
              },
              {
                action: "Start / Stop",
                how: "Click the Play or Stop button on any VM card. The action runs asynchronously — the VM list updates automatically.",
              },
              {
                action: "Snapshots",
                how: 'Click the camera icon on a VM to open the snapshot panel. Create snapshots with a name, restore to a previous state, or delete outdated snapshots. This is the built-in VirtualBox snapshot engine, not a full backup.',
              },
              {
                action: "VM Console",
                how: 'Click a VM name to open the Console page (noVNC-style). View the VM screen via screenshot polling, enable VRDP for remote desktop, or download a .rdp file for mstsc.exe.',
              },
            ].map((item) => (
              <div
                key={item.action}
                className="p-4 rounded-xl border border-border bg-card/40"
              >
                <div className="flex items-center gap-2 mb-1">
                  <Monitor className="w-4 h-4 text-primary" />
                  <h4 className="font-semibold">{item.action}</h4>
                </div>
                <p className="text-sm text-muted-foreground">{item.how}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="p-4 rounded-xl border border-amber-500/20 bg-amber-500/5">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-amber-500">
                VBoxSVC Stability
              </h4>
              <p className="text-sm text-muted-foreground mt-1">
                The backend communicates with VirtualBox via VBoxManage, which
                uses the VBoxSVC COM service. If VBoxSVC becomes unresponsive
                (common after repeated operations), VBoxManage calls will hang.
                The backend has a 30-second timeout and will return an error
                instead of hanging. If this happens repeatedly, kill VBoxSVC.exe
                in Task Manager and restart the app.
              </p>
            </div>
          </div>
        </section>
      </div>
    ),
  },
  {
    id: "proxmox",
    label: "Proxmox VE",
    icon: Server,
    content: () => (
      <div className="space-y-8">
        <section>
          <h3 className="text-xl font-bold mb-3">Getting Started with Proxmox</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Proxmox VE is an open-source virtualization platform (KVM + LXC) with
            a REST API. This MCP server can manage a remote Proxmox host through
            the same tool interface used for VirtualBox and Hyper-V.
          </p>
          <div className="grid gap-4">
            <div className="p-4 rounded-xl border border-green-500/20 bg-green-500/5">
              <h4 className="font-semibold text-green-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                Setup is three env vars
              </h4>
              <pre className="mt-2 p-3 rounded-lg bg-black/40 text-xs font-mono text-green-400 overflow-x-auto">
{`PROXMOX_HOST=192.168.1.100
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=your-password`}
              </pre>
              <p className="text-xs text-muted-foreground mt-2">
                Set these in your shell or start.ps1. The MCP server auto-detects
                Proxmox at startup and registers the proxmox_management tool.
                VMs appear merged in the same /api/v1/vms list as VirtualBox and
                Hyper-V VMs.
              </p>
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-xl font-bold mb-3">Supported Operations</h3>
          <div className="grid gap-3">
            {[
              { op: "list_vms", desc: "List all QEMU VMs on the Proxmox node with status, CPU, memory, disk" },
              { op: "start_vm / stop_vm / shutdown_vm", desc: "Power operations — start, hard-stop, or ACPI shutdown by VMID" },
              { op: "create_vm", desc: "Create a VM with configurable CPU, RAM, disk size, ISO, and network bridge" },
              { op: "delete_vm", desc: "Delete a VM (must be stopped first)" },
              { op: "snapshots", desc: "Create, list, and delete VM snapshots via the Proxmox snapshot API" },
              { op: "node_status", desc: "Get node-level CPU, memory, and disk usage" },
              { op: "cluster_resources", desc: "List all resources (VMs, storage, nodes) across the Proxmox cluster" },
            ].map((item) => (
              <div key={item.op} className="flex items-start gap-3 p-3 rounded-xl border border-border bg-card/40">
                <Server className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <div>
                  <code className="text-xs font-mono text-primary">{item.op}</code>
                  <p className="text-xs text-muted-foreground mt-0.5">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="p-4 rounded-xl border border-amber-500/20 bg-amber-500/5">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-amber-500">Prerequisites</h4>
              <ul className="text-sm text-muted-foreground mt-1 space-y-1 list-disc list-inside">
                <li>A running Proxmox VE host (version 7.x or 8.x) — bare metal or VM</li>
                <li>Network connectivity from this machine to the Proxmox host (port 8006)</li>
                <li>Proxmox user with API access (default root@pam works)</li>
                <li>Self-signed TLS cert is normal — set PROXMOX_VERIFY_SSL=0</li>
                <li>If the Proxmox host changes IP, restart the MCP server to re-authenticate</li>
              </ul>
            </div>
          </div>
        </section>
      </div>
    ),
  },
  {
    id: "sandbox",
    label: "Windows Sandbox",
    icon: Box,
    content: () => (
      <div className="space-y-8">
        <section>
          <h3 className="text-xl font-bold mb-3">Sandbox Modes</h3>
          <div className="grid gap-4">
            {[
              {
                mode: "Consumer Sandbox",
                when: "Testing a fresh Windows install or a naked-PC software install walkthrough.",
                how: 'Select "Consumer" preset and launch. The sandbox boots a clean Windows image with no pre-installed tooling.',
              },
              {
                mode: "Dev Infra Sandbox",
                when: "Testing MCP server installs, fleet deployment scripts, or CI-like workflows.",
                how: 'Select "Dev Infra" preset. Includes winget, uv, git, and connectivity to the host network.',
              },
              {
                mode: "Full Dev Sandbox",
                when: "Building or testing code in an isolated environment.",
                how: "Configure tools (Python, Node, VS Code, etc.) via the checkboxes. The sandbox downloads and installs everything automatically on first boot.",
              },
            ].map((item) => (
              <div
                key={item.mode}
                className="p-4 rounded-xl border border-border bg-card/40"
              >
                <h4 className="font-semibold flex items-center gap-2">
                  <Box className="w-4 h-4 text-primary" />
                  {item.mode}
                </h4>
                <p className="text-sm text-muted-foreground mt-1">
                  <span className="font-medium text-foreground">When:</span>{" "}
                  {item.when}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  <span className="font-medium text-foreground">How:</span>{" "}
                  {item.how}
                </p>
              </div>
            ))}
          </div>
        </section>

        <section className="p-4 rounded-xl border border-border bg-card/40">
          <h4 className="font-semibold mb-2">Prerequisites</h4>
          <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
            <li>
              Windows 11 Pro, Enterprise, or Education edition required
            </li>
            <li>
              Virtualization must be enabled in BIOS (Intel VT-x / AMD-V)
            </li>
            <li>
              Windows Sandbox feature must be enabled: Turn Windows features on
              or off → Windows Sandbox
            </li>
            <li>
              Host network access is shared; VPNs may interfere with guest
              connectivity
            </li>
          </ul>
        </section>
      </div>
    ),
  },
  {
    id: "tauri",
    label: "Desktop App",
    icon: Monitor,
    content: () => (
      <div className="space-y-8">
        <section>
          <h3 className="text-xl font-bold mb-3">
            How the Desktop App Works
          </h3>
          <p className="text-sm text-muted-foreground mb-4">
            The NSIS installer bundles two components: the Rust desktop shell
            and the Python backend (frozen with PyInstaller). When you launch
            the app, the Rust process spawns the Python backend in the
            background, then opens the WebView frontend.
          </p>
          <div className="grid gap-3">
            {[
              {
                step: "1. Native shell starts",
                detail:
                  "virtualization-mcp-native.exe launches, loads the web frontend from its embedded dist/ directory.",
              },
              {
                step: "2. Backend spawns",
                detail:
                  "The Rust code finds virtualization-mcp-backend.exe in the resources/ folder and spawns it with PORT=10701, CORS_ORIGINS (includes tauri://localhost), and CREATE_NO_WINDOW.",
              },
              {
                step: "3. Backend boots (15-25s)",
                detail:
                  "The Python process detects VBoxManage, initializes the service manager, registers MCP tools, and starts uvicorn on 127.0.0.1:10701.",
              },
              {
                step: "4. Frontend connects",
                detail:
                  "The WebView JavaScript polls the health endpoint every 10s. Once the backend responds, the dashboard populates with live data.",
              },
            ].map((item) => (
              <div
                key={item.step}
                className="p-4 rounded-xl border border-border bg-card/40"
              >
                <h4 className="font-semibold text-sm">{item.step}</h4>
                <p className="text-sm text-muted-foreground mt-1">
                  {item.detail}
                </p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h3 className="text-xl font-bold mb-3">Backend Status</h3>
          <div className="grid md:grid-cols-3 gap-3">
            {[
              {
                label: "Starting",
                icon: RefreshCw,
                color: "text-yellow-500",
                bg: "bg-yellow-500/10",
                desc: "Backend is booting. Wait 15-25s on first launch.",
              },
              {
                label: "Connected",
                icon: Wifi,
                color: "text-green-500",
                bg: "bg-green-500/10",
                desc: "Backend is running and responding to API calls.",
              },
              {
                label: "Offline",
                icon: WifiOff,
                color: "text-red-500",
                bg: "bg-red-500/10",
                desc: "Backend is not responding. Click Restart or check the stderr log.",
              },
            ].map((item) => (
              <div
                key={item.label}
                className={`p-4 rounded-xl border border-border ${item.bg}`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <item.icon className={`w-4 h-4 ${item.color}`} />
                  <span className={`font-semibold text-sm ${item.color}`}>
                    {item.label}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="p-4 rounded-xl border border-border bg-card/40">
          <h4 className="font-semibold mb-2">Log Files</h4>
          <p className="text-sm text-muted-foreground mb-3">
            All log files are in{" "}
            <code className="px-1 py-0.5 rounded bg-white/5 text-xs">
              %LOCALAPPDATA%\ai.fleet.virtualization-mcp\logs\
            </code>
          </p>
          <div className="grid gap-2 text-sm">
            {[
              {
                file: "backend-spawn.log",
                what: "Rust spawn process: shows backend.exe path, port, health check results",
              },
              {
                file: "backend-stderr.log",
                what: "Python stderr: shows warnings, errors, and crash tracebacks",
              },
            ].map((log) => (
              <div
                key={log.file}
                className="flex items-start gap-2 p-2 rounded-lg bg-white/5"
              >
                <Terminal className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
                <div>
                  <code className="text-xs font-mono">{log.file}</code>
                  <p className="text-xs text-muted-foreground">{log.what}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="p-4 rounded-xl border border-amber-500/20 bg-amber-500/5">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-amber-500">
                Frontend shows "Offline" but backend is running
              </h4>
              <p className="text-sm text-muted-foreground mt-1">
                The frontend health check uses an HTTP fetch to{" "}
                <code className="px-1 py-0.5 rounded bg-white/5 text-xs">
                  http://127.0.0.1:10701/api/v1/health
                </code>
                . If the backend process is alive but the port is not
                responding, a background task (VBoxManage, Hyper-V PowerShell,
                etc.) may be blocking the uvicorn worker. Click "Restart
                Backend" to kill and respawn the backend process.
              </p>
            </div>
          </div>
        </section>
      </div>
    ),
  },
  {
    id: "troubleshooting",
    label: "Troubleshooting",
    icon: Bug,
    content: () => (
      <div className="space-y-8">
        <section>
          <h3 className="text-xl font-bold mb-3">Common Issues</h3>
          <div className="grid gap-4">
            {[
              {
                problem: "App opens but shows 'Offline'",
                causes: [
                  "Backend is still starting (wait 20-30 seconds on first launch)",
                  "Backend process crashed — check backend-stderr.log for traceback",
                  "Firewall or antivirus blocking 127.0.0.1:10701",
                ],
                fix: "Wait 30 seconds. If still Offline, click 'Restart Backend'. If that fails, check the log file at %LOCALAPPDATA%\\ai.fleet.virtualization-mcp\\logs\\backend-stderr.log.",
              },
              {
                problem: "VirtualBox page shows VMs then goes Offline",
                causes: [
                  "VBoxSVC service is stuck (common after repeated operations)",
                  "VBoxManage list vms --long hangs on a corrupt VBoxSVC instance",
                  "Previous overlapped polling calls corrupted the VBoxSVC state",
                ],
                fix: "Kill VBoxSVC.exe in Task Manager, then restart the app. The backend now has a 30-second subprocess timeout, so hung VBoxManage calls will return an error instead of blocking forever.",
              },
              {
                problem: "Restart Backend button does nothing",
                causes: [
                  "The Tauri invoke command fails silently",
                  "Backend process is in a state where it can't be killed",
                ],
                fix: "Close the app completely, check Task Manager for orphaned virtualization-mcp-backend.exe and kill it, then relaunch.",
              },
              {
                problem: "NSIS installer appears to hang",
                causes: [
                  "PREINSTALL hook is trying to kill old processes",
                  "Old backend.exe is file-locked by a running instance",
                ],
                fix: "Kill any virtualization-mcp-native.exe and virtualization-mcp-backend.exe processes in Task Manager, then run the installer again.",
              },
              {
                problem: "can't connect to http://localhost:10701",
                causes: [
                  "Windows resolves localhost to IPv6 ::1, backend binds to IPv4 127.0.0.1",
                ],
                fix: "Use http://127.0.0.1:10701 instead of http://localhost:10701. The app now uses 127.0.0.1 by default.",
              },
            ].map((item) => (
              <div
                key={item.problem}
                className="p-4 rounded-xl border border-red-500/10 bg-red-500/5"
              >
                <h4 className="font-semibold text-red-400 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  {item.problem}
                </h4>
                <div className="mt-2 space-y-1">
                  <p className="text-xs font-medium text-muted-foreground">
                    Causes:
                  </p>
                  <ul className="text-xs text-muted-foreground list-disc list-inside space-y-0.5">
                    {item.causes.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
                <div className="mt-2 p-2 rounded-lg bg-green-500/10 border border-green-500/20">
                  <p className="text-xs font-medium text-green-400">Fix:</p>
                  <p className="text-xs text-muted-foreground">{item.fix}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="p-4 rounded-xl border border-border bg-card/40">
          <h4 className="font-semibold mb-2">Diagnostics</h4>
          <p className="text-sm text-muted-foreground mb-3">
            Run these commands in PowerShell to check backend health:
          </p>
          <div className="space-y-2">
            {[
              {
                cmd: 'Invoke-WebRequest http://127.0.0.1:10701/api/v1/health',
                what: "Check if backend responds",
              },
              {
                cmd: 'Get-NetTCPConnection -LocalPort 10701',
                what: "Check if port 10701 is listening",
              },
              {
                cmd: 'Get-Process -Name virtualization-mcp-backend',
                what: "Check if backend process exists",
              },
              {
                cmd: 'Get-Content "$env:LOCALAPPDATA\\ai.fleet.virtualization-mcp\\logs\\backend-stderr.log" -Tail 20',
                what: "Read latest backend errors",
              },
            ].map((diag) => (
              <div
                key={diag.cmd}
                className="flex items-start gap-2 p-2 rounded-lg bg-black/30"
              >
                <Terminal className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <div>
                  <code className="text-xs font-mono text-green-400">
                    {diag.cmd}
                  </code>
                  <p className="text-xs text-muted-foreground">{diag.what}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    ),
  },
  {
    id: "faq",
    label: "FAQ",
    icon: HelpCircle,
    content: () => (
      <div className="space-y-6">
        {[
          {
            q: "What's the difference between Consumer and Dev Infra sandboxes?",
            a: 'Consumer sandbox has no pre-installed tooling — it simulates a "naked PC" for testing install walkthroughs. Dev Infra includes winget, uv, git, and network access for testing fleet deployment scripts.',
            cat: "Sandbox",
          },
          {
            q: "Why does the backend take so long to start?",
            a: "On first launch, the PyInstaller bundle extracts to a temp directory, Python initializes, uvicorn starts, the service manager detects VBoxManage, Hyper-V availability is probed via PowerShell, and MCP tools are registered. This takes 15-25 seconds. Subsequent launches are faster due to OS file caching.",
            cat: "Desktop App",
          },
          {
            q: "Can I run the backend without the Tauri desktop app?",
            a: "Yes. Run `uv run python run_server.py` from the repo root, or `uv run uvicorn webapp.backend.app.main:app --host 127.0.0.1 --port 10701` for development. The frontend is a separate Vite dev server at port 10700.",
            cat: "Desktop App",
          },
          {
            q: "How do I add my own VM templates?",
            a: "Templates are defined in config/vm_templates.yaml. Each template specifies CPU, RAM, disk, OS type, and network mode. You can also create templates via the VirtualBox page UI.",
            cat: "VirtualBox",
          },
          {
            q: "Does the app work without VirtualBox installed?",
            a: "Partially. The Dashboard and Hyper-V pages still work. VirtualBox-specific features (VM lifecycle, snapshots, networking) are disabled and show a download prompt.",
            cat: "VirtualBox",
          },
          {
            q: "How do I get help for MCP tools?",
            a: "Open the Tools Console page in the webapp. It lists all registered portmanteau tools with their operations, parameters, and docstrings. You can also call the help tool directly from Claude Desktop or Cursor.",
            cat: "General",
          },
          {
            q: "Can I use the AI Chat without an internet connection?",
            a: "Yes. The Chat page auto-detects local LLM providers (Ollama on :11434, LM Studio on :1234) and uses them as the primary inference backend. Cloud providers (OpenAI, Anthropic, DeepSeek, Gemini) are optional fallbacks.",
            cat: "AI Chat",
          },
          {
            q: "How do I register the MCP server in Cursor or Claude Desktop?",
            a: "The NSIS installer includes an optional post-install hook that registers the server. You can also manually add it: the MCP server listens on http://127.0.0.1:10701/mcp for streamable HTTP, or run `uv run virtualization-mcp` for stdio mode.",
            cat: "MCP",
          },
          {
            q: "Why does the Dashboard show 'Metrics history 404'?",
            a: "The /api/v1/metrics/history endpoint requires psutil data collection that may not be available in all environments. This is cosmetic — the main CPU/Memory chart still works with available data.",
            cat: "Dashboard",
          },
          {
            q: "How do I update to a new version?",
            a: "Download the latest NSIS installer and run it. The installer uninstalls the previous version first (preserving settings), then installs the new one. Your settings and keys are stored in %LOCALAPPDATA%\\virtualization-mcp\\ and persist across updates.",
            cat: "Desktop App",
          },
        ].map((item, i) => (
          <details
            key={i}
            className="group p-4 rounded-xl border border-border bg-card/40 open:border-primary/30 transition-all"
          >
            <summary className="flex items-start gap-3 cursor-pointer list-none">
              <HelpCircle className="w-5 h-5 text-primary shrink-0 mt-0.5 group-open:text-primary" />
              <div>
                <h4 className="font-semibold text-sm">{item.q}</h4>
                <span className="text-xs text-muted-foreground">
                  {item.cat}
                </span>
              </div>
            </summary>
            <p className="text-sm text-muted-foreground mt-3 pl-8">
              {item.a}
            </p>
          </details>
        ))}
      </div>
    ),
  },
];

export default function Help() {
  const [activeTab, setActiveTab] = useState("getting-started");

  const activeContent = tabs.find((t) => t.id === activeTab)?.content;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
            Help & Docs
          </h1>
          <p className="text-muted-foreground mt-1">
            Setup guides, troubleshooting, and reference
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-widest">
          <LifeBuoy className="w-3 h-3" />
          Support Center
        </div>
      </div>

      {/* Horizontal Tabs */}
      <div className="flex gap-1 overflow-x-auto pb-2 border-b border-border">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 rounded-t-xl text-sm font-medium transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? "bg-card border border-b-0 border-border text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Active Tab Content */}
      <div className="animate-in fade-in zoom-in-95 duration-300">
        {activeContent ? activeContent() : null}
      </div>
    </div>
  );
}
