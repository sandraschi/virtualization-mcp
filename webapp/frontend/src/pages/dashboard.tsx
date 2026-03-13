import { useEffect, useState } from 'react';
import { Activity, Cpu, HardDrive, MemoryStick } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { API_BASE } from '../api/config';

interface HostInfo {
    cpu_usage_percent: number;
    memory_used_gb: number;
    memory_total_gb: number;
    disk_free_gb: number;
    disk_total_gb: number;
}

interface VM {
    name: string;
    state: string;
}

export default function Dashboard() {
    const [hostInfo, setHostInfo] = useState<HostInfo | null>(null);
    const [vms, setVms] = useState<VM[]>([]);
    const [history, setHistory] = useState<any[]>([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [infoRes, vmsRes] = await Promise.all([
                    fetch(`${API_BASE}/api/v1/host/info`),
                    fetch(`${API_BASE}/api/v1/vms`)
                ]);

                const infoData = await infoRes.json();
                const vmsData = await vmsRes.json();

                setHostInfo({
                    cpu_usage_percent: infoData.cpu_usage || 0,
                    memory_used_gb: ((infoData.memory_total - infoData.memory_available) / (1024 ** 3)) || 0,
                    memory_total_gb: (infoData.memory_total / (1024 ** 3)) || 0,
                    disk_free_gb: (infoData.disk_usage?.free / (1024 ** 3)) || 0,
                    disk_total_gb: (infoData.disk_usage?.total / (1024 ** 3)) || 0,
                });

                if (vmsData.status === 'success') {
                    setVms(vmsData.vms || []);
                }

                // Append to history for charts
                setHistory(prev => {
                    const newEntry = {
                        time: new Date().toLocaleTimeString(),
                        cpu: infoData.cpu_usage || 0,
                        memory: (((infoData.memory_total - infoData.memory_available) / infoData.memory_total) * 100) || 0,
                    };
                    const updated = [...prev, newEntry].slice(-20);
                    return updated;
                });
            } catch (error) {
                console.error("Failed to fetch dashboard data:", error);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    const stats = [
        {
            label: "Host CPU",
            value: hostInfo ? `${hostInfo.cpu_usage_percent.toFixed(1)}%` : "Loading...",
            icon: Cpu,
            color: "text-blue-500",
            bg: "bg-blue-500/10"
        },
        {
            label: "Host RAM",
            value: hostInfo ? `${hostInfo.memory_used_gb.toFixed(1)}GB / ${hostInfo.memory_total_gb.toFixed(0)}GB` : "Loading...",
            icon: MemoryStick,
            color: "text-purple-500",
            bg: "bg-purple-500/10"
        },
        {
            label: "Active VMs",
            value: vms.length > 0 ? `${vms.filter(v => v.state === 'running').length} Running` : "0 Running",
            icon: Activity,
            color: "text-green-500",
            bg: "bg-green-500/10"
        },
        {
            label: "Storage Free",
            value: hostInfo ? `${hostInfo.disk_free_gb.toFixed(0)}GB Free` : "Loading...",
            icon: HardDrive,
            color: "text-orange-500",
            bg: "bg-orange-500/10"
        },
    ];

    return (
        <div className="space-y-8 pb-8">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
                <p className="text-muted-foreground mt-1">Real-time overview of your virtualization environment</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.map((stat) => (
                    <div key={stat.label} className="p-6 rounded-xl border border-border bg-card/40 backdrop-blur-sm hover:border-primary/20 transition-all duration-300">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
                                <p className="text-2xl font-bold mt-2">{stat.value}</p>
                            </div>
                            <div className={`p-3 rounded-full ${stat.bg}`}>
                                <stat.icon className={`w-6 h-6 ${stat.color}`} />
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="p-6 rounded-xl border border-border bg-card/40 backdrop-blur-sm">
                    <h3 className="font-semibold mb-6 flex items-center gap-2">
                        <Activity className="w-4 h-4 text-primary" />
                        System Resources (Last 2 Minutes)
                    </h3>
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={history}>
                                <defs>
                                    <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="colorMem" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                                <XAxis dataKey="time" hide />
                                <YAxis stroke="#666" fontSize={12} unit="%" />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333', borderRadius: '8px' }}
                                    itemStyle={{ fontSize: '12px' }}
                                />
                                <Area type="monotone" dataKey="cpu" stroke="#3b82f6" fillOpacity={1} fill="url(#colorCpu)" name="CPU Usage" />
                                <Area type="monotone" dataKey="memory" stroke="#a855f7" fillOpacity={1} fill="url(#colorMem)" name="Memory Usage" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="p-6 rounded-xl border border-border bg-card/40 backdrop-blur-sm">
                    <h3 className="font-semibold mb-6 flex items-center gap-2">
                        <HardDrive className="w-4 h-4 text-primary" />
                        Storage Distribution
                    </h3>
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={[
                                { name: 'Free', value: hostInfo?.disk_free_gb || 0 },
                                { name: 'Used', value: (hostInfo?.disk_total_gb || 0) - (hostInfo?.disk_free_gb || 0) }
                            ]}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                                <XAxis dataKey="name" stroke="#666" />
                                <YAxis stroke="#666" fontSize={12} unit="GB" />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333', borderRadius: '8px' }}
                                />
                                <Bar dataKey="value" fill="#f97316" radius={[4, 4, 0, 0]} name="Capacity" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
}
