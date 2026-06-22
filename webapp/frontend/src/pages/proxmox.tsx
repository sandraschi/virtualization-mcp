import { CheckCircle2, Server, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { API_BASE } from "../api/config";

interface ProxmoxVM {
  name: string;
  vmid: string;
  status: string;
  cpus: number;
  mem: number;
  provider: string;
}

export default function Proxmox() {
  const [vms, setVms] = useState<ProxmoxVM[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [configMsg, setConfigMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchVms = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/api/v1/vms`);
        const data = await res.json();
        if (data.status === "success") {
          const proxmoxVms = (data.vms || []).filter(
            (vm: any) => vm.provider === "proxmox"
          );
          setVms(proxmoxVms);
          if (proxmoxVms.length === 0 && !error) {
            setConfigMsg(
              "No Proxmox VMs found. If you have a Proxmox host, set PROXMOX_HOST, PROXMOX_USER, and PROXMOX_PASSWORD env vars."
            );
          } else {
            setConfigMsg(null);
          }
          setError(null);
        } else {
          setError(data.detail || "Failed to fetch VMs");
        }
      } catch (e) {
        setError("Cannot reach backend");
      } finally {
        setLoading(false);
      }
    };
    fetchVms();
    const interval = setInterval(fetchVms, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
            Proxmox VE
          </h1>
          <p className="text-muted-foreground mt-1">
            Remote Proxmox host management via REST API
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-widest">
          <Server className="w-3 h-3" />
          {vms.length > 0 ? `${vms.length} VMs` : "REST API"}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      {configMsg && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-sm">
          {configMsg}
        </div>
      )}

      {loading && vms.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          Loading...
        </div>
      )}

      {vms.length > 0 && (
        <div className="grid gap-3">
          {vms.map((vm) => (
            <div
              key={vm.vmid}
              className="flex items-center justify-between p-4 rounded-xl border border-border bg-card/40 hover:bg-white/5 transition-colors"
            >
              <div className="flex items-center gap-3">
                {vm.status === "running" ? (
                  <CheckCircle2 className="w-5 h-5 text-green-500" />
                ) : (
                  <XCircle className="w-5 h-5 text-gray-500" />
                )}
                <div>
                  <span className="font-medium">{vm.name}</span>
                  <span className="text-xs text-muted-foreground ml-2">
                    VMID {vm.vmid}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <span
                  className={`px-2 py-1 rounded-full font-medium ${
                    vm.status === "running"
                      ? "bg-green-500/10 text-green-400"
                      : "bg-gray-500/10 text-gray-400"
                  }`}
                >
                  {vm.status}
                </span>
                <span>{vm.cpus} CPU</span>
                <span>{(vm.mem / 1024 ** 3).toFixed(1)} GB</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && vms.length === 0 && !error && !configMsg && (
        <div className="text-center py-12 text-muted-foreground">
          <Server className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p>No Proxmox VMs found.</p>
        </div>
      )}
    </div>
  );
}
