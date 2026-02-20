import React, { useState, useEffect, useCallback } from 'react';
import { 
  Settings, 
  Plus, 
  Trash2, 
  TestTube, 
  Check, 
  X, 
  Server, 
  Key,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  AlertCircle,
  Cpu,
  Cloud,
  Bot,
  Sparkles
} from 'lucide-react';
import { clsx } from 'clsx';
import type { LLMProviderConfig, LLMModel, LLMProviderType } from '../types/llm';
import { DEFAULT_PROVIDERS } from '../types/llm';
import {
  fetchOllamaModels,
  fetchLMStudioModels,
  fetchOpenAIModels,
  testProvider as testProviderApi,
} from '../api/llm';

const PROVIDER_ICONS: Record<LLMProviderType, React.ReactNode> = {
  ollama: <Cpu className="w-5 h-5" />,
  lmstudio: <Bot className="w-5 h-5" />,
  openai: <Cloud className="w-5 h-5" />,
  anthropic: <Sparkles className="w-5 h-5" />,
};

const PROVIDER_COLORS: Record<LLMProviderType, string> = {
  ollama: 'text-blue-500 bg-blue-500/10 border-blue-500/20',
  lmstudio: 'text-green-500 bg-green-500/10 border-green-500/20',
  openai: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20',
  anthropic: 'text-orange-500 bg-orange-500/10 border-orange-500/20',
};

