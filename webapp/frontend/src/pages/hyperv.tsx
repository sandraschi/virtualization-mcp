import { Loader2, Monitor, Play, Plus, Power, Pause, RefreshCw, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { API_BASE } from "../api/config";

interface VmInfo {
  name: string;
  state: string;
  os_type: string;
  memory_mb: number;
  cpus: number;
  provider?: string;
}

export default function HyperV() {
  const [vms, setVms] = useState<VmInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionVm, setActionVm] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createMemory, setCreateMemory] = useState(2048);
  const [createDisk, setCreateDisk] = useState(25);
  const [creating, setCreating] = useState(false);

  const fetchVMs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/vms`);
      if (res.ok) {
        const data = await res.json();
        const all: VmInfo[] = data.vms || [];
        setVms(all.filter((vm) => vm.provider === "hyperv"));
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchVMs(); }, [fetchVMs]);

  const vmAction = async (name: string, action: string) => {
    setActionVm(`${name}-${action}`);
    try {
      await fetch(`${API_BASE}/api/v1/vms/${encodeURIComponent(name)}/${action}?provider=hyperv`, { method: "POST" });
      setTimeout(fetchVMs, 1000);
    } catch { /* ignore */ }
    setActionVm(null);
  };

  const createVm = async () => {
    if (!createName.trim()) return;
    setCreating(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/vms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: createName.trim(),
          provider: "hyperv",
          memory_mb: createMemory,
          disk_gb: createDisk,
        }),
      });
      if (res.ok) {
        setShowCreate(false);
        setCreateName("");
        setTimeout(fetchVMs, 1000);
      }
    } catch { /* ignore */ }
    setCreating(false);
  };

  const stateColor = (state: string) => {
    switch (state) {
      case "running": return "text-green-500 border-green-500/20 bg-green-500/10";
      case "paused": return "text-yellow-500 border-yellow-500/20 bg-yellow-500/10";
      default: return "text-muted-foreground border-muted-foreground/20 bg-muted/10";
    }
  };

  const isBusy = (name: string) => actionVm?.startsWith(name);

  return (
    <div className="space-y-6 pb-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Hyper-V Manager</h2>
          <p className="text-muted-foreground mt-1">
            Manage your local Hyper-V virtual machines
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowCreate(true)} className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium">
            <Plus className="w-4 h-4" />
            Create New VM
          </button>
          <button onClick={fetchVMs} className="p-2 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 text-muted-foreground" title="Refresh">
            <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">{error}</div>
      )}

      <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 px-4 py-3 text-sm text-muted-foreground">
        <strong>Requirement:</strong> Hyper-V is only available on{" "}
        <strong>Windows 11 Pro, Enterprise, or Education</strong> (not Home).
        It must be enabled via{" "}
        <span className="font-mono text-xs bg-white/10 px-1.5 py-0.5 rounded">
          Turn Windows features on or off
        </span>{" "}
        &rarr; check{" "}
        <span className="font-mono text-xs bg-white/10 px-1.5 py-0.5 rounded">
          Hyper-V
        </span>
        , or run in PowerShell as Admin:
        <code className="block mt-1 font-mono text-xs bg-black/20 px-2 py-1 rounded">
          Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
        </code>
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => !creating && setShowCreate(false)}>
          <div className="bg-card border border-border rounded-xl shadow-xl max-w-md w-full p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-lg">Create Hyper-V VM</h3>
              <button onClick={() => setShowCreate(false)} className="p-1 rounded hover:bg-white/10 text-muted-foreground"><X className="w-4 h-4" /></button>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <input type="text" value={createName} onChange={(e) => setCreateName(e.target.value)} placeholder="my-vm" className="w-full bg-background/50 border border-input rounded px-3 py-2" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1">RAM (MB)</label>
                <input type="number" min={512} max={131072} step={512} value={createMemory} onChange={(e) => setCreateMemory(Number(e.target.value))} className="w-full bg-background/50 border border-input rounded px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Disk (GB)</label>
                <input type="number" min={1} max={2048} value={createDisk} onChange={(e) => setCreateDisk(Number(e.target.value))} className="w-full bg-background/50 border border-input rounded px-3 py-2" />
              </div>
            </div>
            <div className="flex gap-2 pt-2">
              <button onClick={() => setShowCreate(false)} disabled={creating} className="flex-1 py-2 rounded-lg border border-border hover:bg-white/10">Cancel</button>
              <button onClick={createVm} disabled={creating || !createName.trim()} className="flex-1 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
                {creating ? <Loader2 className="w-4 h-4 animate-spin inline" /> : null} Create
              </button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20 text-muted-foreground">
          <Loader2 className="w-10 h-10 animate-spin mb-4" />
          <p>Scanning Hyper-V...</p>
        </div>
      ) : vms.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
          <Monitor className="w-10 h-10 mb-4 opacity-50" />
          <p>No Hyper-V VMs found</p>
          <p className="text-sm mt-1">Click "Create New VM" to create one.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {vms.map((vm) => (
            <div key={vm.name} className="p-6 rounded-xl border border-blue-500/20 bg-card/40 backdrop-blur-sm hover:border-blue-500/40 transition-all duration-300">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-lg ${vm.state === "running" ? "bg-green-500/10 text-green-500" : "bg-blue-500/10 text-blue-500"}`}>
                    <Monitor className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-lg">{vm.name}</h3>
                      <span className="text-xs px-2 py-0.5 rounded-full border border-blue-500/20 bg-blue-500/10 text-blue-500 uppercase font-bold tracking-wider">hyperv</span>
                      <span className={`text-sm px-2.5 py-0.5 rounded-full border font-medium ${stateColor(vm.state)}`}>{vm.state}</span>
                    </div>
                    <p className="text-sm text-foreground/80 mt-1 font-medium">{vm.os_type} &bull; {vm.memory_mb}MB RAM</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {vm.state === "running" ? (
                    <>
                      <button onClick={() => vmAction(vm.name, "pause")} disabled={isBusy(vm.name)} className="p-2 rounded-lg bg-yellow-500/20 text-yellow-500 hover:bg-yellow-500/30 transition-colors disabled:opacity-50" title="Pause">
                        {isBusy(vm.name) ? <Loader2 className="w-4 h-4 animate-spin" /> : <Pause className="w-4 h-4" />}
                      </button>
                      <button onClick={() => vmAction(vm.name, "stop")} disabled={isBusy(vm.name)} className="p-2 rounded-lg bg-red-500/20 text-red-500 hover:bg-red-500/30 transition-colors disabled:opacity-50" title="Stop">
                        {isBusy(vm.name) ? <Loader2 className="w-4 h-4 animate-spin" /> : <Power className="w-4 h-4" />}
                      </button>
                    </>
                  ) : (
                    <button onClick={() => vmAction(vm.name, "start")} disabled={isBusy(vm.name)} className="p-2 rounded-lg bg-green-500/20 text-green-500 hover:bg-green-500/30 transition-colors disabled:opacity-50" title="Start">
                      {isBusy(vm.name) ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
