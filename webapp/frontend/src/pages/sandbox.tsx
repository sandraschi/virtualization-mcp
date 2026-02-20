import { useState } from 'react';
import { Code, Download, Play, Save } from 'lucide-react';

export default function Sandbox() {
    const [config, setConfig] = useState({
        vGPU: true,
        networking: true,
        audioInput: false,
        videoInput: false,
        printerRedirection: false,
        clipboardRedirection: true,
        memoryInMB: 4096,
    });

    const getXmlPreview = () => `
<Configuration>
  <VGpu>${config.vGPU ? 'Default' : 'Disable'}</VGpu>
  <Networking>${config.networking ? 'Default' : 'Disable'}</Networking>
  <AudioInput>${config.audioInput ? 'Default' : 'Disable'}</AudioInput>
  <VideoInput>${config.videoInput ? 'Default' : 'Disable'}</VideoInput>
  <PrinterRedirection>${config.printerRedirection ? 'Default' : 'Disable'}</PrinterRedirection>
  <ClipboardRedirection>${config.clipboardRedirection ? 'Default' : 'Disable'}</ClipboardRedirection>
  <MemoryInMB>${config.memoryInMB}</MemoryInMB>
</Configuration>
  `.trim();

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-8rem)]">
            {/* Configuration Form */}
            <div className="space-y-6">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Windows Sandbox</h2>
                    <p className="text-muted-foreground mt-1">Configure and launch ephemeral Windows instances</p>
                </div>

                <div className="p-6 rounded-xl border border-border bg-card/40 backdrop-blur-sm space-y-6">
                    <div className="space-y-4">
                        <h3 className="font-semibold text-lg">Hardware</h3>
                        <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/5">
                            <div>
                                <span className="font-medium block">vGPU Support</span>
                                <span className="text-xs text-muted-foreground">Enable virtualized graphics</span>
                            </div>
                            <input
                                type="checkbox"
                                checked={config.vGPU}
                                onChange={(e) => setConfig({ ...config, vGPU: e.target.checked })}
                                className="w-5 h-5 rounded border-input bg-background/50 text-primary focus:ring-primary"
                            />
                        </div>

                        <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/5">
                            <div>
                                <span className="font-medium block">Memory (MB)</span>
                                <span className="text-xs text-muted-foreground">Allocated RAM</span>
                            </div>
                            <input
                                type="number"
                                value={config.memoryInMB}
                                onChange={(e) => setConfig({ ...config, memoryInMB: parseInt(e.target.value) })}
                                className="bg-transparent border border-input rounded px-2 py-1 w-24 text-right"
                            />
                        </div>
                    </div>

                    <div className="space-y-4">
                        <h3 className="font-semibold text-lg">Features</h3>
                        <div className="grid grid-cols-2 gap-4">
                            {[
                                { label: 'Networking', key: 'networking' },
                                { label: 'Audio Input', key: 'audioInput' },
                                { label: 'Video Input', key: 'videoInput' },
                                { label: 'Clipboard', key: 'clipboardRedirection' },
                            ].map((feature) => (
                                <button
                                    key={feature.key}
                                    onClick={() => setConfig({ ...config, [feature.key]: !config[feature.key as keyof typeof config] })}
                                    className={`p-4 rounded-lg border text-left transition-all ${config[feature.key as keyof typeof config]
                                        ? 'bg-primary/10 border-primary/20 text-primary'
                                        : 'bg-white/5 border-white/5 text-muted-foreground hover:bg-white/10'
                                        }`}
                                >
                                    <span className="font-medium text-sm">{feature.label}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="pt-4 flex gap-3">
                        <button className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium shadow-lg shadow-primary/20">
                            <Play className="w-5 h-5" />
                            Launch Sandbox
                        </button>
                        <button className="px-4 py-3 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-colors text-muted-foreground hover:text-foreground">
                            <Save className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Preview */}
            <div className="flex flex-col h-full rounded-xl border border-border bg-card/60 backdrop-blur-md overflow-hidden">
                <div className="p-4 border-b border-border bg-black/20 flex items-center justify-between">
                    <div className="flex items-center gap-2 text-muted-foreground">
                        <Code className="w-4 h-4" />
                        <span className="text-sm font-mono">config.wsb</span>
                    </div>
                    <button className="text-xs flex items-center gap-1 text-primary hover:underline">
                        <Download className="w-3 h-3" />
                        Download .wsb
                    </button>
                </div>
                <div className="flex-1 overflow-auto p-4 bg-black/40">
                    <pre className="font-mono text-sm text-green-400">
                        {getXmlPreview()}
                    </pre>
                </div>
            </div>
        </div>
    );
}
