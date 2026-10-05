import { clsx } from "clsx";
import {
  Bot,
  Command,
  Download,
  Mic,
  Paperclip,
  Send,
  Sparkles,
  Trash2,
  User,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";
import { API_BASE } from "../api/config";

const HISTORY_KEY = "virtualization-mcp-chat-history";
const PERSONALITY_KEY = "virtualization-mcp-chat-personality";
const CUSTOM_KEY = "virtualization-mcp-chat-custom";
const SESSION_KEY = "virtualization-mcp-chat-session";
const HISTORY_CAP = 100;

interface TraceStep {
  tool: string;
  ok: boolean;
  summary: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  ts: string;
  trace?: TraceStep[];
}

interface Personality {
  id: string;
  label: string;
}

const PERSONALITIES: Personality[] = [
  { id: "professional", label: "Professional" },
  { id: "pirate", label: "Pirate Captain" },
  { id: "sarcastic", label: "Sarcastic" },
  { id: "mentor", label: "Mentor" },
  { id: "custom", label: "Custom" },
];

const EXAMPLE_PROMPTS: { group: string; prompts: string[] }[] = [
  {
    group: "Status",
    prompts: [
      "List all my VMs and their states",
      "Which VMs are running right now?",
      "Show host CPU, RAM and disk status",
      "What VirtualBox version is installed?",
    ],
  },
  {
    group: "Details",
    prompts: [
      "Is Windows Sandbox usable right now?",
      "What host-only networks exist?",
      "What virtual disks are attached?",
    ],
  },
];

const DEFAULT_GREETING =
  "Hello Sandra. I'm your virtualization assistant. I can help you manage your fleet, configure VMs, or analyze system logs. How can I assist you today?";

function loadHistory(): Message[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Message[];
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((m) => m && (m.role === "user" || m.role === "assistant"))
      .slice(-HISTORY_CAP);
  } catch {
    return [];
  }
}

function saveHistory(msgs: Message[]) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(msgs.slice(-HISTORY_CAP)));
  } catch {
    /* storage full or unavailable - chat still works in-memory */
  }
}

