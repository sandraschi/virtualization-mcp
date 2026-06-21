import {
  AlertCircle,
  Download,
  Filter,
  Pause,
  RefreshCw,
  ScrollText,
  Search,
  Trash2,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { API_BASE } from "../api/config";

interface LogsResponse {
  files: string[];
  current_file: string;
  lines: string[];
}

export default function Logs() {
  const [files, setFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>(
    "virtualization-mcp.log",
  );
  const [lines, setLines] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [levelFilter, setLevelFilter] = useState("all");
  const [limit, setLimit] = useState(200);

  // Auto-refresh state
  const [autoRefresh, setAutoRefresh] = useState(true);

  const logContainerRef = useRef<HTMLDivElement>(null);
  const intervalRef = useRef<any>(null);

  const fetchLogs = async (showLoading = false) => {
    if (showLoading) setLoading(true);
    try {
      const queryParams = new URLSearchParams({
        file: selectedFile,
        limit: limit.toString(),
        level: levelFilter,
        search: searchQuery,
      });

      const res = await fetch(
        `${API_BASE}/api/v1/logs?${queryParams.toString()}`,
      );
      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      const data: LogsResponse = await res.json();

      setFiles(data.files || []);
      if (data.current_file) {
        setSelectedFile(data.current_file);
      }
      setLines(data.lines || []);
      setError(null);
    } catch (err: any) {
      console.error("Error fetching logs:", err);
      setError(err.message || "Failed to connect to backend");
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  // Initial fetch and polling setup
  useEffect(() => {
    fetchLogs(true);
  }, [selectedFile, levelFilter, limit]);

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(() => {
        fetchLogs(false);
      }, 3000);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [autoRefresh, selectedFile, searchQuery, levelFilter, limit]);

  // Scroll to bottom when logs update
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [lines]);

  const handleDownload = () => {
    const element = document.createElement("a");
    const file = new Blob([lines.join("\n")], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = selectedFile;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handleClearView = () => {
    setLines([]);
  };

  const getLogLevelStyle = (line: string) => {
    const upper = line.toUpperCase();
    if (upper.includes("ERROR") || upper.includes("CRITICAL")) {
      return "text-red-400 bg-red-950/20 border-l-2 border-red-500 pl-2";
    }
    if (upper.includes("WARNING") || upper.includes("WARN")) {
      return "text-yellow-400 bg-yellow-950/20 border-l-2 border-yellow-500 pl-2";
    }
    if (upper.includes("DEBUG")) {
      return "text-purple-400 bg-purple-950/10";
    }
    return "text-emerald-400/90";
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-20">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/50 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <ScrollText className="w-8 h-8 text-primary" />
            <h2 className="text-3xl font-bold tracking-tight">System Logs</h2>
          </div>
          <p className="text-muted-foreground mt-1">
            Real-time diagnostics and event trail for virtualization services
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* File Select */}
          <select
            value={selectedFile}
            onChange={(e) => setSelectedFile(e.target.value)}
            className="bg-card border border-border rounded-xl px-3 py-2 text-sm text-foreground outline-none focus:border-primary transition-colors"
          >
            {files.map((file) => (
              <option key={file} value={file}>
                {file}
              </option>
            ))}
          </select>

          {/* Auto Refresh Toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl border text-sm font-semibold transition-all ${
              autoRefresh
                ? "bg-green-500/10 border-green-500/30 text-green-500"
                : "border-border text-muted-foreground hover:bg-white/5"
            }`}
          >
            {autoRefresh ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Live: ON
              </>
            ) : (
              <>
                <Pause className="w-4 h-4" />
                Live: OFF
              </>
            )}
          </button>

          {/* Download Button */}
          <button
            onClick={handleDownload}
            title="Download Logs"
            className="p-2 border border-border rounded-xl hover:bg-white/5 text-muted-foreground hover:text-foreground transition-colors"
          >
            <Download className="w-4 h-4" />
          </button>

          {/* Clear Button */}
          <button
            onClick={handleClearView}
            title="Clear View"
            className="p-2 border border-border rounded-xl hover:bg-white/5 text-red-500/80 hover:text-red-500 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Toolbar / Filters */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 rounded-2xl border border-border bg-card/20 backdrop-blur-sm">
        {/* Search */}
        <div className="md:col-span-2 relative flex items-center">
          <Search className="absolute left-3 w-4 h-4 text-muted-foreground pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && fetchLogs(true)}
            placeholder="Search log messages... (Press Enter)"
            className="w-full bg-black/20 border border-border rounded-xl pl-9 pr-4 py-2 text-sm outline-none focus:border-primary transition-colors"
          />
        </div>

        {/* Level Filter */}
        <div className="relative flex items-center">
          <Filter className="absolute left-3 w-4 h-4 text-muted-foreground pointer-events-none" />
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="w-full bg-black/20 border border-border rounded-xl pl-9 pr-4 py-2 text-sm outline-none focus:border-primary transition-colors appearance-none"
          >
            <option value="all">All Levels</option>
            <option value="info">INFO</option>
            <option value="warning">WARNING</option>
            <option value="error">ERROR</option>
            <option value="debug">DEBUG</option>
          </select>
        </div>

        {/* Limit Selector */}
        <select
          value={limit}
          onChange={(e) => setLimit(Number(e.target.value))}
          className="bg-black/20 border border-border rounded-xl px-4 py-2 text-sm outline-none focus:border-primary transition-colors"
        >
          <option value={100}>Last 100 lines</option>
          <option value={200}>Last 200 lines</option>
          <option value={500}>Last 500 lines</option>
          <option value={1000}>Last 1000 lines</option>
        </select>
      </div>

      {/* Log Console Container */}
      <div className="relative border border-border/80 bg-black/40 backdrop-blur-lg rounded-2xl overflow-hidden shadow-2xl">
        {/* Terminal Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/50 bg-white/5">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/80" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
            <div className="w-3 h-3 rounded-full bg-green-500/80" />
            <span className="text-xs text-muted-foreground font-mono ml-2">
              CONSOLE // {selectedFile}
            </span>
          </div>
          {loading && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-primary" />
              Syncing...
            </div>
          )}
        </div>

        {/* Log Lines Area */}
        <div
          ref={logContainerRef}
          className="h-[550px] overflow-y-auto p-6 font-mono text-xs leading-relaxed space-y-1.5 custom-scrollbar selection:bg-primary/20"
        >
          {error && (
            <div className="flex items-center gap-3 p-4 rounded-xl border border-red-500/20 bg-red-950/10 text-red-400">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <div>
                <p className="font-bold">Failed to load logs</p>
                <p className="text-xs opacity-80 mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {!error && lines.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground space-y-3">
              <ScrollText className="w-12 h-12 stroke-[1.5] text-muted-foreground/40" />
              <p className="text-sm">No matching log records found.</p>
            </div>
          )}

          {!error &&
            lines.map((line, idx) => (
              <div
                key={idx}
                className={`py-0.5 px-2 rounded hover:bg-white/5 transition-colors whitespace-pre-wrap ${getLogLevelStyle(
                  line,
                )}`}
              >
                {line}
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
