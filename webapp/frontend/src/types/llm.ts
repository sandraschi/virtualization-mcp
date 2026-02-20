// LLM Provider types and configuration

export type LLMProviderType = 'ollama' | 'lmstudio' | 'openai' | 'anthropic';

export interface LLMProviderConfig {
  id: string;
  name: string;
  type: LLMProviderType;
  baseUrl: string;
  apiKey?: string;
  enabled: boolean;
  defaultModel?: string;
}

export interface LLMModel {
  id: string;
  name: string;
  provider: string;
  contextLength?: number;
  capabilities: string[];
}

export const DEFAULT_PROVIDERS: LLMProviderConfig[] = [
  {
    id: 'ollama-local',
    name: 'Ollama (Local)',
    type: 'ollama',
    baseUrl: 'http://localhost:11434',
    enabled: true,
  },
  {
    id: 'lmstudio-local',
    name: 'LM Studio (Local)',
    type: 'lmstudio',
    baseUrl: 'http://localhost:1234',
    enabled: false,
  },
  {
    id: 'openai',
    name: 'OpenAI',
    type: 'openai',
    baseUrl: 'https://api.openai.com/v1',
    apiKey: '',
    enabled: false,
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    type: 'anthropic',
    baseUrl: 'https://api.anthropic.com',
    apiKey: '',
    enabled: false,
  },
];
