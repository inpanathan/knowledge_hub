import { request } from "./client";
import type {
  IngestionResponse,
  FolderIngestionResponse,
  UrlIngestionRequest,
  TextIngestionRequest,
  FolderIngestionRequest,
  SourceDetail,
  SourceListResponse,
  SourceUpdateRequest,
} from "./types";

export function listSources(params?: {
  source_type?: string;
  status?: string;
  tag?: string;
  search?: string;
}): Promise<SourceListResponse> {
  const query = new URLSearchParams();
  if (params?.source_type) query.set("source_type", params.source_type);
  if (params?.status) query.set("status", params.status);
  if (params?.tag) query.set("tag", params.tag);
  if (params?.search) query.set("search", params.search);
  const qs = query.toString();
  return request<SourceListResponse>(`/sources${qs ? `?${qs}` : ""}`);
}

export function getSource(id: string): Promise<SourceDetail> {
  return request<SourceDetail>(`/sources/${id}`);
}

export function updateSource(id: string, data: SourceUpdateRequest): Promise<SourceDetail> {
  return request<SourceDetail>(`/sources/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteSource(id: string): Promise<void> {
  return request<void>(`/sources/${id}`, { method: "DELETE" });
}

export function reindexSource(id: string): Promise<IngestionResponse> {
  return request<IngestionResponse>(`/sources/${id}/reindex`, { method: "POST" });
}

export function uploadFile(file: File, tags?: string[]): Promise<IngestionResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (tags?.length) {
    tags.forEach((tag) => formData.append("tags", tag));
  }
  return request<IngestionResponse>("/sources/upload", {
    method: "POST",
    body: formData,
  });
}

export function ingestUrl(data: UrlIngestionRequest): Promise<IngestionResponse> {
  return request<IngestionResponse>("/sources/url", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function ingestText(data: TextIngestionRequest): Promise<IngestionResponse> {
  return request<IngestionResponse>("/sources/text", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function ingestFolder(data: FolderIngestionRequest): Promise<FolderIngestionResponse> {
  return request<FolderIngestionResponse>("/sources/folder", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getSourceOriginalUrl(id: string): string {
  return `/api/v1/sources/${id}/original`;
}

export function getSourceViewUrl(id: string): string {
  return `/api/v1/sources/${id}/view`;
}
