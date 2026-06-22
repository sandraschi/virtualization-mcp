import { clsx } from "clsx";
import {
  BookOpen,
  Box,
  ChevronLeft,
  ChevronRight,
  Code2,
  Cpu,
  HelpCircle,
  LayoutDashboard,
  Menu,
  MessageSquare,
  ScrollText,
  Server,
  Settings,
  Share2,
  Terminal,
  X,
} from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

export default function Layout() {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(() => {
    return localStorage.getItem("sidebar-minimized") === "true";
  });

  const toggleMinimize = () => {
    setIsMinimized((prev) => {
      const next = !prev;
      localStorage.setItem("sidebar-minimized", String(next));
      return next;
    });
  };
  const navItems = [
    { to: "/", icon: LayoutDashboard, label: "Dashboard" },
    { to: "/virtualbox", icon: Server, label: "VirtualBox" },
    { to: "/hyperv", icon: Cpu, label: "Hyper-V" },
    { to: "/proxmox", icon: Server, label: "Proxmox VE" },
    { to: "/sandbox", icon: Box, label: "Windows Sandbox" },
    { to: "/tools", icon: Terminal, label: "Tools Console" },
    { to: "/apps", icon: Share2, label: "Apps Hub" },
    { to: "/prompts-skills", icon: BookOpen, label: "Prompts & Skills" },
    { to: "/chat", icon: MessageSquare, label: "AI Chat" },
    { to: "/api-docs", icon: Code2, label: "API Docs" },
    { to: "/logs", icon: ScrollText, label: "System Logs" },
    { to: "/help", icon: HelpCircle, label: "Help & Docs" },
    { to: "/settings", icon: Settings, label: "Settings" },
  ];

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans selection:bg-primary/20 relative">
      {/* Mobile Top Header Bar */}
      <header className="md:hidden flex items-center justify-between px-6 py-4 bg-card/50 border-b border-border/50 backdrop-blur-xl absolute top-0 left-0 right-0 z-20 h-16">
        <div className="flex items-center gap-3">
          <Terminal className="w-5 h-5 text-primary" />
          <h1 className="font-bold text-base tracking-tight">Virtualization</h1>
        </div>
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="p-2 hover:bg-white/5 rounded-lg text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Toggle Menu"
        >
          {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </header>

      {/* Sidebar Backdrop Overlay on Mobile */}
      {isOpen && (
        // biome-ignore lint/a11y/useKeyWithClickEvents: backdrop click close doesn't need keyboard navigation
        // biome-ignore lint/a11y/noStaticElementInteractions: backdrop click close doesn't need keyboard navigation
        <div
          onClick={() => setIsOpen(false)}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-20 md:hidden transition-all duration-300"
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          "border-r border-border bg-card/50 backdrop-blur-xl flex flex-col fixed inset-y-0 left-0 md:relative z-30 transition-all duration-300 ease-in-out",
          isMinimized ? "w-64 md:w-20" : "w-64 md:w-64",
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
        )}
      >
        <div
          className={clsx(
            "p-6 border-b border-border/50 flex items-center justify-between",
            isMinimized
              ? "md:px-4 md:py-6 md:flex-col md:gap-4 md:items-center"
              : "",
          )}
        >
          <div
            className={clsx(
              "flex items-center gap-3",
              isMinimized ? "md:flex-col md:gap-2" : "",
            )}
          >
            <div className="p-2 bg-primary/10 rounded-lg border border-primary/20 flex-shrink-0">
              <Terminal className="w-6 h-6 text-primary" />
            </div>
            <div className={clsx("min-w-0", isMinimized ? "md:hidden" : "")}>
              <h1 className="font-bold text-lg tracking-tight truncate">
                Virtualization
              </h1>
              <p className="text-xs text-muted-foreground font-mono">
                MCP SOTA v1.0
              </p>
            </div>
          </div>
          <div
            className={clsx(
              "flex items-center gap-2",
              isMinimized ? "md:flex-col md:gap-2" : "",
            )}
          >
            {/* Desktop Minimize Button */}
            <button
              type="button"
              onClick={toggleMinimize}
              className="hidden md:flex p-2 hover:bg-white/5 rounded-lg text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Toggle Sidebar Size"
            >
              {isMinimized ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
            </button>
            {/* Mobile Close Button */}
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="md:hidden p-2 hover:bg-white/5 rounded-lg text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Close Menu"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-2 overflow-y-auto custom-scrollbar">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setIsOpen(false)}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group border border-transparent",
                  isMinimized
                    ? "md:justify-center md:px-0 md:w-12 md:h-12 md:mx-auto"
                    : "",
                  isActive
                    ? "bg-primary/10 text-primary border-primary/20 shadow-sm shadow-primary/5"
                    : "text-muted-foreground hover:bg-white/5 hover:text-foreground hover:border-white/10",
                )
              }
            >
              <item.icon
                className={clsx(
                  "w-5 h-5 transition-colors flex-shrink-0",
                  "group-hover:text-current",
                )}
              />
              <span
                className={clsx("font-medium", isMinimized ? "md:hidden" : "")}
              >
                {item.label}
              </span>
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-border/50">
          {isMinimized && (
            <div className="hidden md:flex justify-center p-2 rounded-lg bg-green-500/10 border border-green-500/20 w-10 h-10 mx-auto items-center">
              <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse" />
            </div>
          )}
          <div
            className={clsx(
              "p-4 rounded-xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-white/5",
              isMinimized ? "md:hidden" : "",
            )}
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-xs font-medium text-green-500">
                System Online
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Connected to Localhost
            </p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto relative bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900/20 via-background to-background pt-16 md:pt-0">
        <div className="absolute inset-0 bg-grid-white/[0.02]" />
        <div className="relative p-8 max-w-7xl mx-auto animate-in fade-in zoom-in-95 duration-500">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
