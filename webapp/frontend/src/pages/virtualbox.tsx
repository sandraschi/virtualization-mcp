// React import removed for SOTA compliance (automatic runtime)
import { Play, Square, Pause, RotateCcw, Monitor } from 'lucide-react';

const mockVMs = [
    { id: '1', name: 'Ubuntu 24.04 Dev', state: 'Running', os: 'Linux', ram: '8192MB' },
    { id: '2', name: 'Windows 11 Test', state: 'PoweredOff', os: 'Windows', ram: '16384MB' },
    { id: '3', name: 'Kali Linux', state: 'Saved', os: 'Linux', ram: '4096MB' },
];

export default function VirtualBox() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">VirtualBox Manager</h2>
                    <p className="text-muted-foreground mt-1">Manage your local VirtualBox instances</p>
                </div>
                <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium">
                    Create New VM
                </button>
            </div>

            <div className="grid gap-4">
                {mockVMs.map((vm) => (
                    <div key={vm.id} className="p-6 rounded-xl border border-border bg-card/40 backdrop-blur-sm hover:border-primary/20 transition-all duration-300 group">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className={`p-3 rounded-lg ${vm.state === 'Running' ? 'bg-green-500/10 text-green-500' : 'bg-muted text-muted-foreground'}`}>
                                    <Monitor className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-lg flex items-center gap-2">
                                        {vm.name}
                                        <span className={`text-xs px-2 py-0.5 rounded-full border ${vm.state === 'Running'
                                            ? 'bg-green-500/10 text-green-500 border-green-500/20'
                                            : 'bg-muted/50 text-muted-foreground border-border'
                                            }`}>
                                            {vm.state}
                                        </span>
                                    </h3>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        {vm.os} • {vm.ram} RAM • 2 vCPUs
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button className="p-2 rounded-lg hover:bg-green-500/10 hover:text-green-500 transition-colors tooltip" title="Start">
                                    <Play className="w-5 h-5" />
                                </button>
                                <button className="p-2 rounded-lg hover:bg-yellow-500/10 hover:text-yellow-500 transition-colors" title="Pause">
                                    <Pause className="w-5 h-5" />
                                </button>
                                <button className="p-2 rounded-lg hover:bg-red-500/10 hover:text-red-500 transition-colors" title="Stop">
                                    <Square className="w-5 h-5" />
                                </button>
                                <div className="w-px h-6 bg-border mx-2" />
                                <button className="p-2 rounded-lg hover:bg-primary/10 hover:text-primary transition-colors" title="Snapshot">
                                    <RotateCcw className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
