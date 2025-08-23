// src/hooks/useChat.ts
import { useState, useRef, useEffect } from "react";
import { toast } from "sonner";
import { API_BASE_URL } from "../config";
import type { Message, AnswerResponse } from "../types";

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      const el = chatContainerRef.current;
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    }
  }, [messages]);

  const submitQuery = async (query: string, selectedFiles: Record<string, boolean>, model: string) => {
    if (!query.trim()) return;

    setIsLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: query }]);

    const activeFilters = Object.keys(selectedFiles).filter((fileName) => selectedFiles[fileName]);

    try {
      const res = await fetch(`${API_BASE_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          query, 
          top_k: 6, 
          file_filters: activeFilters, 
          model: model 
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "An error occurred");
      }

      const data: AnswerResponse = await res.json();
      setMessages((prev) => [...prev, { role: "ai", content: data.answer, sources: data.sources }]);
    } catch (err: any) {
      const errorMessage = `Query failed: ${err.message}`;
      toast.error(errorMessage);
      setMessages((prev) => [...prev, { role: "ai", content: "Sorry, I ran into an issue. Please try again." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return { messages, isLoading, submitQuery, chatContainerRef };
};