import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronDown, ChevronUp, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Citation } from "@/api/types";

interface CitationCardProps {
  citation: Citation;
  index: number;
}

export function CitationCard({ citation, index }: CitationCardProps) {
  const [expanded, setExpanded] = useState(false);
  const navigate = useNavigate();

  const scorePercent = Math.round(citation.relevance_score * 100);
  const scoreColor =
    scorePercent >= 80
      ? "text-green-600 dark:text-green-400"
      : scorePercent >= 60
        ? "text-yellow-600 dark:text-yellow-400"
        : "text-muted-foreground";

  return (
    <div className="w-full max-w-sm rounded-md border bg-card p-2.5 text-sm">
      <div className="flex items-start gap-2">
        <Badge variant="outline" className="shrink-0 text-xs">
          {index}
        </Badge>
        <button
          className="flex-1 text-left font-medium hover:underline"
          onClick={() => navigate(`/sources`)}
        >
          <FileText className="mr-1 inline h-3.5 w-3.5" />
          {citation.source_title}
        </button>
        <span className={cn("shrink-0 text-xs font-medium", scoreColor)}>
          {scorePercent}%
        </span>
      </div>

      {citation.chunk_text && (
        <button
          className="mt-1.5 flex w-full items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? (
            <ChevronUp className="h-3 w-3" />
          ) : (
            <ChevronDown className="h-3 w-3" />
          )}
          {expanded ? "Hide" : "Show"} source text
        </button>
      )}

      {expanded && (
        <p className="mt-1.5 rounded bg-muted p-2 text-xs text-muted-foreground line-clamp-6">
          {citation.chunk_text}
        </p>
      )}
    </div>
  );
}
