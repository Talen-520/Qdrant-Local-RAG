// src/hooks/useModels.ts
import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { API_BASE_URL } from '../config';

interface ModelsResponse {
  models: string[];
}

export const useModels = () => {
  const [models, setModels] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/models`);
        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'Failed to fetch models from server');
        }
        const data: ModelsResponse = await response.json();
        setModels(data.models);
      } catch (err: any) {
        const errorMessage = `Error fetching models: ${err.message}`;
        toast.error(errorMessage);
        setModels([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchModels();
  }, []); 

  return { models, isLoading };
};