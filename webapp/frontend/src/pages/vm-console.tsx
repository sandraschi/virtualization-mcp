import { Loader2, Monitor, Play, Power, RefreshCw, Download, Wifi, WifiOff } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { API_BASE } from "../api/config";

export default function VmConsole() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const [vmState, setVmState] = useState<string>("unknown");
  const [vrde, setVrde] = useState<boolean | null>(null);
  const [vrdePort, setVrdePort] = useState(3389);
  const [enabling, setEnabling] = useState(false);
  const [vncConnected, setVncConnected] = useState(false);
  const [useScreenshot, setUseScreenshot] = useState(false);
  const [screenshotTs, setScreenshotTs] = useState(Date.now());
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const scrInterval = useRef<ReturnType<typeof setInterval>>();

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

  const connectVnc = () => {
    if (!name || !vrde) return;
    setVncConnected(true);
    setUseScreenshot(false);
    // RFB protocol via WebSocket — simple canvas rendering
    const ws = new WebSocket(`${API_BASE.replace("http", "ws")}/api/v1/vms/${encodeURIComponent(name)}/vnc`);
    ws.binaryType = "arraybuffer";
    ws.onopen = () => console.log("VNC WebSocket connected");
    ws.onerror = () => { setVncConnected(false); setUseScreenshot(true); };
    ws.onclose = () => { setVncConnected(false); };
    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        const canvas = canvasRef.current;
        if (!canvas) return;
        // For full RFB we need noVNC lib — fallback to screenshot for now
        setUseScreenshot(true);
        ws.close();
      }
    };
    wsRef.current = ws;
  };

  useEffect(() => {
    if (useScreenshot) {
      scrInterval.current = setInterval(() => setScreenshotTs(Date.now()), 3000);
      return () => { if (scrInterval.current) clearInterval(scrInterval.current); };
    }
  }, [useScreenshot]);

  useEffect(() => {
    if (vrde && !vncConnected) connectVnc();
  }, [vrde]);

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

      {/* Screen */}
      <div className="flex-1 relative overflow-hidden flex items-center justify-center bg-black">
        <canvas ref={canvasRef} className="hidden" />
        {useScreenshot && isRunning ? (
          <img
            key={screenshotTs}
            src={`${API_BASE}/api/v1/vms/${encodeURIComponent(name!)}/screenshot?t=${screenshotTs}`}
            alt={`${name} screen`}
            className="max-w-full max-h-full object-contain"
            onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
          />
        ) : isRunning ? (
          <div className="flex flex-col items-center justify-center text-white/40">
            <Monitor className="w-16 h-16 mb-4" />
            <p className="text-lg">Connecting to VM...</p>
            <p className="text-sm mt-2 text-white/20">
              {!vrde ? "Enable Remote Desktop above" : "Use RDP File or screenshot view"}
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center text-white/40">
            <Monitor className="w-20 h-20 mb-4" />
            <p className="text-xl font-medium">VM is not running</p>
            <p className="text-sm mt-2">Click <strong className="text-white/60">Start</strong> to boot.</p>
          </div>
        )}
        {useScreenshot && (
          <div className="absolute bottom-4 right-4 px-2 py-1 rounded bg-black/60 text-[10px] text-white/30">
            Screenshot mode — use RDP for full interaction
          </div>
        )}
      </div>
    </div>
  );
}
