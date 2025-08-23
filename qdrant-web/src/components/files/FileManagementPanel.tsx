// src/components/files/FileManagementPanel.tsx
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useEmbedding } from '../../hooks/useEmbedding';
import { FileList } from './FileList';
import { EmbeddingSection } from './EmbeddingSection';
import type { FileInfo } from '../../types';

interface Props {
    files: FileInfo[];
    selectedFiles: Record<string, boolean>;
    onFileSelectionChange: (fileName: string) => void;
    onUpload: (files: File[]) => void;
    onDelete: (file: FileInfo) => void;
}

export const FileManagementPanel: React.FC<Props> = ({ files, selectedFiles, onFileSelectionChange, onUpload, onDelete }) => {
  const { isEmbedding, embeddingLogs, startEmbedding } = useEmbedding();
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const uploaded = Array.from(e.dataTransfer.files);
    if (uploaded.length > 0) onUpload(uploaded);
  };

  return (
    <Card
      className={`flex w-1/3 flex-col rounded-lg border-2 border-dashed transition-all ${
        dragOver ? "border-blue-500 bg-blue-50" : "border-gray-300"
      }`}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      <CardHeader><CardTitle>Knowledge Base</CardTitle></CardHeader>
      <CardContent className="flex flex-1 flex-col p-4">
        <div className="rounded-md border border-dashed p-4 text-center text-gray-500">
            Drag & Drop Files Here
        </div>
        <div className="mt-4 flex-1 overflow-y-auto">
            <FileList files={files} selectedFiles={selectedFiles} onFileSelect={onFileSelectionChange} onFileDelete={onDelete} />
        </div>
        <EmbeddingSection isEmbedding={isEmbedding} embeddingLogs={embeddingLogs} onEmbed={startEmbedding} />
      </CardContent>
    </Card>
  );
};