import { request } from "./client";
import type { QnAGenerateRequest, QASet, QnAExportRequest } from "./types";

export function generateQnA(data: QnAGenerateRequest): Promise<QASet> {
  return request<QASet>("/qna/generate", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getQASet(id: string): Promise<QASet> {
  return request<QASet>(`/qna/${id}`);
}

export function exportQASet(id: string, data: QnAExportRequest): Promise<Blob> {
  return fetch(`/api/v1/qna/${id}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then((r) => r.blob());
}
