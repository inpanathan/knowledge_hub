import { FileText, Globe, Type, Folder, MoreVertical, RefreshCw, Trash2, Download } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import type { SourceSummary } from "@/api/types";
import { deleteSource, reindexSource, getSourceOriginalUrl } from "@/api/sources";

interface SourceCardProps {
  source: SourceSummary;
  onClick: () => void;
}

const typeIcons: Record<string, typeof FileText> = {
  file: FileText,
  url: Globe,
  text: Type,
  folder: Folder,
};

const statusColors: Record<string, string> = {
  ready: "bg-green-500",
  processing: "bg-yellow-500",
  error: "bg-red-500",
};

export function SourceCard({ source, onClick }: SourceCardProps) {
  const queryClient = useQueryClient();
  const Icon = typeIcons[source.source_type] ?? FileText;

  const deleteMutation = useMutation({
    mutationFn: () => deleteSource(source.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sources"] }),
  });

  const reindexMutation = useMutation({
    mutationFn: () => reindexSource(source.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sources"] }),
  });

  return (
    <Card
      className="cursor-pointer transition-shadow hover:shadow-md"
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Icon className="h-5 w-5 text-muted-foreground" />
            <div
              className={cn("h-2 w-2 rounded-full", statusColors[source.status] ?? "bg-gray-400")}
            />
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
              <Button variant="ghost" size="icon" className="h-7 w-7">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
              <DropdownMenuItem onClick={() => reindexMutation.mutate()}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Re-index
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <a href={getSourceOriginalUrl(source.id)} download>
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </a>
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-destructive"
                onClick={() => deleteMutation.mutate()}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <h3 className="mt-3 truncate text-sm font-medium">{source.title}</h3>

        <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
          <span className="uppercase">{source.file_format}</span>
          <span>&middot;</span>
          <span>{source.chunk_count} chunks</span>
        </div>

        {source.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {source.tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
            {source.tags.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{source.tags.length - 3}
              </Badge>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
