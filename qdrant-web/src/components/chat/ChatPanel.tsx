// src/components/chat/ChatPanel.tsx
import React, { useState, useEffect } from 'react'; // 引入 useEffect
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2Icon } from 'lucide-react';
import { useChat } from '../../hooks/useChat';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

// ✅ 1. 导入新的 Hook
import { useModels } from '../../hooks/useModels'; 
import { toast } from 'sonner';

interface Props {
  selectedFiles: Record<string, boolean>;
}

export const ChatPanel: React.FC<Props> = ({ selectedFiles }) => {
  const { messages, isLoading, submitQuery, chatContainerRef } = useChat();
  const [query, setQuery] = useState('');
  
  const { models: availableModels, isLoading: isLoadingModels } = useModels();

  const [selectedModel, setSelectedModel] = useState<string>('');

  useEffect(() => {
    if (availableModels.length > 0 && !selectedModel) {
      setSelectedModel(availableModels[0]);
    }
  }, [availableModels, selectedModel]);

  const handleQuerySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModel) {
      toast.error("Please wait for models to load or select a model.");
      return;
    }
    await submitQuery(query, selectedFiles, selectedModel);
    setQuery('');
  };

  return (
    <Card className="flex w-2/3 flex-col">
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-4">
          <CardTitle>Ask Your Documents</CardTitle>
          <div className="flex items-center gap-2">
            <Label htmlFor="model-select" className="text-sm font-medium text-muted-foreground">
              Model:
            </Label>
            <Select 
              value={selectedModel} 
              onValueChange={setSelectedModel} 
              disabled={isLoadingModels || isLoading}
            >
              <SelectTrigger id="model-select" className="w-[220px]">
                {isLoadingModels ? "Loading models..." : <SelectValue placeholder="Select a model" />}
              </SelectTrigger>
              <SelectContent>
                {!isLoadingModels && availableModels.length === 0 ? (
                  <SelectItem value="no-models" disabled>No local models found</SelectItem>
                ) : (
                  availableModels.map(model => (
                    <SelectItem key={model} value={model}>{model}</SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="flex items-center text-sm text-gray-500">
          {isLoading ? ( <><Loader2Icon className="mr-2 h-4 w-4 animate-spin" /><span>Thinking...</span></> ) : ( <span>Idle</span> )}
        </div>
      </CardHeader>
      
      <CardContent ref={chatContainerRef} className="flex-1 space-y-4 overflow-y-auto py-4 px-16">
        {messages.length > 0 ? (
          messages.map((msg, i) => <ChatMessage key={`chat-${i}`} message={msg} />)
        ) : (
           <div className="flex h-full items-center justify-center">
             <p className="text-muted-foreground animate-pulse">Start the conversation!</p>
           </div>
        )}
      </CardContent>

      <ChatInput query={query} setQuery={setQuery} onSubmit={handleQuerySubmit} isLoading={isLoading} />
    </Card>
  );
};