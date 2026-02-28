import { ArrowLeft, Download, List, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import type { QASet } from "@/api/types";
import { FlashCard } from "./FlashCard";

interface QASetViewProps {
  qaSet: QASet;
  onBack: () => void;
  onExport: (format: "json" | "markdown") => void;
  isExporting: boolean;
}

export function QASetView({ qaSet, onBack, onExport, isExporting }: QASetViewProps) {
  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-6 py-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-lg font-semibold">{qaSet.topic}</h1>
            <div className="flex gap-2 mt-1">
              <Badge variant="outline">{qaSet.pairs.length} questions</Badge>
              <Badge variant="outline">{qaSet.difficulty}</Badge>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onExport("json")}
            disabled={isExporting}
          >
            <Download className="mr-1.5 h-4 w-4" />
            JSON
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onExport("markdown")}
            disabled={isExporting}
          >
            <Download className="mr-1.5 h-4 w-4" />
            Markdown
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        <Tabs defaultValue="list" className="mx-auto max-w-2xl">
          <TabsList className="mb-4">
            <TabsTrigger value="list">
              <List className="mr-1.5 h-4 w-4" />
              List
            </TabsTrigger>
            <TabsTrigger value="flashcard">
              <Layers className="mr-1.5 h-4 w-4" />
              Flashcards
            </TabsTrigger>
          </TabsList>

          <TabsContent value="list" className="space-y-4">
            {qaSet.pairs.map((pair, i) => (
              <Card key={i}>
                <CardContent className="p-4 space-y-2">
                  <div className="flex items-start gap-2">
                    <Badge variant="outline" className="shrink-0">
                      Q{i + 1}
                    </Badge>
                    <p className="text-sm font-medium">{pair.question}</p>
                  </div>
                  <div className="pl-8">
                    <MarkdownRenderer content={pair.answer} />
                    {pair.source_title && (
                      <p className="mt-1 text-xs text-muted-foreground">
                        Source: {pair.source_title}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="flashcard">
            <FlashCard pairs={qaSet.pairs} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
