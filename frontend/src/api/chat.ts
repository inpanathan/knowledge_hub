import { request } from "./client";
import type {
  ChatRequest,
  ChatResponse,
  ChatSession,
  ChatSessionSummary,
} from "./types";

export function sendMessage(data: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function listSessions(): Promise<ChatSessionSummary[]> {
  return request<ChatSessionSummary[]>("/chat/sessions");
}

export function getSession(id: string): Promise<ChatSession> {
  return request<ChatSession>(`/chat/sessions/${id}`);
}
