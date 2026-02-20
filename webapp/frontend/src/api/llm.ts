// API utilities for LLM provider interactions
import type { LLMProviderConfig, LLMModel } from '../types/llm';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:10761';

export async function fetchProviders(): Promise<LLMProviderConfig[]> {
  const response = await fetch(`${API_BASE}/api/llm/providers`);
  if (!response.ok) throw new Error('Failed to fetch providers');
  return response.json();
}

export async function saveProvider(provider: LLMProviderConfig): Promise<void> {
  const response = await fetch(`${API_BASE}/api/llm/providers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(provider),
  });
  if (!response.ok) throw new Error('Failed to save provider');
}

export async function deleteProvider(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/llm/providers/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete provider');
}

export async function testProvider(provider: LLMProviderConfig): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/api/llm/providers/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(provider),
  });
  if (!response.ok) throw new Error('Failed to test provider');
  return response.json();
}

export async function fetchModels(provider: LLMProviderConfig): Promise<LLMModel[]> {
  const response = await fetch(`${API_BASE}/api/llm/models`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(provider),
  });
  if (!response.ok) throw new Error('Failed to fetch models');
  return response.json();
}

// Direct provider API calls (client-side for local providers)
export async function fetchOllamaModels(baseUrl: string): Promise<LLMModel[]> {
  const response = await fetch(`${baseUrl}/api/tags`);
  if (!response.ok) throw new Error('Failed to fetch Ollama models');
  const data = await response.json();
  
  return data.models.map((model: any) => ({
    id: model.name || model.model,
    name: model.name || model.model,
    provider: 'ollama',
    contextLength: model.details?.context_length,
    capabilities: ['chat', 'completion'],
  }));
}

export async function fetchLMStudioModels(baseUrl: string): Promise<LLMModel[]> {
  const response = await fetch(`${baseUrl}/v1/models`);
  if (!response.ok) throw new Error('Failed to fetch LM Studio models');
  const data = await response.json();
  
  return data.data.map((model: any) => ({
    id: model.id,
    name: model.id,
    provider: 'lmstudio',
    contextLength: undefined,
    capabilities: ['chat', 'completion'],
  }));
}

export async function fetchOpenAIModels(apiKey: string): Promise<LLMModel[]> {
  const response = await fetch('https://api.openai.com/v1/models', {
    headers: { 'Authorization': `Bearer ${apiKey}` },
  });
  if (!response.ok) throw new Error('Failed to fetch OpenAI models');
  const data = await response.json();
  
  return data.data
    .filter((model: any) => model.id.includes('gpt'))
    .map((model: any) => ({
      id: model.id,
      name: model.id,
      provider: 'openai',
      contextLength: undefined,
      capabilities: ['chat', 'completion'],
    }));
}

// Chat API
export async function sendChatMessage(
  provider: LLMProviderConfig,
  model: string,
  messages: { role: string; content: string }[]
): Promise<{ content: string }> {
  const response = await fetch(`${API_BASE}/api/llm/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, model, messages }),
  });
  if (!response.ok) throw new Error('Failed to send message');
  return response.json();
}
