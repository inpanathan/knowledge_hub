import { useState } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import type { InterviewSession, InterviewAnswerResponse } from "@/api/types";
import { FeedbackPanel } from "./FeedbackPanel";

interface InterviewSessionViewProps {
  session: InterviewSession;
  lastFeedback: InterviewAnswerResponse | null;
  onSubmitAnswer: (answer: string) => void;
  isSubmitting: boolean;
}

export function InterviewSessionView({
  session,
  lastFeedback,
  onSubmitAnswer,
  isSubmitting,
}: InterviewSessionViewProps) {
  const [answer, setAnswer] = useState("");

  const progress = ((session.current_index + 1) / session.total_questions) * 100;
  const question = session.current_question;

  const handleSubmit = () => {
    if (!answer.trim()) return;
    onSubmitAnswer(answer.trim());
    setAnswer("");
  };

  return (
    <div className="flex h-full flex-col">
      {/* Progress header */}
      <div className="border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold">{session.topic}</h1>
            <div className="flex gap-2 mt-1">
              <Badge variant="outline">{session.mode}</Badge>
              <Badge variant="outline">{session.difficulty}</Badge>
            </div>
          </div>
          <span className="text-sm text-muted-foreground">
            {session.current_index + 1} / {session.total_questions}
          </span>
        </div>
        <Progress value={progress} className="mt-3" />
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-2xl space-y-6">
          {/* Previous question feedback */}
          {lastFeedback && (
            <FeedbackPanel question={lastFeedback.question} />
          )}

          {/* Current question */}
          {question && (
            <Card>
              <CardContent className="p-6">
                <p className="text-xs font-medium text-muted-foreground mb-2">
                  Question {question.index + 1}
                </p>
                <p className="text-base leading-relaxed">{question.question}</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Answer input */}
      {question && !question.answered && (
        <div className="border-t px-6 py-4">
          <div className="mx-auto max-w-2xl">
            <Textarea
              placeholder="Type your answer..."
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={4}
              className="mb-3"
            />
            <Button
              className="w-full"
              onClick={handleSubmit}
              disabled={!answer.trim() || isSubmitting}
            >
              <Send className="mr-2 h-4 w-4" />
              {isSubmitting ? "Evaluating..." : "Submit Answer"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
