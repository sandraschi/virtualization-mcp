import { Loader2, Monitor, Play, Power, Download, Wifi, WifiOff } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { API_BASE } from "../api/config";

declare global {
  interface Window {
    RFB?: new (target: HTMLElement, url: string) => {
      scaleViewport: boolean;
      resizeSession: boolean;
      addEventListener: (event: string, handler: (e?: any) => void) => void;
      disconnect: () => void;
    };
  }
}

export default function VmConsole() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const [vmState, setVmState] = useState<string>("unknown");
  const [vrde, setVrde] = useState<boolean | null>(null);
  const [vrdePort, setVrdePort] = useState(3389);
  const [enabling, setEnabling] = useState(false);
  const [vncConnected, setVncConnected] = useState(false);
  const [novncLoaded, setNovncLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const rfbRef = useRef<any>(null);

  const fetchVmInfo = useCallback(async () => {
    if (!name) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/vms`);
      if (res.ok) {
        const data = await res.json();
        const all: any[] = data.vms || [];
        const vm = all.find((v: any) => v.name === name);
        if (vm) setVmState(vm.state);
      }
    } catch { /* ignore */ }
  }, [name]);

  const fetchVrde = useCallback(async () => {
    if (!name) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/vms/${encodeURIComponent(name)}/vrde`);
      if (res.ok) {
        const data = await res.json();
        setVrde(data.vrde);
        setVrdePort(data.port);
      }
    } catch { /* ignore */ }
  }, [name]);

  useEffect(() => {
    fetchVmInfo();
    fetchVrde();
  }, [fetchVmInfo, fetchVrde]);

  // Load noVNC from CDN
  useEffect(() => {
    if (document.querySelector('script[src*="novnc"]')) return;
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/@novnc/novnc@1.5.0/dist/rfb.min.js";
    script.async = true;
    script.onload = () => setNovncLoaded(true);
    script.onerror = () => setError("Failed to load noVNC library");
    document.head.appendChild(script);
  }, []);

  const disconnectRfb = useCallback(() => {
    if (rfbRef.current) {
      try { rfbRef.current.disconnect(); } catch { /* ignore */ }
      rfbRef.current = null;
    }
    setVncConnected(false);
  }, []);

  const connectRfb = useCallback(() => {
    if (!name || !novncLoaded || !window.RFB || !containerRef.current) return;
    disconnectRfb();

    const wsUrl = `${API_BASE.replace("http", "ws")}/api/v1/vms/${encodeURIComponent(name)}/vnc`;

    try {
      const rfb = new window.RFB(containerRef.current, wsUrl);
      rfb.scaleViewport = true;
      rfb.resizeSession = true;

      rfb.addEventListener("connect", () => {
        setVncConnected(true);
        setError(null);
      });

      rfb.addEventListener("disconnect", (e: any) => {
        setVncConnected(false);
        setError(e?.detail?.reason ? `Disconnected: ${e.detail.reason}` : null);
      });

      rfb.addEventListener("credentialsrequired", () => {
        setError("VNC credentials required but not available");
      });

      rfbRef.current = rfb;
    } catch (e: any) {
      setError(`VNC connection error: ${e.message}`);
    }
  }, [name, novncLoaded, disconnectRfb]);

  useEffect(() => {
    if (novncLoaded && vrde) connectRfb();
    return () => disconnectRfb();
  }, [novncLoaded, vrde, connectRfb, disconnectRfb]);

  const enableVrde = async () => {
    if (!name) return;
    setEnabling(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/vms/${encodeURIComponent(name)}/vrde`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: true }),
      });
      if (res.ok) {
        const data = await res.json();
        setVrde(true);
        setVrdePort(data.port);
      }
    } catch { /* ignore */ }
    setEnabling(false);
  };

  const isRunning = vmState === "running";
  const vmAction = async (action: string) => {
    if (!name) return;
    await fetch(`${API_BASE}/api/v1/vms/${encodeURIComponent(name)}/${action}`, { method: "POST" });
    setTimeout(fetchVmInfo, 1500);
  };

  return (
    <div className="h-full flex flex-col bg-black text-white">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-white/10 bg-black/80 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="text-sm text-white/60 hover:text-white transition-colors">
            &larr; Back
          </button>
          <div className="flex items-center gap-2">
            <Monitor className="w-5 h-5 text-blue-400" />
            <h2 className="font-bold text-lg">{name}</h2>
          </div>
          <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${
            isRunning ? "text-green-400 border-green-500/30 bg-green-500/20" : "text-white/40 border-white/10 bg-white/5"
          }`}>{vmState}</span>
          {vrde !== null && (
            <span className={`text-xs flex items-center gap-1 ${vrde ? "text-green-400" : "text-white/40"}`}>
              {vrde ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
              VRDP:{vrdePort}
            </span>
          )}
          {vncConnected && (
            <span className="text-xs text-green-400">VNC connected</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {!vrde && isRunning && (
            <button onClick={enableVrde} disabled={enabling}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-colors font-medium">
              {enabling ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Wifi className="w-3.5 h-3.5" />}
              Enable Remote Desktop
            </button>
          )}
          {vrde && (
            <a href={`${API_BASE}/api/v1/vms/${encodeURIComponent(name!)}/rdp`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-white/10 text-white hover:bg-white/20 transition-colors font-medium">
              <Download className="w-3.5 h-3.5" /> RDP File
            </a>
          )}
          {isRunning ? (
            <button onClick={() => vmAction("stop")}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors font-medium">
              <Power className="w-3.5 h-3.5" /> Stop
            </button>
          ) : (
            <button onClick={() => vmAction("start")}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors font-medium">
              <Play className="w-3.5 h-3.5" /> Start
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="px-4 py-2 bg-red-900/40 text-red-300 text-sm border-b border-red-900/50">
          {error}
        </div>
      )}

      {/* Screen */}
      <div className="flex-1 relative overflow-hidden flex items-center justify-center bg-black">
        {!isRunning ? (
          <div className="flex flex-col items-center justify-center text-white/40">
            <Monitor className="w-20 h-20 mb-4" />
            <p className="text-xl font-medium">VM is not running</p>
            <p className="text-sm mt-2">Click <strong className="text-white/60">Start</strong> to boot.</p>
          </div>
        ) : !vncConnected ? (
          <div className="flex flex-col items-center justify-center text-white/40">
            <Monitor className="w-16 h-16 mb-4" />
            <p className="text-lg">Connecting to VM...</p>
            <p className="text-sm mt-2 text-white/20">
              {!vrde ? "Enable Remote Desktop above" : "Establishing VNC session via noVNC"}
            </p>
          </div>
        ) : null}
        <div ref={containerRef} className={vncConnected ? "w-full h-full" : "hidden"} />
      </div>
    </div>
  );
}
