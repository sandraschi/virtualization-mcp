import { Activity, Box, Cpu, ExternalLink, HardDrive, MemoryStick, Monitor, Server } from "lucide-react";
import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../api/config";

interface HostInfo {
  cpu_usage: number;
  memory_total: number;
  memory_available: number;
  disk_usage: { total: number; free: number; used: number; percent: number };
  virtualbox: { version: string };
}

interface VmInfo {
  name: string;
  state: string;
  provider?: string;
}

interface DashboardData {
  host: HostInfo;
  vms: { total: number; running: number; stopped: number; paused: number; list: VmInfo[] };
  virtualbox: { version: string };
}

const VBOX_DOWNLOAD_URL = "https://www.virtualbox.org/wiki/Downloads";

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [vboxAvail, setVboxAvail] = useState<boolean | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const r = await fetch(`${API_BASE}/api/v1/vbox/status`);
        if (r.ok) {
          const s = await r.json();
          setVboxAvail(s.available);
        }
      } catch { /* backend down */ }
    };
    fetchStatus();
    const fetchData = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/dashboard`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const d: DashboardData = await res.json();
        setData(d);

        const h = d.host || {} as HostInfo;
        setHistory((prev) => {
          const memTotal = h.memory_total || 1;
          const memAvail = h.memory_available || 0;
          const entry = {
            time: new Date().toLocaleTimeString(),
            cpu: h.cpu_usage || 0,
            memory: ((memTotal - memAvail) / memTotal) * 100,
          };
          return [...prev, entry].slice(-20);
        });
        setError(null);
      } catch (e: any) {
        setError(e.message);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const h = data?.host;
  const vms = data?.vms;

  const stats = [
    {
      label: "CPU",
      value: h ? `${h.cpu_usage?.toFixed(1) ?? "?"}%` : "...",
      icon: Cpu,
      color: "text-blue-500",
      bg: "bg-blue-500/10",
    },
    {
      label: "RAM",
      value: h
        ? `${(((h.memory_total || 0) - (h.memory_available || 0)) / 1024 ** 3).toFixed(1)} / ${(h.memory_total / 1024 ** 3).toFixed(0)} GB`
        : "...",
      icon: MemoryStick,
      color: "text-purple-500",
      bg: "bg-purple-500/10",
    },
    {
      label: "VMs",
      value: vms ? `${vms.running} running / ${vms.total} total` : "...",
      icon: Monitor,
      color: "text-green-500",
      bg: "bg-green-500/10",
    },
    {
      label: "Disk Free",
      value: h ? `${((h.disk_usage?.free || 0) / 1024 ** 3).toFixed(0)} GB` : "...",
      icon: HardDrive,
      color: "text-orange-500",
      bg: "bg-orange-500/10",
    },
  ];

  return (
    <div className="space-y-8 pb-8">
      <div className="rounded-2xl border border-primary/20 bg-gradient-to-br from-primary/15 via-card/60 to-card/20 p-6 md:p-8">
        <p className="text-xs uppercase tracking-widest text-primary font-semibold">
          Virtualization Control Center
        </p>
        <h2 className="text-3xl md:text-4xl font-black tracking-tight mt-2">
          Host & VM Overview
        </h2>
              <p className="text-foreground/80 mt-3 max-w-3xl text-base">
          Live host metrics, VM status, and VirtualBox info. Refreshes every 5s.
          {data?.virtualbox?.version && (
            <span className="ml-2 text-primary font-semibold">
              VBox {data.virtualbox.version}
            </span>
          )}
        </p>
        {error && (
          <p className="mt-2 text-sm text-red-400">{error}</p>
        )}
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => (
          <div
            key={s.label}
            className="p-5 rounded-xl border border-border bg-card/40 backdrop-blur-sm hover:border-primary/20 transition-all"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">{s.label}</p>
                <p className="text-2xl font-bold mt-1">{s.value}</p>
              </div>
              <div className={`p-3 rounded-full ${s.bg}`}>
                <s.icon className={`w-5 h-5 ${s.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Virtualization stack status */}
      {vboxAvail === false && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-6">
          <h3 className="font-semibold text-lg text-amber-200">VirtualBox not detected</h3>
          <p className="text-sm text-muted-foreground mt-2">
            VirtualBox is required to create and manage VMs. If you just installed it, open
            VirtualBox once to initialize the service, then refresh this page.
          </p>
          <div className="flex gap-3 mt-4">
            <a href={VBOX_DOWNLOAD_URL} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-200 hover:bg-amber-500/30 transition-colors font-medium text-sm">
              <ExternalLink className="w-4 h-4" /> Download VirtualBox
            </a>
            <button onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-muted-foreground hover:bg-white/10 transition-colors text-sm">
              Refresh
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Resources chart */}
        <div className="lg:col-span-2 p-6 rounded-xl border border-border bg-card/40 backdrop-blur-sm">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary" />
            CPU & Memory (last ~2 min)
          </h3>
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="memGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                <XAxis dataKey="time" hide />
                <YAxis stroke="#666" fontSize={12} unit="%" />
                <Tooltip contentStyle={{ backgroundColor: "#1a1a1a", border: "1px solid #333", borderRadius: "8px" }} itemStyle={{ fontSize: "12px" }} />
                <Area type="monotone" dataKey="cpu" stroke="#3b82f6" fill="url(#cpuGrad)" name="CPU" />
                <Area type="monotone" dataKey="memory" stroke="#a855f7" fill="url(#memGrad)" name="Memory" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* VM Status Breakdown */}
        <div className="p-6 rounded-xl border border-border bg-card/40 backdrop-blur-sm">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Server className="w-4 h-4 text-primary" />
            VMs
          </h3>
          {vms ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: "Running", count: vms.running, color: "text-green-500", bg: "bg-green-500/10" },
                  { label: "Stopped", count: vms.stopped, color: "text-gray-400", bg: "bg-gray-500/10" },
                  { label: "Paused", count: vms.paused, color: "text-yellow-500", bg: "bg-yellow-500/10" },
                ].map((s) => (
                  <div key={s.label} className={`p-3 rounded-lg ${s.bg} text-center`}>
                    <p className={`text-2xl font-bold ${s.color}`}>{s.count}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => navigate("/virtualbox")}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs rounded-lg bg-primary/20 text-primary hover:bg-primary/30 transition-colors"
                >
                  <Monitor className="w-3.5 h-3.5" /> VirtualBox
                </button>
                <button
                  onClick={() => navigate("/sandbox")}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-colors"
                >
                  <Box className="w-3.5 h-3.5" /> Sandbox
                </button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Loading...</p>
          )}
        </div>
      </div>

      {/* VM list */}
      {vms && vms.list && vms.list.length > 0 && (
        <div className="p-6 rounded-xl border border-border bg-card/40 backdrop-blur-sm">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Monitor className="w-4 h-4 text-primary" />
            Recent VMs
          </h3>
          <div className="space-y-2">
            {vms.list.map((vm) => (
              <div key={vm.name} className="flex items-center justify-between py-2 px-3 rounded-lg bg-background/30 border border-border/50">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${vm.state === "running" ? "bg-green-500" : vm.state === "paused" ? "bg-yellow-500" : "bg-gray-500"}`} />
                  <span className="text-sm font-medium">{vm.name}</span>
                  {vm.provider && (
                    <span className="text-xs px-1.5 py-0.5 rounded-full bg-muted/50 text-muted-foreground uppercase font-bold">
                      {vm.provider}
                    </span>
                  )}
                </div>
                <span className="text-xs capitalize text-muted-foreground">{vm.state}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
