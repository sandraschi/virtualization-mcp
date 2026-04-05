import { Book, HelpCircle, LifeBuoy, Shield, Zap, Terminal, Box, Server, Container } from 'lucide-react';

const faqItems = [
    {
        question: "How do I launch a Windows Sandbox?",
        answer: "Navigate to the 'Windows Sandbox' page, configure your XML parameters (mapped folders, startup scripts), and click 'Launch Sandbox'. The backend generates a temporary .wsb file and executes it via the system shell.",
        icon: Box
    },
    {
        question: "Can I manage headless VirtualBox VMs?",
        answer: "Yes. The VirtualBox Manager interface detects all registered VMs. Clicking 'Start' will initiate the VM in the mode configured in your VirtualBox global settings (usually GUI or Headless).",
        icon: Server
    },
    {
        question: "Why are there reserved ports in this app?",
        answer: "The app uses reserved local ports so the dashboard, API, and MCP server can find each other reliably without manual wiring.",
        icon: Terminal
    }
];

const containerTech = [
    {
        name: "Docker",
        summary: "Most common container runtime for app packaging.",
        bestFor: "Developer workflows, local testing, CI builds.",
        notes: "Great tooling and ecosystem. Use when you need fast, repeatable app environments.",
    },
    {
        name: "Podman",
        summary: "Daemonless Docker-compatible container engine.",
        bestFor: "Security-focused hosts, rootless container usage.",
        notes: "Strong drop-in option where Docker CLI compatibility matters but daemonless operation is preferred.",
    },
    {
        name: "containerd",
        summary: "Core container runtime used under orchestration platforms.",
        bestFor: "Platform teams and orchestrated workloads.",
        notes: "Lower-level than Docker. Usually consumed via Kubernetes or managed stacks.",
    },
    {
        name: "Kubernetes",
        summary: "Cluster orchestration for containerized services.",
        bestFor: "Production-scale deployments with self-healing and rolling updates.",
        notes: "Powerful but complex. Best when you need scaling, scheduling, and policy controls.",
    },
    {
        name: "LXC/LXD",
        summary: "System containers that feel closer to lightweight VMs.",
        bestFor: "OS-level isolation with low overhead.",
        notes: "Useful when you need full user-space behavior without running full virtual machines.",
    },
    {
        name: "Windows Containers",
        summary: "Container support for Windows-native workloads.",
        bestFor: ".NET/Windows service packaging on Windows hosts.",
        notes: "Use process or Hyper-V isolation based on compatibility and security requirements.",
    },
];

export default function Help() {
    return (
        <div className="max-w-4xl mx-auto space-y-12 pb-20">
            {/* Hero Section */}
            <div className="text-center space-y-4">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-widest">
                    <LifeBuoy className="w-3 h-3" />
                    Support Center
                </div>
                <h2 className="text-5xl font-black tracking-tighter">Need help fast?</h2>
                <p className="text-muted-foreground text-lg max-w-xl mx-auto">
                    Start here for plain-language setup steps, troubleshooting, and clear guidance for VM and container workflows.
                </p>
            </div>

            {/* Quick Links */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                    { label: "User Guide", icon: Book, iconClass: "text-blue-500", bgClass: "bg-blue-500/10" },
                    { label: "API Reference", icon: Terminal, iconClass: "text-emerald-500", bgClass: "bg-emerald-500/10" },
                    { label: "Security Policy", icon: Shield, iconClass: "text-purple-500", bgClass: "bg-purple-500/10" }
                ].map((item) => (
                    <button key={item.label} className="p-6 rounded-2xl border border-border bg-card/40 backdrop-blur-sm hover:border-primary/30 transition-all flex flex-col items-center gap-4 group">
                        <div className={`p-4 rounded-xl ${item.bgClass} ${item.iconClass} group-hover:scale-110 transition-transform`}>
                            <item.icon className="w-8 h-8" />
                        </div>
                        <span className="font-bold">{item.label}</span>
                    </button>
                ))}
            </div>

            <div className="space-y-6">
                <div className="flex items-center gap-3 mb-2">
                    <Container className="w-6 h-6 text-primary" />
                    <h3 className="text-2xl font-bold tracking-tight">Container Technologies at a Glance</h3>
                </div>
                <p className="text-muted-foreground">
                    This section compares common container technologies in simple terms so teams can pick the right fit quickly.
                </p>
                <div className="grid gap-4">
                    {containerTech.map((tech) => (
                        <div key={tech.name} className="p-5 rounded-2xl border border-border bg-card/40">
                            <div className="flex items-center justify-between gap-4">
                                <h4 className="font-bold text-lg">{tech.name}</h4>
                                <span className="text-xs px-2 py-1 rounded-full border border-primary/30 text-primary">Container Tech</span>
                            </div>
                            <p className="text-sm text-muted-foreground mt-2">{tech.summary}</p>
                            <p className="text-sm mt-3"><span className="font-semibold">Best for:</span> {tech.bestFor}</p>
                            <p className="text-sm text-muted-foreground mt-1">{tech.notes}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* FAQs */}
            <div className="space-y-6">
                <div className="flex items-center gap-3 mb-8">
                    <HelpCircle className="w-6 h-6 text-primary" />
                    <h3 className="text-2xl font-bold tracking-tight">Common Questions</h3>
                </div>
                <div className="grid gap-4">
                    {faqItems.map((item, idx) => (
                        <div key={idx} className="p-6 rounded-2xl border border-border bg-card/40 hover:bg-white/5 transition-colors group">
                            <div className="flex items-start gap-4">
                                <div className="p-2 rounded-lg bg-muted text-muted-foreground group-hover:text-foreground transition-colors">
                                    <item.icon className="w-5 h-5" />
                                </div>
                                <div className="space-y-2">
                                    <h4 className="font-bold text-lg">{item.question}</h4>
                                    <p className="text-muted-foreground text-sm leading-relaxed">{item.answer}</p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Troubleshooting CTA */}
            <div className="p-10 rounded-3xl bg-gradient-to-br from-primary/20 via-primary/5 to-transparent border border-primary/20 flex flex-col md:flex-row items-center justify-between gap-8">
                <div className="space-y-2 text-center md:text-left">
                    <h4 className="text-2xl font-bold">Still stuck?</h4>
                    <p className="text-muted-foreground">Run diagnostics first, then share results with your platform admin if needed.</p>
                </div>
                <button className="px-8 py-3 bg-primary text-primary-foreground rounded-xl font-bold hover:bg-primary/90 transition-all shadow-xl shadow-primary/20 flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    Open Diagnostics
                </button>
            </div>
        </div>
    );
}
