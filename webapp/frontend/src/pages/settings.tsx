import { useState } from 'react';
import { Cpu, Globe, Lock, Bell, Database, Save, RotateCcw, Monitor } from 'lucide-react';

export default function Settings() {
    const [config, setConfig] = useState({
        ollamaEndpoint: 'http://localhost:11434',
        defaultModel: 'llama3:8b',
        gpuAcceleration: true,
        autoDiscovery: true,
        systemTheme: 'dark',
        port: 10760
    });

    const [saved, setSaved] = useState(false);

    const handleSave = () => {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8 pb-20">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">System Settings</h2>
                    <p className="text-muted-foreground mt-1">Configure your virtualization environment and LLM substrate</p>
                </div>
                <button
                    onClick={handleSave}
                    className={`flex items-center gap-2 px-6 py-2 rounded-lg font-bold transition-all ${saved ? 'bg-green-500 text-white' : 'bg-primary text-primary-foreground hover:bg-primary/90'
                        }`}
                >
                    {saved ? <Lock className="w-4 h-4" /> : <Save className="w-4 h-4" />}
                    {saved ? 'Settings Saved' : 'Save Changes'}
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Sidebar Navigation */}
                <div className="md:col-span-1 space-y-1">
                    {[
                        { label: 'General', icon: Globe },
                        { label: 'Local Intelligence', icon: Cpu },
                        { label: 'Notifications', icon: Bell },
                        { label: 'Security', icon: Lock },
                        { label: 'Database', icon: Database }
                    ].map((item) => (
                        <button
                            key={item.label}
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${item.label === 'Local Intelligence' ? 'bg-primary/10 text-primary border border-primary/20' : 'hover:bg-white/5 text-muted-foreground'
                                }`}
                        >
                            <item.icon className="w-5 h-5" />
                            <span className="font-medium">{item.label}</span>
                        </button>
                    ))}
                </div>

                {/* Content Area */}
                <div className="md:col-span-2 space-y-8">
                    {/* Local LLM Orchestration */}
                    <div className="p-6 rounded-2xl border border-border bg-card/40 backdrop-blur-sm space-y-6">
                        <div className="flex items-center gap-3 border-b border-border pb-4">
                            <Cpu className="w-5 h-5 text-primary" />
                            <h3 className="font-bold text-lg">Local Intelligence</h3>
                        </div>

                        <div className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-muted-foreground">Ollama Endpoint</label>
                                <input
                                    type="text"
                                    id="ollama-endpoint"
                                    title="Ollama API Endpoint"
                                    value={config.ollamaEndpoint}
                                    onChange={(e) => setConfig({ ...config, ollamaEndpoint: e.target.value })}
                                    className="w-full bg-black/20 border border-white/10 rounded-xl px-4 py-2 text-sm outline-none focus:border-primary transition-colors"
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium text-muted-foreground">Default Model</label>
                                <select
                                    id="default-model"
                                    title="Select Default LLM Model"
                                    value={config.defaultModel}
                                    onChange={(e) => setConfig({ ...config, defaultModel: e.target.value })}
                                    className="w-full bg-black/20 border border-white/10 rounded-xl px-4 py-2 text-sm outline-none focus:border-primary transition-colors appearance-none"
                                >
                                    <option value="llama3:8b">Llama 3 (8B)</option>
                                    <option value="gemma:7b">Gemma (7B)</option>
                                    <option value="mistral:latest">Mistral (Latest)</option>
                                </select>
                            </div>

                            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5">
                                <div className="space-y-0.5">
                                    <div className="text-sm font-bold uppercase tracking-wider">GPU Acceleration</div>
                                    <div className="text-xs text-muted-foreground">Utilize NVIDIA RTX 4090 for inference</div>
                                </div>
                                <div className={`w-12 h-6 rounded-full p-1 cursor-pointer transition-colors ${config.gpuAcceleration ? 'bg-primary' : 'bg-muted'}`}
                                    onClick={() => setConfig({ ...config, gpuAcceleration: !config.gpuAcceleration })}>
                                    <div className={`w-4 h-4 rounded-full bg-white transition-transform ${config.gpuAcceleration ? 'translate-x-6' : 'translate-x-0'}`} />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Hardware Status */}
                    <div className="p-6 rounded-2xl border border-border bg-card/40 backdrop-blur-sm space-y-4">
                        <div className="flex items-center gap-3 mb-2">
                            <Monitor className="w-5 h-5 text-primary" />
                            <h3 className="font-bold text-lg">Hardware Status</h3>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 rounded-xl bg-black/20 border border-white/5">
                                <div className="text-[10px] uppercase font-bold text-muted-foreground tracking-widest mb-1">Compute Substrate</div>
                                <div className="text-sm font-mono truncate">AMD Ryzen 9 5900X</div>
                            </div>
                            <div className="p-4 rounded-xl bg-black/20 border border-white/5">
                                <div className="text-[10px] uppercase font-bold text-muted-foreground tracking-widest mb-1">Graphics Substrate</div>
                                <div className="text-sm font-mono truncate text-green-500">NVIDIA RTX 4090</div>
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end gap-3 pt-4 border-t border-border">
                        <button className="flex items-center gap-2 px-4 py-2 rounded-lg text-muted-foreground hover:bg-white/5 transition-colors text-sm font-medium uppercase tracking-widest">
                            <RotateCcw className="w-4 h-4" />
                            Reset Defaults
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
