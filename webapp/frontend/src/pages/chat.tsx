import { useState } from 'react';
import { Send, User, Bot, Sparkles, Command, Paperclip, Mic } from 'lucide-react';
import { API_BASE } from '../api/config';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

export default function Chat() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'assistant',
            content: "Hello Sandra. I'm your virtualization assistant. I can help you manage your fleet, configure VMs, or analyze system logs. How can I assist you today?",
            timestamp: new Date()
        }
    ]);
    const [input, setInput] = useState('');

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMsg]);
        const currentInput = input;
        setInput('');

        try {
            const res = await fetch(`${API_BASE}/api/v1/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: currentInput,
                    history: messages.map(m => ({ role: m.role, content: m.content }))
                })
            });
            const data = await res.json();

            const assistantMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: data.reply || "I'm sorry, I couldn't process that.",
                timestamp: new Date()
            };
            setMessages(prev => [...prev, assistantMsg]);
        } catch (error) {
            console.error("Chat error:", error);
            const errorMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: "I'm having trouble connecting to my intelligence core. Is the backend running?",
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMsg]);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)] max-w-5xl mx-auto border border-border bg-card/40 backdrop-blur-xl rounded-2xl overflow-hidden shadow-2xl shadow-black/50">
            {/* Chat Header */}
            <div className="p-6 border-b border-border bg-white/5 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-primary/10 rounded-xl border border-primary/20">
                        <Sparkles className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                        <h3 className="font-bold text-lg leading-tight">Fleet Intelligence</h3>
                        <p className="text-xs text-muted-foreground flex items-center gap-1.5 mt-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                            Local LLM Active (Ollama)
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        title="Open Command Center"
                        aria-label="Commands"
                        className="p-2 hover:bg-white/5 rounded-lg text-muted-foreground transition-colors"><Command className="w-4 h-4" /></button>
                </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-auto p-6 space-y-6 custom-scrollbar">
                {messages.map((msg) => (
                    <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center border shadow-sm shrink-0 ${msg.role === 'assistant'
                            ? 'bg-primary/10 border-primary/20 text-primary'
                            : 'bg-muted/50 border-border text-foreground'
                            }`}>
                            {msg.role === 'assistant' ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
                        </div>
                        <div className={`max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed ${msg.role === 'assistant'
                            ? 'bg-white/5 text-foreground rounded-tl-none'
                            : 'bg-primary text-primary-foreground rounded-tr-none'
                            }`}>
                            {msg.content}
                            <div className={`text-[10px] mt-2 opacity-50 ${msg.role === 'user' ? 'text-right' : ''}`}>
                                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Input Area */}
            <div className="p-6 border-t border-border bg-black/20">
                <div className="relative group">
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
                        placeholder="Ask anything about your fleet..."
                        className="w-full bg-card/60 border border-white/10 rounded-2xl p-4 pr-32 min-h-[100px] resize-none focus:ring-1 focus:ring-primary outline-none transition-all duration-300 group-hover:border-white/20"
                    />
                    <div className="absolute right-3 bottom-3 flex items-center gap-2">
                        <button title="Attach File" aria-label="Attach" className="p-2 hover:bg-white/5 rounded-lg text-muted-foreground transition-colors"><Paperclip className="w-4 h-4" /></button>
                        <button title="Voice Input" aria-label="Mic" className="p-2 hover:bg-white/5 rounded-lg text-muted-foreground transition-colors"><Mic className="w-4 h-4" /></button>
                        <button
                            onClick={handleSend}
                            title="Send Message"
                            aria-label="Send"
                            className="p-2 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-all shadow-lg shadow-primary/20"
                        >
                            <Send className="w-5 h-5" />
                        </button>
                    </div>
                </div>
                <div className="mt-4 flex items-center justify-between px-2 text-[10px] text-muted-foreground font-medium uppercase tracking-widest">
                    <span>Shift + Enter for newline</span>
                    <span className="flex items-center gap-1"><Command className="w-3 h-3" /> J to open tools</span>
                </div>
            </div>
        </div>
    );
}
