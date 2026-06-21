import {
  AlertCircle,
  CheckCircle2,
  Code,
  Download,
  ExternalLink,
  Loader2,
  Package,
  Play,
  Save,
  Wrench,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { API_BASE } from "../api/config";

type WsbPreviewTab = "basic" | "devInfra" | "consumer" | "fullDev";

const DEV_TOOL_OPTIONS = [
  { id: "python", label: "Python 3.12" },
  { id: "node", label: "Node.js LTS" },
  { id: "uv", label: "uv / uvx" },
  { id: "git", label: "Git" },
  { id: "just", label: "Just" },
  { id: "vscode", label: "VS Code" },
  { id: "notepad++", label: "Notepad++" },
  { id: "windsurf", label: "Windsurf" },
  { id: "cursor", label: "Cursor" },
  { id: "antigravity", label: "Antigravity" },
  { id: "claude_desktop", label: "Claude Desktop" },
  { id: "openclaw", label: "OpenClaw" },
  { id: "openfang", label: "OpenFang" },
  { id: "robofang", label: "RoboFang" },
] as const;

export default function Sandbox() {
  const [config, setConfig] = useState({
    vGPU: true,
    networking: true,
    audioInput: false,
    videoInput: false,
    printerRedirection: false,
    clipboardRedirection: true,
    memoryInMB: 4096,
  });
  const [status, setStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [error, setError] = useState<string | null>(null);

  const [assetsFolder, setAssetsFolder] = useState("");
  const [devInfraFolder, setDevInfraFolder] = useState("");
  const [devInfraStatus, setDevInfraStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [devInfraError, setDevInfraError] = useState<string | null>(null);
  const [consumerStatus, setConsumerStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [consumerError, setConsumerError] = useState<string | null>(null);
  const [consumerInstallClaude, setConsumerInstallClaude] = useState(true);
  const [previewTab, setPreviewTab] = useState<WsbPreviewTab>("devInfra");
  const [previewXml, setPreviewXml] = useState<string | null>(null);
  const [previewFilename, setPreviewFilename] = useState("DevInfra.wsb");
  const [previewError, setPreviewError] = useState<string | null>(null);

  const [devTools, setDevTools] = useState<Record<string, boolean>>(() => {
    const core = ["python", "node", "uv", "git", "just", "vscode", "notepad++"];
    return Object.fromEntries(
      DEV_TOOL_OPTIONS.map(({ id }) => [id, core.includes(id)]),
    );
  });
  const [devStatus, setDevStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [devError, setDevError] = useState<string | null>(null);
  const [airgap, setAirgap] = useState(false);
  const [useHostOllama, setUseHostOllama] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/assets/paths`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.assets_sandbox) {
          setAssetsFolder((prev) => prev || data.assets_sandbox);
          setDevInfraFolder((prev) => prev || data.assets_sandbox);
        }
      })
      .catch(() => {});
  }, []);

  const fetchWsbPreview = useCallback(async () => {
    if (previewTab === "basic") {
      setPreviewXml(null);
      setPreviewError(null);
      setPreviewFilename("BasicSandbox.wsb");
      return;
    }
    setPreviewError(null);
    const params = new URLSearchParams();
    params.set(
      "preset",
      previewTab === "devInfra"
        ? "dev-infra"
        : previewTab === "consumer"
          ? "consumer"
          : "full-dev",
    );
    params.set("memory_in_mb", String(config.memoryInMB));
    params.set("vgpu", config.vGPU ? "true" : "false");
    params.set("networking", config.networking ? "true" : "false");
    if (previewTab === "devInfra" || previewTab === "consumer") {
      if (devInfraFolder.trim())
        params.set("assets_folder", devInfraFolder.trim());
    } else if (assetsFolder.trim()) {
      params.set("assets_folder", assetsFolder.trim());
    }
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/sandbox/wsb-preview?${params}`,
      );
      const text = await res.text();
      if (!res.ok) {
        let msg = text;
        try {
          const j = JSON.parse(text);
          if (j.detail)
            msg =
              typeof j.detail === "string"
                ? j.detail
                : JSON.stringify(j.detail);
        } catch {
          /* keep raw */
        }
        throw new Error(msg);
      }
      const data = JSON.parse(text);
      setPreviewXml(data.xml);
      setPreviewFilename(data.filename || "sandbox.wsb");
    } catch (e: unknown) {
      setPreviewXml(null);
      setPreviewError(e instanceof Error ? e.message : "Preview failed");
    }
  }, [
    previewTab,
    devInfraFolder,
    assetsFolder,
    config.memoryInMB,
    config.vGPU,
    config.networking,
  ]);

  useEffect(() => {
    const t = window.setTimeout(() => {
      void fetchWsbPreview();
    }, 300);
    return () => window.clearTimeout(t);
  }, [fetchWsbPreview]);

  const getXmlPreview = () =>
    `
<Configuration>
  <VGpu>${config.vGPU ? "Default" : "Disable"}</VGpu>
  <Networking>${config.networking ? "Default" : "Disable"}</Networking>
  <AudioInput>${config.audioInput ? "Default" : "Disable"}</AudioInput>
  <VideoInput>${config.videoInput ? "Default" : "Disable"}</VideoInput>
  <PrinterRedirection>${config.printerRedirection ? "Default" : "Disable"}</PrinterRedirection>
  <ClipboardRedirection>${config.clipboardRedirection ? "Default" : "Disable"}</ClipboardRedirection>
  <MemoryInMB>${config.memoryInMB}</MemoryInMB>
</Configuration>
  `.trim();

  const checkSandboxRunning = async (): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/sandbox/status`);
      if (res.ok) {
        const status = await res.json();
        if (status.running) {
          return window.confirm(
            "A Windows Sandbox is already running.\n\n" +
              "Close it and launch a new one?\n\n" +
              "Click OK to close the existing sandbox and start a new one.\n" +
              "Click Cancel to keep the existing sandbox running.",
          );
        }
      }
    } catch {
      /* backend unreachable, proceed anyway */
    }
    return true;
  };

  const handleLaunch = async () => {
    if (!(await checkSandboxRunning())) return;
    setStatus("loading");
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/v1/sandbox/launch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "DevSandbox",
          config_xml: getXmlPreview(),
        }),
      });

      if (!response.ok) throw new Error(await response.text());

      setStatus("success");
      setTimeout(() => setStatus("idle"), 3000);
    } catch (err: any) {
      console.error("Launch failed:", err);
      setError(err.message || "Failed to launch sandbox");
      setStatus("error");
    }
  };

  const handleDownloadSetupScript = async () => {
    const tools = DEV_TOOL_OPTIONS.filter(({ id }) => devTools[id]).map(
      ({ id }) => id,
    );
    const params = new URLSearchParams();
    if (tools.length) params.set("tools", tools.join(","));
    if (useHostOllama) params.set("use_host_ollama", "true");
    const q = params.toString() ? `?${params.toString()}` : "";
    const res = await fetch(`${API_BASE}/api/v1/sandbox/dev-setup-script${q}`);
    if (!res.ok) throw new Error(await res.text());
    const { script } = await res.json();
    const blob = new Blob([script], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "Setup-DevSandbox.ps1";
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const handleLaunchFullDev = async () => {
    if (!(await checkSandboxRunning())) return;
    if (!assetsFolder.trim()) {
      setDevError("Enter the assets folder path");
      return;
    }
    setDevStatus("loading");
    setDevError(null);
    try {
      const tools = DEV_TOOL_OPTIONS.filter(({ id }) => devTools[id]).map(
        ({ id }) => id,
      );
      const response = await fetch(`${API_BASE}/api/v1/sandbox/launch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "DevSandbox",
          config_xml: "",
          full_dev_setup: true,
          assets_folder: assetsFolder.trim(),
          dev_tools: tools.length ? tools : undefined,
          memory_in_mb: config.memoryInMB,
          vgpu: config.vGPU,
          networking: airgap ? false : config.networking,
          airgap: airgap,
          use_host_ollama: airgap ? false : useHostOllama,
        }),
      });
      if (!response.ok) {
        const text = await response.text();
        let msg = text;
        try {
          const j = JSON.parse(text);
          if (j.detail)
            msg =
              typeof j.detail === "string"
                ? j.detail
                : JSON.stringify(j.detail);
        } catch (_) {}
        throw new Error(msg);
      }
      setDevStatus("success");
      setTimeout(() => setDevStatus("idle"), 3000);
    } catch (err: any) {
      setDevError(err.message || "Launch failed");
      setDevStatus("error");
    }
  };

  const toggleDevTool = (id: string) =>
    setDevTools((prev) => ({ ...prev, [id]: !prev[id] }));

  const handleLaunchDevInfra = async () => {
    if (!(await checkSandboxRunning())) return;
    setDevInfraStatus("loading");
    setDevInfraError(null);
    try {
      const body: Record<string, unknown> = {
        name: "DevInfraSandbox",
        config_xml: "",
        dev_infra_setup: true,
        memory_in_mb: config.memoryInMB,
        vgpu: config.vGPU,
        networking: config.networking,
      };
      if (devInfraFolder.trim()) body.assets_folder = devInfraFolder.trim();
      const response = await fetch(`${API_BASE}/api/v1/sandbox/launch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const text = await response.text();
        let msg = text;
        try {
          const j = JSON.parse(text);
          if (j.detail)
            msg =
              typeof j.detail === "string"
                ? j.detail
                : JSON.stringify(j.detail);
        } catch {
          /* keep raw */
        }
        throw new Error(msg);
      }
      setDevInfraStatus("success");
      setTimeout(() => setDevInfraStatus("idle"), 3000);
    } catch (err: unknown) {
      setDevInfraError(err instanceof Error ? err.message : "Launch failed");
      setDevInfraStatus("error");
    }
  };

  const handleLaunchConsumer = async () => {
    if (!(await checkSandboxRunning())) return;
    setConsumerStatus("loading");
    setConsumerError(null);
    try {
      const body: Record<string, unknown> = {
        name: "ConsumerSandbox",
        config_xml: "",
        consumer_setup: true,
        consumer_install_claude: consumerInstallClaude,
        memory_in_mb: config.memoryInMB,
        vgpu: config.vGPU,
        networking: config.networking,
      };
      if (devInfraFolder.trim()) body.assets_folder = devInfraFolder.trim();
      const response = await fetch(`${API_BASE}/api/v1/sandbox/launch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const text = await response.text();
        let msg = text;
        try {
          const j = JSON.parse(text);
          if (j.detail)
            msg =
              typeof j.detail === "string"
                ? j.detail
                : JSON.stringify(j.detail);
        } catch {
          /* keep raw */
        }
        throw new Error(msg);
      }
      setConsumerStatus("success");
      setTimeout(() => setConsumerStatus("idle"), 3000);
    } catch (err: unknown) {
      setConsumerError(err instanceof Error ? err.message : "Launch failed");
      setConsumerStatus("error");
    }
  };

  const handleDownloadCurrentWsb = () => {
    const xml = previewTab === "basic" ? getXmlPreview() : previewXml;
    if (previewTab !== "basic" && !xml) {
      window.alert(
        previewError ||
          "Preview not ready. Fix errors above or wait for preview to load.",
      );
      return;
    }
    const blob = new Blob([xml || ""], { type: "application/xml" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = previewFilename;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const previewBody =
    previewTab === "basic"
      ? getXmlPreview()
      : previewError
        ? `<!-- ${previewError} -->`
        : previewXml || "Loading preview…";

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-8rem)]">
      {/* Configuration Form */}
      <div className="space-y-6">
        <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 px-4 py-3 text-xs text-muted-foreground">
          <strong>Requirement:</strong> Windows Sandbox is only available on{" "}
          <strong>Windows 11 Pro, Enterprise, or Education</strong>. It is not
          available on Windows Home edition.
        </div>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Windows Sandbox</h2>
          <p className="text-muted-foreground mt-1">
            Configure and launch ephemeral Windows instances
          </p>
          <p className="text-amber-400 mt-2 text-sm">
            Under construction: some Sandbox automation paths are not
            implemented yet and will return explicit errors.
          </p>
        </div>

        <div className="p-6 rounded-xl border border-border bg-card/40 backdrop-blur-sm space-y-6">
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">Hardware</h3>
            <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/5">
              <div>
                <span className="font-medium block">vGPU Support</span>
                <span className="text-xs text-muted-foreground">
                  Enable virtualized graphics
                </span>
              </div>
              <input
                type="checkbox"
                title="vGPU Support"
                aria-label="vGPU Support"
                checked={config.vGPU}
                onChange={(e) =>
                  setConfig({ ...config, vGPU: e.target.checked })
                }
                className="w-5 h-5 rounded border-input bg-background/50 text-primary focus:ring-primary"
              />
            </div>

            <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/5">
              <div>
                <span className="font-medium block">Memory (MB)</span>
                <span className="text-xs text-muted-foreground">
                  Allocated RAM
                </span>
              </div>
              <input
                type="number"
                title="Memory in MB"
                aria-label="Memory in MB"
                value={config.memoryInMB}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    memoryInMB: parseInt(e.target.value, 10),
                  })
                }
                className="bg-transparent border border-input rounded px-2 py-1 w-24 text-right"
              />
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="font-semibold text-lg">Features</h3>
            <div className="grid grid-cols-2 gap-4">
              {[
                { label: "Networking", key: "networking" },
                { label: "Audio Input", key: "audioInput" },
                { label: "Video Input", key: "videoInput" },
                { label: "Clipboard", key: "clipboardRedirection" },
              ].map((feature) => (
                <button
                  key={feature.key}
                  onClick={() =>
                    setConfig({
                      ...config,
                      [feature.key]:
                        !config[feature.key as keyof typeof config],
                    })
                  }
                  className={`p-4 rounded-lg border text-left transition-all ${
                    config[feature.key as keyof typeof config]
                      ? "bg-primary/10 border-primary/20 text-primary"
                      : "bg-white/5 border-white/5 text-muted-foreground hover:bg-white/10"
                  }`}
                >
                  <span className="font-medium text-sm">{feature.label}</span>
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {error}
            </div>
          )}

          <div className="pt-4 flex gap-3">
            <button
              disabled={status === "loading"}
              onClick={handleLaunch}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all transform active:scale-95 ${
                status === "success"
                  ? "bg-green-600 text-white"
                  : "bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg shadow-primary/20"
              }`}
            >
              {status === "loading" ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : status === "success" ? (
                <CheckCircle2 className="w-5 h-5" />
              ) : (
                <Play className="w-5 h-5" />
              )}
              {status === "loading"
                ? "Launching..."
                : status === "success"
                  ? "Launched"
                  : "Launch Sandbox"}
            </button>
            <button
              title="Save Configuration"
              aria-label="Save Configuration"
              className="px-4 py-3 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-colors text-muted-foreground hover:text-foreground"
            >
              <Save className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* WSB: online dev infra (repo script + winget from network) */}
        <div className="p-6 rounded-xl border border-border bg-card/40 backdrop-blur-sm space-y-4">
          <h3 className="font-semibold text-lg flex items-center gap-2">
            <Package className="w-5 h-5" />
            WSB: Dev infra (online)
          </h3>
          <p className="text-sm text-muted-foreground">
            Launches Windows Sandbox with{" "}
            <code className="text-foreground/80">assets/sandbox</code> mapped to{" "}
            <code className="text-foreground/80">C:\Assets</code> and runs{" "}
            <code className="text-foreground/80">Run-DevInfra.cmd</code> at
            logon (short wait, then{" "}
            <code className="text-foreground/80">
              Setup-DevInfraSandbox.ps1
            </code>
            ). That script installs winget from GitHub, then winget installs:
            Git, GitHub CLI, Node LTS (npm), Python 3.12, ruff, just, Biome.
            Requires outbound HTTPS. If nothing happens, a second PowerShell
            window opens with the tail of{" "}
            <code className="text-foreground/80">
              Desktop\dev-infra-launch.log
            </code>{" "}
            (Notepad is often missing in Sandbox).
          </p>
          <div>
            <label className="block text-sm font-medium mb-1">
              Host folder (Setup-DevInfraSandbox.ps1, Run-DevInfra.cmd,
              Show-DevInfraLog.ps1)
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={devInfraFolder}
                onChange={(e) => setDevInfraFolder(e.target.value)}
                placeholder="Defaults to repo assets/sandbox from API"
                className="flex-1 bg-background/50 border border-input rounded px-3 py-2 font-mono text-sm"
              />
              <button
                type="button"
                onClick={() =>
                  fetch(`${API_BASE}/api/v1/assets/paths`)
                    .then((r) => (r.ok ? r.json() : null))
                    .then(
                      (d) =>
                        d?.assets_sandbox &&
                        setDevInfraFolder(d.assets_sandbox),
                    )
                }
                className="px-3 py-2 rounded-lg border border-border bg-white/5 hover:bg-white/10 text-sm whitespace-nowrap"
              >
                Use repo assets
              </button>
            </div>
          </div>
          {devInfraError && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {devInfraError}
            </div>
          )}
          <div className="flex gap-2">
            <button
              type="button"
              disabled={devInfraStatus === "loading"}
              onClick={handleLaunchDevInfra}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium ${devInfraStatus === "success" ? "bg-green-600 text-white" : "bg-primary text-primary-foreground hover:bg-primary/90"}`}
            >
              {devInfraStatus === "loading" ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : devInfraStatus === "success" ? (
                <CheckCircle2 className="w-5 h-5" />
              ) : (
                <Play className="w-5 h-5" />
              )}
              {devInfraStatus === "loading"
                ? "Launching…"
                : devInfraStatus === "success"
                  ? "Launched"
                  : "Launch dev infra sandbox"}
            </button>
          </div>
        </div>

        {/* WSB: consumer / nearly-naked install test */}
        <div className="p-6 rounded-xl border border-emerald-500/20 bg-emerald-500/5 backdrop-blur-sm space-y-4">
          <h3 className="font-semibold text-lg flex items-center gap-2">
            <Package className="w-5 h-5" />
            WSB: Consumer (nearly naked)
          </h3>
          <p className="text-sm text-muted-foreground">
            Validates fleet{" "}
            <code className="text-foreground/80">INSTALL.md</code> Options A–C.
            Bootstraps winget only — does <strong>not</strong> install git, uv,
            node, just, ruff, or biome. Optional Claude Desktop MSIX for Option
            A drag-and-drop tests. Checklist on Desktop:{" "}
            <code className="text-foreground/80">
              consumer-install-test-checklist.txt
            </code>
            .
          </p>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={consumerInstallClaude}
              onChange={(e) => setConsumerInstallClaude(e.target.checked)}
              className="rounded border-input bg-background/50 text-primary"
            />
            <span className="text-sm">
              Install Claude Desktop MSIX at logon (Option A fixture)
            </span>
          </label>
          <p className="text-xs text-muted-foreground">
            Host script:{" "}
            <code className="text-foreground/80">
              scripts/Launch-ConsumerSandbox.ps1
            </code>{" "}
            (same assets folder as dev infra below)
          </p>
          {consumerError && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {consumerError}
            </div>
          )}
          <div className="flex gap-2">
            <button
              type="button"
              disabled={consumerStatus === "loading"}
              onClick={handleLaunchConsumer}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium ${consumerStatus === "success" ? "bg-green-600 text-white" : "bg-emerald-600 text-white hover:bg-emerald-700"}`}
            >
              {consumerStatus === "loading" ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : consumerStatus === "success" ? (
                <CheckCircle2 className="w-5 h-5" />
              ) : (
                <Play className="w-5 h-5" />
              )}
              {consumerStatus === "loading"
                ? "Launching…"
                : consumerStatus === "success"
                  ? "Launched"
                  : "Launch consumer sandbox"}
            </button>
          </div>
        </div>

        {/* Full dev setup */}
        <div className="p-6 rounded-xl border border-border bg-card/40 backdrop-blur-sm space-y-4">
          <h3 className="font-semibold text-lg flex items-center gap-2">
            <Wrench className="w-5 h-5" />
            Full dev setup
          </h3>
          <p className="text-sm text-muted-foreground">
            Place{" "}
            <code className="text-foreground/80">
              DesktopAppInstaller_Dependencies.zip
            </code>{" "}
            and{" "}
            <code className="text-foreground/80">
              Microsoft.DesktopAppInstaller_*.msixbundle
            </code>{" "}
            in a folder, then launch. Script installs winget, then selected
            tools.
          </p>
          <a
            href="https://github.com/microsoft/winget-cli/releases"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs flex items-center gap-1 text-primary hover:underline"
          >
            <ExternalLink className="w-3 h-3" />
            winget-cli releases (Assets)
          </a>
          <div>
            <label className="block text-sm font-medium mb-1">
              Assets folder (host path)
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={assetsFolder}
                onChange={(e) => setAssetsFolder(e.target.value)}
                placeholder="e.g. D:\Dev\repos\virtualization-mcp\assets\sandbox"
                className="flex-1 bg-background/50 border border-input rounded px-3 py-2 font-mono text-sm"
              />
              <button
                type="button"
                onClick={() =>
                  fetch(`${API_BASE}/api/v1/assets/paths`)
                    .then((r) => (r.ok ? r.json() : null))
                    .then(
                      (d) =>
                        d?.assets_sandbox && setAssetsFolder(d.assets_sandbox),
                    )
                }
                className="px-3 py-2 rounded-lg border border-border bg-white/5 hover:bg-white/10 text-sm whitespace-nowrap"
              >
                Use repo assets
              </button>
            </div>
          </div>
          <div>
            <span className="block text-sm font-medium mb-2">
              Tools to install
            </span>
            <div className="flex flex-wrap gap-2">
              {DEV_TOOL_OPTIONS.map(({ id, label }) => (
                <label
                  key={id}
                  className="flex items-center gap-2 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={!!devTools[id]}
                    onChange={() => toggleDevTool(id)}
                    className="rounded border-input bg-background/50 text-primary"
                  />
                  <span className="text-sm">{label}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="flex flex-col gap-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={useHostOllama}
                disabled={airgap}
                onChange={(e) => setUseHostOllama(e.target.checked)}
                className="rounded border-input bg-background/50 text-primary"
              />
              <span className="text-sm">
                Use host Ollama (sandbox can reach Ollama on host at
                gateway:11434)
              </span>
            </label>
            <button
              type="button"
              onClick={() => setAirgap((a) => !a)}
              className={`w-full py-4 rounded-xl font-bold text-lg uppercase tracking-widest border-2 transition-all ${
                airgap
                  ? "bg-red-600 border-red-700 text-white hover:bg-red-700"
                  : "bg-transparent border-red-500/50 text-red-500 hover:bg-red-500/10"
              }`}
              title="Disable networking for this sandbox (100% air-gapped; use after initial install or with pre-installed assets)"
            >
              {airgap ? "🔒 Airgap on" : "AIRGAP"}
            </button>
            {airgap && (
              <p className="text-xs text-muted-foreground">
                Networking disabled. OpenClaw and other tools cannot reach the
                internet. Run setup once with network, then launch with AIRGAP
                for a safe session.
              </p>
            )}
          </div>
          {devError && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {devError}
            </div>
          )}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleDownloadSetupScript}
              className="px-4 py-2 rounded-lg border border-border bg-background/50 hover:bg-white/10 text-sm"
            >
              <Download className="w-4 h-4 inline mr-1" />
              Download script
            </button>
            <button
              disabled={devStatus === "loading"}
              onClick={handleLaunchFullDev}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium text-sm ${devStatus === "success" ? "bg-green-600 text-white" : "bg-primary text-primary-foreground hover:bg-primary/90"}`}
            >
              {devStatus === "loading" ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              {devStatus === "loading"
                ? "Launching..."
                : devStatus === "success"
                  ? "Launched"
                  : "Launch with full dev setup"}
            </button>
          </div>
        </div>
      </div>

      {/* Preview */}
      <div className="flex flex-col h-full rounded-xl border border-border bg-card/60 backdrop-blur-md overflow-hidden min-h-[24rem]">
        <div className="p-4 border-b border-border bg-black/20 flex flex-col gap-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Code className="w-4 h-4" />
              <span className="text-sm font-mono">WSB preview</span>
            </div>
            <button
              type="button"
              onClick={handleDownloadCurrentWsb}
              className="text-xs flex items-center gap-1 text-primary hover:underline"
            >
              <Download className="w-3 h-3" />
              Download {previewFilename}
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {(
              [
                { id: "basic" as const, label: "Basic hardware" },
                { id: "devInfra" as const, label: "Dev infra WSB" },
                { id: "consumer" as const, label: "Consumer WSB" },
                { id: "fullDev" as const, label: "Full dev WSB" },
              ] as const
            ).map(({ id, label }) => (
              <button
                key={id}
                type="button"
                onClick={() => setPreviewTab(id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                  previewTab === id
                    ? "bg-primary/20 border-primary/40 text-primary"
                    : "bg-white/5 border-white/10 text-muted-foreground hover:bg-white/10"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        <div className="flex-1 overflow-auto p-4 bg-black/40">
          <pre className="font-mono text-sm text-green-400 whitespace-pre-wrap break-all">
            {previewBody}
          </pre>
        </div>
      </div>
    </div>
  );
}