export default function SettingsPage() {
  const [providers, setProviders] = useState<LLMProviderConfig[]>([]);
  const [expandedProvider, setExpandedProvider] = useState<string | null>(null);
  const [models, setModels] = useState<Record<string, LLMModel[]>>({});
  const [loadingModels, setLoadingModels] = useState<Record<string, boolean>>({});
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({});
  const [hasChanges, setHasChanges] = useState(false);

  // Load providers from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('llm-providers');
    if (saved) {
      try {
        setProviders(JSON.parse(saved));
      } catch {
        setProviders(DEFAULT_PROVIDERS);
      }
    } else {
      setProviders(DEFAULT_PROVIDERS);
    }
  }, []);

  // Save providers when they change
  useEffect(() => {
    if (providers.length > 0) {
      localStorage.setItem('llm-providers', JSON.stringify(providers));
      setHasChanges(true);
    }
  }, [providers]);

  const updateProvider = (id: string, updates: Partial<LLMProviderConfig>) => {
    setProviders(prev => prev.map(p => p.id === id ? { ...p, ...updates } : p));
  };

  const addProvider = () => {
    const newProvider: LLMProviderConfig = {
      id: `custom-${Date.now()}`,
      name: 'New Provider',
      type: 'ollama',
      baseUrl: 'http://localhost:11434',
      enabled: false,
    };
    setProviders(prev => [...prev, newProvider]);
    setExpandedProvider(newProvider.id);
  };

  const deleteProvider = (id: string) => {
    setProviders(prev => prev.filter(p => p.id !== id));
    setExpandedProvider(null);
  };

  const loadModels = useCallback(async (provider: LLMProviderConfig) => {
    if (loadingModels[provider.id]) return;
    
    setLoadingModels(prev => ({ ...prev, [provider.id]: true }));
    try {
      let fetchedModels: LLMModel[] = [];
      
      switch (provider.type) {
        case 'ollama':
          fetchedModels = await fetchOllamaModels(provider.baseUrl);
          break;
        case 'lmstudio':
          fetchedModels = await fetchLMStudioModels(provider.baseUrl);
          break;
        case 'openai':
          if (provider.apiKey) {
            fetchedModels = await fetchOpenAIModels(provider.apiKey);
          }
          break;
        default:
          fetchedModels = [];
      }
      
      setModels(prev => ({ ...prev, [provider.id]: fetchedModels }));
    } catch (error) {
      console.error('Failed to load models:', error);
      setModels(prev => ({ ...prev, [provider.id]: [] }));
    } finally {
      setLoadingModels(prev => ({ ...prev, [provider.id]: false }));
    }
  }, [loadingModels]);

  const testProvider = async (provider: LLMProviderConfig) => {
    setTestingProvider(provider.id);
    try {
      // First try to fetch models as a connectivity test
      await loadModels(provider);
      
      // Then do a deeper test via backend
      const result = await testProviderApi(provider);
      setTestResults(prev => ({ ...prev, [provider.id]: result }));
      
      // Auto-expand on successful test to show models
      if (result.success) {
        setExpandedProvider(provider.id);
      }
    } catch (error) {
      setTestResults(prev => ({ 
        ...prev, 
        [provider.id]: { 
          success: false, 
          message: error instanceof Error ? error.message : 'Connection failed' 
        } 
      }));
    } finally {
      setTestingProvider(null);
    }
  };

  const toggleProvider = (id: string) => {
    const provider = providers.find(p => p.id === id);
    if (provider) {
      updateProvider(id, { enabled: !provider.enabled });
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Settings className="w-8 h-8 text-primary" />
            Settings
          </h2>
          <p className="text-muted-foreground mt-1">
            Configure LLM providers and application preferences
          </p>
        </div>
        {hasChanges && (
          <div className="flex items-center gap-2 text-sm text-yellow-500">
            <AlertCircle className="w-4 h-4" />
            Unsaved changes
          </div>
        )}
      </div>

      {/* LLM Providers Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-semibold flex items-center gap-2">
            <Server className="w-5 h-5 text-primary" />
            LLM Providers
          </h3>
          <button
            onClick={addProvider}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Provider
          </button>
        </div>

        <p className="text-sm text-muted-foreground">
          Configure AI providers for chat and assistance. Local providers (Ollama, LM Studio) run on your machine. 
          Cloud providers (OpenAI, Anthropic) require API keys.
        </p>

        {/* Provider Cards */}
        <div className="space-y-3">
          {providers.map((provider) => (
            <div
              key={provider.id}
              className={clsx(
                "rounded-xl border transition-all duration-200 overflow-hidden",
                provider.enabled 
                  ? "border-primary/30 bg-primary/5" 
                  : "border-border bg-card/40"
              )}
            >
              {/* Provider Header */}
              <div 
                className="flex items-center gap-4 p-4 cursor-pointer hover:bg-white/5 transition-colors"
                onClick={() => setExpandedProvider(expandedProvider === provider.id ? null : provider.id)}
              >
                <div className={clsx("p-2 rounded-lg border", PROVIDER_COLORS[provider.type])}>
                  {PROVIDER_ICONS[provider.type]}
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold">{provider.name}</h4>
                    {provider.enabled && (
                      <span className="px-2 py-0.5 text-xs rounded-full bg-green-500/10 text-green-500 border border-green-500/20">
                        Active
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">{provider.baseUrl}</p>
                </div>

                {/* Toggle */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleProvider(provider.id);
                  }}
                  className={clsx(
                    "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                    provider.enabled
                      ? "bg-green-500/10 text-green-500 border border-green-500/20"
                      : "bg-white/5 text-muted-foreground border border-white/10 hover:bg-white/10"
                  )}
                >
                  {provider.enabled ? 'Enabled' : 'Disabled'}
                </button>

                {/* Expand/Collapse */}
                <button className="p-2 rounded-lg hover:bg-white/10 transition-colors">
                  {expandedProvider === provider.id ? (
                    <ChevronUp className="w-5 h-5 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-muted-foreground" />
                  )}
                </button>
              </div>

              {/* Expanded Configuration */}
              {expandedProvider === provider.id && (
                <div className="px-4 pb-4 space-y-4 border-t border-border/50 pt-4">
                  {/* Name */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Name</label>
                      <input
                        type="text"
                        value={provider.name}
                        onChange={(e) => updateProvider(provider.id, { name: e.target.value })}
                        className="w-full px-3 py-2 rounded-lg bg-background border border-border focus:border-primary focus:outline-none"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Type</label>
                      <select
                        value={provider.type}
                        onChange={(e) => updateProvider(provider.id, { type: e.target.value as LLMProviderType })}
                        className="w-full px-3 py-2 rounded-lg bg-background border border-border focus:border-primary focus:outline-none"
                      >
                        <option value="ollama">Ollama</option>
                        <option value="lmstudio">LM Studio</option>
                        <option value="openai">OpenAI</option>
                        <option value="anthropic">Anthropic</option>
                      </select>
                    </div>
                  </div>

                  {/* Base URL */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Base URL</label>
                    <input
                      type="text"
                      value={provider.baseUrl}
                      onChange={(e) => updateProvider(provider.id, { baseUrl: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-background border border-border focus:border-primary focus:outline-none"
                      placeholder="http://localhost:11434"
                    />
                  </div>

                  {/* API Key (for cloud providers) */}
                  {(provider.type === 'openai' || provider.type === 'anthropic') && (
                    <div className="space-y-2">
                      <label className="text-sm font-medium flex items-center gap-2">
                        <Key className="w-4 h-4" />
                        API Key
                      </label>
                      <input
                        type="password"
                        value={provider.apiKey || ''}
                        onChange={(e) => updateProvider(provider.id, { apiKey: e.target.value })}
                        className="w-full px-3 py-2 rounded-lg bg-background border border-border focus:border-primary focus:outline-none"
                        placeholder="sk-..."
                      />
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-2">
                    <button
                      onClick={() => testProvider(provider)}
                      disabled={testingProvider === provider.id}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 transition-colors disabled:opacity-50"
                    >
                      {testingProvider === provider.id ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <TestTube className="w-4 h-4" />
                      )}
                      Test Connection
                    </button>

                    {/* Test Result */}
                    {testResults[provider.id] && (
                      <div className={clsx(
                        "flex items-center gap-2 px-3 py-2 rounded-lg text-sm",
                        testResults[provider.id].success
                          ? "bg-green-500/10 text-green-500 border border-green-500/20"
                          : "bg-red-500/10 text-red-500 border border-red-500/20"
                      )}>
                        {testResults[provider.id].success ? (
                          <Check className="w-4 h-4" />
                        ) : (
                          <X className="w-4 h-4" />
                        )}
                        {testResults[provider.id].message}
                      </div>
                    )}

                    <div className="flex-1" />

                    <button
                      onClick={() => deleteProvider(provider.id)}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500/20 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </div>

                  {/* Models List */}
                  {models[provider.id] && models[provider.id].length > 0 && (
                    <div className="mt-4 p-4 rounded-lg bg-background/50 border border-border">
                      <h5 className="text-sm font-medium mb-3 flex items-center gap-2">
                        <Bot className="w-4 h-4" />
                        Available Models ({models[provider.id].length})
                      </h5>
                      <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
                        {models[provider.id].map((model) => (
                          <div
                            key={model.id}
                            onClick={() => updateProvider(provider.id, { defaultModel: model.id })}
                            className={clsx(
                              "p-2 rounded-lg text-sm cursor-pointer transition-colors flex items-center justify-between",
                              provider.defaultModel === model.id
                                ? "bg-primary/20 border border-primary/30"
                                : "bg-white/5 hover:bg-white/10 border border-transparent"
                            )}
                          >
                            <span className="truncate">{model.name}</span>
                            {provider.defaultModel === model.id && (
                              <Check className="w-4 h-4 text-primary flex-shrink-0" />
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {loadingModels[provider.id] && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Loading models...
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {providers.length === 0 && (
          <div className="p-8 rounded-xl border border-border bg-card/40 text-center">
            <Server className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h4 className="font-semibold mb-2">No Providers Configured</h4>
            <p className="text-sm text-muted-foreground mb-4">
              Add an LLM provider to enable AI chat and assistance features.
            </p>
            <button
              onClick={addProvider}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 transition-colors mx-auto"
            >
              <Plus className="w-4 h-4" />
              Add Provider
            </button>
          </div>
        )}
      </div>

      {/* Application Preferences */}
      <div className="space-y-4">
        <h3 className="text-xl font-semibold">Application Preferences</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl border border-border bg-card/40">
            <h4 className="font-medium mb-2">Auto-Discovery</h4>
            <p className="text-sm text-muted-foreground mb-3">
              Automatically detect local LLM providers on startup
            </p>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" defaultChecked className="rounded border-border" />
              <span className="text-sm">Enable auto-discovery</span>
            </label>
          </div>

          <div className="p-4 rounded-xl border border-border bg-card/40">
            <h4 className="font-medium mb-2">Default Model</h4>
            <p className="text-sm text-muted-foreground mb-3">
              Select the default model for new conversations
            </p>
            <select className="w-full px-3 py-2 rounded-lg bg-background border border-border text-sm">
              <option>Auto-select from first available provider</option>
              {providers.filter(p => p.enabled && p.defaultModel).map(p => (
                <option key={p.id} value={p.defaultModel}>{p.name} - {p.defaultModel}</option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
