import { request } from "./client";
import type {
  InterviewStartRequest,
  InterviewSession,
  InterviewAnswerRequest,
  InterviewAnswerResponse,
  InterviewSummary,
} from "./types";

export function startInterview(data: InterviewStartRequest): Promise<InterviewSession> {
  return request<InterviewSession>("/interview/start", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function submitAnswer(
  id: string,
  data: InterviewAnswerRequest,
): Promise<InterviewAnswerResponse> {
  return request<InterviewAnswerResponse>(`/interview/${id}/answer`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getInterviewSummary(id: string): Promise<InterviewSummary> {
  return request<InterviewSummary>(`/interview/${id}/summary`);
}
