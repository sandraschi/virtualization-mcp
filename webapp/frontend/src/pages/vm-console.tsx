import { Loader2, Monitor, Play, Power, RefreshCw, ExternalLink } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { API_BASE } from "../api/config";

export default function VmConsole() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const [vmState, setVmState] = useState<string>("unknown");
  const [screenshotTs, setScreenshotTs] = useState(Date.now());
  const [loadError, setLoadError] = useState(false);
  const [paused, setPaused] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval>>();

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

  const refreshScreenshot = useCallback(() => {
    if (!paused) {
      setScreenshotTs(Date.now());
      setLoadError(false);
    }
  }, [paused]);

  useEffect(() => {
    fetchVmInfo();
    intervalRef.current = setInterval(refreshScreenshot, 3000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [fetchVmInfo, refreshScreenshot]);

  const vmAction = async (action: string) => {
    if (!name) return;
    await fetch(`${API_BASE}/api/v1/vms/${encodeURIComponent(name)}/${action}`, { method: "POST" });
    setTimeout(fetchVmInfo, 1500);
  };

  const isRunning = vmState === "running";

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-card/60 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            &larr; Back
          </button>
          <h2 className="font-bold text-lg flex items-center gap-2">
            <Monitor className="w-5 h-5" />
            {name}
          </h2>
          <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${
            isRunning ? "text-green-500 border-green-500/30 bg-green-500/20" : "text-muted-foreground border-muted-foreground/30 bg-muted/20"
          }`}>
            {vmState}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPaused(!paused)}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${paused ? "bg-yellow-500/20 text-yellow-500 border-yellow-500/30" : "bg-white/5 text-muted-foreground border-border"}`}
          >
            {paused ? "Paused" : "Live"}
          </button>
          <button onClick={refreshScreenshot} className="p-2 rounded-lg hover:bg-white/10 text-muted-foreground" title="Refresh now">
            <RefreshCw className="w-4 h-4" />
          </button>
          {isRunning ? (
            <button onClick={() => vmAction("stop")} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-red-500/20 text-red-500 hover:bg-red-500/30 transition-colors font-medium">
              <Power className="w-3.5 h-3.5" /> Stop
            </button>
          ) : (
            <button onClick={() => vmAction("start")} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-green-500/20 text-green-500 hover:bg-green-500/30 transition-colors font-medium">
              <Play className="w-3.5 h-3.5" /> Start
            </button>
          )}
          <a
            href={`https://www.virtualbox.org/manual/ch07.html#vboxheadless`}
            target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg bg-white/5 text-muted-foreground hover:bg-white/10 transition-colors"
          >
            <ExternalLink className="w-3 h-3" /> VBox VRDP
          </a>
        </div>
      </div>

      {/* Screen */}
      <div className="flex-1 bg-black relative overflow-hidden flex items-center justify-center">
        {isRunning ? (
          <>
            <img
              ref={imgRef}
              key={screenshotTs}
              src={`${API_BASE}/api/v1/vms/${encodeURIComponent(name!)}/screenshot?t=${screenshotTs}`}
              alt={`${name} screen`}
              className="max-w-full max-h-full object-contain"
              onError={() => setLoadError(true)}
              onLoad={() => setLoadError(false)}
            />
            {loadError && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground bg-black/80">
                <Monitor className="w-16 h-16 mb-4 opacity-30" />
                <p className="text-lg font-medium">Screen unavailable</p>
                <p className="text-sm mt-1">The VM is running but the screen cannot be captured.</p>
                <p className="text-xs mt-3 text-muted-foreground/60">
                  Try opening VirtualBox directly to interact with this VM.
                </p>
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center text-muted-foreground">
            <Monitor className="w-20 h-20 mb-4 opacity-20" />
            <p className="text-xl font-medium">VM is not running</p>
            <p className="text-sm mt-2">Click <strong>Start</strong> to boot this VM.</p>
          </div>
        )}
      </div>
    </div>
  );
}
