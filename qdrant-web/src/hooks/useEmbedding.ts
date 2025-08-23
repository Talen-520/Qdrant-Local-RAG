// src/hooks/useEmbedding.ts
import { useState } from "react";
import { toast } from "sonner";
import { API_BASE_URL } from "../config";

export const useEmbedding = () => {
  const [isEmbedding, setIsEmbedding] = useState(false);
  const [embeddingLogs, setEmbeddingLogs] = useState<string[]>([]);

  const startEmbedding = () => {
    setIsEmbedding(true);
    setEmbeddingLogs([]);
    const eventSource = new EventSource(`${API_BASE_URL}/embed-stream`);

    eventSource.onmessage = (event) => {
      const message = event.data;
      if (message === "[DONE]") {
        toast.success("Vector store created successfully!");
        eventSource.close();
        setIsEmbedding(false);
      } else {
        setEmbeddingLogs((prev) => [...prev, message]);
      }
    };

    eventSource.onerror = (err) => {
      console.error("EventSource failed:", err);
      toast.error("Embedding failed, connection interrupted.");
      eventSource.close();
      setIsEmbedding(false);
    };
  };

  return { isEmbedding, embeddingLogs, startEmbedding };
};