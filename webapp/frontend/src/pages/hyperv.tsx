import { Loader2, Monitor, Play, Power, Pause, RotateCcw, RefreshCw } from "lucide-react";
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
        <button
          onClick={fetchVMs}
          className="p-2 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 text-muted-foreground"
          title="Refresh"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
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
          <p className="text-sm mt-1">Create a VM in Hyper-V Manager or PowerShell to see it here.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {vms.map((vm) => (
            <div
              key={vm.name}
              className="p-6 rounded-xl border border-blue-500/20 bg-card/40 backdrop-blur-sm hover:border-blue-500/40 transition-all duration-300"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-lg ${vm.state === "running" ? "bg-green-500/10 text-green-500" : "bg-blue-500/10 text-blue-500"}`}>
                    <Monitor className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-lg">{vm.name}</h3>
                      <span className="text-xs px-2 py-0.5 rounded-full border border-blue-500/20 bg-blue-500/10 text-blue-500 uppercase font-bold tracking-wider">
                        hyperv
                      </span>
                      <span className={`text-sm px-2.5 py-0.5 rounded-full border font-medium ${stateColor(vm.state)}`}>
                        {vm.state}
                      </span>
                    </div>
                    <p className="text-sm text-foreground/80 mt-1 font-medium">
                      {vm.os_type} &bull; {vm.memory_mb}MB RAM
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {vm.state === "running" ? (
                    <>
                      <button
                        onClick={() => vmAction(vm.name, "pause")}
                        disabled={isBusy(vm.name)}
                        className="p-2 rounded-lg bg-yellow-500/20 text-yellow-500 hover:bg-yellow-500/30 transition-colors disabled:opacity-50"
                        title="Pause"
                      >
                        {isBusy(vm.name) ? <Loader2 className="w-4 h-4 animate-spin" /> : <Pause className="w-4 h-4" />}
                      </button>
                      <button
                        onClick={() => vmAction(vm.name, "stop")}
                        disabled={isBusy(vm.name)}
                        className="p-2 rounded-lg bg-red-500/20 text-red-500 hover:bg-red-500/30 transition-colors disabled:opacity-50"
                        title="Stop"
                      >
                        {isBusy(vm.name) ? <Loader2 className="w-4 h-4 animate-spin" /> : <Power className="w-4 h-4" />}
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => vmAction(vm.name, "start")}
                      disabled={isBusy(vm.name)}
                      className="p-2 rounded-lg bg-green-500/20 text-green-500 hover:bg-green-500/30 transition-colors disabled:opacity-50"
                      title="Start"
                    >
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
