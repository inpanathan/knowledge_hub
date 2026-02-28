import { RotateCcw, Trophy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { cn } from "@/lib/utils";
import type { InterviewSummary } from "@/api/types";
import { FeedbackPanel } from "./FeedbackPanel";

interface InterviewSummaryViewProps {
  summary: InterviewSummary;
  onNewSession: () => void;
}

export function InterviewSummaryView({ summary, onNewSession }: InterviewSummaryViewProps) {
  const overallPercent = Math.round(summary.overall_score * 100);
  const scoreColor =
    overallPercent >= 80
      ? "text-green-600 dark:text-green-400"
      : overallPercent >= 50
        ? "text-yellow-600 dark:text-yellow-400"
        : "text-red-600 dark:text-red-400";

  return (
    <div className="flex h-full flex-col overflow-auto">
      <div className="border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold">Interview Summary</h1>
          <Button variant="outline" onClick={onNewSession}>
            <RotateCcw className="mr-2 h-4 w-4" />
            New Session
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-2xl space-y-6">
          {/* Score card */}
          <Card>
            <CardContent className="flex items-center gap-4 p-6">
              <Trophy className={cn("h-10 w-10", scoreColor)} />
              <div>
                <p className={cn("text-3xl font-bold", scoreColor)}>
                  {overallPercent}%
                </p>
                <p className="text-sm text-muted-foreground">{summary.topic}</p>
              </div>
            </CardContent>
          </Card>

          {/* Overall feedback */}
          {summary.overall_feedback && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Overall Feedback</CardTitle>
              </CardHeader>
              <CardContent>
                <MarkdownRenderer content={summary.overall_feedback} />
              </CardContent>
            </Card>
          )}

          <Separator />

          {/* Individual questions */}
          <div className="space-y-4">
            <h2 className="text-sm font-semibold">Question Breakdown</h2>
            {summary.questions.map((q) => (
              <FeedbackPanel key={q.index} question={q} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
