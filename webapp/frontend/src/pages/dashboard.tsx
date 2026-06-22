import {
  Activity,
  Box,
  Cpu,
  ExternalLink,
  HardDrive,
  MemoryStick,
  Monitor,
  Server,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
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
  vms: {
    total: number;
    running: number;
    stopped: number;
    paused: number;
    list: VmInfo[];
  };
  virtualbox: { version: string };
}

const VBOX_DOWNLOAD_URL = "https://www.virtualbox.org/wiki/Downloads";

async function checkBackendHealth(): Promise<{ ok: boolean; error?: string }> {
  try {
    const r = await fetch(`${API_BASE}/api/v1/health`);
    if (!r.ok) return { ok: false, error: `HTTP ${r.status}` };
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : "Network error" };
  }
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [vboxAvail, setVboxAvail] = useState<boolean | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [restarting, setRestarting] = useState(false);
  const navigate = useNavigate();

  const refresh = useCallback(async () => {
    const h = await checkBackendHealth();
    setBackendOk(h.ok);
  }, []);

  // Poll via HTTP every 10s (works in dev browser)
  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 10_000);
    return () => clearInterval(interval);
  }, [refresh]);

  // Listen for Tauri backend-status event (instant updates in WebView)
  useEffect(() => {
    let unlisten: (() => void) | undefined;
    (async () => {
      try {
        const { listen } = await import("@tauri-apps/api/event");
        unlisten = await listen<string>("backend-status", (event) => {
          if (event.payload === "ready") {
            refresh();
          } else if (typeof event.payload === "string" && event.payload.startsWith("error:")) {
            setBackendOk(false);
          }
        });
      } catch {
        // Not inside Tauri - HTTP polling handles it
      }
    })();
    return () => { if (unlisten) unlisten(); };
  }, [refresh]);

  const restartBackend = useCallback(async () => {
    setRestarting(true);
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("start_backend");
    } catch {
      setRestarting(false);
    }
  }, []);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/dashboard`);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const result = await res.json();
        setData(result);
        setVboxAvail(result.host?.virtualbox?.version ? true : false);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch dashboard data");
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/metrics/history`);
        if (res.ok) {
          const result = await res.json();
          setHistory(result.history || []);
        }
      } catch {
        // Silently fail for history
      }
    };

    fetchHistory();
    const interval = setInterval(fetchHistory, 15000);
    return () => clearInterval(interval);
  }, []);

  const formatBytes = (bytes: number) => {
    const gb = bytes / 1024 ** 3;
    return `${gb.toFixed(1)} GB`;
  };

  const getStatusColor = (state: string) => {
    switch (state?.toLowerCase()) {
      case "running":
        return "text-green-500";
      case "paused":
        return "text-yellow-500";
      default:
        return "text-gray-500";
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
            Dashboard
          </h1>
          <p className="text-muted-foreground mt-1">
            System overview and fleet health
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Backend status indicator */}
          <div
            data-testid="backend-status"
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
              backendOk === null
                ? "bg-gray-500/10 text-gray-400"
                : backendOk
                  ? "bg-green-500/10 text-green-400"
                  : "bg-red-500/10 text-red-400"
            }`}
          >
            <div
              className={`w-2 h-2 rounded-full animate-pulse ${
                backendOk === null
                  ? "bg-gray-500"
                  : backendOk
                    ? "bg-green-500"
                    : "bg-red-500"
              }`}
            />
            {backendOk === null ? "Connecting..." : backendOk ? "Connected" : "Offline"}
          </div>
          {/* Restart button when offline */}
          {backendOk === false && (
            <button
              type="button"
              data-testid="restart-backend"
              onClick={restartBackend}
              disabled={restarting}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors disabled:opacity-50"
            >
              {restarting ? "Restarting..." : "Restart Backend"}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div data-testid="kpi-cpu" className="glass-panel p-6 rounded-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-blue-500/10 rounded-lg border border-blue-500/20">
              <Cpu className="w-5 h-5 text-blue-400" />
            </div>
            <span className="text-2xl font-bold">
              {data?.host?.cpu_usage?.toFixed(1) ?? "--"}%
            </span>
          </div>
          <p className="text-sm text-muted-foreground">CPU Usage</p>
        </div>

        <div data-testid="kpi-memory" className="glass-panel p-6 rounded-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-green-500/10 rounded-lg border border-green-500/20">
              <MemoryStick className="w-5 h-5 text-green-400" />
            </div>
            <span className="text-2xl font-bold">
              {data?.host ? formatBytes(data.host.memory_total - data.host.memory_available) : "--"}
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            Memory Used / {data?.host ? formatBytes(data.host.memory_total) : "--"}
          </p>
        </div>

        <div data-testid="kpi-disk" className="glass-panel p-6 rounded-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-purple-500/10 rounded-lg border border-purple-500/20">
              <HardDrive className="w-5 h-5 text-purple-400" />
            </div>
            <span className="text-2xl font-bold">
              {data?.host?.disk_usage?.percent?.toFixed(1) ?? "--"}%
            </span>
          </div>
          <p className="text-sm text-muted-foreground">Disk Usage</p>
        </div>

        <div data-testid="kpi-vms" className="glass-panel p-6 rounded-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-amber-500/10 rounded-lg border border-amber-500/20">
              <Monitor className="w-5 h-5 text-amber-400" />
            </div>
            <span className="text-2xl font-bold">
              {data?.vms?.total ?? "--"}
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            VMs: {data?.vms?.running ?? 0} running, {data?.vms?.stopped ?? 0} stopped
          </p>
        </div>
      </div>

      {/* CPU/Memory History Chart */}
      <div className="glass-panel p-6 rounded-xl">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary" />
          System Metrics (Last 5 min)
        </h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={history}>
              <defs>
                <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="memGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="time"
                stroke="hsl(var(--muted-foreground))"
                tick={{ fontSize: 12 }}
              />
              <YAxis
                stroke="hsl(var(--muted-foreground))"
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                contentStyle={{
                  background: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                }}
              />
              <Area
                type="monotone"
                dataKey="cpu"
                stroke="#3b82f6"
                fill="url(#cpuGradient)"
                strokeWidth={2}
                name="CPU %"
              />
              <Area
                type="monotone"
                dataKey="memory"
                stroke="#22c55e"
                fill="url(#memGradient)"
                strokeWidth={2}
                name="Memory %"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* VirtualBox Status */}
      <div className="glass-panel p-6 rounded-xl">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Box className="w-5 h-5 text-primary" />
          VirtualBox Status
        </h2>
        {vboxAvail === null ? (
          <p className="text-muted-foreground">Checking...</p>
        ) : vboxAvail ? (
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-sm">
              Version {data?.host?.virtualbox?.version ?? "unknown"}{" "}
              <span className="text-green-400">(Available)</span>
            </span>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <span className="text-sm text-red-400">VirtualBox not found</span>
            </div>
            <a
              href={VBOX_DOWNLOAD_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/10 text-primary text-sm hover:bg-primary/20 transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              Download VirtualBox
            </a>
          </div>
        )}
      </div>

      {/* VM List */}
      <div className="glass-panel p-6 rounded-xl">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Server className="w-5 h-5 text-primary" />
          Virtual Machines
        </h2>
        {data?.vms?.list && data.vms.list.length > 0 ? (
          <div className="grid gap-3">
            {data.vms.list.map((vm) => (
              <button
                type="button"
                key={vm.name}
                onClick={() => navigate(`/vm/${vm.name}/console`)}
                data-testid={`vm-item-${vm.name}`}
                className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/[0.07] transition-all text-left w-full"
              >
                <div className="flex items-center gap-3">
                  <Server className="w-4 h-4 text-muted-foreground" />
                  <span className="font-medium text-sm">{vm.name}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-medium ${getStatusColor(vm.state)}`}>
                    {vm.state}
                  </span>
                  {vm.provider && (
                    <span className="text-xs text-muted-foreground bg-white/5 px-2 py-1 rounded-md">
                      {vm.provider}
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground text-sm">
            {data ? "No VMs found. Create one in the VirtualBox or Hyper-V section." : "Loading..."}
          </p>
        )}
      </div>
    </div>
  );
}
