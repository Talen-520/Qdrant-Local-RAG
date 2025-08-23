// src/types.ts
export interface Message {
  role: "user" | "ai";
  content: string;
  sources?: SourceDocument[]; // Sources are now part of the AI message
}

export interface FileInfo {
  name: string;
  path: string;
}

export interface SourceDocument {
  content: string;
  metadata: Record<string, any>;
  score: number;
}

export interface AnswerResponse {
  answer: string;
  sources: SourceDocument[];
}