import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { FileText, Copy, Check, BookOpen, ChevronDown, ChevronRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState } from "@/components/shared/EmptyState";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { SourceSelector } from "@/components/shared/SourceSelector";
import { summarize } from "@/api/summarize";
import { listBooks, summarizeBook } from "@/api/books";
import type { SummarizeResponse, BookSummarizeResponse } from "@/api/types";

export function SummarizePage() {
  const [mode, setMode] = useState<"short" | "detailed">("short");
  const [topic, setTopic] = useState("");
  const [sourceIds, setSourceIds] = useState<string[]>([]);
  const [inputMode, setInputMode] = useState<"sources" | "topic" | "book">("sources");
  const [result, setResult] = useState<SummarizeResponse | null>(null);
  const [copied, setCopied] = useState(false);

  // Book summarization state
  const [selectedBookId, setSelectedBookId] = useState("");
  const [bookResult, setBookResult] = useState<BookSummarizeResponse | null>(null);
  const [expandedChapters, setExpandedChapters] = useState<Set<number>>(new Set());

  const { data: bookList } = useQuery({
    queryKey: ["books", "embedded"],
    queryFn: () => listBooks({ embedding_status: "completed", limit: 200 }),
    enabled: inputMode === "book",
  });

  const mutation = useMutation({
    mutationFn: summarize,
    onSuccess: (data) => setResult(data),
  });

  const bookMutation = useMutation({
    mutationFn: () => summarizeBook(selectedBookId, "detailed"),
    onSuccess: (data) => setBookResult(data),
  });

  const handleSummarize = () => {
    if (inputMode === "book") {
      bookMutation.mutate();
      return;
    }
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

  const toggleChapter = (chapterNum: number) => {
    setExpandedChapters((prev) => {
      const next = new Set(prev);
      if (next.has(chapterNum)) next.delete(chapterNum);
      else next.add(chapterNum);
      return next;
    });
  };

  const canSubmit =
    (inputMode === "sources" && sourceIds.length > 0) ||
    (inputMode === "topic" && topic.trim().length > 0) ||
    (inputMode === "book" && selectedBookId.length > 0);

  const isPending = mutation.isPending || bookMutation.isPending;

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
                onValueChange={(v) => setInputMode(v as "sources" | "topic" | "book")}
              >
                <TabsList className="mb-3">
                  <TabsTrigger value="sources">By Sources</TabsTrigger>
                  <TabsTrigger value="topic">By Topic</TabsTrigger>
                  <TabsTrigger value="book">By Book</TabsTrigger>
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

                <TabsContent value="book">
                  <select
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={selectedBookId}
                    onChange={(e) => {
                      setSelectedBookId(e.target.value);
                      setBookResult(null);
                      setExpandedChapters(new Set());
                    }}
                  >
                    <option value="">Select an embedded book...</option>
                    {bookList?.books.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.title} — {b.author}
                      </option>
                    ))}
                  </select>
                </TabsContent>
              </Tabs>

              {/* Mode toggle (not shown for book mode — always detailed) */}
              {inputMode !== "book" && (
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
              )}

              <Button
                className="w-full"
                disabled={!canSubmit || isPending}
                onClick={handleSummarize}
              >
                {isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {inputMode === "book"
                      ? "Summarizing book... (this may take a minute)"
                      : "Summarizing..."}
                  </>
                ) : (
                  <>
                    {inputMode === "book" && <BookOpen className="mr-2 h-4 w-4" />}
                    Generate Summary
                  </>
                )}
              </Button>

              {mutation.isError && (
                <p className="text-sm text-destructive">
                  {mutation.error?.message ?? "Failed to generate summary"}
                </p>
              )}
              {bookMutation.isError && (
                <p className="text-sm text-destructive">
                  {bookMutation.error?.message ?? "Failed to summarize book"}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Book result */}
          {inputMode === "book" && bookResult ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">
                    {bookResult.book_title}
                    {bookResult.author && (
                      <span className="ml-1 font-normal text-muted-foreground">
                        by {bookResult.author}
                      </span>
                    )}
                  </CardTitle>
                  <Badge variant="outline">detailed</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="mb-2 text-sm font-medium">Overall Summary</h4>
                  <MarkdownRenderer content={bookResult.overall_summary} />
                </div>

                {bookResult.chapters.length > 0 && (
                  <div>
                    <h4 className="mb-2 text-sm font-medium">
                      Chapter Summaries ({bookResult.chapters.length})
                    </h4>
                    <div className="space-y-1">
                      {bookResult.chapters.map((ch) => (
                        <div key={ch.chapter_number} className="rounded-md border">
                          <button
                            type="button"
                            className="flex w-full items-center gap-2 p-2 text-left text-sm hover:bg-muted/50"
                            onClick={() => toggleChapter(ch.chapter_number)}
                          >
                            {expandedChapters.has(ch.chapter_number) ? (
                              <ChevronDown className="h-3 w-3 shrink-0" />
                            ) : (
                              <ChevronRight className="h-3 w-3 shrink-0" />
                            )}
                            <span className="font-medium truncate">{ch.chapter_title}</span>
                            <Badge
                              variant="secondary"
                              className="ml-auto shrink-0 text-[10px]"
                            >
                              {ch.chunk_count} chunks
                            </Badge>
                          </button>
                          {expandedChapters.has(ch.chapter_number) && (
                            <div className="border-t p-3 text-sm">
                              <MarkdownRenderer content={ch.summary} />
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <p className="text-xs text-muted-foreground">
                  Processed {bookResult.total_chunks_processed} chunks in{" "}
                  {bookResult.total_llm_calls} LLM calls
                </p>
              </CardContent>
            </Card>
          ) : inputMode !== "book" && result ? (
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
            !isPending && (
              <EmptyState
                icon={FileText}
                title="No summary yet"
                description="Select sources, enter a topic, or choose a book to generate a summary."
              />
            )
          )}
        </div>
      </div>
    </div>
  );
}
