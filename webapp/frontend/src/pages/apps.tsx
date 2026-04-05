import { useEffect, useState } from 'react';
import { Share2, ExternalLink, Zap, Activity, Book, Cpu, Home, Globe, MessageSquare, Terminal } from 'lucide-react';
import { API_BASE } from '../api/config';

interface FleetApp {
    id: string;
    label: string;
    port: number;
    tags: string[];
    description?: string;
    status?: string;
}

const getIconForApp = (app: FleetApp) => {
    const tags = app.tags || [];
    if (tags.includes('ai') || tags.includes('llm')) return MessageSquare;
    if (tags.includes('smart-home')) return Home;
    if (tags.includes('books')) return Book;
    if (tags.includes('media') || tags.includes('vj')) return Activity;
    if (tags.includes('infra') || tags.includes('development')) return Cpu;
    if (tags.includes('transit')) return Globe;
    if (tags.includes('terminal')) return Terminal;
    return Zap;
};

export default function Apps() {
    const [apps, setApps] = useState<FleetApp[]>([]);
    const [loading, setLoading] = useState(true);
    const [backendError, setBackendError] = useState<string | null>(null);

    useEffect(() => {
        const fetchApps = async () => {
            setBackendError(null);
            try {
                const res = await fetch(`${API_BASE}/api/v1/apps`);
                const data = await res.json().catch(() => ({}));
                if (res.ok && data.webapps) {
                    setApps(data.webapps.map((app: any) => ({
                        ...app,
                        description: app.description || `${app.label} service running on port ${app.port}`,
                        status: 'Active'
                    })));
                } else if (!res.ok) {
                    setBackendError(data.detail || `Backend returned ${res.status}. Run webapp\\start.ps1 to start backend.`);
                }
            } catch (error) {
                setBackendError(`Cannot reach backend at ${API_BASE}. Run webapp\\start.ps1 to start backend.`);
                console.error("Failed to fetch fleet apps:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchApps();
    }, []);

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {backendError && (
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                    {backendError}
                </div>
            )}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">Apps Hub</h2>
                    <p className="text-muted-foreground mt-1 text-lg">Real-time Fleet Discovery & Navigation ({apps.length} Apps)</p>
                </div>
                <div className="p-3 bg-white/5 border border-white/10 rounded-full">
                    <Share2 className="w-5 h-5 text-muted-foreground" />
                </div>
            </div>

            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="h-64 rounded-2xl border border-border bg-card/20 animate-pulse" />
                    ))}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {apps.map((app) => {
                        const Icon = getIconForApp(app);
                        return (
                            <a
                                key={app.id || app.label}
                                href={`http://localhost:${app.port}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="group relative p-8 rounded-2xl border border-border bg-card/40 backdrop-blur-md hover:border-primary/40 hover:bg-white/5 transition-all duration-500 overflow-hidden"
                            >
                                <div className="absolute top-6 right-6 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/40 border border-white/5">
                                    <div className={`w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse`} />
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-white/70">Active</span>
                                </div>

                                <div className={`w-14 h-14 rounded-2xl mb-6 flex items-center justify-center bg-blue-500/10 border border-blue-500/20 group-hover:scale-110 group-hover:rotate-3 transition-transform duration-500`}>
                                    <Icon className={`w-7 h-7 text-blue-500`} />
                                </div>

                                <div className="space-y-2">
                                    <h3 className="text-xl font-bold flex items-center gap-2 group-hover:text-primary transition-colors">
                                        {app.label}
                                        <ExternalLink className="w-4 h-4 opacity-0 group-hover:opacity-100 -translate-y-1 translate-x-1 transition-all" />
                                    </h3>
                                    <p className="text-muted-foreground text-sm leading-relaxed line-clamp-2">
                                        {app.description}
                                    </p>
                                </div>

                                <div className="mt-8 pt-6 border-t border-white/5 flex items-center justify-between">
                                    <span className="text-xs font-mono text-muted-foreground tracking-widest uppercase">Port {app.port}</span>
                                    <span className="text-xs font-medium text-primary uppercase tracking-tighter group-hover:tracking-widest transition-all">Launch &rarr;</span>
                                </div>

                                <div className={`absolute -bottom-12 -right-12 w-32 h-32 bg-blue-500/5 blur-3xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-700`} />
                            </a>
                        );
                    })}
                </div>
            )}

            <div className="p-8 rounded-3xl border border-dashed border-border bg-black/20 flex flex-col items-center justify-center text-center space-y-4">
                <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                    <Share2 className="w-6 h-6 text-muted-foreground" />
                </div>
                <div>
                    <h4 className="font-bold text-lg">Add New Webapp</h4>
                    <p className="text-sm text-muted-foreground max-w-sm mt-1">Register a new MCP server webapp to the central fleet discovery registry.</p>
                </div>
                <button className="px-6 py-2 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-colors font-medium">
                    Configure Registry
                </button>
            </div>
        </div>
    );
}

