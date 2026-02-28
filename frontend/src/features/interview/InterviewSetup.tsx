import { useState } from "react";
import { GraduationCap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SourceSelector } from "@/components/shared/SourceSelector";
import type { InterviewStartRequest } from "@/api/types";

interface InterviewSetupProps {
  onStart: (data: InterviewStartRequest) => void;
  isStarting: boolean;
}

export function InterviewSetup({ onStart, isStarting }: InterviewSetupProps) {
  const [topic, setTopic] = useState("");
  const [mode, setMode] = useState("mixed");
  const [difficulty, setDifficulty] = useState("intermediate");
  const [questionCount, setQuestionCount] = useState(10);
  const [sourceIds, setSourceIds] = useState<string[]>([]);

  return (
    <div className="flex h-full items-center justify-center p-6">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <GraduationCap className="mx-auto mb-2 h-10 w-10 text-muted-foreground" />
          <CardTitle>Interview Preparation</CardTitle>
          <p className="text-sm text-muted-foreground">
            Practice with AI-generated questions based on your knowledge base
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Topic</label>
            <Input
              placeholder="e.g., React hooks, System design, Python async"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium">Mode</label>
              <Select value={mode} onValueChange={setMode}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="mixed">Mixed</SelectItem>
                  <SelectItem value="conceptual">Conceptual</SelectItem>
                  <SelectItem value="practical">Practical</SelectItem>
                  <SelectItem value="behavioral">Behavioral</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Difficulty</label>
              <Select value={difficulty} onValueChange={setDifficulty}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="beginner">Beginner</SelectItem>
                  <SelectItem value="intermediate">Intermediate</SelectItem>
                  <SelectItem value="advanced">Advanced</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">
              Questions: {questionCount}
            </label>
            <input
              type="range"
              min={3}
              max={20}
              value={questionCount}
              onChange={(e) => setQuestionCount(Number(e.target.value))}
              className="w-full accent-primary"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">
              Sources (optional)
            </label>
            <SourceSelector selected={sourceIds} onChange={setSourceIds} />
          </div>

          <Button
            className="w-full"
            disabled={!topic.trim() || isStarting}
            onClick={() =>
              onStart({
                topic,
                mode,
                difficulty,
                question_count: questionCount,
                source_ids: sourceIds.length ? sourceIds : undefined,
              })
            }
          >
            {isStarting ? "Starting..." : "Start Interview"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
