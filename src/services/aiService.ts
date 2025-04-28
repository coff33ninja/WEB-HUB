export interface AIModel {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'loading';
  description?: string;
  parameters?: Record<string, unknown>;
}

export interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
  timestamp?: number;
}

export interface AIResponse {
  message: Message;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

export interface AIProvider {
  id: string;
  name: string;
  listModels(): Promise<AIModel[]>;
  generateResponse(model: string, messages: Message[], options?: Record<string, unknown>): Promise<AIResponse>;
}

// Base Provider class for common functionality
abstract class BaseProvider implements AIProvider {
  id: string;
  name: string;
  baseUrl: string;

  constructor(id: string, name: string, baseUrl: string) {
    this.id = id;
    this.name = name;
    this.baseUrl = baseUrl;
  }

  async listModels(): Promise<AIModel[]> {
    try {
      console.log(`Fetching models from ${this.baseUrl}/models`);
      const response = await fetch(`${this.baseUrl}/models`);
      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.status} ${response.statusText}`);
      }
      const data = await response.json();

      // Helper function to validate status
      function validateStatus(status: unknown): 'active' | 'inactive' | 'loading' {
        const validStatuses = ['active', 'inactive', 'loading'];
        if (typeof status === 'string' && validStatuses.includes(status)) {
          return status as 'active' | 'inactive' | 'loading';
        }
        return 'active';
      }

      const models: AIModel[] = (data as unknown[]).map((model: unknown) => {
        if (typeof model === 'object' && model !== null) {
          const m = model as Record<string, unknown>;
          return {
            id: typeof m.id === 'string' ? m.id : (typeof m.name === 'string' ? m.name : ''),
            name: typeof m.name === 'string' ? m.name : (typeof m.id === 'string' ? m.id : ''),
            status: validateStatus(m.status),
            description: typeof m.description === 'string' ? m.description : '',
          };
        }
        return {
          id: '',
          name: '',
          status: 'active' as 'active' | 'inactive' | 'loading',
          description: '',
        };
      });
      console.log(`Fetched models for ${this.name}:`, models);
      return models;
    } catch (error: unknown) {
      let errorMessage = 'An unknown error occurred.';
      if (error instanceof Error) {
        errorMessage = error.message.includes('NetworkError')
          ? `Network error fetching models from ${this.name}. Check if the backend is running and CORS is configured for ${this.baseUrl}.`
          : error.message;
      }
      console.error(`${this.name} error fetching models:`, error);
      throw new Error(errorMessage);
    }
  }

  async generateResponse(model: string, messages: Message[], options: Record<string, unknown> = {}): Promise<AIResponse> {
    if (!model) throw new Error('Model is required');
    if (!messages || messages.length === 0) throw new Error('At least one message is required');

    try {
      console.log(`Validating model: ${model} for ${this.name}`);
      const body = { model, messages, ...options };
      console.log(`Sending request to ${this.baseUrl}/generate:`, body);
      const response = await fetch(`${this.baseUrl}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to generate response: ${response.status} ${response.statusText} - ${errorText}`);
      }
      const data = await response.json();
      if (!data.message?.content) {
        throw new Error('Invalid response: No content received');
      }
      return {
        message: {
          role: 'assistant',
          content: data.message.content,
          timestamp: Date.now(),
        },
        usage: data.usage || {},
      };
    } catch (error: unknown) {
      const errorMessage = (error as Error).message.includes('NetworkError')
        ? `Network error generating response from ${this.name}. Check if the backend is running and CORS is configured for ${this.baseUrl}.`
        : (error as Error).message;
      console.error(`${this.name} error generating response:`, error);
      throw new Error(errorMessage);
    }
  }
}

// Ollama Provider
class OllamaProvider extends BaseProvider {
  constructor(baseUrl: string = 'http://localhost:5000/api/providers/ollama') {
    super('ollama', 'Ollama AI', baseUrl);
  }
}

// LM Studio Provider
class LMStudioProvider extends BaseProvider {
  constructor(baseUrl: string = 'http://localhost:5000/api/providers/lmstudio') {
    super('lmstudio', 'LM Studio', baseUrl);
  }
}

// Llama.cpp Provider
class LlamaCppProvider extends BaseProvider {
  constructor(baseUrl: string = 'http://localhost:5000/api/providers/llamacpp') {
    super('llamacpp', 'Llama.cpp', baseUrl);
  }
}

// Mock Provider
class MockProvider implements AIProvider {
  id = 'mock';
  name = 'Mock AI';

  async listModels(): Promise<AIModel[]> {
    console.log('Returning mock models');
    const models: AIModel[] = [
      { id: 'mock-model-1', name: 'Mock Model 1', status: 'active', description: 'Mock model for testing' },
      { id: 'mock-model-2', name: 'Mock Model 2', status: 'active', description: 'Mock model for testing' },
    ];
    console.log('Fetched models for Mock AI:', models);
    return models;
  }

  async generateResponse(model: string, messages: Message[], options: Record<string, unknown> = {}): Promise<AIResponse> {
    if (!model) throw new Error('Model is required');
    if (!messages || messages.length === 0) throw new Error('At least one message is required');

    console.log('Generating mock response for model:', model, 'messages:', messages);
    const lastMessage = messages[messages.length - 1];
    const responseContent = `Mock response to "${lastMessage.content}" from model ${model}`;
    return {
      message: {
        role: 'assistant',
        content: responseContent,
        timestamp: Date.now(),
      },
      usage: {
        promptTokens: 0,
        completionTokens: 0,
        totalTokens: 0,
      },
    };
  }
}

// Available providers
const providers: AIProvider[] = [
  new OllamaProvider(),
  new LMStudioProvider(),
  new LlamaCppProvider(),
  new MockProvider(),
];

  // Selected provider id (default to Ollama since it's confirmed working)
  let selectedProviderId = 'ollama';

  // Functions to interact with providers
  export function setActiveProvider(providerId: string) {
    if (!providers.find(p => p.id === providerId)) {
      throw new Error(`AI provider ${providerId} not found`);
    }
    console.log(`Setting active provider: ${providerId}`);
    selectedProviderId = providerId;
  }

  function getActiveProvider(): AIProvider {
    const provider = providers.find(p => p.id === selectedProviderId);
    if (!provider) {
      throw new Error(`AI provider ${selectedProviderId} not found`);
    }
    return provider;
  }

  export async function listLocalModels(): Promise<AIModel[]> {
    console.log(`Listing models for provider: ${selectedProviderId}`);
    return getActiveProvider().listModels();
  }

  export async function generateAIResponse(
    model: string,
    messages: Message[],
    options: Record<string, unknown> = {}
  ): Promise<AIResponse> {
    console.log(`Generating response with model: ${model}`);
    return getActiveProvider().generateResponse(model, messages, options);
  }

  export function getAvailableProviders(): AIProvider[] {
    console.log('Returning available providers:', providers.map(p => p.id));
    return providers;
  }
