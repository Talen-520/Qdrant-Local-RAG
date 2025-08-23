// src/pages/ChatPage.tsx
import React, { useState, useEffect } from 'react';
import { Toaster } from 'sonner';
import { FileManagementPanel } from '../components/files/FileManagementPanel';
import { ChatPanel } from '../components/chat/ChatPanel';
import { useFiles } from '../hooks/useFiles';
import type { FileInfo } from '../types';

const ChatPage: React.FC = () => {
  const { files, handleUpload, handleDelete } = useFiles();
  const [selectedFiles, setSelectedFiles] = useState<Record<string, boolean>>({});

  // Sync selectedFiles state when the main file list changes
  useEffect(() => {
    setSelectedFiles(prev => {
        const newSelected: Record<string, boolean> = {};
        files.forEach(file => { newSelected[file.name] = prev[file.name] || false; });
        return newSelected;
    });
  }, [files]);

  const handleFileSelectionChange = (fileName: string) => {
    setSelectedFiles(prev => ({ ...prev, [fileName]: !prev[fileName] }));
  };
  
  // When deleting a file, also remove it from the selection state
  const handleDeleteAndDeselect = async (file: FileInfo) => {
    await handleDelete(file);
    setSelectedFiles(prev => {
      const { [file.name]: _, ...rest } = prev;
      return rest;
    });
  };

  return (
    <div className="flex h-screen w-full gap-4 bg-gray-50 p-4 dark:bg-gray-900">
      <Toaster position="top-center" richColors />
      <FileManagementPanel 
        files={files}
        selectedFiles={selectedFiles}
        onFileSelectionChange={handleFileSelectionChange}
        onUpload={handleUpload}
        onDelete={handleDeleteAndDeselect}
      />
      <ChatPanel selectedFiles={selectedFiles} />
    </div>
  );
};

export default ChatPage;