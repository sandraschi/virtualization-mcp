import {
  Bell,
  Cpu,
  Database,
  Eye,
  EyeOff,
  ExternalLink,
  Globe,
  KeyRound,
  Loader2,
  Lock,
  Monitor,
  RefreshCw,
  RotateCcw,
  Save,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { API_BASE } from "../api/config";

interface ProviderInfo {
  available: boolean;
  version?: string;
  error?: string;
  models: { name: string; size: number | string }[];
}

interface ProvidersData {
  ollama: ProviderInfo;
  lm_studio: ProviderInfo;
}

interface KeyDef {
  id: string;
  label: string;
  link: string;
}

export default function Settings() {
  const [providers, setProviders] = useState<ProvidersData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [apiKeyDefs, setApiKeyDefs] = useState<KeyDef[]>([]);
  const [visibleKeys, setVisibleKeys] = useState<Record<string, boolean>>({});
  const [editKeys, setEditKeys] = useState<Record<string, string>>({});

  const [selectedProvider, setSelectedProvider] = useState<"ollama" | "lm_studio">("ollama");
  const [customEndpoint, setCustomEndpoint] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [gpuAccel, setGpuAccel] = useState(true);
  const [testResult, setTestResult] = useState<{ ok: boolean; msg: string } | null>(null);

  const fetchProviders = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/llm/providers`);
      if (res.ok) {
        const data: ProvidersData = await res.json();
        setProviders(data);
        if (data.ollama.available && data.ollama.models.length > 0) {
          setSelectedProvider("ollama");
          setSelectedModel(data.ollama.models[0].name);
        } else if (data.lm_studio.available && data.lm_studio.models.length > 0) {
          setSelectedProvider("lm_studio");
          setSelectedModel(data.lm_studio.models[0].name);
        }
      }
    } catch { /* server down */ }
    setLoading(false);
  }, []);

  const fetchKeys = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/keys`);
      if (res.ok) {
        const d = await res.json();
        setApiKeys(d.keys || {});
        setApiKeyDefs(d.definitions || []);
      }
    } catch { /* server down */ }
  }, []);

  useEffect(() => { fetchProviders(); fetchKeys(); }, [fetchProviders, fetchKeys]);

  const saveKeys = async () => {
    const toSave: Record<string, string> = {};
    for (const kd of apiKeyDefs) {
      if (editKeys[kd.id] !== undefined) {
        toSave[kd.id] = editKeys[kd.id] ?? "";
      }
    }
    if (Object.keys(toSave).length > 0) {
      try {
        const res = await fetch(`${API_BASE}/api/v1/settings/keys`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ keys: toSave }),
        });
        if (res.ok) {
          const d = await res.json();
          setApiKeys(d.keys || {});
          setEditKeys({});
          setSaved(true);
          setTimeout(() => setSaved(false), 2000);
        }
      } catch { /* server down */ }
    }
  };

  const activeProvider = providers?.[selectedProvider];
  const models = activeProvider?.models || [];

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const [activeSection, setActiveSection] = useState("Local Intelligence");

  const sidebarItems = [
    { label: "Local Intelligence", icon: Cpu },
    { label: "API Keys", icon: KeyRound },
    { label: "Notifications", icon: Bell },
    { label: "Security", icon: Lock },
    { label: "Database", icon: Database },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-20">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">System Settings</h2>
          <p className="text-muted-foreground mt-1">
            Configure your virtualization environment and LLM substrate
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchProviders}
            className="p-2 rounded-lg border border-border hover:bg-white/10 text-muted-foreground"
            title="Rescan providers"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button
            onClick={handleSave}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg font-bold transition-all ${
              saved
                ? "bg-green-500 text-white"
                : "bg-primary text-primary-foreground hover:bg-primary/90"
            }`}
          >
            {saved ? <Lock className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            {saved ? "Settings Saved" : "Save Changes"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-1 space-y-1">
          {sidebarItems.map((item) => (
            <button
              key={item.label}
              onClick={() => setActiveSection(item.label)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${
                item.label === activeSection
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "hover:bg-white/5 text-muted-foreground"
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </button>
          ))}
        </div>

        <div className="md:col-span-2 space-y-8">
          {/* LLM Provider Status */}
          {activeSection === "Local Intelligence" && (
          <div className="p-6 rounded-2xl border border-border bg-card/40 backdrop-blur-sm space-y-6">
            <div className="flex items-center gap-3 border-b border-border pb-4">
              <Cpu className="w-5 h-5 text-primary" />
              <h3 className="font-bold text-lg">Local Intelligence</h3>
            </div>

            {/* Provider cards */}
            <div className="grid grid-cols-2 gap-4">
              {(["ollama", "lm_studio"] as const).map((name) => {
                const p = providers?.[name];
                const isActive = name === selectedProvider;
                return (
                  <div
                    key={name}
                    onClick={() => p?.available && setSelectedProvider(name)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer ${
                      isActive
                        ? "border-primary/40 bg-primary/5"
                        : p?.available
                          ? "border-border hover:border-primary/20"
                          : "border-border/50 opacity-50"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold capitalize">{name.replace("_", " ")}</span>
                      {loading ? (
                        <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
                      ) : p?.available ? (
                        <Wifi className="w-4 h-4 text-green-500" />
                      ) : (
                        <WifiOff className="w-4 h-4 text-muted-foreground" />
                      )}
                    </div>
                    {p?.available ? (
                      <>
                        <p className="text-xs text-muted-foreground">
                          {p.version ? `v${p.version}` : "Connected"}
                        </p>
                        <p className="text-xs text-green-500 mt-1">
                          {p.models.length} model{p.models.length !== 1 ? "s" : ""} available
                        </p>
                      </>
                    ) : (
                      <p className="text-xs text-muted-foreground">
                        {p?.error || "Not detected"}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Endpoint */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground">
                Endpoint ({selectedProvider})
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customEndpoint || (selectedProvider === "ollama" ? "http://localhost:11434" : "http://localhost:1234")}
                  onChange={(e) => setCustomEndpoint(e.target.value)}
                  className="flex-1 bg-gray-800 border border-gray-600 rounded-xl px-4 py-2 text-sm text-white outline-none focus:border-primary transition-colors font-mono"
                />
                <button
                  onClick={async () => {
                    setLoading(true);
                    setTestResult(null);
                    try {
                      const ep = customEndpoint || (selectedProvider === "ollama" ? "http://localhost:11434" : "http://localhost:1234");
                      const res = await fetch(`${API_BASE}/api/v1/settings/llm/models?endpoint=${encodeURIComponent(ep)}&provider=${selectedProvider}`);
                      if (res.ok) {
                        const data = await res.json();
                        if (data.available) {
                          setTestResult({ ok: true, msg: `${data.models?.length || 0} models found` });
                          setProviders((prev) => ({ ...prev!, [selectedProvider]: data }));
                          if (data.models?.length > 0) setSelectedModel(data.models[0].name);
                        } else {
                          setTestResult({ ok: false, msg: data.error || "Not available" });
                        }
                      } else {
                        setTestResult({ ok: false, msg: `HTTP ${res.status}` });
                      }
                    } catch (e: any) {
                      setTestResult({ ok: false, msg: e.message || "Connection failed" });
                    }
                    setLoading(false);
                  }}
                  className="px-3 py-2 text-sm rounded-lg bg-primary/20 text-primary hover:bg-primary/30 transition-colors"
                >
                  Test
                </button>
                {testResult && (
                  <span className={`text-xs flex items-center gap-1 ${testResult.ok ? "text-green-500" : "text-red-500"}`}>
                    {testResult.ok ? "\u2713" : "\u2717"} {testResult.msg}
                  </span>
                )}
              </div>
            </div>

            {/* Model selector */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground">
                Model
              </label>
              {loading ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Scanning...
                </div>
              ) : models.length > 0 ? (
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-600 rounded-xl px-4 py-2 text-sm text-white outline-none focus:border-primary transition-colors"
                >
                  {models.map((m) => (
                    <option key={m.name} value={m.name}>
                      {m.name}
                    </option>
                  ))}
                </select>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No models found. Start {selectedProvider === "ollama" ? "Ollama" : "LM Studio"} and pull a model.
                </p>
              )}
            </div>

            {/* GPU toggle */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5">
              <div className="space-y-0.5">
                <div className="text-sm font-bold uppercase tracking-wider">GPU Acceleration</div>
                <div className="text-xs text-muted-foreground">Utilize NVIDIA RTX 4090 for inference</div>
              </div>
              <div
                className={`w-12 h-6 rounded-full p-1 cursor-pointer transition-colors ${gpuAccel ? "bg-primary" : "bg-muted"}`}
                onClick={() => setGpuAccel(!gpuAccel)}
              >
                <div className={`w-4 h-4 rounded-full bg-white transition-transform ${gpuAccel ? "translate-x-6" : "translate-x-0"}`} />
              </div>
            </div>
          </div>
          )}

          {/* API Keys */}
          {activeSection === "API Keys" && apiKeyDefs.length > 0 && (
            <div className="p-6 rounded-2xl border border-border bg-card/40 backdrop-blur-sm space-y-6">
              <div className="flex items-center gap-3 border-b border-border pb-4">
                <KeyRound className="w-5 h-5 text-primary" />
                <h3 className="font-bold text-lg">API Keys</h3>
              </div>
              <p className="text-sm text-foreground/80">
                Keys are stored locally in{" "}
                <code className="text-foreground">keys.json</code> and override
                <code className="text-foreground"> .env</code> variables.
              </p>
              <div className="space-y-4">
                {apiKeyDefs.map((kd) => {
                  const masked = apiKeys[kd.id] || "";
                  const isVisible = visibleKeys[kd.id];
                  const editVal = editKeys[kd.id] ?? "";
                  const hasEdit = editKeys[kd.id] !== undefined;
                  return (
                    <div key={kd.id} className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <label className="text-sm font-medium text-muted-foreground">{kd.label}</label>
                        <a href={kd.link} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline flex items-center gap-1">
                          Get key <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                      <div className="flex gap-2">
                        <div className="relative flex-1">
                          <input
                            type={isVisible ? "text" : "password"}
                            value={hasEdit ? editVal : masked}
                            onChange={(e) => setEditKeys((prev) => ({ ...prev, [kd.id]: e.target.value }))}
                            placeholder={masked ? "Leave empty to keep current" : "Paste API key..."}
                            className="w-full bg-gray-800 border border-gray-600 rounded-xl px-4 py-2 pr-10 text-sm text-white font-mono outline-none focus:border-primary transition-colors"
                          />
                          <button
                            type="button"
                            onClick={() => setVisibleKeys((prev) => ({ ...prev, [kd.id]: !prev[kd.id] }))}
                            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground"
                          >
                            {isVisible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="flex justify-end">
                <button
                  onClick={saveKeys}
                  className="flex items-center gap-2 px-6 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 font-bold transition-colors"
                >
                  <Save className="w-4 h-4" />
                  Save Keys
                </button>
              </div>
            </div>
          )}

          {/* Hardware Status */}
          <div className="p-6 rounded-2xl border border-border bg-card/40 backdrop-blur-sm space-y-4">
            <div className="flex items-center gap-3 mb-2">
              <Monitor className="w-5 h-5 text-primary" />
              <h3 className="font-bold text-lg">Hardware Status</h3>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-black/20 border border-white/5">
                <div className="text-xs uppercase font-bold text-muted-foreground tracking-widest mb-1">Compute</div>
                <div className="text-sm font-mono truncate">AMD Ryzen 9 5900X</div>
              </div>
              <div className="p-4 rounded-xl bg-black/20 border border-white/5">
                <div className="text-xs uppercase font-bold text-muted-foreground tracking-widest mb-1">Graphics</div>
                <div className="text-sm font-mono truncate text-green-500">NVIDIA RTX 4090</div>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg text-muted-foreground hover:bg-white/5 transition-colors text-sm font-medium uppercase tracking-widest">
              <RotateCcw className="w-4 h-4" />
              Reset Defaults
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
