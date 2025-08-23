// src/components/chat/ChatInput.tsx
import React, { useRef, useEffect } from 'react';
import { Textarea } from '@/components/ui/textarea';


interface Props {
  query: string;
  setQuery: (q: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
}

export const ChatInput: React.FC<Props> = ({ query, setQuery, onSubmit, isLoading }) => {
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = 'auto';
      ref.current.style.height = `${Math.min(ref.current.scrollHeight, 200)}px`;
    }
  }, [query]);

  return (
    <form onSubmit={onSubmit} className="flex items-end gap-2 p-4">
      <Textarea
        ref={ref}
        className="flex-1 resize-none"
        placeholder="Ask anything about your files..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); onSubmit(e as any); }}}
        rows={1}
        disabled={isLoading}
      />
    </form>
  );
};