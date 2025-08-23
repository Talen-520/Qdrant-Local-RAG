// src/hooks/useFiles.ts
import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { API_BASE_URL } from "../config";
import type { FileInfo } from "../types";

export const useFiles = () => {
  const [files, setFiles] = useState<FileInfo[]>([]);

  const fetchFiles = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/files`);
      if (!res.ok) throw new Error("Server failed to respond");
      const data: FileInfo[] = await res.json();
      setFiles(data);
    } catch (err: any) {
      toast.error(`Failed to fetch files: ${err.message}`);
    }
  }, []);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  const handleUpload = async (uploadedFiles: File[]) => {
    const formData = new FormData();
    uploadedFiles.forEach((file) => formData.append("files", file));

    try {
      const res = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Upload failed");
      toast.success("File(s) uploaded successfully!");
      await fetchFiles(); // Refresh file list
    } catch (err: any) {
      toast.error(`File upload failed: ${err.message}`);
    }
  };

  const handleDelete = async (fileToDelete: FileInfo) => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/delete?filename=${encodeURIComponent(fileToDelete.name)}`,
        { method: "DELETE" }
      );
      if (!res.ok) throw new Error((await res.json()).detail || "Delete failed");
      toast.success(`File "${fileToDelete.name}" deleted.`);
      await fetchFiles(); // Refresh file list
    } catch (err: any) {
      toast.error(`File deletion failed: ${err.message}`);
    }
  };

  return { files, handleUpload, handleDelete };
};