// src/pages/ChatPage.tsx
import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Loader2Icon } from "lucide-react";
import { Toaster, toast } from "sonner";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
// import { Input } from "@/components/ui/input";

// Define message types
interface Message {
  role: "user" | "ai";
  content: string;
}

interface FileInfo {
  name: string;
  path: string;
}

// Define backend API response types
interface SourceDocument {
  content: string;
  metadata: Record<string, any>;
  score: number;
}

interface AnswerResponse {
  answer: string;
  sources: SourceDocument[];
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<Record<string, boolean>>({});
  const [isEmbedding, setIsEmbedding] = useState(false);
  const [embeddingLogs, setEmbeddingLogs] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // On component mount fetch file list
  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const res = await fetch("http://localhost:5000/files");
        if (!res.ok) throw new Error("Failed to fetch files");
        const data: FileInfo[] = await res.json();
        setFiles(data);
        const initialSelected: Record<string, boolean> = {};
        data.forEach(file => {
            initialSelected[file.name] = false;
        });
        setSelectedFiles(initialSelected);
      } catch (err: any) {
        toast.error(`Failed to fetch files: ${err.message}`);
        setError(err.message);
      }
    };
    fetchFiles();
  }, []);

  //  Textarea  
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight, 200)}px`;
    }
  }, [query]); // watch query changes

  // Scroll chat container to bottom
  useEffect(() => {
    if (chatContainerRef.current) {
      const chatContainer = chatContainerRef.current;
      chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages]);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const uploaded = Array.from(e.dataTransfer.files);

    const formData = new FormData();
    uploaded.forEach((file) => formData.append("files", file));

    fetch("http://localhost:5000/upload", {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then((data: FileInfo[]) => {
        setFiles(data);
        const newSelected: Record<string, boolean> = {};
        data.forEach(file => {
            newSelected[file.name] = selectedFiles[file.name] || false;
        });
        setSelectedFiles(newSelected);
        toast.success("File uploaded successfully!");
      })
      .catch((err) => {
        console.error("Upload failed:", err);
        toast.error("File upload failed.");
      });
  };

  const handleDelete = (file: FileInfo) => {
    fetch(
      `http://localhost:5000/delete?filename=${encodeURIComponent(file.name)}`,
      {
        method: "DELETE",
      }
    )
      .then((res) => res.json())
      .then((data: FileInfo[]) => {
        setFiles(data);
        setSelectedFiles(prevSelectedFiles => {
            const newSelected = { ...prevSelectedFiles };
            delete newSelected[file.name];
            return newSelected;
        });
        toast.success(`File ${file.name} deleted successfully!`);
      })
      .catch((err) => {
        console.error("Delete failed:", err);
        toast.error("File deletion failed.");
      });
  };

  const handleEmbedding = () => {
    setIsEmbedding(true);
    setEmbeddingLogs([]);

    const eventSource = new EventSource("http://localhost:5000/embed-stream");

    eventSource.onmessage = (event) => {
      const message = event.data;

      if (message === "[DONE]") {
        toast.success("Vector store created successfully!");
        eventSource.close();
        setIsEmbedding(false);
      } else {
        setEmbeddingLogs((prevLogs) => [...prevLogs, message]);
      }
    };

    eventSource.onerror = (err) => {
      console.error("EventSource failed:", err);
      toast.error("Embedding failed, connection interrupted.");
      eventSource.close();
      setIsEmbedding(false);
    };
  };

  const handleFileSelectionChange = (fileName: string) => {
    setSelectedFiles((prevSelectedFiles) => ({
      ...prevSelectedFiles,
      [fileName]: !prevSelectedFiles[fileName],
    }));
  };

  const handleQuerySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);

    // Immediately add user input to chat history
    const userQuery = query.trim();
    setMessages((prev) => [...prev, { role: "user", content: userQuery }]);
    setQuery(""); // 清空输入框

    const activeFilters = Object.keys(selectedFiles).filter(
      (fileName) => selectedFiles[fileName]
    );

    try {
      const res = await fetch("http://localhost:5000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: userQuery,
          top_k: 6,
          file_filters: activeFilters,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "An error occurred");
      }

      const data: AnswerResponse = await res.json();

      // Add AI answer to chat history
      setMessages((prev) => [
        ...prev,
        { role: "ai", content: data.answer }
      ]);

      // If there are sources, also add them to the chat
      if (data.sources && data.sources.length > 0) {
        const sourcesText = data.sources
          .map((s: any, idx: number) => `📄 [${idx + 1}] ${s.metadata.source || "unknown"} (score: ${s.score.toFixed(2)})`)
          .join("\n");

        setMessages((prev) => [
          ...prev,
          { role: "ai", content: `Sources:\n${sourcesText}` }
        ]);
      }

    } catch (err: any) {
      setError(err.message);
      toast.error(`Query failed: ${err.message}`);
      setMessages((prev) => [
        ...prev,
        { role: "ai", content: "Query failed, please try again later." }
      ]);
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <div className="flex h-screen w-full gap-4 p-4 bg-gray-100">
      <Toaster position="top-center" richColors />
      
      {/* Left file panel */}
      <Card
        className={`w-1/3 flex flex-col relative border-2 border-dashed rounded-2xl transition-all ${
          dragOver ? "border-blue-500 bg-blue-50" : "border-gray-300"
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <CardHeader>
          <CardTitle>Knowledge Base Files</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-6">
          <p className="text-center text-gray-600">
            Drag and drop files into this area
          </p>
          <ul className="mt-4 w-full text-sm text-gray-800 space-y-2">
            {files.length > 0 ? (
              files.map((file) => (
                <li key={file.name} className="flex justify-between items-center py-1">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id={file.name}
                      checked={!!selectedFiles[file.name]}
                      onCheckedChange={() => handleFileSelectionChange(file.name)}
                    />
                    <Label htmlFor={file.name} className="cursor-pointer text-sm font-medium leading-none">
                      <span className="truncate max-w-[150px] inline-block">📄 {file.name}</span>
                    </Label>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDelete(file)}
                  >
                    Delete
                  </Button>
                </li>
              ))
            ) : (
              <p className="text-sm text-muted-foreground mt-4 text-center">upload file here。</p>
            )}
          </ul>
          {isEmbedding && (
            <div className="mt-4 w-full p-2 border rounded-md bg-gray-50 h-40 overflow-y-auto">
              <p className="font-semibold text-sm mb-2">Embedding logs:</p>
              <ul className="text-xs text-gray-600 space-y-1">
                {embeddingLogs.map((log, idx) => (
                  <li key={idx}>{log}</li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>

        {/* 底部按钮区域 */}
        <div className="absolute bottom-4 right-4 flex items-center gap-2">
          {/* Qdrant DB 按钮 */}
          <a href="http://localhost:6333/dashboard#/collections" target="_blank" rel="noopener noreferrer">
            <Button variant="outline" size="sm">
              View Collections
            </Button>
          </a>
          
          {/* Embedding 按钮 */}
          <Button
            onClick={handleEmbedding}
            disabled={isEmbedding}
            size="sm"
          >
            {isEmbedding ? (
              <>
                <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                Embedding...
              </>
            ) : (
              "Embedding"
            )}
          </Button>
        </div>
      </Card>

      {/* 右侧聊天界面 (现在整合了 RAG 问答和聊天历史) */}
      <Card className="w-2/3 flex flex-col relative">
        <CardHeader className="flex flex-row items-center justify-between pr-4">
          <CardTitle>Ask question about your files</CardTitle>
          {/* 右上角状态指示器 */}
          <div className="flex items-center text-sm text-gray-500">
            {isLoading ? (
              <>
                <Loader2Icon className="mr-1 h-4 w-4 animate-spin" />
                <span>Thinking...</span>
              </>
            ) : (
              <span className="text-gray-700 animate-bounce">Idle...</span>
            )}
          </div>
        </CardHeader>
        <CardContent ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 space-y-3">
          {/* 显示所有聊天历史消息，包括 RAG 问答的输入、回答和来源 */}
          {messages.map((msg, idx) => (
            <div
              key={`chat-${idx}`}
              // ✅ 修改：移除 self-end/ml-auto 和 self-start，添加 mx-auto 进行居中
              className={`p-2 rounded-xl max-w-lg whitespace-pre-wrap mx-auto ${msg.role === "user"
                  ? "bg-gray-100" // 保持用户消息的颜色
                  : "" // 保持 AI 消息的颜色
                }`}
            >
              {msg.content}
            </div>
          ))}

          {/* 错误信息现在可以作为普通消息显示，或者单独处理，这里保留独立显示 */}
          {error && <p className="text-red-500 mt-4 text-center">{error}</p>}
        </CardContent>
        <div className="flex items-end gap-2 p-2">
          <Textarea
            ref={textareaRef}
            className="flex-1 resize-none overflow-y-auto"
            placeholder="Ask anything about your files..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleQuerySubmit(e as React.FormEvent);
              }
            }}
            rows={1}
            style={{ maxHeight: "200px" }}
          />
        </div>
      </Card>
    </div>
  );
};

export default ChatPage;
