// app/page.tsx or your component file
"use client";

import { useState, useEffect } from "react";
import type { FormEvent } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

// 定义从后端获取的文件和API响应的类型
interface KnowledgeFile {
  name: string;
  path: string;
}

interface SourceDocument {
  content: string;
  metadata: Record<string, any>;
  score: number;
}

interface AnswerResponse {
  answer: string;
  sources: SourceDocument[];
}

export default function ChatPage_v2() {
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  // ✅ 新增: 使用一个对象来跟踪每个文件的选中状态
  const [selectedFiles, setSelectedFiles] = useState<Record<string, boolean>>({});
  
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<AnswerResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 1. 组件加载时获取文件列表
  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const res = await fetch("http://localhost:5000/files");
        if (!res.ok) throw new Error("Failed to fetch files");
        const data: KnowledgeFile[] = await res.json();
        setFiles(data);
      } catch (err: any) {
        setError(err.message);
      }
    };
    fetchFiles();
  }, []);

  // 2. 处理复选框变化的函数
  const handleFileSelectionChange = (fileName: string) => {
    setSelectedFiles((prevSelectedFiles) => ({
      ...prevSelectedFiles,
      [fileName]: !prevSelectedFiles[fileName],
    }));
  };

  // 3. 提交查询的函数
  const handleQuerySubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setResponse(null);

    // ✅ 核心改动: 从状态中获取选中的文件名列表
    const activeFilters = Object.keys(selectedFiles).filter(
      (fileName) => selectedFiles[fileName]
    );

    try {
      const res = await fetch("http://localhost:5000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          top_k: 6,
          file_filters: activeFilters, // ✅ 发送过滤器列表
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "An error occurred");
      }

      const data: AnswerResponse = await res.json();
      setResponse(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4 grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* 左侧文件列表 */}
      <Card className="md:col-span-1">
        <CardHeader>
          <CardTitle>知识库文件</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {files.length > 0 ? (
            files.map((file) => (
              <div key={file.name} className="flex items-center space-x-2">
                <Checkbox
                  id={file.name}
                  checked={!!selectedFiles[file.name]}
                  onCheckedChange={() => handleFileSelectionChange(file.name)}
                />
                <Label htmlFor={file.name} className="cursor-pointer text-sm font-medium leading-none">
                  {file.name}
                </Label>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">知识库为空。</p>
          )}
        </CardContent>
      </Card>

      {/* 右侧问答界面 */}
      <div className="md:col-span-2">
        <Card>
          <CardHeader>
            <CardTitle>RAG 问答</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleQuerySubmit} className="flex gap-2">
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="在此输入你的问题..."
                disabled={isLoading}
              />
              <Button type="submit" disabled={isLoading}>
                {isLoading ? "思考中..." : "提问"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {error && <p className="text-red-500 mt-4">{error}</p>}

        {response && (
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>回答</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="mb-4">{response.answer}</p>
              <h4 className="font-bold mb-2">参考来源:</h4>
              <div className="space-y-2">
                {response.sources.map((source, index) => (
                  <div key={index} className="p-2 border rounded">
                    <p className="text-xs text-muted-foreground">
                      <strong>文件:</strong> {source.metadata.source}, <strong>相关度:</strong> {source.score.toFixed(4)}
                    </p>
                    <p className="text-sm mt-1 line-clamp-3">{source.content}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}