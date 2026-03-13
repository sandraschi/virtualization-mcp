import { Book, HelpCircle, LifeBuoy, Shield, Zap, Terminal, Box, Server } from 'lucide-react';

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
        question: "What is the SOTA Port Registry?",
        answer: "SOTA (State of the Art) standards designate port 10760-10761 for Virtualization services. The Apps Hub uses these reserved ports to discover and link to other fleet components automatically.",
        icon: Terminal
    }
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
                <h2 className="text-5xl font-black tracking-tighter">How can we help?</h2>
                <p className="text-muted-foreground text-lg max-w-xl mx-auto">Explore documentation, system guides, and troubleshooting steps for your virtualization fleet.</p>
            </div>

            {/* Quick Links */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                    { label: "User Guide", icon: Book, color: "blue" },
                    { label: "API Reference", icon: Terminal, color: "emerald" },
                    { label: "Security Policy", icon: Shield, color: "purple" }
                ].map((item) => (
                    <button key={item.label} className="p-6 rounded-2xl border border-border bg-card/40 backdrop-blur-sm hover:border-primary/30 transition-all flex flex-col items-center gap-4 group">
                        <div className={`p-4 rounded-xl bg-${item.color}-500/10 text-${item.color}-500 group-hover:scale-110 transition-transform`}>
                            <item.icon className="w-8 h-8" />
                        </div>
                        <span className="font-bold">{item.label}</span>
                    </button>
                ))}
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
                    <p className="text-muted-foreground">Run the system diagnostic tool or contact the fleet administrator.</p>
                </div>
                <button className="px-8 py-3 bg-primary text-primary-foreground rounded-xl font-bold hover:bg-primary/90 transition-all shadow-xl shadow-primary/20 flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    Open Diagnostics
                </button>
            </div>
        </div>
    );
}
