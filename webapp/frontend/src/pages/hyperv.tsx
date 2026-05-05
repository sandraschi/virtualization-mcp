import { Loader2, Monitor, Power, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { API_BASE } from "../api/config";

interface VmInfo {
  uuid: string;
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

  const fetchVMs = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/vms`);
      if (res.ok) {
        const data = await res.json();
        const all: VmInfo[] = data.vms || data || [];
        setVms(all.filter((vm) => vm.provider === "hyperv"));
      } else {
        setError(`HTTP ${res.status}`);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVMs();
  }, []);

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

      {!error && (
        <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-6">
          <h3 className="font-semibold text-lg text-blue-200 flex items-center gap-2">
            <Power className="w-5 h-5" />
            Hyper-V
          </h3>
          <p className="text-sm text-muted-foreground mt-2">
            Hyper-V integration is under construction. VM listing and lifecycle
            management will appear here. Currently, Hyper-V VMs are listed on the
            VirtualBox page when detected.
          </p>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20 text-muted-foreground">
          <Loader2 className="w-10 h-10 animate-spin mb-4" />
          <p>Scanning Hyper-V...</p>
        </div>
      ) : vms.length > 0 ? (
        <div className="grid gap-4">
          {vms.map((vm) => (
            <div
              key={vm.uuid || vm.name}
              className="p-6 rounded-xl border border-blue-500/20 bg-card/40 backdrop-blur-sm"
            >
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-lg bg-blue-500/10 text-blue-500">
                  <Monitor className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-lg">{vm.name}</h3>
                    <span className="text-xs px-2 py-0.5 rounded-full border border-blue-500/20 bg-blue-500/10 text-blue-500 uppercase font-bold tracking-wider">
                      hyperv
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full border ${
                        vm.state === "running"
                          ? "border-green-500/20 bg-green-500/10 text-green-500"
                          : "border-muted-foreground/20 bg-muted/10 text-muted-foreground"
                      }`}
                    >
                      {vm.state}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    {vm.os_type} &bull; {vm.memory_mb}MB RAM &bull; {vm.cpus}{" "}
                    vCPUs
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        !error && (
          <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
            <Monitor className="w-10 h-10 mb-4 opacity-50" />
            <p>No Hyper-V VMs found</p>
            <p className="text-sm mt-1">
              Hyper-V VMs managed by this server will appear here.
            </p>
          </div>
        )
      )}
    </div>
  );
}
