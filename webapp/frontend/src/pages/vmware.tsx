import { Loader2, Monitor, Pause, Play, Power, RefreshCw, Camera, RotateCcw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { API_BASE } from "../api/config";

interface VmwareVm {
  name: string;
  vmx_path: string;
  state: string;
  guest_os: string;
  memory_mb: number;
  cpus: number;
  provider?: string;
}

export default function Vmware() {
  const [vms, setVms] = useState<VmwareVm[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionVm, setActionVm] = useState<string | null>(null);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [snapName, setSnapName] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [snapshots, setSnapshots] = useState<Record<string, { name: string }[]>>({});

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/vmware/status`);
      if (res.ok) {
        const data = await res.json();
        setAvailable(data.available ?? null);
      }
    } catch {
      /* ignore */
    }
  }, []);

  const fetchVMs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/vmware/vms`);
      if (res.ok) {
        const data = await res.json();
        setVms(data.vms || []);
        setError(null);
      } else {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || "VMware vmrun not found. Install Workstation Pro (free).");
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    fetchVMs();
  }, [fetchStatus, fetchVMs]);

  const doAction = async (vmx_path: string, action: string, extra: any = {}) => {
    setActionVm(`${vmx_path}-${action}`);
    try {
      await fetch(`${API_BASE}/api/v1/vmware/action?action=${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vmx_path, ...extra }),
      });
      setTimeout(fetchVMs, 1000);
    } catch {
      /* ignore */
    }
    setActionVm(null);
  };

  const loadSnapshots = async (vmx_path: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/vmware/action?action=snapshot_list`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vmx_path }),
      });
      if (res.ok) {
        const data = await res.json();
        setSnapshots((prev) => ({ ...prev, [vmx_path]: data.snapshots || [] }));
      }
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">VMware Workstation Pro</h2>
          <p className="text-sm text-muted-foreground">
            Free since Broadcom Nov 2024. Best Windows option for macOS guests (Unlocker, EULA-grey).
            {available === false && " vmrun not detected."}
          </p>
        </div>
        <button
          type="button"
          onClick={() => { fetchStatus(); fetchVMs(); }}
          className="p-2 hover:bg-white/5 rounded-lg"
          aria-label="Refresh VMware VMs"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-yellow-500/20 bg-yellow-500/10 text-sm">{error}</div>
      )}

      {loading ? (
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading VMware VMs...
        </div>
      ) : vms.length === 0 ? (
        <div className="p-8 text-center rounded-xl border border-border bg-card/40 text-muted-foreground text-sm">
          No VMware VMs found. Create one in Workstation Pro under Documents/Virtual Machines, then refresh.
        </div>
      ) : (
        <div className="grid gap-3">
          {vms.map((vm) => (
            <div key={vm.vmx_path} className="p-4 rounded-xl border border-border bg-card/40">
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-3">
                  <Monitor className="w-5 h-5 text-primary" />
                  <div>
                    <div className="font-semibold">{vm.name}</div>
                    <div className="text-xs text-muted-foreground font-mono truncate max-w-[420px]">{vm.vmx_path}</div>
                    <div className="text-xs text-muted-foreground">
                      {vm.state} - {vm.guest_os} - {vm.memory_mb} MB - {vm.cpus} vCPU
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1 flex-wrap">
                  <button type="button" onClick={() => doAction(vm.vmx_path, "start")} className="p-2 hover:bg-white/5 rounded-lg" title="Start (nogui)">
                    <Play className="w-4 h-4" />
                  </button>
                  <button type="button" onClick={() => doAction(vm.vmx_path, "stop")} className="p-2 hover:bg-white/5 rounded-lg" title="Stop (soft)">
                    <Power className="w-4 h-4" />
                  </button>
                  <button type="button" onClick={() => doAction(vm.vmx_path, "suspend")} className="p-2 hover:bg-white/5 rounded-lg" title="Suspend">
                    <Pause className="w-4 h-4" />
                  </button>
                  <button type="button" onClick={() => doAction(vm.vmx_path, "reset")} className="p-2 hover:bg-white/5 rounded-lg" title="Reset">
                    <RotateCcw className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (expanded === vm.vmx_path) setExpanded(null);
                      else { setExpanded(vm.vmx_path); loadSnapshots(vm.vmx_path); }
                    }}
                    className="p-2 hover:bg-white/5 rounded-lg"
                    title="Snapshots"
                  >
                    <Camera className="w-4 h-4" />
                  </button>
                  {actionVm?.startsWith(vm.vmx_path) && <Loader2 className="w-4 h-4 animate-spin" />}
                </div>
              </div>
              {expanded === vm.vmx_path && (
                <div className="mt-3 pt-3 border-t border-border/50 space-y-2">
                  <div className="flex gap-2">
                    <input
                      value={snapName}
                      onChange={(e) => setSnapName(e.target.value)}
                      placeholder="Snapshot name"
                      className="flex-1 px-3 py-1.5 rounded-lg bg-background border border-border text-sm"
                    />
                    <button
                      type="button"
                      onClick={() => { doAction(vm.vmx_path, "snapshot_create", { snapshot_name: snapName }); setSnapName(""); setTimeout(() => loadSnapshots(vm.vmx_path), 1500); }}
                      className="px-3 py-1.5 rounded-lg bg-primary/10 text-primary text-sm"
                    >
                      Take
                    </button>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {(snapshots[vm.vmx_path] || []).length === 0
                      ? "No snapshots."
                      : (snapshots[vm.vmx_path] || []).map((s) => s.name).join(", ")}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
