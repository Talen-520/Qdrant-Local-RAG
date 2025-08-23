// src/components/files/FileList.tsx
import React from 'react';
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import type { FileInfo } from '../../types';

interface Props {
  files: FileInfo[];
  selectedFiles: Record<string, boolean>;
  onFileSelect: (fileName: string) => void;
  onFileDelete: (file: FileInfo) => void;
}

export const FileList: React.FC<Props> = ({ files, selectedFiles, onFileSelect, onFileDelete }) => {
  if (files.length === 0) {
    return <p className="mt-4 text-center text-sm text-muted-foreground">No files uploaded yet.</p>;
  }
  return (
    <ul className="w-full space-y-2 text-sm text-gray-800">
      {files.map((file) => (
        <li key={file.name} className="group flex items-center justify-between py-1">
          <div className="flex items-center space-x-2 overflow-hidden">
            <Checkbox id={file.name} checked={!!selectedFiles[file.name]} onCheckedChange={() => onFileSelect(file.name)} />
            <Label htmlFor={file.name} className="truncate cursor-pointer font-medium">📄 {file.name}</Label>
          </div>
          <Button size="sm" variant="ghost" className="text-red-500 opacity-0 transition-opacity group-hover:opacity-100" onClick={() => onFileDelete(file)}>Delete</Button>
        </li>
      ))}
    </ul>
  );
};