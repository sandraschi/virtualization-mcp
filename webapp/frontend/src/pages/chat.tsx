import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Trash2, 
  RefreshCw,
  AlertCircle,
  Cpu,
  Cloud,
  Sparkles,
  Settings,
  Plus
} from 'lucide-react';
import { clsx } from 'clsx';
import type { LLMProviderConfig, LLMModel } from '../types/llm';
import { sendChatMessage, fetchOllamaModels, fetchLMStudioModels, fetchOpenAIModels } from '../api/llm';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  model?: string;
  provider?: string;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
}

const PROVIDER_ICONS: Record<string, React.ReactNode> = {
  ollama: <Cpu className="w-4 h-4" />,
  lmstudio: <Bot className="w-4 h-4" />,
  openai: <Cloud className="w-4 h-4" />,
  anthropic: <Sparkles className="w-4 h-4" />,
};

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [providers, setProviders] = useState<LLMProviderConfig[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [availableModels, setAvailableModels] = useState<LLMModel[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load providers from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('llm-providers');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setProviders(parsed);
        const enabled = parsed.filter((p: LLMProviderConfig) => p.enabled);
        if (enabled.length > 0 && !selectedProvider) {
          setSelectedProvider(enabled[0].id);
          if (enabled[0].defaultModel) {
            setSelectedModel(enabled[0].defaultModel);
          }
        }
      } catch {
        console.error('Failed to parse providers');
      }
    }
  }, []);

  // Load available models when provider changes
  useEffect(() => {
    if (!selectedProvider) return;
    
    const provider = providers.find(p => p.id === selectedProvider);
    if (!provider) return;

    const loadModels = async () => {
      setLoadingModels(true);
      setError(null);
      try {
        let models: LLMModel[] = [];
        switch (provider.type) {
          case 'ollama':
            models = await fetchOllamaModels(provider.baseUrl);
            break;
          case 'lmstudio':
            models = await fetchLMStudioModels(provider.baseUrl);
            break;
          case 'openai':
            if (provider.apiKey) {
              models = await fetchOpenAIModels(provider.apiKey);
            }
            break;
        }
        setAvailableModels(models);
        
        // Auto-select first model if none selected
        if (models.length > 0 && !selectedModel) {
          setSelectedModel(models[0].id);
        }
      } catch (err) {
        setError(`Failed to load models from ${provider.name}: ${err instanceof Error ? err.message : 'Unknown error'}`);
        setAvailableModels([]);
      } finally {
        setLoadingModels(false);
      }
    };

    loadModels();
  }, [selectedProvider, providers]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversations, currentConversationId]);

  const currentConversation = conversations.find(c => c.id === currentConversationId);

  const createNewConversation = () => {
    const newConv: Conversation = {
      id: `conv-${Date.now()}`,
      title: 'New Conversation',
      messages: [],
      createdAt: new Date(),
    };
    setConversations(prev => [newConv, ...prev]);
    setCurrentConversationId(newConv.id);
  };

  const deleteConversation = (id: string) => {
    setConversations(prev => prev.filter(c => c.id !== id));
    if (currentConversationId === id) {
      setCurrentConversationId(null);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;
    if (!selectedProvider || !selectedModel) {
      setError('Please select a provider and model first');
      return;
    }

    const provider = providers.find(p => p.id === selectedProvider);
    if (!provider) {
      setError('Selected provider not found');
      return;
    }

    // Create conversation if none exists
    if (!currentConversationId) {
      createNewConversation();
    }

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    // Add user message
    setConversations(prev => {
      const conv = prev.find(c => c.id === currentConversationId);
      if (conv) {
        const updated = { ...conv, messages: [...conv.messages, userMessage] };
        if (conv.messages.length === 0) {
          updated.title = input.trim().slice(0, 50) + (input.trim().length > 50 ? '...' : '');
        }
        return prev.map(c => c.id === currentConversationId ? updated : c);
      }
      return prev;
    });

    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const messages = currentConversation?.messages.map(m => ({
        role: m.role,
        content: m.content,
      })) || [];
      
      messages.push({ role: 'user', content: userMessage.content });

      const response = await sendChatMessage(provider, selectedModel, messages);

      const assistantMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: response.content,
        timestamp: new Date(),
        model: selectedModel,
        provider: provider.name,
      };

      setConversations(prev => prev.map(c => 
        c.id === currentConversationId 
          ? { ...c, messages: [...c.messages, assistantMessage] }
          : c
      ));
    } catch (err) {
      setError(`Failed to get response: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const enabledProviders = providers.filter(p => p.enabled);

  return (
    <div className="flex h-[calc(100vh-4rem)] -m-8">
      {/* Sidebar - Conversation List */}
      <div className="w-64 border-r border-border bg-card/50 flex flex-col">
        <div className="p-4 border-b border-border/50">
          <button
            onClick={createNewConversation}
            className="flex items-center gap-2 w-full px-4 py-2 rounded-lg bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.map(conv => (
            <div
              key={conv.id}
              onClick={() => setCurrentConversationId(conv.id)}
              className={clsx(
                "group flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-all",
                currentConversationId === conv.id
                  ? "bg-primary/10 border border-primary/20"
                  : "hover:bg-white/5 border border-transparent"
              )}
            >
              <Bot className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{conv.title}</p>
                <p className="text-xs text-muted-foreground">
                  {conv.messages.length} messages
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteConversation(conv.id);
                }}
                className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-500/10 hover:text-red-500 transition-all"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}

          {conversations.length === 0 && (
            <div className="p-4 text-center text-sm text-muted-foreground">
              No conversations yet. Start a new chat!
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header - Model Selection */}
        <div className="flex items-center gap-4 p-4 border-b border-border/50 bg-card/50">
          {enabledProviders.length === 0 ? (
            <div className="flex items-center gap-2 text-yellow-500 text-sm">
              <AlertCircle className="w-4 h-4" />
              No LLM providers configured. 
              <a href="/settings" className="underline">Configure in Settings</a>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Provider:</span>
                <select
                  value={selectedProvider}
                  onChange={(e) => {
                    setSelectedProvider(e.target.value);
                    setSelectedModel('');
                  }}
                  className="px-3 py-1.5 rounded-lg bg-background border border-border text-sm focus:border-primary focus:outline-none"
                >
                  {enabledProviders.map(p => (
                    <option key={p.id} value={p.id}>
                      {PROVIDER_ICONS[p.type]} {p.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Model:</span>
                <div className="relative">
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    disabled={loadingModels || availableModels.length === 0}
                    className="px-3 py-1.5 rounded-lg bg-background border border-border text-sm focus:border-primary focus:outline-none disabled:opacity-50 min-w-[200px]"
                  >
                    {loadingModels ? (
                      <option>Loading models...</option>
                    ) : availableModels.length === 0 ? (
                      <option>No models available</option>
                    ) : (
                      availableModels.map(m => (
                        <option key={m.id} value={m.id}>{m.name}</option>
                      ))
                    )}
                  </select>
                  {loadingModels && (
                    <RefreshCw className="absolute right-8 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-muted-foreground" />
                  )}
                </div>
              </div>
            </>
          )}

          <div className="flex-1" />

          <a
            href="/settings"
            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
          >
            <Settings className="w-5 h-5 text-muted-foreground" />
          </a>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="flex items-center gap-2 px-4 py-2 bg-red-500/10 border-b border-red-500/20 text-red-500 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
            <button 
              onClick={() => setError(null)}
              className="ml-auto hover:underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {!currentConversation || currentConversation.messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-4">
              <div className="p-4 rounded-full bg-primary/10 border border-primary/20">
                <Bot className="w-12 h-12 text-primary" />
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Start a Conversation</h3>
                <p className="text-muted-foreground max-w-md">
                  Ask questions about virtualization, get help with VM configuration, 
                  or discuss best practices for managing your virtual machines.
                </p>
              </div>
              {enabledProviders.length === 0 && (
                <a
                  href="/settings"
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  Configure LLM Provider
                </a>
              )}
            </div>
          ) : (
            <>
              {currentConversation.messages.map((message) => (
                <div
                  key={message.id}
                  className={clsx(
                    "flex gap-4",
                    message.role === 'user' ? "flex-row-reverse" : ""
                  )}
                >
                  <div className={clsx(
                    "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                    message.role === 'user' 
                      ? "bg-primary/10 text-primary" 
                      : "bg-secondary text-secondary-foreground"
                  )}>
                    {message.role === 'user' ? (
                      <User className="w-5 h-5" />
                    ) : (
                      <Bot className="w-5 h-5" />
                    )}
                  </div>
                  <div className={clsx(
                    "max-w-[70%] space-y-1",
                    message.role === 'user' ? "items-end" : ""
                  )}>
                    <div className={clsx(
                      "p-4 rounded-2xl",
                      message.role === 'user'
                        ? "bg-primary text-primary-foreground rounded-tr-sm"
                        : "bg-card border border-border rounded-tl-sm"
                    )}>
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{message.timestamp.toLocaleTimeString()}</span>
                      {message.model && (
                        <>
                          <span>·</span>
                          <span>{message.model}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </>
          )}

          {isLoading && (
            <div className="flex gap-4">
              <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
                <Bot className="w-5 h-5" />
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <RefreshCw className="w-4 h-4 animate-spin" />
                Thinking...
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-border/50 bg-card/50">
          <div className="flex items-end gap-2 max-w-4xl mx-auto">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={enabledProviders.length === 0 
                ? "Configure an LLM provider in Settings to start chatting..."
                : "Type your message... (Enter to send, Shift+Enter for new line)"
              }
              disabled={isLoading || enabledProviders.length === 0}
              className="flex-1 min-h-[60px] max-h-[200px] px-4 py-3 rounded-xl bg-background border border-border focus:border-primary focus:outline-none resize-none disabled:opacity-50"
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading || enabledProviders.length === 0}
              className="p-3 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          <p className="text-xs text-muted-foreground text-center mt-2">
            Responses are generated by AI and may contain inaccuracies. Always verify important information.
          </p>
        </div>
      </div>
    </div>
  );
}
