import { useState } from "react";
import { ChevronLeft, ChevronRight, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import type { QAPair } from "@/api/types";

interface FlashCardProps {
  pairs: QAPair[];
}

export function FlashCard({ pairs }: FlashCardProps) {
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);

  const pair = pairs[index];
  if (!pair) return null;

  const goNext = () => {
    setFlipped(false);
    setIndex((prev) => Math.min(prev + 1, pairs.length - 1));
  };

  const goPrev = () => {
    setFlipped(false);
    setIndex((prev) => Math.max(prev - 1, 0));
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Badge variant="outline">
          {index + 1} / {pairs.length}
        </Badge>
        <Button variant="ghost" size="sm" onClick={() => setFlipped(!flipped)}>
          <RotateCcw className="mr-1.5 h-4 w-4" />
          {flipped ? "Show Question" : "Show Answer"}
        </Button>
      </div>

      <Card
        className="min-h-[200px] cursor-pointer transition-all hover:shadow-md"
        onClick={() => setFlipped(!flipped)}
      >
        <CardContent className="flex items-center justify-center p-8">
          {flipped ? (
            <div className="text-center">
              <p className="mb-2 text-xs font-medium text-muted-foreground">Answer</p>
              <MarkdownRenderer content={pair.answer} />
            </div>
          ) : (
            <div className="text-center">
              <p className="mb-2 text-xs font-medium text-muted-foreground">Question</p>
              <p className="text-lg">{pair.question}</p>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={goPrev} disabled={index === 0}>
          <ChevronLeft className="mr-1 h-4 w-4" />
          Previous
        </Button>
        <Button variant="outline" onClick={goNext} disabled={index === pairs.length - 1}>
          Next
          <ChevronRight className="ml-1 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
