import { useEffect, useState } from 'react';
import { Play, Square, Pause, RotateCcw, Monitor, Loader2, RefreshCw, ExternalLink, Power, Plus, Disc } from 'lucide-react';
import { API_BASE } from '../api/config';

const VBOX_DOWNLOAD_URL = 'https://www.virtualbox.org/wiki/Downloads';
const VM_TEMPLATES = [
    { id: 'ubuntu-dev', label: 'Ubuntu (dev)' },
    { id: 'win11-pro', label: 'Win 11 Pro' },
    { id: 'windows-test', label: 'Windows (test)' },
    { id: 'test-template', label: 'Test template (Linux 64)' },
];

interface VM {
    uuid: string;
    name: string;
    state: string;
    os_type: string;
    memory_mb: number;
    cpus: number;
    provider?: 'virtualbox' | 'hyperv';
}

interface VBoxAsset {
    name: string;
    path: string;
}

export default function VirtualBox() {
    const [vms, setVms] = useState<VM[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionId, setActionId] = useState<string | null>(null);
    const [backendError, setBackendError] = useState<string | null>(null);
    const [vboxAvailable, setVboxAvailable] = useState<boolean | null>(null);
    const [launching, setLaunching] = useState(false);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [createName, setCreateName] = useState('');
    const [createTemplate, setCreateTemplate] = useState('ubuntu-dev');
    const [createIsoPath, setCreateIsoPath] = useState('');
    const [createSubmitting, setCreateSubmitting] = useState(false);
    const [vboxAssets, setVboxAssets] = useState<VBoxAsset[]>([]);
    const [showAttachModal, setShowAttachModal] = useState(false);
    const [attachVmName, setAttachVmName] = useState('');
    const [attachIsoPath, setAttachIsoPath] = useState('');
    const [attachSubmitting, setAttachSubmitting] = useState(false);

    const fetchVMs = async () => {
        setLoading(true);
        setBackendError(null);
        try {
            const res = await fetch(`${API_BASE}/api/v1/vms`);
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.status === 'success') {
                setVms(data.vms || []);
                setVboxAvailable(true);
            } else {
                setBackendError(data.detail || `Backend returned ${res.status}. Ensure backend is running (e.g. run webapp\\start.ps1).`);
                if (res.status === 503 || (data.detail && String(data.detail).includes('VM Service'))) {
                    setVboxAvailable(false);
                }
            }
        } catch (error) {
            setBackendError(`Cannot reach backend at ${API_BASE}. Run webapp\\start.ps1 to start backend.`);
            console.error("Failed to fetch VMs:", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchVboxStatus = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/vbox/status`);
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.available === false) setVboxAvailable(false);
        } catch {
            setVboxAvailable(null);
        }
    };

    useEffect(() => {
        fetchVMs();
        fetchVboxStatus();
        const interval = setInterval(fetchVMs, 10000);
        return () => clearInterval(interval);
    }, []);

    const handleOpenVirtualBox = async () => {
        setLaunching(true);
        try {
            const res = await fetch(`${API_BASE}/api/v1/vbox/launch`, { method: 'POST' });
            const data = await res.json().catch(() => ({}));
            if (data.success) {
                setTimeout(fetchVMs, 5000);
            } else {
                console.warn("VirtualBox launch:", data.message);
            }
        } finally {
            setLaunching(false);
        }
    };

    const handleAction = async (vmName: string, action: string, provider: string = 'virtualbox') => {
        setActionId(vmName + action);
        try {
            const res = await fetch(`${API_BASE}/api/v1/vms/${vmName}/${action}?provider=${provider}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: action === 'snapshot' ? JSON.stringify({ snapshot_name: `snap_${Date.now()}` }) : undefined
            });
            const data = await res.json();
            console.log(`Action ${action} on ${vmName} (${provider}) result:`, data);
            setTimeout(fetchVMs, 1500);
        } catch (error) {
            console.error(`Failed to execute ${action} on ${vmName}:`, error);
        } finally {
            setActionId(null);
        }
    };

    const fetchVboxAssets = () => {
        fetch(`${API_BASE}/api/v1/assets/vbox`)
            .then((r) => r.ok ? r.json() : { files: [] })
            .then((d) => setVboxAssets(d.files || []))
            .catch(() => setVboxAssets([]));
    };

    const openCreateModal = () => {
        setCreateName('');
        setCreateTemplate('ubuntu-dev');
        setCreateIsoPath('');
        setShowCreateModal(true);
        fetchVboxAssets();
    };

    const submitCreateVm = async () => {
        if (!createName.trim()) return;
        setCreateSubmitting(true);
        try {
            const res = await fetch(`${API_BASE}/api/v1/vms`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: createName.trim(),
                    template: createTemplate,
                    iso_path: createIsoPath || undefined,
                }),
            });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
            setShowCreateModal(false);
            setTimeout(fetchVMs, 1000);
        } catch (e: any) {
            console.error(e);
            setBackendError(e.message || 'Create VM failed');
        } finally {
            setCreateSubmitting(false);
        }
    };

    const openAttachModal = (vmName: string) => {
        setAttachVmName(vmName);
        setAttachIsoPath('');
        setShowAttachModal(true);
        fetchVboxAssets();
    };

    const submitAttachIso = async () => {
        if (!attachVmName || !attachIsoPath) return;
        setAttachSubmitting(true);
        try {
            const res = await fetch(`${API_BASE}/api/v1/vms/${attachVmName}/attach-iso`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ iso_path: attachIsoPath }),
            });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
            setShowAttachModal(false);
            setTimeout(fetchVMs, 500);
        } catch (e: any) {
            setBackendError(e.message || 'Attach ISO failed');
        } finally {
            setAttachSubmitting(false);
        }
    };

    const isVboxRequired = vboxAvailable === false || (backendError && (backendError.includes('VM Service') || backendError.includes('503')));
    const isConnectionError = backendError && !backendError.includes('503') && !backendError.includes('VM Service');

    return (
        <div className="space-y-6 pb-8">
            {isConnectionError && (
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                    {backendError}
                </div>
            )}
            {isVboxRequired && (
                <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-6 space-y-4">
                    <h3 className="font-semibold text-lg text-amber-200">VirtualBox is required</h3>
                    <p className="text-sm text-muted-foreground">
                        To list and manage VMs, snapshots, and networks, VirtualBox must be installed and <code className="text-amber-200/90">VBoxManage</code> must be in your PATH.
                        If you just installed VirtualBox, open it once below so the service can start; then refresh this page.
                    </p>
                    <div className="flex flex-wrap gap-3">
                        <button
                            type="button"
                            onClick={handleOpenVirtualBox}
                            disabled={launching}
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-200 hover:bg-amber-500/30 transition-colors font-medium disabled:opacity-50"
                        >
                            {launching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Power className="w-4 h-4" />}
                            Open VirtualBox
                        </button>
                        <a
                            href={VBOX_DOWNLOAD_URL}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-muted-foreground hover:bg-white/10 transition-colors font-medium"
                        >
                            <ExternalLink className="w-4 h-4" />
                            Download VirtualBox
                        </a>
                    </div>
                </div>
            )}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">VirtualBox Manager</h2>
                    <p className="text-muted-foreground mt-1">Manage your local VirtualBox instances</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={fetchVMs}
                        title="Refresh VM List"
                        aria-label="Refresh VMs"
                        className="p-2 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 text-muted-foreground"
                    >
                        <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                    <button onClick={openCreateModal} className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium">
                        <Plus className="w-4 h-4" />
                        Create New VM
                    </button>
                </div>
            </div>

            {loading && vms.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
                    <Loader2 className="w-10 h-10 animate-spin mb-4" />
                    <p>Scanning VirtualBox registry...</p>
                </div>
            ) : (
                <div className="grid gap-4">
                    {vms.map((vm) => (
                        <div key={vm.uuid || vm.name} className="p-6 rounded-xl border border-border bg-card/40 backdrop-blur-sm hover:border-primary/20 transition-all duration-300 group">
                            <div className="flex items-start justify-between">
                                <div className="flex items-start gap-4">
                                    <div className="relative">
                                        <div className={`p-3 rounded-lg ${vm.state === 'running' ? 'bg-green-500/10 text-green-500' : 'bg-muted text-muted-foreground'}`}>
                                            <Monitor className="w-6 h-6" />
                                        </div>
                                        {vm.state === 'running' && (
                                            <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 border-2 border-background rounded-full animate-pulse" />
                                        )}
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <h3 className="font-semibold text-lg">{vm.name}</h3>
                                            <span className={`text-[10px] px-2 py-0.5 rounded-full border uppercase font-bold tracking-wider ${vm.provider === 'hyperv'
                                                ? 'bg-blue-500/10 text-blue-500 border-blue-500/20'
                                                : 'bg-orange-500/10 text-orange-500 border-orange-500/20'
                                                }`}>
                                                {vm.provider || 'vbox'}
                                            </span>
                                            <span className={`text-xs px-2 py-0.5 rounded-full border ${vm.state === 'running'
                                                ? 'bg-green-500/10 text-green-500 border-green-500/20'
                                                : 'bg-muted/50 text-muted-foreground border-border'
                                                }`}>
                                                {vm.state}
                                            </span>
                                        </div>
                                        <p className="text-sm text-muted-foreground mt-1">
                                            {vm.os_type} • {vm.memory_mb}MB RAM • {vm.cpus} vCPUs
                                        </p>

                                        {vm.state === 'running' && (
                                            <div className="mt-4 rounded-lg overflow-hidden border border-border aspect-video bg-black/20 group-hover:border-primary/30 transition-colors">
                                                <img
                                                    src={`${API_BASE}/api/v1/vms/${vm.name}/screenshot?t=${Date.now()}`}
                                                    alt="VM Live View"
                                                    className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
                                                    onError={(e) => {
                                                        (e.target as HTMLImageElement).style.display = 'none';
                                                    }}
                                                />
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="flex flex-col items-end gap-4">
                                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button
                                            disabled={vm.state === 'running' || actionId === vm.name + 'start'}
                                            onClick={() => handleAction(vm.name, 'start', vm.provider)}
                                            className="p-2 rounded-lg hover:bg-green-500/10 hover:text-green-500 transition-colors disabled:opacity-30"
                                            title="Start"
                                        >
                                            {actionId === vm.name + 'start' ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                                        </button>
                                        <button
                                            disabled={vm.state !== 'running' || actionId === vm.name + 'pause'}
                                            onClick={() => handleAction(vm.name, 'pause', vm.provider)}
                                            className="p-2 rounded-lg hover:bg-yellow-500/10 hover:text-yellow-500 transition-colors disabled:opacity-30"
                                            title="Pause"
                                        >
                                            <Pause className="w-5 h-5" />
                                        </button>
                                        <button
                                            disabled={vm.state !== 'running' || actionId === vm.name + 'stop'}
                                            onClick={() => handleAction(vm.name, 'stop', vm.provider)}
                                            className="p-2 rounded-lg hover:bg-red-500/10 hover:text-red-500 transition-colors disabled:opacity-30"
                                            title="Stop"
                                        >
                                            <Square className="w-5 h-5" />
                                        </button>
                                        <div className="w-px h-6 bg-border mx-1" />
                                        <button
                                            onClick={() => handleAction(vm.name, 'snapshot', vm.provider)}
                                            className="p-2 rounded-lg hover:bg-primary/10 hover:text-primary transition-colors"
                                            title="Take Snapshot"
                                        >
                                            <RotateCcw className="w-5 h-5" />
                                        </button>
                                    </div>
                                    {vm.provider === 'virtualbox' && (
                                        <button onClick={() => openAttachModal(vm.name)} className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-primary transition-colors" title="Attach ISO from repo assets">
                                            <Disc className="w-3 h-3" />
                                            Attach ISO
                                        </button>
                                    )}
                                    <button className="text-xs text-muted-foreground hover:text-primary transition-colors">
                                        Advanced Settings →
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                    {vms.length === 0 && !loading && (
                        <div className="text-center py-12 border border-dashed border-border rounded-xl">
                            <p className="text-muted-foreground">No VirtualBox VMs detected.</p>
                        </div>
                    )}
                </div>
            )}

            {showCreateModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => !createSubmitting && setShowCreateModal(false)}>
                    <div className="bg-card border border-border rounded-xl shadow-xl max-w-md w-full p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
                        <h3 className="font-semibold text-lg">Create New VM</h3>
                        <p className="text-sm text-muted-foreground">Uses repo <code className="text-foreground/80">assets/vbox</code> for optional ISO.</p>
                        <div>
                            <label className="block text-sm font-medium mb-1">Name</label>
                            <input type="text" value={createName} onChange={(e) => setCreateName(e.target.value)} placeholder="my-vm" className="w-full bg-background/50 border border-input rounded px-3 py-2" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Template</label>
                            <select value={createTemplate} onChange={(e) => setCreateTemplate(e.target.value)} className="w-full bg-background/50 border border-input rounded px-3 py-2">
                                {VM_TEMPLATES.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">ISO (optional, from repo assets/vbox)</label>
                            <select value={createIsoPath} onChange={(e) => setCreateIsoPath(e.target.value)} className="w-full bg-background/50 border border-input rounded px-3 py-2">
                                <option value="">— None —</option>
                                {vboxAssets.map((f) => <option key={f.path} value={f.path}>{f.name}</option>)}
                            </select>
                        </div>
                        <div className="flex gap-2 pt-2">
                            <button type="button" onClick={() => setShowCreateModal(false)} disabled={createSubmitting} className="flex-1 py-2 rounded-lg border border-border hover:bg-white/10">Cancel</button>
                            <button type="button" onClick={submitCreateVm} disabled={createSubmitting || !createName.trim()} className="flex-1 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
                                {createSubmitting ? <Loader2 className="w-4 h-4 animate-spin inline" /> : null} Create
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {showAttachModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => !attachSubmitting && setShowAttachModal(false)}>
                    <div className="bg-card border border-border rounded-xl shadow-xl max-w-md w-full p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
                        <h3 className="font-semibold text-lg">Attach ISO to {attachVmName}</h3>
                        <p className="text-sm text-muted-foreground">Choose from repo <code className="text-foreground/80">assets/vbox</code>.</p>
                        <div>
                            <label className="block text-sm font-medium mb-1">ISO file</label>
                            <select value={attachIsoPath} onChange={(e) => setAttachIsoPath(e.target.value)} className="w-full bg-background/50 border border-input rounded px-3 py-2">
                                <option value="">— Select —</option>
                                {vboxAssets.map((f) => <option key={f.path} value={f.path}>{f.name}</option>)}
                            </select>
                            {vboxAssets.length === 0 && <p className="text-xs text-muted-foreground mt-1">Put .iso files in repo assets/vbox folder.</p>}
                        </div>
                        <div className="flex gap-2 pt-2">
                            <button type="button" onClick={() => setShowAttachModal(false)} disabled={attachSubmitting} className="flex-1 py-2 rounded-lg border border-border hover:bg-white/10">Cancel</button>
                            <button type="button" onClick={submitAttachIso} disabled={attachSubmitting || !attachIsoPath} className="flex-1 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
                                {attachSubmitting ? <Loader2 className="w-4 h-4 animate-spin inline" /> : null} Attach
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
