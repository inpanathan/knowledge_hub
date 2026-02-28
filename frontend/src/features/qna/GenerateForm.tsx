import { useState } from "react";
import { HelpCircle } from "lucide-react";
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
import type { QnAGenerateRequest } from "@/api/types";

interface GenerateFormProps {
  onGenerate: (data: QnAGenerateRequest) => void;
  isGenerating: boolean;
  error?: string;
}

export function GenerateForm({ onGenerate, isGenerating, error }: GenerateFormProps) {
  const [topic, setTopic] = useState("");
  const [count, setCount] = useState(10);
  const [difficulty, setDifficulty] = useState("intermediate");
  const [sourceIds, setSourceIds] = useState<string[]>([]);

  return (
    <div className="flex h-full items-center justify-center p-6">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <HelpCircle className="mx-auto mb-2 h-10 w-10 text-muted-foreground" />
          <CardTitle>Generate Q&A</CardTitle>
          <p className="text-sm text-muted-foreground">
            Create question-answer pairs from your knowledge base
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Topic</label>
            <Input
              placeholder="e.g., Machine Learning, React, Databases"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium">Count: {count}</label>
              <input
                type="range"
                min={3}
                max={30}
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
                className="w-full accent-primary"
              />
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
              Sources (optional)
            </label>
            <SourceSelector selected={sourceIds} onChange={setSourceIds} />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <Button
            className="w-full"
            disabled={(!topic.trim() && sourceIds.length === 0) || isGenerating}
            onClick={() =>
              onGenerate({
                topic: topic || undefined,
                source_ids: sourceIds.length ? sourceIds : undefined,
                count,
                difficulty,
              })
            }
          >
            {isGenerating ? "Generating..." : "Generate Q&A"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
