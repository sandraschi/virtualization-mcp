// React import removed for SOTA compliance (automatic runtime)
import { Activity, Cpu, HardDrive, MemoryStick } from 'lucide-react';

const stats = [
    { label: "Host CPU", value: "12%", icon: Cpu, color: "text-blue-500", bg: "bg-blue-500/10" },
    { label: "Host RAM", value: "32GB / 64GB", icon: MemoryStick, color: "text-purple-500", bg: "bg-purple-500/10" },
    { label: "Active VMs", value: "3 Running", icon: Activity, color: "text-green-500", bg: "bg-green-500/10" },
    { label: "Storage", value: "1.2TB Free", icon: HardDrive, color: "text-orange-500", bg: "bg-orange-500/10" },
];

export default function Dashboard() {
    return (
        <div className="space-y-8">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
                <p className="text-muted-foreground mt-1">Overview of your virtualization environment</p>
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
                <div className="p-6 rounded-xl border border-border bg-card/40 backdrop-blur-sm h-[400px]">
                    <h3 className="font-semibold mb-4 flex items-center gap-2">
                        <Activity className="w-4 h-4 text-primary" />
                        Recent Activity
                    </h3>
                    <div className="space-y-4">
                        {[1, 2, 3, 4].map((i) => (
                            <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                                <div className="flex items-center gap-3">
                                    <div className="w-2 h-2 rounded-full bg-green-500" />
                                    <div>
                                        <p className="text-sm font-medium">Ubuntu 22.04 LTS Started</p>
                                        <p className="text-xs text-muted-foreground">Just now</p>
                                    </div>
                                </div>
                                <span className="text-xs px-2 py-1 rounded-full bg-green-500/10 text-green-500 border border-green-500/20">Success</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="p-6 rounded-xl border border-border bg-card/40 backdrop-blur-sm h-[400px]">
                    <h3 className="font-semibold mb-4 flex items-center gap-2">
                        <Cpu className="w-4 h-4 text-primary" />
                        Resource Usage
                    </h3>
                    <div className="h-full flex items-center justify-center text-muted-foreground">
                        Chart Placeholder (Recharts implementation pending)
                    </div>
                </div>
            </div>
        </div>
    );
}
