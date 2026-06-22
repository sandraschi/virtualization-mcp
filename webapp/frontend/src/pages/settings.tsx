import {
  Bell,
  CheckCircle2,
  Cpu,
  ExternalLink,
  Eye,
  EyeOff,
  KeyRound,
  Loader2,
  Lock,
  Monitor,
  RefreshCw,
  Save,
  Server,
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
  openai?: ProviderInfo;
  deepseek?: ProviderInfo;
  anthropic?: ProviderInfo;
  gemini?: ProviderInfo;
}

interface KeyDef {
  id: string;
  label: string;
  link: string;
}

const DEFAULT_KEY_DEFS: KeyDef[] = [
  {
    id: "DEEPSEEK_API_KEY",
    label: "DeepSeek",
    link: "https://platform.deepseek.com/api_keys",
  },
  {
    id: "ANTHROPIC_API_KEY",
    label: "Anthropic (Claude)",
    link: "https://console.anthropic.com/settings/keys",
  },
  {
    id: "GOOGLE_API_KEY",
    label: "Google (Gemini)",
    link: "https://aistudio.google.com/app/apikey",
  },
  {
    id: "OPENAI_API_KEY",
    label: "OpenAI",
    link: "https://platform.openai.com/api-keys",
  },
];

export default function Settings() {
  const [providers, setProviders] = useState<ProvidersData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [apiKeyDefs, setApiKeyDefs] = useState<KeyDef[]>(DEFAULT_KEY_DEFS);
  const [visibleKeys, setVisibleKeys] = useState<Record<string, boolean>>({});
  const [editKeys, setEditKeys] = useState<Record<string, string>>({});

  const [selectedProvider, setSelectedProvider] = useState<
    "ollama" | "lm_studio" | "openai" | "deepseek" | "anthropic" | "gemini"
  >("ollama");
  const [customEndpoint, setCustomEndpoint] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [gpuAccel, setGpuAccel] = useState(true);

  // Proxmox settings
  const [proxmoxHost, setProxmoxHost] = useState("");
  const [proxmoxUser, setProxmoxUser] = useState("root@pam");
  const [proxmoxPassword, setProxmoxPassword] = useState("");
  const [proxmoxNode, setProxmoxNode] = useState("");
  const [proxmoxTesting, setProxmoxTesting] = useState(false);
  const [proxmoxTestResult, setProxmoxTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  const [proxmoxSaved, setProxmoxSaved] = useState(false);
  const [testResult, setTestResult] = useState<{
    ok: boolean;
    msg: string;
  } | null>(null);

  const fetchLlmSettings = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/llm`);
      if (res.ok) {
        const data = await res.json();
        if (data.provider) setSelectedProvider(data.provider);
        if (data.endpoint) setCustomEndpoint(data.endpoint);
        if (data.model) setSelectedModel(data.model);
        if (data.gpu_accel !== undefined) setGpuAccel(data.gpu_accel);
        return data;
      }
    } catch {
      /* server down */
    }
    return null;
  }, []);

  const fetchProviders = useCallback(async (savedSettings?: any) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/llm/providers`);
      if (res.ok) {
        const data: ProvidersData = await res.json();
        setProviders(data);
        if (!savedSettings) {
          if (data.ollama.available && data.ollama.models.length > 0) {
            setSelectedProvider("ollama");
            setSelectedModel(data.ollama.models[0].name);
          } else if (
            data.lm_studio.available &&
            data.lm_studio.models.length > 0
          ) {
            setSelectedProvider("lm_studio");
            setSelectedModel(data.lm_studio.models[0].name);
          } else if (data.openai?.available && data.openai.models.length > 0) {
            setSelectedProvider("openai");
            setSelectedModel(data.openai.models[0].name);
          } else if (
            data.deepseek?.available &&
            data.deepseek.models.length > 0
          ) {
            setSelectedProvider("deepseek");
            setSelectedModel(data.deepseek.models[0].name);
          } else if (
            data.anthropic?.available &&
            data.anthropic.models.length > 0
          ) {
            setSelectedProvider("anthropic");
            setSelectedModel(data.anthropic.models[0].name);
          } else if (data.gemini?.available && data.gemini.models.length > 0) {
            setSelectedProvider("gemini");
            setSelectedModel(data.gemini.models[0].name);
          }
        }
      }
    } catch {
      /* server down */
    }
    setLoading(false);
  }, []);

  const fetchKeys = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/keys`);
      if (res.ok) {
        const d = await res.json();
        setApiKeys(d.keys || {});
        setApiKeyDefs(d.definitions || DEFAULT_KEY_DEFS);
      }
    } catch {
      /* server down */
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      const saved = await fetchLlmSettings();
      await fetchProviders(saved);
      await fetchKeys();
    };
    init();
  }, [fetchLlmSettings, fetchProviders, fetchKeys]);

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
      } catch {
        /* server down */
      }
    }
  };

  const activeProvider = providers?.[selectedProvider];
  const models = activeProvider?.models || [];

  const handleSave = async () => {
    setLoading(true);
    try {
      const llmRes = await fetch(`${API_BASE}/api/v1/settings/llm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: selectedProvider,
          endpoint:
            customEndpoint ||
            (selectedProvider === "ollama"
              ? "http://localhost:11434"
              : selectedProvider === "lm_studio"
                ? "http://localhost:1234"
                : selectedProvider === "deepseek"
                  ? "https://api.deepseek.com/v1"
                  : selectedProvider === "anthropic"
                    ? "https://api.anthropic.com/v1"
                    : selectedProvider === "gemini"
                      ? "https://generativelanguage.googleapis.com"
                      : "https://api.openai.com/v1"),
          model: selectedModel,
          gpu_accel: gpuAccel,
        }),
      });

      const keysToSave: Record<string, string> = {};
      for (const kd of apiKeyDefs) {
        if (editKeys[kd.id] !== undefined) {
          keysToSave[kd.id] = editKeys[kd.id] ?? "";
        }
      }
      let keysSaved = true;
      if (Object.keys(keysToSave).length > 0) {
        const keysRes = await fetch(`${API_BASE}/api/v1/settings/keys`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ keys: keysToSave }),
        });
        if (keysRes.ok) {
          const d = await keysRes.json();
          setApiKeys(d.keys || {});
          setEditKeys({});
        } else {
          keysSaved = false;
        }
      }

      if (llmRes.ok && keysSaved) {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      }
    } catch (err) {
      console.error("Error saving settings:", err);
    } finally {
      setLoading(false);
    }
  };

  const [activeSection, setActiveSection] = useState("Local Intelligence");

  const settingsTabs = [
    { id: "Local Intelligence", label: "Local LLM", icon: Cpu },
    { id: "API Keys", label: "API Keys", icon: KeyRound },
    { id: "Proxmox", label: "Proxmox VE", icon: Server },
    { id: "Hardware", label: "Hardware", icon: Monitor },
    { id: "Notifications", label: "Alerts", icon: Bell },
  ];

  // ---- Proxmox handlers ----

  const testProxmox = async () => {
    setProxmoxTesting(true);
    setProxmoxTestResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/proxmox/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          host: proxmoxHost,
          user: proxmoxUser,
          password: proxmoxPassword,
          node: proxmoxNode || undefined,
        }),
      });
      const data = await res.json();
      setProxmoxTestResult(
        data.success
          ? { success: true, message: data.message || "Connected" }
          : { success: false, message: data.detail || data.message || "Connection failed" }
      );
    } catch {
      setProxmoxTestResult({ success: false, message: "Cannot reach backend" });
    } finally {
      setProxmoxTesting(false);
    }
  };

  const saveProxmox = async () => {
    setProxmoxSaved(false);
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/proxmox`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          host: proxmoxHost,
          user: proxmoxUser,
          password: proxmoxPassword,
          node: proxmoxNode || undefined,
        }),
      });
      const data = await res.json();
      if (data.success) {
        setProxmoxSaved(true);
        setTimeout(() => setProxmoxSaved(false), 3000);
      }
    } catch {
      // ignore
    }
  };

  // Load saved Proxmox config on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/settings/proxmox`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.host) setProxmoxHost(data.host);
        if (data?.user) setProxmoxUser(data.user);
        if (data?.node) setProxmoxNode(data.node);
      })
      .catch(() => {});
  }, []);

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
            {saved ? (
              <Lock className="w-4 h-4" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {saved ? "Settings Saved" : "Save Changes"}
          </button>
        </div>
      </div>

      {/* Horizontal Tabs */}
      <div className="flex gap-1 overflow-x-auto pb-2 border-b border-border">
        {settingsTabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveSection(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 rounded-t-xl text-sm font-medium transition-all whitespace-nowrap ${
                tab.id === activeSection
                  ? "bg-card border border-b-0 border-border text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="space-y-8">
        {/* LLM Provider Status */}
        {activeSection === "Local Intelligence" && (
            <div className="p-6 rounded-2xl border border-border bg-card/40 backdrop-blur-sm space-y-6">
              <div className="flex items-center gap-3 border-b border-border pb-4">
                <Cpu className="w-5 h-5 text-primary" />
                <h3 className="font-bold text-lg">Local Intelligence</h3>
              </div>

              {/* Provider cards */}
              <div className="grid grid-cols-3 gap-4">
                {(
                  [
                    "ollama",
                    "lm_studio",
                    "openai",
                    "deepseek",
                    "anthropic",
                    "gemini",
                  ] as const
                ).map((name) => {
                  const p = providers?.[name];
                  const isActive = name === selectedProvider;
                  return (
                    <div
                      key={name}
                      onClick={() => {
                        setSelectedProvider(name);
                        setCustomEndpoint("");
                        setTestResult(null);
                      }}
                      className={`p-4 rounded-xl border transition-all cursor-pointer ${
                        isActive
                          ? "border-primary/40 bg-primary/5 shadow-sm shadow-primary/5"
                          : p?.available
                            ? "border-border hover:border-primary/20 bg-card/20"
                            : "border-border hover:border-primary/10 bg-card/10 opacity-70"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold capitalize">
                          {name.replace("_", " ")}
                        </span>
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
                            {p.version ? p.version : "Connected"}
                          </p>
                          <p className="text-xs text-green-500 mt-1">
                            {p.models?.length || 0} model
                            {p.models?.length !== 1 ? "s" : ""} available
                          </p>
                        </>
                      ) : (
                        <p className="text-xs text-muted-foreground text-red-400">
                          {name === "ollama" || name === "lm_studio"
                            ? p?.error || "Not detected"
                            : "API Key missing"}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Endpoint */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">
                  Endpoint (
                  {selectedProvider === "openai"
                    ? "OpenAI Compatible Cloud"
                    : selectedProvider === "deepseek"
                      ? "DeepSeek API"
                      : selectedProvider === "anthropic"
                        ? "Anthropic API"
                        : selectedProvider === "gemini"
                          ? "Gemini API"
                          : selectedProvider}
                  )
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={
                      customEndpoint ||
                      (selectedProvider === "ollama"
                        ? "http://localhost:11434"
                        : selectedProvider === "lm_studio"
                          ? "http://localhost:1234"
                          : selectedProvider === "deepseek"
                            ? "https://api.deepseek.com/v1"
                            : selectedProvider === "anthropic"
                              ? "https://api.anthropic.com/v1"
                              : selectedProvider === "gemini"
                                ? "https://generativelanguage.googleapis.com"
                                : "https://api.openai.com/v1")
                    }
                    onChange={(e) => setCustomEndpoint(e.target.value)}
                    className="flex-1 bg-gray-800 border border-gray-600 rounded-xl px-4 py-2 text-sm text-white outline-none focus:border-primary transition-colors font-mono"
                  />
                  <button
                    onClick={async () => {
                      setLoading(true);
                      setTestResult(null);
                      try {
                        const ep =
                          customEndpoint ||
                          (selectedProvider === "ollama"
                            ? "http://localhost:11434"
                            : selectedProvider === "lm_studio"
                              ? "http://localhost:1234"
                              : selectedProvider === "deepseek"
                                ? "https://api.deepseek.com/v1"
                                : selectedProvider === "anthropic"
                                  ? "https://api.anthropic.com/v1"
                                  : selectedProvider === "gemini"
                                    ? "https://generativelanguage.googleapis.com"
                                    : "https://api.openai.com/v1");
                        const res = await fetch(
                          `${API_BASE}/api/v1/settings/llm/models?endpoint=${encodeURIComponent(ep)}&provider=${selectedProvider}`,
                        );
                        if (res.ok) {
                          const data = await res.json();
                          if (data.available) {
                            setTestResult({
                              ok: true,
                              msg: `${data.models?.length || 0} models found`,
                            });
                            setProviders((prev) => ({
                              ...prev!,
                              [selectedProvider]: data,
                            }));
                            if (data.models?.length > 0)
                              setSelectedModel(data.models[0].name);
                          } else {
                            setTestResult({
                              ok: false,
                              msg: data.error || "Not available",
                            });
                          }
                        } else {
                          setTestResult({
                            ok: false,
                            msg: `HTTP ${res.status}`,
                          });
                        }
                      } catch (e: any) {
                        setTestResult({
                          ok: false,
                          msg: e.message || "Connection failed",
                        });
                      }
                      setLoading(false);
                    }}
                    className="px-3 py-2 text-sm rounded-lg bg-primary/20 text-primary hover:bg-primary/30 transition-colors"
                  >
                    Test
                  </button>
                  {testResult && (
                    <span
                      className={`text-xs flex items-center gap-1 ${testResult.ok ? "text-green-500" : "text-red-500"}`}
                    >
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
                ) : (
                  <div className="space-y-2">
                    {models.length > 0 && (
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
                        <option value="custom">Custom model...</option>
                      </select>
                    )}
                    {(models.length === 0 ||
                      selectedModel === "custom" ||
                      !models.some((m) => m.name === selectedModel)) && (
                      <input
                        type="text"
                        value={selectedModel === "custom" ? "" : selectedModel}
                        onChange={(e) => setSelectedModel(e.target.value)}
                        placeholder="Enter model name (e.g. gpt-4o, deepseek-chat)..."
                        className="w-full bg-gray-800 border border-gray-600 rounded-xl px-4 py-2 text-sm text-white outline-none focus:border-primary transition-colors font-mono"
                      />
                    )}
                    {models.length === 0 && (
                      <p className="text-xs text-muted-foreground font-mono">
                        No models auto-detected. Type model name manually.
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* GPU toggle */}
              <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5">
                <div className="space-y-0.5">
                  <div className="text-sm font-bold uppercase tracking-wider">
                    GPU Acceleration
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Utilize NVIDIA RTX 4090 for inference
                  </div>
                </div>
                <div
                  className={`w-12 h-6 rounded-full p-1 cursor-pointer transition-colors ${gpuAccel ? "bg-primary" : "bg-muted"}`}
                  onClick={() => setGpuAccel(!gpuAccel)}
                >
                  <div
                    className={`w-4 h-4 rounded-full bg-white transition-transform ${gpuAccel ? "translate-x-6" : "translate-x-0"}`}
                  />
                </div>
              </div>
            </div>
          )}

          {/* API Keys */}
          {activeSection === "API Keys" && (
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
                        <label className="text-sm font-medium text-muted-foreground">
                          {kd.label}
                        </label>
                        <a
                          href={kd.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-primary hover:underline flex items-center gap-1"
                        >
                          Get key <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                      <div className="flex gap-2">
                        <div className="relative flex-1">
                          <input
                            type={isVisible ? "text" : "password"}
                            value={hasEdit ? editVal : masked}
                            onChange={(e) =>
                              setEditKeys((prev) => ({
                                ...prev,
                                [kd.id]: e.target.value,
                              }))
                            }
                            placeholder={
                              masked
                                ? "Leave empty to keep current"
                                : "Paste API key..."
                            }
                            className="w-full bg-gray-800 border border-gray-600 rounded-xl px-4 py-2 pr-10 text-sm text-white font-mono outline-none focus:border-primary transition-colors"
                          />
                          <button
                            type="button"
                            onClick={() =>
                              setVisibleKeys((prev) => ({
                                ...prev,
                                [kd.id]: !prev[kd.id],
                              }))
                            }
                            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground"
                          >
                            {isVisible ? (
                              <EyeOff className="w-4 h-4" />
                            ) : (
                              <Eye className="w-4 h-4" />
                            )}
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

          {/* Proxmox Configuration */}
          {activeSection === "Proxmox" && (
          <div className="p-6 rounded-2xl border border-border bg-card/40 backdrop-blur-sm space-y-4">
            <div className="flex items-center gap-3 mb-2">
              <Server className="w-5 h-5 text-primary" />
              <h3 className="font-bold text-lg">Proxmox VE</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              Connect to a remote Proxmox VE host to manage QEMU VMs via the
              REST API. The backend uses ticket-based auth (user + password).
            </p>
            <div className="grid gap-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-muted-foreground">
                  Host
                </label>
                <input
                  type="text"
                  value={proxmoxHost}
                  onChange={(e) => setProxmoxHost(e.target.value)}
                  placeholder="192.168.1.100 or proxmox.example.com"
                  className="w-full bg-gray-800 border border-gray-600 rounded-xl px-4 py-2 text-sm text-white font-mono outline-none focus:border-primary transition-colors"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-muted-foreground">
                    User
                  </label>
                  <input
                    type="text"
                    value={proxmoxUser}
                    onChange={(e) => setProxmoxUser(e.target.value)}
                    placeholder="root@pam"
                    className="w-full bg-gray-800 border border-gray-600 rounded-xl px-4 py-2 text-sm text-white font-mono outline-none focus:border-primary transition-colors"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-muted-foreground">
                    Password
                  </label>
                  <input
                    type="password"
                    value={proxmoxPassword}
                    onChange={(e) => setProxmoxPassword(e.target.value)}
                    placeholder="Proxmox password"
                    className="w-full bg-gray-800 border border-gray-600 rounded-xl px-4 py-2 text-sm text-white font-mono outline-none focus:border-primary transition-colors"
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-muted-foreground">
                  Node <span className="text-xs text-muted-foreground">(optional — autodetected)</span>
                </label>
                <input
                  type="text"
                  value={proxmoxNode}
                  onChange={(e) => setProxmoxNode(e.target.value)}
                  placeholder="pve1"
                  className="w-full bg-gray-800 border border-gray-600 rounded-xl px-4 py-2 text-sm text-white font-mono outline-none focus:border-primary transition-colors"
                />
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={testProxmox}
                disabled={proxmoxTesting}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-primary/30 text-primary hover:bg-primary/10 transition-colors text-sm font-medium"
              >
                {proxmoxTesting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                Test Connection
              </button>
              <button
                onClick={saveProxmox}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors text-sm font-bold"
              >
                <Save className="w-4 h-4" />
                Save
              </button>
              {proxmoxSaved && (
                <span className="text-xs text-green-500 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  Saved
                </span>
              )}
            </div>
            {proxmoxTestResult && (
              <div
                className={`p-3 rounded-xl text-sm ${
                  proxmoxTestResult.success
                    ? "bg-green-500/10 border border-green-500/20 text-green-400"
                    : "bg-red-500/10 border border-red-500/20 text-red-400"
                }`}
              >
                {proxmoxTestResult.message}
              </div>
            )}
          </div>
          )}

          {/* Hardware Status */}
          {activeSection === "Hardware" && (
          <div className="p-6 rounded-2xl border border-border bg-card/40 backdrop-blur-sm space-y-4">
            <div className="flex items-center gap-3 mb-2">
              <Monitor className="w-5 h-5 text-primary" />
              <h3 className="font-bold text-lg">Hardware Status</h3>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-black/20 border border-white/5">
                <div className="text-xs uppercase font-bold text-muted-foreground tracking-widest mb-1">
                  Compute
                </div>
                <div className="text-sm font-mono truncate">
                  AMD Ryzen 9 5900X
                </div>
              </div>
              <div className="p-4 rounded-xl bg-black/20 border border-white/5">
                <div className="text-xs uppercase font-bold text-muted-foreground tracking-widest mb-1">
                  Graphics
                </div>
                <div className="text-sm font-mono truncate text-green-500">
                  NVIDIA RTX 4090
                </div>
              </div>
            </div>
          </div>
          )}
      </div>
    </div>
  );
}
