import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import type { InterviewQuestion } from "@/api/types";

interface FeedbackPanelProps {
  question: InterviewQuestion;
}

export function FeedbackPanel({ question }: FeedbackPanelProps) {
  const [showModelAnswer, setShowModelAnswer] = useState(false);
  const score = question.score;

  const scoreColor =
    score >= 0.8
      ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
      : score >= 0.5
        ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
        : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";

  return (
    <Card className="border-l-4 border-l-primary">
      <CardContent className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">
            Question {question.index + 1} — Feedback
          </span>
          <Badge className={cn("text-sm", scoreColor)}>
            {Math.round(score * 100)}%
          </Badge>
        </div>

        {question.user_answer && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Your answer:</p>
            <p className="text-sm bg-muted rounded p-2">{question.user_answer}</p>
          </div>
        )}

        {question.feedback && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Feedback:</p>
            <MarkdownRenderer content={question.feedback} />
          </div>
        )}

        {question.model_answer && (
          <div>
            <button
              onClick={() => setShowModelAnswer(!showModelAnswer)}
              className="flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground"
            >
              {showModelAnswer ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              {showModelAnswer ? "Hide" : "Show"} model answer
            </button>
            {showModelAnswer && (
              <div className="mt-1.5 rounded bg-muted p-3">
                <MarkdownRenderer content={question.model_answer} />
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
