import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, Server, Box, Terminal, MessageSquare, Settings } from 'lucide-react';
import { clsx } from 'clsx';

export default function Layout() {
    const navItems = [
        { to: "/", icon: LayoutDashboard, label: "Dashboard" },
        { to: "/virtualbox", icon: Server, label: "VirtualBox" },
        { to: "/sandbox", icon: Box, label: "Windows Sandbox" },
        { to: "/chat", icon: MessageSquare, label: "AI Chat" },
        { to: "/settings", icon: Settings, label: "Settings" },
    ];

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans selection:bg-primary/20">
            {/* Sidebar */}
            <aside className="w-64 border-r border-border bg-card/50 backdrop-blur-xl flex flex-col z-20">
                <div className="p-6 border-b border-border/50">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg border border-primary/20">
                            <Terminal className="w-6 h-6 text-primary" />
                        </div>
                        <div>
                            <h1 className="font-bold text-lg tracking-tight">Virtualization</h1>
                            <p className="text-xs text-muted-foreground font-mono">MCP SOTA v1.0</p>
                        </div>
                    </div>
                </div>

                <nav className="flex-1 p-4 space-y-2">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            className={({ isActive }) =>
                                clsx(
                                    "flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group",
                                    isActive
                                        ? "bg-primary/10 text-primary border border-primary/20 shadow-sm shadow-primary/5"
                                        : "text-muted-foreground hover:bg-white/5 hover:text-foreground hover:border hover:border-white/10"
                                )
                            }
                        >
                            <item.icon className={clsx("w-5 h-5 transition-colors", "group-hover:text-current")} />
                            <span className="font-medium">{item.label}</span>
                        </NavLink>
                    ))}
                </nav>

                <div className="p-4 border-t border-border/50">
                    <div className="p-4 rounded-xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-white/5">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                            <span className="text-xs font-medium text-green-500">System Online</span>
                        </div>
                        <p className="text-xs text-muted-foreground">Connected to Localhost</p>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto relative bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900/20 via-background to-background">
                <div className="absolute inset-0 bg-grid-white/[0.02]" />
                <div className="relative p-8 max-w-7xl mx-auto animate-in fade-in zoom-in-95 duration-500">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
