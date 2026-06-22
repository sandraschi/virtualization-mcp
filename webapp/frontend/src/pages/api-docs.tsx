import { Code2, ExternalLink } from "lucide-react";
import { useState } from "react";

const endpoints = [
  { method: "GET", path: "/api/v1/health", desc: "Backend health check" },
  { method: "GET", path: "/api/v1/dashboard", desc: "Dashboard overview" },
  { method: "GET", path: "/api/v1/host/info", desc: "Host system info" },
  { method: "GET", path: "/api/v1/vms", desc: "List all VMs" },
  { method: "POST", path: "/api/v1/vms", desc: "Create a VM" },
  { method: "GET", path: "/api/v1/sandbox", desc: "Sandbox status" },
  { method: "GET", path: "/api/v1/fleet/apps", desc: "Fleet app registry" },
  { method: "POST", path: "/api/v1/chat", desc: "AI Chat completion" },
];

export default function ApiDocs() {
  const [view, setView] = useState<"swagger" | "redoc">("swagger");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
            API Docs
          </h1>
          <p className="text-muted-foreground mt-1">
            FastAPI auto-generated documentation
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* View toggle */}
          <div className="flex rounded-lg border border-border bg-card p-1">
            <button
              type="button"
              onClick={() => setView("swagger")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                view === "swagger"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Swagger UI
            </button>
            <button
              type="button"
              onClick={() => setView("redoc")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                view === "redoc"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              ReDoc
            </button>
          </div>
          {/* Open in browser */}
          <a
            href={`http://127.0.0.1:10701/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/10 text-primary text-xs font-medium hover:bg-primary/20 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            Open in browser
          </a>
        </div>
      </div>

      {/* Quick-ref strip */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {endpoints.map((ep) => (
          <div
            key={ep.path}
            className="flex-shrink-0 flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-xs"
          >
            <span
              className={`font-mono font-bold ${
                ep.method === "GET"
                  ? "text-green-400"
                  : ep.method === "POST"
                    ? "text-blue-400"
                    : "text-yellow-400"
              }`}
            >
              {ep.method}
            </span>
            <span className="text-muted-foreground font-mono">{ep.path}</span>
          </div>
        ))}
      </div>

      {/* Swagger / ReDoc iframe */}
      <div className="glass-panel rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/50">
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium">
              {view === "swagger" ? "Swagger UI" : "ReDoc"}
            </span>
          </div>
        </div>
        <div className="relative">
          <iframe
            src={
              view === "swagger"
                ? `/docs`
                : `/redoc`
            }
            title={view === "swagger" ? "Swagger UI" : "ReDoc"}
            className="w-full border-0"
            style={{ height: "70vh", background: "#09090b" }}
            sandbox="allow-scripts allow-same-origin"
          />
        </div>
      </div>
    </div>
  );
}
