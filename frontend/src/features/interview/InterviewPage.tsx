import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { startInterview, submitAnswer, getInterviewSummary } from "@/api/interview";
import type { InterviewSession, InterviewAnswerResponse } from "@/api/types";
import { InterviewSetup } from "./InterviewSetup";
import { InterviewSessionView } from "./InterviewSession";
import { InterviewSummaryView } from "./InterviewSummary";

export function InterviewPage() {
  const { sessionId: urlSessionId } = useParams();
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [lastFeedback, setLastFeedback] = useState<InterviewAnswerResponse | null>(null);

  // Fetch summary if we have a completed session
  const { data: summary } = useQuery({
    queryKey: ["interview-summary", session?.id ?? urlSessionId],
    queryFn: () => getInterviewSummary((session?.id ?? urlSessionId)!),
    enabled: !!session?.completed || !!urlSessionId,
  });

  const startMutation = useMutation({
    mutationFn: startInterview,
    onSuccess: (data) => {
      setSession(data);
      setLastFeedback(null);
    },
  });

  const answerMutation = useMutation({
    mutationFn: ({ answer }: { answer: string }) =>
      submitAnswer(session!.id, { answer }),
    onSuccess: (data) => {
      setLastFeedback(data);
      if (data.completed) {
        setSession((prev) => prev ? { ...prev, completed: true } : null);
      } else if (data.next_question) {
        setSession((prev) =>
          prev
            ? {
                ...prev,
                current_question: data.next_question,
                current_index: data.next_question!.index,
              }
            : null,
        );
      }
    },
  });

  // Show summary if completed
  if (session?.completed && summary) {
    return (
      <InterviewSummaryView
        summary={summary}
        onNewSession={() => {
          setSession(null);
          setLastFeedback(null);
        }}
      />
    );
  }

  // Show session if active
  if (session) {
    return (
      <InterviewSessionView
        session={session}
        lastFeedback={lastFeedback}
        onSubmitAnswer={(answer) => answerMutation.mutate({ answer })}
        isSubmitting={answerMutation.isPending}
      />
    );
  }

  // Show setup
  return (
    <InterviewSetup
      onStart={(data) => startMutation.mutate(data)}
      isStarting={startMutation.isPending}
    />
  );
}
