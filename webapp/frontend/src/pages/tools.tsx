import { useState, useEffect } from 'react';
import { Terminal, Search, Play, ChevronRight, Info, Loader2 } from 'lucide-react';
import { API_BASE } from '../api/config';

interface Tool {
    name: string;
    description: string;
    inputSchema: any;
}

export default function Tools() {
    const [tools, setTools] = useState<Tool[]>([]);
    const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [parameters, setParameters] = useState<Record<string, any>>({});
    const [executing, setExecuting] = useState(false);
    const [results, setResults] = useState<any>(null);

    useEffect(() => {
        const fetchTools = async () => {
            try {
                const response = await fetch(`${API_BASE}/mcp/tools`);
                const data = await response.json();
                const list = Array.isArray(data) ? data : (data.tools ?? []);
                setTools(list.map((t: string | { name: string; description?: string; inputSchema?: any }) =>
                    typeof t === "string" ? { name: t, description: "", inputSchema: {} } : t
                ));
            } catch (error) {
                console.error("Failed to fetch tools:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchTools();
    }, []);

    const handleRunTool = async () => {
        if (!selectedTool) return;
        setExecuting(true);
        setResults(null);
        try {
            const res = await fetch(`${API_BASE}/mcp/tools/call`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: selectedTool.name,
                    arguments: parameters
                })
            });
            const data = await res.json();
            setResults(data.result);
        } catch (error) {
            console.error("Tool execution failed:", error);
            setResults({ error: "Execution failed. Check backend logs." });
        } finally {
            setExecuting(false);
        }
    };

    const filteredTools = tools.filter(t => t.name.toLowerCase().includes(searchQuery.toLowerCase()));

    return (
        <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Tools Console</h2>
                    <p className="text-muted-foreground mt-1">Direct access to virtualization MCP capabilities</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 overflow-hidden">
                {/* Tool List */}
                <div className="lg:col-span-1 flex flex-col gap-4 overflow-hidden">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <input
                            type="text"
                            placeholder="Search tools..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full bg-card/40 border border-border rounded-lg pl-10 pr-4 py-2 focus:ring-1 focus:ring-primary outline-none"
                        />
                    </div>

                    <div className="flex-1 overflow-auto space-y-2 pr-2 custom-scrollbar">
                        {loading ? (
                            <div className="flex justify-center p-8"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
                        ) : filteredTools.map((tool) => (
                            <button
                                key={tool.name}
                                onClick={() => {
                                    setSelectedTool(tool);
                                    setParameters({});
                                    setResults(null);
                                }}
                                className={`w-full text-left p-4 rounded-xl border transition-all duration-200 group flex items-center justify-between ${selectedTool?.name === tool.name
                                    ? 'bg-primary/10 border-primary/30 text-primary'
                                    : 'bg-card/40 border-border hover:border-primary/20 text-muted-foreground hover:text-foreground'
                                    }`}
                            >
                                <div className="flex items-center gap-3">
                                    <div className={`p-2 rounded-lg ${selectedTool?.name === tool.name ? 'bg-primary/20' : 'bg-muted'}`}>
                                        <Terminal className="w-4 h-4" />
                                    </div>
                                    <span className="font-medium truncate">{tool.name}</span>
                                </div>
                                <ChevronRight className={`w-4 h-4 transition-transform ${selectedTool?.name === tool.name ? 'translate-x-1' : 'opacity-0'}`} />
                            </button>
                        ))}
                    </div>
                </div>

                {/* Tool Detail / Execution */}
                <div className="lg:col-span-2 rounded-xl border border-border bg-card/40 backdrop-blur-sm overflow-hidden flex flex-col">
                    {selectedTool ? (
                        <div className="flex flex-col h-full">
                            <div className="p-6 border-b border-border bg-white/5">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-2xl font-bold tracking-tight">{selectedTool.name}</h3>
                                    <button
                                        onClick={handleRunTool}
                                        disabled={executing}
                                        className="flex items-center gap-2 px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-all shadow-lg shadow-primary/20 disabled:opacity-50"
                                    >
                                        {executing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                                        Run Tool
                                    </button>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <Info className="w-4 h-4" />
                                    <span>{selectedTool.description}</span>
                                </div>
                            </div>

                            <div className="flex-1 p-6 overflow-auto space-y-6">
                                <div className="space-y-4">
                                    <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Parameters</h4>
                                    <div className="grid grid-cols-1 gap-4">
                                        {Object.entries(selectedTool.inputSchema?.properties || {}).map(([key, prop]: [string, any]) => (
                                            <div key={key} className="p-4 rounded-lg bg-black/20 border border-white/5 space-y-2">
                                                <div className="flex items-center justify-between">
                                                    <label className="text-sm font-medium">{key}</label>
                                                    {selectedTool.inputSchema?.required?.includes(key) && (
                                                        <span className="text-[10px] bg-primary/20 text-primary px-1.5 py-0.5 rounded uppercase">required</span>
                                                    )}
                                                </div>
                                                <input
                                                    type="text"
                                                    placeholder={prop.description || ""}
                                                    value={parameters[key] || ""}
                                                    onChange={(e) => setParameters(prev => ({ ...prev, [key]: e.target.value }))}
                                                    className="w-full bg-transparent border-b border-white/10 py-1 text-sm outline-none focus:border-primary transition-colors"
                                                />
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {results && (
                                    <div className="space-y-4">
                                        <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground text-primary">Execution Result</h4>
                                        <div className="p-4 rounded-lg bg-black/40 border border-primary/20 text-sm font-mono overflow-auto max-h-64 custom-scrollbar">
                                            <pre>{JSON.stringify(results, null, 2)}</pre>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground p-12 text-center">
                            <div className="p-6 rounded-full bg-muted/50 mb-6 border border-border/50">
                                <Terminal className="w-12 h-12" />
                            </div>
                            <h3 className="text-xl font-bold text-foreground">Select a Tool</h3>
                            <p className="mt-2 max-w-xs">Pick a virtualization primitive from the left to configure and execute its logic.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
