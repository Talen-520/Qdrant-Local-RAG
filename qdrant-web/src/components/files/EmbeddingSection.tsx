// src/components/files/EmbeddingSection.tsx
import React from 'react';
import { Button } from "@/components/ui/button";
import { Loader2Icon } from "lucide-react";

interface Props {
    isEmbedding: boolean;
    embeddingLogs: string[];
    onEmbed: () => void;
}

export const EmbeddingSection: React.FC<Props> = ({ isEmbedding, embeddingLogs, onEmbed }) => (
    <>
        {isEmbedding && (
            <div className="mt-4 h-40 w-full overflow-y-auto rounded-md border bg-gray-50 p-2">
                <p className="mb-2 text-sm font-semibold">Embedding logs:</p>
                <ul className="space-y-1 font-mono text-xs text-gray-600">
                    {embeddingLogs.map((log, idx) => <li key={idx}>{log}</li>)}
                </ul>
            </div>
        )}
        <div className="flex items-center justify-end gap-2 pt-4 mt-auto">
             <a href="http://localhost:6333/dashboard" target="_blank" rel="noopener noreferrer">
                <Button variant="outline" size="sm">View Collect    ion in Qdrant</Button>
             </a>
            <Button onClick={onEmbed} disabled={isEmbedding} size="sm">
                {isEmbedding ? (
                    <><Loader2Icon className="mr-2 h-4 w-4 animate-spin" /> Embedding...</>
                ) : "Embed All Documents"}
            </Button>
        </div>
    </>
);