import { Download, ExternalLink, Loader2, Play } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { API_BASE } from "../api/config";

interface FleetApp {
  id: string;
  label: string;
  port: number;
  tags: string[];
  description?: string;
  repo_path?: string;
  start_command?: string;
}

const CATEGORIES: { key: string; label: string; match: (t: string[]) => boolean }[] = [
  { key: "ai", label: "AI & LLM", match: (t) => t.some((x) => ["ai", "llm", "agent", "local-llm"].includes(x)) },
  { key: "media", label: "Media & VJ", match: (t) => t.some((x) => ["media", "vj", "vr", "3d", "creative"].includes(x)) },
  { key: "dev", label: "Dev & Infra", match: (t) => t.some((x) => ["development", "infra", "cli", "toolbench", "factory"].includes(x)) },
  { key: "smarthome", label: "Smart Home & IoT", match: (t) => t.some((x) => ["smart-home", "control", "voice"].includes(x)) },
  { key: "research", label: "Knowledge & Research", match: (t) => t.some((x) => ["books", "knowledge", "research", "arxiv", "rss", "rag"].includes(x)) },
  { key: "comm", label: "Communication", match: (t) => t.some((x) => ["discord", "command"].includes(x)) },
  { key: "other", label: "Other", match: () => true },
];

function categorize(app: FleetApp): string {
  for (const cat of CATEGORIES) {
    if (cat.match(app.tags || [])) return cat.key;
  }
  return "other";
}

export default function Apps() {
  const [apps, setApps] = useState<FleetApp[]>([]);
  const [loading, setLoading] = useState(true);
  const [statuses, setStatuses] = useState<Record<string, string>>({});
  const [starting, setStarting] = useState<string | null>(null);
  const [selectedApps, setSelectedApps] = useState<Set<string>>(new Set());

  const fetchApps = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/apps`);
      if (res.ok) {
        const data = await res.json();
        setApps((data.webapps || []).sort((a: FleetApp, b: FleetApp) => a.label.localeCompare(b.label)));
      }
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/apps/check`);
      if (res.ok) {
        const data = await res.json();
        setStatuses(data.statuses || {});
      }
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { fetchApps().then(checkHealth); }, [fetchApps, checkHealth]);

  const grouped = useMemo(() => {
    const groups: Record<string, FleetApp[]> = {};
    for (const app of apps) {
      const cat = categorize(app);
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push(app);
    }
    return groups;
  }, [apps]);

  const startApp = async (appId: string) => {
    setStarting(appId);
    try {
      await fetch(`${API_BASE}/api/v1/apps/${appId}/start`, { method: "POST" });
      setTimeout(checkHealth, 3000);
    } catch { /* ignore */ }
    setStarting(null);
  };

  return (
    <div className="space-y-8 pb-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Apps Hub</h2>
          <p className="text-muted-foreground mt-1">Fleet app discovery, health monitoring, and launch ({apps.length} apps)</p>
        </div>
        <button onClick={checkHealth} className="p-2 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 text-muted-foreground">
          <Loader2 className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 rounded-2xl border border-border bg-card/20 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="space-y-10">
          {CATEGORIES.map((cat) => {
            const items = grouped[cat.key];
            if (!items || items.length === 0) return null;
            return (
              <div key={cat.key}>
                <h3 className="text-lg font-semibold text-muted-foreground mb-4 flex items-center gap-2">
                  {cat.label}
                  <span className="text-xs font-mono text-muted-foreground/50">{items.length}</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {items.map((app) => {
                    const status = statuses[app.id] || "unknown";
                    const isRunning = status === "running";
                    return (
                      <div
                        key={app.id}
                        className="group p-4 rounded-xl border border-border bg-card/30 backdrop-blur-sm hover:border-primary/30 transition-all"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="min-w-0 flex-1">
                            <h4 className="font-semibold text-sm">{app.label}</h4>
                            <p className="text-[11px] text-muted-foreground/60 mt-0.5">{app.id}</p>
                          </div>
                          <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider flex-shrink-0 ml-2 ${
                            isRunning ? "bg-green-500/20 text-green-500" : "bg-muted/30 text-muted-foreground"
                          }`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${isRunning ? "bg-green-500" : "bg-muted-foreground"}`} />
                            {status}
                          </div>
                        </div>
                        {app.description && (
                          <p className="text-xs text-muted-foreground/70 mb-3">{app.description}</p>
                        )}
                        <div className="flex items-center gap-2 mt-auto">
                          {isRunning ? (
                            <a
                              href={`http://localhost:${app.port}`}
                              target="_blank" rel="noopener noreferrer"
                              className="flex-1 flex items-center justify-center gap-1.5 py-1.5 text-xs rounded-lg bg-primary/20 text-primary hover:bg-primary/30 transition-colors font-medium"
                            >
                              <ExternalLink className="w-3 h-3" /> Open :{app.port}
                            </a>
                          ) : (
                            <button
                              onClick={() => startApp(app.id)}
                              disabled={starting === app.id}
                              className="flex-1 flex items-center justify-center gap-1.5 py-1.5 text-xs rounded-lg bg-white/10 text-muted-foreground hover:bg-white/20 transition-colors font-medium disabled:opacity-50"
                            >
                              {starting === app.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                              Start
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Fleet Installer */}
      <div className="rounded-xl border border-border bg-card/40 backdrop-blur-sm p-5 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Fleet Installer</h3>
          <button
            onClick={async () => {
              const selected = apps.filter((a) => selectedApps.has(a.id));
              if (selected.length === 0) return;
              const res = await fetch(`${API_BASE}/api/v1/fleet/install-script`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ repos: selected.map((a) => a.id) }),
              });
              if (res.ok) {
                const data = await res.json();
                const blob = new Blob([data.script], { type: "text/plain" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "fleet-install.ps1";
                a.click();
                URL.revokeObjectURL(url);
              }
            }}
            disabled={selectedApps.size === 0}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors font-medium disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" /> Script ({selectedApps.size})
          </button>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {apps.map((app) => (
            <button
              key={app.id}
              onClick={() => {
                const next = new Set(selectedApps);
                if (next.has(app.id)) next.delete(app.id);
                else next.add(app.id);
                setSelectedApps(next);
              }}
              className={`px-2.5 py-1 text-[11px] rounded-lg border transition-colors ${
                selectedApps.has(app.id) ? "bg-primary/20 text-primary border-primary/30" : "bg-white/5 text-muted-foreground border-border hover:border-primary/30"
              }`}
            >
              {app.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
