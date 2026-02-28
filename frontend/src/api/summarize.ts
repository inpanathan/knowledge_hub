import { request } from "./client";
import type { SummarizeRequest, SummarizeResponse } from "./types";

export function summarize(data: SummarizeRequest): Promise<SummarizeResponse> {
  return request<SummarizeResponse>("/summarize", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
