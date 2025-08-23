// src/components/chat/ChatMessage.tsx
import React from 'react';
import type { Message, SourceDocument } from '../../types';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Source: React.FC<{ source: SourceDocument; index: number }> = ({ source, index }) => (
  <div className="mt-2 border-l-2 border-gray-300 pl-2 text-xs text-gray-600">
    <p><b>Source {index + 1}:</b> {source.metadata.source || "Unknown"} (Score: {source.score.toFixed(2)})</p>
  </div>
);

export const ChatMessage: React.FC<{ message: Message }> = ({ message }) => {
  const isUser = message.role === 'user';

  return (

    <div className={`flex items-start max-w-3xl mx-auto ${
        isUser ? 'justify-end' : 'justify-start'
      }`}
    >
      <div className={`rounded-xl p-3 whitespace-pre-wrap ${
          isUser
            ? 'bg-zinc-100 max-w-[70%]'      
            : 'bg-zinc-transparent w-full'  
        }`}
      >
        <div className="prose prose-sm dark:prose-invert prose-p:my-2 prose-headings:my-2">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({node, ...props}) => <a {...props} target="_blank" rel="noopener noreferrer" />
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3 border-t border-gray-300 pt-2">
            <h4 className="text-sm font-semibold">Sources:</h4>
            {message.sources.map((s, i) => <Source key={i} source={s} index={i} />)}
          </div>
        )}
      </div>
    </div>
  );
};