function getSessionId(): string {
  try {
    let sid = localStorage.getItem(SESSION_KEY);
    if (!sid) {
      sid = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
      localStorage.setItem(SESSION_KEY, sid);
    }
    return sid;
  } catch {
    return "default";
  }
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>(() => {
    const restored = loadHistory();
    if (restored.length > 0) return restored;
    return [
      {
        id: "greeting",
        role: "assistant",
        content: DEFAULT_GREETING,
        ts: new Date().toISOString(),
      },
    ];
  });
  const [input, setInput] = useState("");
  const [provider, setProvider] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);
  const [activeModel, setActiveModel] = useState<string | null>(null);
  const [refining, setRefining] = useState(false);
  const [sending, setSending] = useState(false);
  const [personality, setPersonality] = useState<string>(() => {
    try {
      return localStorage.getItem(PERSONALITY_KEY) || "professional";
    } catch {
      return "professional";
    }
  });
  const [customPrompt, setCustomPrompt] = useState<string>(() => {
    try {
      return localStorage.getItem(CUSTOM_KEY) || "";
    } catch {
      return "";
    }
  });
  const [skillName, setSkillName] = useState<string | null>(null);
  const [agentMode, setAgentMode] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/settings/llm`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.provider) {
          const mapping: Record<string, string> = {
            ollama: "Ollama",
            lm_studio: "LM Studio",
            openai: "OpenAI Compatible",
            deepseek: "DeepSeek",
            anthropic: "Anthropic Claude",
            gemini: "Google Gemini",
          };
          const provName = mapping[d.provider] || d.provider;
          const modelName = d.model ? ` (${d.model})` : "";
          setProvider(`${provName}${modelName}`);
          if (d.model) {
            setActiveModel(d.model);
          }
        } else {
          setProvider(null);
        }
      })
      .catch(() => setProvider(null))
      .finally(() => setChecking(false));
  }, []);

  // Skill-first preprompt discovery (fleet standard S1.2): load the primary
  // skill on mount for the controls-bar indicator. The backend composes the
  // same skill server-side, so this also verifies the contract is live.
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/skills`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        const skills = d?.skills as
          | { id?: string; name?: string }[]
          | undefined;
        const match = (skills || []).find(
          (s) =>
            s.id === "virtualization-expert" ||
            s.name === "virtualization-expert",
        );
        if (match) {
          setSkillName(`skill:${match.id || match.name}`);
        } else if ((skills || []).length > 0) {
          const first = skills![0];
          setSkillName(`skill:${first.id || first.name}`);
        } else {
          setSkillName("built-in default");
        }
      })
      .catch(() => setSkillName("built-in default"));
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(PERSONALITY_KEY, personality);
    } catch {
      /* ignore */
    }
  }, [personality]);

  useEffect(() => {
    try {
      localStorage.setItem(CUSTOM_KEY, customPrompt);
    } catch {
      /* ignore */
    }
  }, [customPrompt]);

  const pushMessages = (updater: (prev: Message[]) => Message[]) => {
    setMessages((prev) => {
      const next = updater(prev).slice(-HISTORY_CAP);
      saveHistory(next);
      return next;
    });
  };

  const handleRefine = async () => {
    if (!input.trim() || refining) return;
    setRefining(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/chat/refine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: input,
          model: activeModel || undefined,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.refined) {
          setInput(data.refined);
        }
      }
    } catch (error) {
      console.error("Refine error:", error);
    } finally {
      setRefining(false);
    }
  };

  const handleExport = () => {
    if (messages.length === 0) return;
    const lines = messages.map(
      (m) =>
        `[${m.ts}] ${m.role === "user" ? "User" : "Assistant"}: ${m.content}`,
    );
    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `virtualization-mcp-chat-${new Date().toISOString().replace(/[:.]/g, "-")}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleClear = () => {
    setMessages([]);
    try {
      localStorage.removeItem(HISTORY_KEY);
    } catch {
      /* ignore */
    }
  };

  const handleSend = async () => {
    if (!input.trim() || sending) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      ts: new Date().toISOString(),
    };

    pushMessages((prev) => [...prev, userMsg]);
    const currentInput = input;
    setInput("");
    setSending(true);

    try {
      if (agentMode) {
        const historyPayload = [...messages, userMsg].map((m) => ({
          role: m.role,
          content: m.content,
        }));
        const res = await fetch(`${API_BASE}/api/llm/chat-agent`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            model: activeModel || undefined,
            messages: historyPayload,
            personality:
              personality === "custom" ? "professional" : personality,
            custom_prompt: personality === "custom" ? customPrompt : "",
          }),
        });
        const data = await res.json();
        const assistantMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: data.reply || "I'm sorry, I couldn't process that.",
          ts: new Date().toISOString(),
          trace: Array.isArray(data.trace) ? data.trace : undefined,
        };
        pushMessages((prev) => [...prev, assistantMsg]);
      } else {
        const res = await fetch(`${API_BASE}/api/v1/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: currentInput,
            history: messages.map((m) => ({
              role: m.role,
              content: m.content,
            })),
            model: activeModel || undefined,
            personality:
              personality === "custom" ? "professional" : personality,
            custom_prompt: personality === "custom" ? customPrompt : "",
            session_id: getSessionId(),
          }),
        });
        const data = await res.json();

        const assistantMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: data.reply || "I'm sorry, I couldn't process that.",
          ts: new Date().toISOString(),
        };
        pushMessages((prev) => [...prev, assistantMsg]);
      }
    } catch (error) {
      console.error("Chat error:", error);
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "I'm having trouble connecting to my intelligence core. Is the backend running?",
        ts: new Date().toISOString(),
      };
      pushMessages((prev) => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div
      data-testid="chat-page"
      className="flex flex-col h-[calc(100vh-8rem)] md:h-[calc(100vh-4.5rem)] max-w-5xl mx-auto border border-border bg-card/40 backdrop-blur-xl rounded-2xl overflow-hidden shadow-2xl shadow-black/50"
    >
      {/* Chat Header */}
      <div className="p-6 border-b border-border bg-white/5 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-primary/10 rounded-xl border border-primary/20">
            <Sparkles className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h3 className="font-bold text-lg leading-tight">
              Fleet Intelligence
            </h3>
            <p className="text-xs text-muted-foreground flex items-center gap-1.5 mt-1">
              <span
                className={`w-1.5 h-1.5 rounded-full ${provider ? "bg-green-500" : "bg-red-500"}`}
              />
              {checking
                ? "Scanning..."
                : provider
                  ? provider
                  : "No LLM available"}
              {skillName && (
                <span className="ml-2 px-1.5 py-0.5 rounded bg-primary/10 border border-primary/20 text-primary">
                  {skillName}
                </span>
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            title="Open Command Center"
            aria-label="Commands"
            className="p-2 hover:bg-white/5 rounded-lg text-muted-foreground transition-colors"
          >
            <Command className="w-4 h-4" />
          </button>
          <button
            type="button"
            data-testid="chat-export"
            title="Export conversation (.txt)"
            aria-label="Export"
            onClick={handleExport}
            disabled={messages.length === 0}
            className="p-2 hover:bg-white/5 rounded-lg text-muted-foreground transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            type="button"
            data-testid="chat-clear"
            title="Clear conversation"
            aria-label="Clear"
            onClick={handleClear}
            disabled={messages.length === 0}
            className="p-2 hover:bg-white/5 rounded-lg text-muted-foreground transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Controls bar: personality + agent mode */}
      <div
        data-testid="chat-controls"
        className="px-6 py-3 border-b border-border bg-black/20 flex flex-wrap items-center gap-3 text-sm"
      >
        <label
          htmlFor="personality-select"
          className="text-xs text-muted-foreground uppercase tracking-widest font-medium"
        >
          Personality
        </label>
        <select
          id="personality-select"
          data-testid="personality-select"
          value={personality}
          onChange={(e) => setPersonality(e.target.value)}
          className="bg-zinc-800 text-zinc-100 border border-zinc-600 rounded-lg px-2 py-1 text-sm"
        >
          {PERSONALITIES.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
        {personality === "custom" && (
          <input
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            placeholder="Custom instructions..."
            className="flex-1 min-w-[12rem] bg-card/60 border border-white/10 rounded-lg px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-primary"
          />
        )}
        <label className="ml-auto flex items-center gap-2 text-xs text-muted-foreground uppercase tracking-widest font-medium cursor-pointer">
          <button
            type="button"
            role="switch"
            aria-checked={agentMode}
            aria-label="Agent mode"
            title="Agent mode: chat uses live estate tools (list VMs, inspect, snapshots)"
            onClick={() => setAgentMode((v) => !v)}
            className={clsx(
              "relative w-9 h-5 rounded-full transition-colors",
              agentMode ? "bg-primary" : "bg-zinc-700",
            )}
          >
            <span
              className={clsx(
                "absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all",
                agentMode ? "left-[1.125rem]" : "left-0.5",
              )}
            />
          </button>
          <Zap className="w-3.5 h-3.5" />
          Agent tools
        </label>
      </div>

      {/* Messages Area */}
      <div
        data-testid="chat-messages"
        className="flex-1 overflow-auto p-6 space-y-6 custom-scrollbar"
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
          >
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center border shadow-sm shrink-0 ${
                msg.role === "assistant"
                  ? "bg-primary/10 border-primary/20 text-primary"
                  : "bg-muted/50 border-border text-foreground"
              }`}
            >
              {msg.role === "assistant" ? (
                <Bot className="w-5 h-5" />
              ) : (
                <User className="w-5 h-5" />
              )}
            </div>
            <div
              className={`max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed ${
                msg.role === "assistant"
                  ? "bg-white/5 text-foreground rounded-tl-none"
                  : "bg-primary text-primary-foreground rounded-tr-none"
              }`}
            >
              {msg.trace && msg.trace.length > 0 && (
                <div data-testid="chat-tool-call" className="mb-2 space-y-1">
                  {msg.trace.map((t, i) => (
                    <div
                      key={i}
                      data-testid="chat-tool-call-status"
                      className="font-mono text-xs opacity-70"
                    >
                      [{t.ok ? "done" : "error"}] {t.tool}
                      {t.summary ? ` - ${t.summary}` : ""}
                    </div>
                  ))}
                </div>
              )}
              {msg.content}
              <div
                className={`text-xs mt-2 opacity-50 ${msg.role === "user" ? "text-right" : ""}`}
              >
                {new Date(msg.ts).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </div>
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex gap-4">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center border shadow-sm shrink-0 bg-primary/10 border-primary/20 text-primary">
              <Bot className="w-5 h-5 animate-pulse" />
            </div>
            <div className="max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed bg-white/5 text-foreground rounded-tl-none animate-pulse">
              Thinking...
            </div>
          </div>
        )}
      </div>

      {/* Example prompts */}
      {messages.length <= 1 && (
        <div data-testid="example-prompts" className="px-6 pb-2">
          {EXAMPLE_PROMPTS.map((g) => (
            <div key={g.group} className="mb-2">
              <div className="text-[11px] uppercase tracking-widest text-muted-foreground font-medium mb-1">
                {g.group}
              </div>
              <div className="flex flex-wrap gap-2">
                {g.prompts.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setInput(p)}
                    className="px-3 py-1.5 text-xs rounded-full border border-white/10 bg-white/5 hover:bg-white/10 hover:border-primary/40 transition-colors"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div className="p-6 border-t border-border bg-black/20">
        <div className="relative group">
          <textarea
            data-testid="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) =>
              e.key === "Enter" &&
              !e.shiftKey &&
              (e.preventDefault(), handleSend())
            }
            placeholder="Ask anything about your fleet..."
            className="w-full bg-card/60 border border-white/10 rounded-2xl p-4 pr-32 min-h-[100px] resize-none focus:ring-1 focus:ring-primary outline-none transition-all duration-300 group-hover:border-white/20"
          />
          <div className="absolute right-3 bottom-3 flex items-center gap-2">
            <button
              type="button"
              onClick={handleRefine}
              disabled={refining || !input.trim()}
              title="Refine Prompt (AI Optimization)"
              aria-label="Refine"
              className={clsx(
                "p-2 rounded-lg text-muted-foreground transition-colors hover:bg-white/5 hover:text-primary",
                refining ? "animate-pulse text-primary" : "",
                !input.trim() || refining
                  ? "opacity-40 cursor-not-allowed"
                  : "",
              )}
            >
              <Sparkles className="w-4 h-4" />
            </button>
            <button
              type="button"
              title="Attach File"
              aria-label="Attach"
              className="p-2 hover:bg-white/5 rounded-lg text-muted-foreground transition-colors"
            >
              <Paperclip className="w-4 h-4" />
            </button>
            <button
              type="button"
              title="Voice Input"
              aria-label="Mic"
              className="p-2 hover:bg-white/5 rounded-lg text-muted-foreground transition-colors"
            >
              <Mic className="w-4 h-4" />
            </button>
            <button
              type="button"
              data-testid="chat-send"
              onClick={handleSend}
              disabled={sending}
              title="Send Message"
              aria-label="Send"
              className="p-2 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-all shadow-lg shadow-primary/20 disabled:opacity-40"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
        <div className="mt-4 flex items-center justify-between px-2 text-xs text-muted-foreground font-medium uppercase tracking-widest">
          <span>Shift + Enter for newline</span>
          <span className="flex items-center gap-1">
            <Command className="w-3 h-3" /> J to open tools
          </span>
        </div>
      </div>
    </div>
  );
}
