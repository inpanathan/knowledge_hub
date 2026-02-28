import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { FileText, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState } from "@/components/shared/EmptyState";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { SourceSelector } from "@/components/shared/SourceSelector";
import { summarize } from "@/api/summarize";
import type { SummarizeResponse } from "@/api/types";

export function SummarizePage() {
  const [mode, setMode] = useState<"short" | "detailed">("short");
  const [topic, setTopic] = useState("");
  const [sourceIds, setSourceIds] = useState<string[]>([]);
  const [inputMode, setInputMode] = useState<"sources" | "topic">("sources");
  const [result, setResult] = useState<SummarizeResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const mutation = useMutation({
    mutationFn: summarize,
    onSuccess: (data) => setResult(data),
  });

  const handleSummarize = () => {
    mutation.mutate({
      source_ids: inputMode === "sources" && sourceIds.length ? sourceIds : undefined,
      topic: inputMode === "topic" && topic.trim() ? topic.trim() : undefined,
      mode,
    });
  };

  const handleCopy = async () => {
    if (!result) return;
    await navigator.clipboard.writeText(result.summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const canSubmit =
    (inputMode === "sources" && sourceIds.length > 0) ||
    (inputMode === "topic" && topic.trim().length > 0);

  return (
    <div className="flex h-full flex-col">
      <div className="border-b px-6 py-4">
        <h1 className="text-lg font-semibold">Summarize</h1>
        <p className="text-sm text-muted-foreground">
          Generate summaries from your knowledge base
        </p>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-2xl space-y-6">
          {/* Input form */}
          <Card>
            <CardContent className="p-6 space-y-4">
              <Tabs
                value={inputMode}
                onValueChange={(v) => setInputMode(v as "sources" | "topic")}
              >
                <TabsList className="mb-3">
                  <TabsTrigger value="sources">By Sources</TabsTrigger>
                  <TabsTrigger value="topic">By Topic</TabsTrigger>
                </TabsList>

                <TabsContent value="sources">
                  <SourceSelector selected={sourceIds} onChange={setSourceIds} />
                </TabsContent>

                <TabsContent value="topic">
                  <Input
                    placeholder="Enter a topic to summarize..."
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                  />
                </TabsContent>
              </Tabs>

              {/* Mode toggle */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Mode:</span>
                <Button
                  variant={mode === "short" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setMode("short")}
                >
                  Short
                </Button>
                <Button
                  variant={mode === "detailed" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setMode("detailed")}
                >
                  Detailed
                </Button>
              </div>

              <Button
                className="w-full"
                disabled={!canSubmit || mutation.isPending}
                onClick={handleSummarize}
              >
                {mutation.isPending ? "Summarizing..." : "Generate Summary"}
              </Button>

              {mutation.isError && (
                <p className="text-sm text-destructive">
                  {mutation.error?.message ?? "Failed to generate summary"}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Result */}
          {result ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">Summary</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{result.mode}</Badge>
                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleCopy}>
                      {copied ? (
                        <Check className="h-4 w-4 text-green-600" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <MarkdownRenderer content={result.summary} />
                {result.source_titles.length > 0 && (
                  <div className="mt-4 border-t pt-3">
                    <p className="text-xs font-medium text-muted-foreground mb-1">Sources</p>
                    <div className="flex flex-wrap gap-1">
                      {result.source_titles.map((title, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          {title}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            !mutation.isPending && (
              <EmptyState
                icon={FileText}
                title="No summary yet"
                description="Select sources or enter a topic to generate a summary."
              />
            )
          )}
        </div>
      </div>
    </div>
  );
}
