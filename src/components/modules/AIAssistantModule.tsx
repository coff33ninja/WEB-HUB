import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Bot, Send } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { ScrollArea } from '../ui/scroll-area';
import {
  AIModel,
  AIProvider,
  Message,
  AIResponse,
  getAvailableProviders,
  listLocalModels,
  generateAIResponse,
  setActiveProvider,
} from '../../services/aiService';

export function AIAssistantModule() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { role: 'system', content: 'AI Assistant is ready to help. Select a provider and model (e.g., deepseek-coder-v2:latest for Ollama) to start.' },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [availableProviders, setAvailableProviders] = useState<AIProvider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [availableModels, setAvailableModels] = useState<AIModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [error, setError] = useState<string>('');

  // Fetch providers on mount
  useEffect(() => {
    async function fetchProviders() {
      try {
        console.log('Fetching available providers...');
        const providers = await getAvailableProviders();
        console.log('Fetched providers:', providers);
        setAvailableProviders(providers);
        if (providers.length > 0) {
          setSelectedProvider('ollama'); // Default to Ollama since it's confirmed working
          setActiveProvider('ollama');
        } else {
          setError('No AI providers available. Please check the backend configuration at http://localhost:5000.');
        }
      } catch (error: unknown) {
        if (error instanceof Error) {
          console.error('Failed to fetch providers:', error);
          setError('Failed to load providers. Ensure the backend is running and accessible at http://localhost:5000.');
        } else {
          console.error('Failed to fetch providers:', error);
          setError('Failed to load providers. Ensure the backend is running and accessible at http://localhost:5000.');
        }
      }
    }
    fetchProviders();
  }, []);

  // Fetch models when provider changes
  useEffect(() => {
    async function fetchModels() {
      if (!selectedProvider) {
        setAvailableModels([]);
        setSelectedModel('');
        return;
      }
      try {
        console.log(`Fetching models for provider: ${selectedProvider}`);
        setActiveProvider(selectedProvider);
        const models = await listLocalModels();
        console.log('Fetched models:', models);
        setAvailableModels(models);
        if (models.length > 0) {
          setSelectedModel(models[0].id);
        } else {
          setSelectedModel('');
          setError(`No models available for ${selectedProvider}. Ensure the provider service (e.g., Ollama at http://localhost:11434) is running and has models like deepseek-coder-v2:latest.`);
        }
      } catch (error: unknown) {
        if (error instanceof Error) {
          const errorMessage = error.message.includes('NetworkError') || error.message.includes('CORS')
            ? `Cannot connect to ${selectedProvider} at http://localhost:5000. Check if the backend is running and CORS is configured for http://localhost:8080.`
            : `Failed to load models for ${selectedProvider}: ${error.message}`;
          setError(errorMessage);
          setAvailableModels([]);
          setSelectedModel('');
          console.error(`Failed to fetch models for ${selectedProvider}:`, error);
        } else {
          setError(`Failed to load models for ${selectedProvider}: Unknown error`);
          setAvailableModels([]);
          setSelectedModel('');
          console.error(`Failed to fetch models for ${selectedProvider}:`, error);
        }
      }
    }
    fetchModels();
  }, [selectedProvider]);

  // Handle sending messages
  const handleSendMessage = async () => {
    console.log('handleSendMessage:', { input, selectedModel, selectedProvider });
    if (!input.trim()) {
      setError('Please enter a message.');
      return;
    }
    if (!selectedProvider) {
      setError('Please select an AI provider.');
      return;
    }
    if (!selectedModel) {
      setError('Please select a model (e.g., deepseek-coder-v2:latest for Ollama).');
      return;
    }

    setError('');
    const newMessage: Message = { role: 'user', content: input };
    const updatedMessages = [...messages, newMessage];
    setMessages(updatedMessages);
    setIsLoading(true);
    setInput('');

    try {
      console.log(`Generating AI response for model: ${selectedModel}`);
      const data: AIResponse = await generateAIResponse(selectedModel, updatedMessages);
      console.log('AI Response:', data);
      setMessages(prev => [...prev, data.message]);
    } catch (error: unknown) {
      let errorMessage = 'An unknown error occurred.';
      if (error instanceof Error) {
        errorMessage = error.message.includes('NetworkError') || error.message.includes('CORS')
          ? 'Cannot connect to the backend at http://localhost:5000. Check if it’s running and CORS is configured for http://localhost:8080.'
          : `Failed to get response: ${error.message}`;
      }
      console.error('Error generating AI response:', error);
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: `Error: ${errorMessage}` },
      ]);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[300px]">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Bot className="h-4 w-4 text-primary" />
          <h4 className="text-sm font-medium">AI Assistant</h4>
        </div>

        <Select value={selectedProvider} onValueChange={setSelectedProvider}>
          <SelectTrigger className="w-[150px] h-7 text-xs">
            <SelectValue placeholder="Select provider" />
          </SelectTrigger>
          <SelectContent>
            {availableProviders.length > 0 ? (
              availableProviders.map(provider => (
                <SelectItem key={provider.id} value={provider.id}>
                  {provider.name}
                </SelectItem>
              ))
            ) : (
              <SelectItem value="none" disabled>
                No providers available
              </SelectItem>
            )}
          </SelectContent>
        </Select>

        <Select value={selectedModel} onValueChange={setSelectedModel}>
          <SelectTrigger className="w-[150px] h-7 text-xs">
            <SelectValue placeholder="Select model" />
          </SelectTrigger>
          <SelectContent>
            {availableModels.length > 0 ? (
              availableModels.map(model => (
                <SelectItem
                  key={model.id}
                  value={model.id}
                  disabled={model.status === 'inactive'}
                >
                  {model.name}
                </SelectItem>
              ))
            ) : (
              <SelectItem value="none" disabled>
                No models available
              </SelectItem>
            )}
          </SelectContent>
        </Select>
      </div>

      {error && (
        <div className="text-red-500 text-sm mb-2">{error}</div>
      )}

      <ScrollArea className="flex-1 mb-3 pr-4">
        <div className="space-y-2">
          {messages.slice(1).map((message, index) => (
            <div
              key={index}
              className={message.role === 'user' ? 'user-message' : 'ai-message'}
            >
              <div className="text-sm">{message.content}</div>
            </div>
          ))}
          {isLoading && (
            <div className="ai-message">
              <div className="text-sm flex items-center space-x-2">
                <span className="inline-block h-2 w-2 bg-primary rounded-full animate-pulse-gentle" />
                <span className="inline-block h-2 w-2 bg-primary rounded-full animate-pulse-gentle delay-150" />
                <span className="inline-block h-2 w-2 bg-primary rounded-full animate-pulse-gentle delay-300" />
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="flex items-center space-x-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your request..."
          className="flex-1"
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSendMessage();
          }}
        />
        <Button size="icon" onClick={handleSendMessage} disabled={isLoading}>
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}