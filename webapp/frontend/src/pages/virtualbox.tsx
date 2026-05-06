import {
  Disc,
  ExternalLink,
  Loader2,
  Monitor,
  Pause,
  Play,
  Plus,
  Power,
  RefreshCw,
  RotateCcw,
  Square,
  Trash2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { API_BASE } from "../api/config";

const VBOX_DOWNLOAD_URL = "https://www.virtualbox.org/wiki/Downloads";
const NETWORK_MODES = [
  { id: "", label: "Default (from template)" },
  { id: "nat", label: "NAT" },
  { id: "bridged", label: "Bridged" },
  { id: "hostonly", label: "Host-Only" },
  { id: "intnet", label: "Internal" },
];

interface VM {
  uuid: string;
  name: string;
  state: string;
  os_type: string;
  memory_mb: number;
  cpus: number;
  provider?: "virtualbox" | "hyperv";
}

interface VBoxAsset {
  name: string;
  path: string;
}

interface IsoItem {
  version: string;
  url: string;
  description: string;
  size: string;
}

interface IsoCategory {
  id: string;
  label: string;
  items: IsoItem[];
}

interface DownloadTask {
  task_id: string;
  url: string;
  filename: string;
  status: string;
  progress: number;
  downloaded: number;
  total: number;
  human_size: string;
  error: string | null;
  file_path: string | null;
}

export default function VirtualBox() {
  const [vms, setVms] = useState<VM[]>([]);
  const [loading, setLoading] = useState(true);
  const [snapshots, setSnapshots] = useState<Record<string, any[]>>({});
  const [expandedSnapshots, setExpandedSnapshots] = useState<Set<string>>(new Set());
  const [actionId, setActionId] = useState<string | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [vboxAvailable, setVboxAvailable] = useState<boolean | null>(null);
  const [launching, setLaunching] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createTemplate, setCreateTemplate] = useState("ubuntu-dev");
  const [createCpus, setCreateCpus] = useState(2);
  const [createMemoryMb, setCreateMemoryMb] = useState(4096);
  const [createDiskGb, setCreateDiskGb] = useState(25);
  const [createIsoPath, setCreateIsoPath] = useState("");
  const [failedScreenshots, setFailedScreenshots] = useState<Set<string>>(new Set());
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [vboxAssets, setVboxAssets] = useState<VBoxAsset[]>([]);
  const [showAttachModal, setShowAttachModal] = useState(false);
  const [attachVmName, setAttachVmName] = useState("");
  const [attachIsoPath, setAttachIsoPath] = useState("");
  const [attachSubmitting, setAttachSubmitting] = useState(false);
  const [showIsoDownload, setShowIsoDownload] = useState(false);
  const [isoCategories, setIsoCategories] = useState<IsoCategory[]>([]);
  const [activeIsoTab, setActiveIsoTab] = useState("ubuntu");
  const [downloadTasks, setDownloadTasks] = useState<Record<string, DownloadTask>>({});
  const [customIsoUrl, setCustomIsoUrl] = useState("");
  const [customIsoName, setCustomIsoName] = useState("");
  const [networkMode, setNetworkMode] = useState("");
  const [templates, setTemplates] = useState<any[]>([]);
  const [showTemplateManager, setShowTemplateManager] = useState(false);
  const [editTemplateName, setEditTemplateName] = useState("");
  const [editTemplateConfig, setEditTemplateConfig] = useState("{}");
  const [creatingTemplate, setCreatingTemplate] = useState(false);
  const [vmNetworks, setVmNetworks] = useState<Record<string, any>>({});
  const [showNetworkConfig, setShowNetworkConfig] = useState<string | null>(null);
  const [showUnattended, setShowUnattended] = useState<string | null>(null);
  const [unattendedUsername, setUnattendedUsername] = useState("user");
  const [unattendedPassword, setUnattendedPassword] = useState("password");
  const [unattendedDevTools, setUnattendedDevTools] = useState<Record<string, boolean>>({});
  const [unattendedUseOllama, setUnattendedUseOllama] = useState(false);

  const fetchVMs = async () => {
    setLoading(true);
    setBackendError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/vms`);
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.status === "success") {
        setVms(data.vms || []);
        setVboxAvailable(true);
      } else {
        setBackendError(
          data.detail ||
            `Backend returned ${res.status}. Ensure backend is running (e.g. run webapp\\start.ps1).`,
        );
        if (
          res.status === 503 ||
          (data.detail && String(data.detail).includes("VM Service"))
        ) {
          setVboxAvailable(false);
        }
      }
    } catch (error) {
      setBackendError(
        `Cannot reach backend at ${API_BASE}. Run webapp\\start.ps1 to start backend.`,
      );
      console.error("Failed to fetch VMs:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchVboxStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/vbox/status`);
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.available === false) setVboxAvailable(false);
    } catch {
      setVboxAvailable(null);
    }
  };

  useEffect(() => {
    fetchVMs();
    fetchVboxStatus();
    fetchTemplates();
    const interval = setInterval(fetchVMs, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleOpenVirtualBox = async () => {
    setLaunching(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/vbox/launch`, {
        method: "POST",
      });
      const data = await res.json().catch(() => ({}));
      if (data.success) {
        setTimeout(fetchVMs, 5000);
      } else {
        console.warn("VirtualBox launch:", data.message);
      }
    } finally {
      setLaunching(false);
    }
  };

  const handleAction = async (
    vmName: string,
    action: string,
    provider: string = "virtualbox",
  ) => {
    setActionId(vmName + action);
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/vms/${vmName}/${action}?provider=${provider}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body:
            action === "snapshot"
              ? JSON.stringify({ snapshot_name: `snap_${Date.now()}` })
              : undefined,
        },
      );
      const data = await res.json();
      console.log(`Action ${action} on ${vmName} (${provider}) result:`, data);
      setTimeout(fetchVMs, 1500);
    } catch (error) {
      console.error(`Failed to execute ${action} on ${vmName}:`, error);
    } finally {
      setActionId(null);
    }
  };

  const fetchSnapshots = async (vmName: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/vms/${encodeURIComponent(vmName)}/snapshots`);
      if (res.ok) {
        const data = await res.json();
        setSnapshots((prev) => ({ ...prev, [vmName]: data.snapshots || [] }));
      }
    } catch { /* ignore */ }
  };

  const toggleSnapshots = (vmName: string) => {
    const next = new Set(expandedSnapshots);
    if (next.has(vmName)) { next.delete(vmName); }
    else { next.add(vmName); fetchSnapshots(vmName); }
    setExpandedSnapshots(next);
  };

  const fetchVboxAssets = () => {
    fetch(`${API_BASE}/api/v1/assets/vbox`)
      .then((r) => (r.ok ? r.json() : { files: [] }))
      .then((d) => setVboxAssets(d.files || []))
      .catch(() => setVboxAssets([]));
  };

  const fetchTemplates = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/templates`);
      if (res.ok) {
        const d = await res.json();
        setTemplates(d.templates || []);
      }
    } catch { /* ignore */ }
  };

  const submitTemplate = async () => {
    if (!editTemplateName.trim()) return;
    setCreatingTemplate(true);
    try {
      let config;
      try { config = JSON.parse(editTemplateConfig); } catch { config = { os_type: "Linux_64", memory_mb: 2048, disk_gb: 20, cpus: 2 }; }
      await fetch(`${API_BASE}/api/v1/templates`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: editTemplateName.trim(), config }),
      });
      setEditTemplateName("");
      setEditTemplateConfig("{}");
      fetchTemplates();
    } catch (e: any) { console.error(e); }
    finally { setCreatingTemplate(false); }
  };

  const deleteTemplate = async (name: string) => {
    try {
      await fetch(`${API_BASE}/api/v1/templates/${encodeURIComponent(name)}`, { method: "DELETE" });
      fetchTemplates();
    } catch { /* ignore */ }
  };

  const fetchNetworkConfig = async (vmName: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/vms/${encodeURIComponent(vmName)}/network`);
      if (res.ok) {
        const d = await res.json();
        setVmNetworks(prev => ({ ...prev, [vmName]: d }));
      }
    } catch { /* ignore */ }
  };

  const submitUnattended = async (vmName: string) => {
    try {
      const devTools = Object.entries(unattendedDevTools)
        .filter(([, v]) => v)
        .map(([k]) => k);
      await fetch(`${API_BASE}/api/v1/vms/${encodeURIComponent(vmName)}/unattended`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          os_type: "windows",
          hostname: vmName,
          username: unattendedUsername,
          password: unattendedPassword,
          dev_tools: devTools.length > 0 ? devTools : undefined,
          use_host_ollama: unattendedUseOllama,
        }),
      });
      setShowUnattended(null);
    } catch (e: any) { console.error(e); }
  };

  const fetchIsoCandidates = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/iso/candidates`);
      if (res.ok) {
        const d = await res.json();
        const cats = d.categories || [];
        setIsoCategories(cats);
        if (cats.length > 0) setActiveIsoTab(cats[0].id);
      }
    } catch {
      /* server may not have ISO endpoints yet */
    }
  };

  const pollDownloadTask = (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/iso/download/${taskId}`);
        if (res.ok) {
          const task = await res.json();
          setDownloadTasks((prev) => ({ ...prev, [taskId]: task }));
          if (task.status === "completed" || task.status === "failed") {
            clearInterval(interval);
            if (task.status === "completed") {
              fetchVboxAssets();
            }
          }
        } else {
          clearInterval(interval);
        }
      } catch {
        clearInterval(interval);
      }
    }, 1500);
  };

  const startIsoDownload = async (url: string, filename?: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/iso/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, filename }),
      });
      if (res.ok) {
        const task = await res.json();
        setDownloadTasks((prev) => ({ ...prev, [task.task_id]: task }));
        pollDownloadTask(task.task_id);
      }
    } catch (e) {
      console.error("Download failed", e);
    }
  };

  const openIsoDownload = () => {
    setShowIsoDownload(true);
    fetchIsoCandidates();
  };

  const openCreateModal = () => {
    setCreateName("");
    setCreateTemplate("ubuntu-dev");
    setCreateCpus(2);
    setCreateMemoryMb(4096);
    setCreateDiskGb(25);
    setCreateIsoPath("");
    setShowCreateModal(true);
    fetchVboxAssets();
  };

  const submitCreateVm = async () => {
    if (!createName.trim()) return;
    setCreateSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/vms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: createName.trim(),
          template: createTemplate,
          cpus: createCpus,
          memory_mb: createMemoryMb,
          disk_gb: createDiskGb,
          iso_path: createIsoPath || undefined,
          network_mode: networkMode || undefined,
        }),
      });
      if (!res.ok)
        throw new Error(
          (await res.json().catch(() => ({}))).detail || res.statusText,
        );
      setShowCreateModal(false);
      setTimeout(fetchVMs, 1000);
    } catch (e: any) {
      console.error(e);
      setBackendError(e.message || "Create VM failed");
    } finally {
      setCreateSubmitting(false);
    }
  };

  const openAttachModal = (vmName: string) => {
    setAttachVmName(vmName);
    setAttachIsoPath("");
    setShowAttachModal(true);
    fetchVboxAssets();
  };

  const submitAttachIso = async () => {
    if (!attachVmName || !attachIsoPath) return;
    setAttachSubmitting(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/vms/${attachVmName}/attach-iso`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ iso_path: attachIsoPath }),
        },
      );
      if (!res.ok)
        throw new Error(
          (await res.json().catch(() => ({}))).detail || res.statusText,
        );
      setShowAttachModal(false);
      setTimeout(fetchVMs, 500);
    } catch (e: any) {
      setBackendError(e.message || "Attach ISO failed");
    } finally {
      setAttachSubmitting(false);
    }
  };

  const isVboxRequired =
    vboxAvailable === false ||
    (backendError &&
      (backendError.includes("VM Service") || backendError.includes("503")));
  const isConnectionError =
    backendError &&
    !backendError.includes("503") &&
    !backendError.includes("VM Service");

  return (
    <div className="space-y-6 pb-8">
      {isConnectionError && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {backendError}
        </div>
      )}
      {isVboxRequired && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-6 space-y-4">
          <h3 className="font-semibold text-lg text-amber-200">
            VirtualBox is required
          </h3>
          <p className="text-sm text-muted-foreground">
            To list and manage VMs, snapshots, and networks, VirtualBox must be
            installed and <code className="text-amber-200/90">VBoxManage</code>{" "}
            must be in your PATH. If you just installed VirtualBox, open it once
            below so the service can start; then refresh this page.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleOpenVirtualBox}
              disabled={launching}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-200 hover:bg-amber-500/30 transition-colors font-medium disabled:opacity-50"
            >
              {launching ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Power className="w-4 h-4" />
              )}
              Open VirtualBox
            </button>
            <a
              href={VBOX_DOWNLOAD_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-muted-foreground hover:bg-white/10 transition-colors font-medium"
            >
              <ExternalLink className="w-4 h-4" />
              Download VirtualBox
            </a>
          </div>
        </div>
      )}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            VirtualBox Manager
          </h2>
          <p className="text-muted-foreground mt-1">
            Manage your local VirtualBox instances
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchVMs}
            title="Refresh VM List"
            aria-label="Refresh VMs"
            className="p-2 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 text-muted-foreground"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button
            onClick={openCreateModal}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium"
          >
            <Plus className="w-4 h-4" />
            Create New VM
          </button>
          <button
            onClick={openIsoDownload}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:bg-white/10 transition-colors font-medium text-muted-foreground"
          >
            <Disc className="w-4 h-4" />
            Download ISOs
          </button>
        </div>
      </div>

      {showIsoDownload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div
            className="bg-card border border-border rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-lg">Download ISOs</h3>
              <button
                onClick={() => setShowIsoDownload(false)}
                className="p-1 rounded hover:bg-white/10 text-muted-foreground"
              >
                ✕
              </button>
            </div>
            <p className="text-sm text-muted-foreground">
              ISOs are downloaded to{" "}
              <code className="text-foreground/80">assets/vbox/</code> and appear
              in the ISO dropdown automatically.
            </p>
            {/* Horizontal tabs */}
            <div className="flex gap-1 border-b border-border pb-0.5 overflow-x-auto">
              {isoCategories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setActiveIsoTab(cat.id)}
                  className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors whitespace-nowrap ${
                    activeIsoTab === cat.id
                      ? "bg-primary/10 text-primary border-b-2 border-primary"
                      : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            <div className="space-y-2">
              {isoCategories.length === 0 ? (
                <p className="text-sm text-muted-foreground">Loading...</p>
              ) : (
                <div className="grid gap-2">
                  {isoCategories
                    .find((c) => c.id === activeIsoTab)
                    ?.items.map((iso, i) => {
                    const activeTask = Object.values(downloadTasks).find(
                      (t: DownloadTask) => t.url === iso.url,
                    );
                    return (
                      <div
                        key={i}
                        className="flex items-center justify-between p-3 rounded-lg border border-border bg-background/30"
                      >
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">
                            {iso.version}
                          </p>
                          <p className="text-xs text-muted-foreground truncate">
                            {iso.description}
                          </p>
                          <p className="text-xs text-muted-foreground/60 mt-0.5">
                            {iso.size}
                          </p>
                        </div>
                        <div className="flex-shrink-0 ml-3">
                          {activeTask ? (
                            <div className="text-right min-w-[120px]">
                              {activeTask.status === "queued" && (
                                <span className="text-xs text-muted-foreground">Queued...</span>
                              )}
                              {activeTask.status === "connecting" && (
                                <div className="flex items-center gap-2 justify-end">
                                  <Loader2 className="w-3 h-3 animate-spin" />
                                  <span className="text-xs text-muted-foreground">Connecting...</span>
                                </div>
                              )}
                              {activeTask.status === "downloading" && (
                                <>
                                  <div className="flex items-center gap-2 justify-end">
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                    <span className="text-xs tabular-nums font-medium">
                                      {activeTask.total > 0
                                        ? `${activeTask.progress?.toFixed(0) ?? 0}%`
                                        : activeTask.human_size}
                                    </span>
                                  </div>
                                  {activeTask.total > 0 && (
                                    <div className="w-24 h-1.5 bg-muted rounded-full mt-1 overflow-hidden">
                                      <div
                                        className="h-full bg-primary rounded-full transition-all duration-300"
                                        style={{ width: `${activeTask.progress ?? 0}%` }}
                                      />
                                    </div>
                                  )}
                                  {activeTask.total === 0 && activeTask.downloaded > 0 && (
                                    <div className="w-24 h-1.5 bg-muted rounded-full mt-1 overflow-hidden">
                                      <div className="h-full bg-blue-500 rounded-full animate-pulse" style={{ width: "30%" }} />
                                    </div>
                                  )}
                                </>
                              )}
                              {activeTask.status === "completed" && (
                                <div className="flex items-center gap-1 justify-end">
                                  <span className="text-xs text-green-500 font-medium">Done</span>
                                </div>
                              )}
                              {activeTask.status === "failed" && (
                                <div className="text-right">
                                  <span className="text-xs text-red-500 font-medium">Failed</span>
                                  {activeTask.error && (
                                    <p className="text-xs text-red-400/70 max-w-[180px] truncate" title={activeTask.error}>
                                      {activeTask.error}
                                    </p>
                                  )}
                                </div>
                              )}
                            </div>
                          ) : (
                            <button
                              onClick={() => startIsoDownload(iso.url, (iso as any).filename)}
                              className="px-3 py-1.5 text-xs rounded-lg bg-primary/20 text-primary hover:bg-primary/30 transition-colors"
                            >
                              Download
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
            <div className="border-t border-border pt-4">
              <h4 className="text-sm font-medium mb-2">Custom URL</h4>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customIsoUrl}
                  onChange={(e) => setCustomIsoUrl(e.target.value)}
                  placeholder="https://example.com/os.iso"
                  className="flex-1 bg-background/50 border border-input rounded px-3 py-2 text-sm"
                />
                <input
                  type="text"
                  value={customIsoName}
                  onChange={(e) => setCustomIsoName(e.target.value)}
                  placeholder="filename.iso"
                  className="w-32 bg-background/50 border border-input rounded px-3 py-2 text-sm"
                />
                <button
                  onClick={() => {
                    if (customIsoUrl) {
                      startIsoDownload(customIsoUrl, customIsoName || undefined);
                      setCustomIsoUrl("");
                      setCustomIsoName("");
                    }
                  }}
                  disabled={!customIsoUrl}
                  className="px-3 py-2 text-sm rounded-lg bg-primary/20 text-primary hover:bg-primary/30 transition-colors disabled:opacity-50"
                >
                  Download
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {loading && vms.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
          <Loader2 className="w-10 h-10 animate-spin mb-4" />
          <p>Scanning VirtualBox registry...</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {vms.map((vm) => (
            <div
              key={vm.uuid || vm.name}
              className="p-6 rounded-xl border border-border bg-card/40 backdrop-blur-sm hover:border-primary/30 transition-all duration-300"
            >
              {/* Top row: icon, name, state, actions */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`relative p-3 rounded-xl ${vm.state === "running" ? "bg-green-500/15 text-green-400" : "bg-muted/50 text-muted-foreground"}`}>
                    <Monitor className="w-7 h-7" />
                    {vm.state === "running" && <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 border-2 border-background rounded-full animate-pulse" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-3">
                      <h3 className="text-xl font-bold">{vm.name}</h3>
                      <span className={`text-xs px-2.5 py-0.5 rounded-full border font-semibold ${
                        vm.provider === "hyperv" ? "bg-blue-500/20 text-blue-400 border-blue-500/30" : "bg-orange-500/20 text-orange-400 border-orange-500/30"
                      }`}>
                        {vm.provider || "vbox"}
                      </span>
                      <span className={`text-sm px-2.5 py-0.5 rounded-full border font-medium ${
                        vm.state === "running" ? "border-green-500/30 bg-green-500/20 text-green-400"
                        : vm.state === "paused" ? "border-yellow-500/30 bg-yellow-500/20 text-yellow-400"
                        : "border-muted-foreground/30 bg-muted/20 text-muted-foreground"
                      }`}>{vm.state}</span>
                    </div>
                    <p className="text-sm text-foreground/70 mt-1 font-medium">
                      {vm.os_type || "Unknown OS"} &bull; {vm.memory_mb || "?"}MB RAM &bull; {vm.cpus || "?"} vCPUs
                    </p>
                  </div>
                </div>
                {/* Primary actions */}
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 mr-1 pr-2 border-r border-border/50">
                    <span className="text-[11px] text-muted-foreground font-mono">Dsk:</span>
                    {[1, 2, 3].map((d) => (
                      <button key={d} onClick={async () => { await fetch(`${API_BASE}/api/v1/vms/${encodeURIComponent(vm.name)}/move-desktop?desktop=${d}`, { method: "POST" }); }}
                        className="px-2 py-1 text-xs rounded-md bg-white/5 text-muted-foreground hover:bg-white/20 hover:text-white transition-colors font-mono"
                        title={`Move to Desktop ${d}`}>D{d}</button>
                    ))}
                  </div>
                  {vm.state === "running" ? (
                    <>
                      <button onClick={() => handleAction(vm.name, "pause", vm.provider)} disabled={actionId === vm.name + "pause"}
                        className="inline-flex items-center gap-1.5 px-3.5 py-2 text-sm rounded-lg bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 transition-colors font-medium disabled:opacity-40">
                        {actionId === vm.name + "pause" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Pause className="w-4 h-4" />} Pause
                      </button>
                      <button onClick={() => handleAction(vm.name, "stop", vm.provider)} disabled={actionId === vm.name + "stop"}
                        className="inline-flex items-center gap-1.5 px-3.5 py-2 text-sm rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors font-medium disabled:opacity-40">
                        {actionId === vm.name + "stop" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Square className="w-4 h-4" />} Stop
                      </button>
                    </>
                  ) : (
                    <button onClick={() => handleAction(vm.name, "start", vm.provider)} disabled={actionId === vm.name + "start"}
                      className="inline-flex items-center gap-1.5 px-4 py-2 text-sm rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors font-medium disabled:opacity-40">
                      {actionId === vm.name + "start" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Start
                    </button>
                  )}
                </div>
              </div>
              {/* Bottom bar: secondary actions */}
              <div className="flex items-center gap-2 mt-4 pt-3 border-t border-border/40">
                <button onClick={() => handleAction(vm.name, "snapshot", vm.provider)} disabled={actionId === vm.name + "snapshot"}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-white/5 text-muted-foreground hover:bg-white/15 hover:text-white transition-colors font-medium">
                  {actionId === vm.name + "snapshot" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RotateCcw className="w-3.5 h-3.5" />} Snapshot
                </button>
                <button onClick={() => toggleSnapshots(vm.name)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-white/5 text-muted-foreground hover:bg-white/15 hover:text-white transition-colors font-medium">
                  <RotateCcw className="w-3.5 h-3.5" /> Snapshots
                  {snapshots[vm.name]?.length > 0 && <span className="px-1.5 py-0.5 rounded-full bg-primary/20 text-primary text-[10px] font-bold">{snapshots[vm.name].length}</span>}
                </button>
                {vm.provider === "virtualbox" && (
                  <button onClick={() => openAttachModal(vm.name)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-white/5 text-muted-foreground hover:bg-white/15 hover:text-white transition-colors font-medium">
                    <Disc className="w-3.5 h-3.5" /> Attach ISO
                  </button>
                )}
                <a href={`/vm/${encodeURIComponent(vm.name)}/console`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-white/5 text-muted-foreground hover:bg-white/15 hover:text-white transition-colors font-medium">
                  <Monitor className="w-3.5 h-3.5" /> Console
                </a>
                {vm.provider === "virtualbox" && (
                  <button onClick={() => { setShowNetworkConfig(vm.name); fetchNetworkConfig(vm.name); }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-white/5 text-muted-foreground hover:bg-white/15 hover:text-white transition-colors font-medium">
                    Network
                  </button>
                )}
                {vm.state === "running" && (
                  <button onClick={async () => { await fetch(`${API_BASE}/api/v1/vms/${encodeURIComponent(vm.name)}/vrde`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({enabled: true}) }); }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-white/5 text-muted-foreground hover:bg-white/15 hover:text-white transition-colors font-medium">
                    VRDP
                  </button>
                )}
                <button onClick={() => { setShowUnattended(vm.name); setUnattendedDevTools({python: true, git: true, node: true, vscode: true, uv: true}); }}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-white/5 text-muted-foreground hover:bg-white/15 hover:text-white transition-colors font-medium">
                  Autoinstall
                </button>
                <div className="flex-1" />
                {vm.state !== "running" && (
                  <button onClick={async () => { if (!window.confirm(`Delete VM "${vm.name}"?`)) return; setActionId(vm.name + "delete"); try { await fetch(`${API_BASE}/api/v1/vms/${encodeURIComponent(vm.name)}`, { method: "DELETE" }); setTimeout(fetchVMs, 1000); } catch {} setActionId(null); }}
                    disabled={actionId === vm.name + "delete"}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/25 transition-colors font-medium disabled:opacity-40">
                    <Trash2 className="w-3.5 h-3.5" /> Delete
                  </button>
                )}
              </div>
              {/* Snapshots */}
              {expandedSnapshots.has(vm.name) && (
                <div className="mt-3 pt-3 border-t border-border/40">
                  {snapshots[vm.name]?.length > 0 ? (
                    <div className="space-y-2">
                      {snapshots[vm.name].map((snap: any, i: number) => (
                        <div key={i} className="flex items-center justify-between py-2 px-3 rounded-lg bg-black/20 border border-border/40">
                          <div className="min-w-0">
                            <p className="text-sm font-medium">{snap.name}</p>
                            {snap.description && <p className="text-xs text-muted-foreground">{snap.description}</p>}
                          </div>
                          <div className="flex gap-2 ml-3">
                            <button onClick={async () => { await fetch(`${API_BASE}/api/v1/vms/${encodeURIComponent(vm.name)}/restore`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({snapshot_name: snap.name}) }); toggleSnapshots(vm.name); }}
                              className="px-3 py-1 text-xs rounded-md bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 transition-colors font-medium">Restore</button>
                            <button onClick={async () => { await fetch(`${API_BASE}/api/v1/vms/${encodeURIComponent(vm.name)}/delete-snapshot`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({snapshot_name: snap.name}) }); fetchSnapshots(vm.name); }}
                              className="px-3 py-1 text-xs rounded-md bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors font-medium">Delete</button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No snapshots yet.</p>
                  )}
                </div>
              )}
            </div>
          ))}
          {vms.length === 0 && !loading && (
            <div className="text-center py-12 border border-dashed border-border rounded-xl">
              <p className="text-muted-foreground">
                No VirtualBox VMs detected.
              </p>
            </div>
          )}
        </div>
      )}

      {showCreateModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          onClick={() => !createSubmitting && setShowCreateModal(false)}
        >
          <div
            className="bg-card border border-border rounded-xl shadow-xl max-w-md w-full p-6 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="font-semibold text-lg">Create New VM</h3>
            <p className="text-sm text-muted-foreground">
              Uses repo <code className="text-foreground/80">assets/vbox</code>{" "}
              for optional ISO.
            </p>
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <input
                type="text"
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                placeholder="my-vm"
                className="w-full bg-background/50 border border-input rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Template</label>
              <div className="flex gap-2">
                <select
                  value={createTemplate}
                  onChange={(e) => setCreateTemplate(e.target.value)}
                  className="flex-1 bg-background/50 border border-input rounded px-3 py-2"
                >
                  {(templates.length > 0 ? templates : [
                    { name: "ubuntu-dev", description: "Ubuntu (dev)" },
                    { name: "win11-pro", description: "Win 11 Pro" },
                    { name: "minimal-linux", description: "Minimal Linux" },
                  ]).map((t: any) => (
                    <option key={t.name} value={t.name}>
                      {t.description || t.name}
                    </option>
                  ))}
                </select>
                <button onClick={() => { setShowTemplateManager(true); fetchTemplates(); }}
                  className="px-3 py-2 text-xs rounded-lg bg-white/5 text-muted-foreground hover:bg-white/15 border border-border"
                  title="Manage Templates">+</button>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1">CPUs</label>
                <input
                  type="number"
                  min={1}
                  max={32}
                  value={createCpus}
                  onChange={(e) => setCreateCpus(Number(e.target.value))}
                  className="w-full bg-background/50 border border-input rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">RAM (MB)</label>
                <input
                  type="number"
                  min={512}
                  max={131072}
                  step={512}
                  value={createMemoryMb}
                  onChange={(e) => setCreateMemoryMb(Number(e.target.value))}
                  className="w-full bg-background/50 border border-input rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Disk (GB)</label>
                <input
                  type="number"
                  min={1}
                  max={2048}
                  value={createDiskGb}
                  onChange={(e) => setCreateDiskGb(Number(e.target.value))}
                  className="w-full bg-background/50 border border-input rounded px-3 py-2"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                ISO (optional, from repo assets/vbox)
              </label>
              <select
                value={createIsoPath}
                onChange={(e) => setCreateIsoPath(e.target.value)}
                className="w-full bg-background/50 border border-input rounded px-3 py-2"
              >
                <option value="">— None —</option>
                {vboxAssets.map((f) => (
                  <option key={f.path} value={f.path}>
                    {f.name}
                  </option>
                ))}
              </select>
              {vboxAssets.length === 0 && (
                <p className="text-xs text-muted-foreground mt-1">
                  Use the <strong>Download ISOs</strong> button above to download
                  ISOs, or put .iso files in repo assets/vbox folder.
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Network</label>
              <select value={networkMode} onChange={(e) => setNetworkMode(e.target.value)}
                className="w-full bg-background/50 border border-input rounded px-3 py-2">
                {NETWORK_MODES.map((m) => (
                  <option key={m.id} value={m.id}>{m.label}</option>
                ))}
              </select>
            </div>
            <div className="flex gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                disabled={createSubmitting}
                className="flex-1 py-2 rounded-lg border border-border hover:bg-white/10"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={submitCreateVm}
                disabled={createSubmitting || !createName.trim()}
                className="flex-1 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {createSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin inline" />
                ) : null}{" "}
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {showAttachModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          onClick={() => !attachSubmitting && setShowAttachModal(false)}
        >
          <div
            className="bg-card border border-border rounded-xl shadow-xl max-w-md w-full p-6 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="font-semibold text-lg">
              Attach ISO to {attachVmName}
            </h3>
            <p className="text-sm text-muted-foreground">
              Choose from repo{" "}
              <code className="text-foreground/80">assets/vbox</code>.
            </p>
            <div>
              <label className="block text-sm font-medium mb-1">ISO file</label>
              <select
                value={attachIsoPath}
                onChange={(e) => setAttachIsoPath(e.target.value)}
                className="w-full bg-background/50 border border-input rounded px-3 py-2"
              >
                <option value="">— Select —</option>
                {vboxAssets.map((f) => (
                  <option key={f.path} value={f.path}>
                    {f.name}
                  </option>
                ))}
              </select>
              {vboxAssets.length === 0 && (
                <p className="text-xs text-muted-foreground mt-1">
                  Use the <strong>Download ISOs</strong> button to download ISOs,
                  or put .iso files in repo assets/vbox folder.
                </p>
              )}
            </div>
            <div className="flex gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowAttachModal(false)}
                disabled={attachSubmitting}
                className="flex-1 py-2 rounded-lg border border-border hover:bg-white/10"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={submitAttachIso}
                disabled={attachSubmitting || !attachIsoPath}
                className="flex-1 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {attachSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin inline" />
                ) : null}{" "}
                Attach
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Template Manager Modal */}
      {showTemplateManager && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          onClick={() => setShowTemplateManager(false)}>
          <div className="bg-card border border-border rounded-xl shadow-xl max-w-lg w-full max-h-[80vh] overflow-y-auto p-6 space-y-4"
            onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-lg">VM Templates</h3>
              <button onClick={() => setShowTemplateManager(false)} className="p-1 rounded hover:bg-white/10 text-muted-foreground">✕</button>
            </div>
            <div className="space-y-2">
              <input value={editTemplateName} onChange={(e) => setEditTemplateName(e.target.value)}
                placeholder="Template name (e.g. my-custom-vm)"
                className="w-full bg-background/50 border border-input rounded px-3 py-2 text-sm" />
              <textarea value={editTemplateConfig} onChange={(e) => setEditTemplateConfig(e.target.value)}
                placeholder='{"os_type":"Ubuntu_64","memory_mb":4096,"disk_gb":25,"cpus":2,"network":"NAT"}'
                rows={4} className="w-full bg-background/50 border border-input rounded px-3 py-2 text-xs font-mono" />
              <button onClick={submitTemplate} disabled={creatingTemplate || !editTemplateName.trim()}
                className="w-full py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 text-sm font-medium">
                {creatingTemplate ? <Loader2 className="w-4 h-4 animate-spin inline" /> : null} Save Template
              </button>
            </div>
            <div className="border-t border-border pt-3 space-y-2">
              <p className="text-xs text-muted-foreground font-medium">Saved Templates ({templates.length})</p>
              {templates.map((t: any) => (
                <div key={t.name} className="flex items-center justify-between py-2 px-3 rounded-lg bg-black/20 border border-border/40">
                  <div className="min-w-0">
                    <p className="text-sm font-medium">{t.name}</p>
                    <p className="text-xs text-muted-foreground">{t.config?.os_type || t.os_type} · {(t.config?.memory_mb || t.memory_mb || "?")}MB</p>
                  </div>
                  {!t.builtin && (
                    <button onClick={() => deleteTemplate(t.name)}
                      className="px-2 py-1 text-xs rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors font-medium">
                      Delete
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Network Config Modal */}
      {showNetworkConfig && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          onClick={() => setShowNetworkConfig(null)}>
          <div className="bg-card border border-border rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4"
            onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-lg">Network: {showNetworkConfig}</h3>
              <button onClick={() => setShowNetworkConfig(null)} className="p-1 rounded hover:bg-white/10 text-muted-foreground">✕</button>
            </div>
            {vmNetworks[showNetworkConfig]?.adapters?.length > 0 ? (
              <div className="space-y-2">
                {vmNetworks[showNetworkConfig]?.adapters?.map((a: any) => (
                  <div key={a.adapter} className="flex items-center justify-between py-2 px-3 rounded-lg bg-black/20 border border-border/40">
                    <span className="text-sm">NIC{a.adapter}</span>
                    <span className="text-xs font-mono text-muted-foreground">{a.mode}</span>
                    <select value={a.mode} onChange={async (e) => {
                      await fetch(`${API_BASE}/api/v1/vms/${encodeURIComponent(showNetworkConfig)}/network`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ adapter: a.adapter, mode: e.target.value }),
                      });
                      fetchNetworkConfig(showNetworkConfig!);
                    }} className="text-xs bg-background/50 border border-input rounded px-2 py-1">
                      <option value="nat">NAT</option>
                      <option value="bridged">Bridged</option>
                      <option value="hostonly">Host-Only</option>
                      <option value="intnet">Internal</option>
                      <option value="none">None</option>
                    </select>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-muted-foreground">No adapters found.</p>}
            <div className="border-t border-border pt-3">
              <p className="text-xs text-muted-foreground font-medium mb-2">Port Forwarding</p>
              {vmNetworks[showNetworkConfig]?.port_forwarding?.length > 0 ? (
                <div className="space-y-1 mb-2">
                  {vmNetworks[showNetworkConfig]?.port_forwarding?.map((r: any, i: number) => (
                    <div key={i} className="flex items-center justify-between text-xs py-1 px-2 rounded bg-black/20">
                      <span>{r.name}: {r.protocol}://host:{r.host_port} → guest:{r.guest_port}</span>
                      <button onClick={async () => {
                        await fetch(`${API_BASE}/api/v1/vms/${encodeURIComponent(showNetworkConfig)}/network/port-forwarding/${encodeURIComponent(r.name)}`, { method: "DELETE" });
                        fetchNetworkConfig(showNetworkConfig!);
                      }} className="text-red-400 hover:text-red-300">✕</button>
                    </div>
                  ))}
                </div>
              ) : <p className="text-xs text-muted-foreground mb-2">No port forwarding rules.</p>}
            </div>
          </div>
        </div>
      )}

      {/* Unattended Install Modal */}
      {showUnattended && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          onClick={() => setShowUnattended(null)}>
          <div className="bg-card border border-border rounded-xl shadow-xl max-w-lg w-full max-h-[85vh] overflow-y-auto p-6 space-y-4"
            onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold text-lg">Autoinstall: {showUnattended}</h3>
            <p className="text-sm text-muted-foreground">For Windows VMs, selected dev tools install via winget on first login.</p>
            <div>
              <label className="block text-sm font-medium mb-1">Username</label>
              <input value={unattendedUsername} onChange={(e) => setUnattendedUsername(e.target.value)}
                className="w-full bg-background/50 border border-input rounded px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Password</label>
              <input type="password" value={unattendedPassword} onChange={(e) => setUnattendedPassword(e.target.value)}
                className="w-full bg-background/50 border border-input rounded px-3 py-2" />
            </div>
            <div className="border-t border-border pt-3">
              <p className="text-sm font-medium mb-2">Dev Tools (Windows only)</p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  ["python", "Python 3.12"],
                  ["git", "Git"],
                  ["node", "Node.js LTS"],
                  ["vscode", "VS Code"],
                  ["uv", "uv (pip+venv)"],
                  ["just", "Just"],
                  ["notepad++", "Notepad++"],
                  ["windsurf", "Windsurf"],
                  ["cursor", "Cursor"],
                  ["antigravity", "Antigravity"],
                  ["claude_desktop", "Claude Desktop"],
                ].map(([id, label]) => (
                  <label key={id} className="flex items-center gap-2 text-sm py-1 px-2 rounded hover:bg-white/5 cursor-pointer">
                    <input type="checkbox" checked={unattendedDevTools[id] ?? false}
                      onChange={(e) => setUnattendedDevTools(prev => ({ ...prev, [id]: e.target.checked }))}
                      className="rounded border-white/20 bg-white/5" />
                    {label}
                  </label>
                ))}
              </div>
              <label className="flex items-center gap-2 text-sm mt-2 py-1 px-2 rounded hover:bg-white/5 cursor-pointer">
                <input type="checkbox" checked={unattendedUseOllama} onChange={() => setUnattendedUseOllama(!unattendedUseOllama)}
                  className="rounded border-white/20 bg-white/5" />
                Use host Ollama (set OLLAMA_HOST)
              </label>
            </div>
            <div className="flex gap-2 pt-2">
              <button onClick={() => setShowUnattended(null)}
                className="flex-1 py-2 rounded-lg border border-border hover:bg-white/10">Cancel</button>
              <button onClick={() => submitUnattended(showUnattended!)}
                className="flex-1 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90">Generate</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
