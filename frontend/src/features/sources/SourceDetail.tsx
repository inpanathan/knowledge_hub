import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, RefreshCw, Trash2, ExternalLink, Save } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  getSource,
  updateSource,
  deleteSource,
  reindexSource,
  getSourceOriginalUrl,
  getSourceViewUrl,
} from "@/api/sources";

interface SourceDetailProps {
  sourceId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SourceDetail({ sourceId, open, onOpenChange }: SourceDetailProps) {
  const queryClient = useQueryClient();

  const { data: source, isLoading } = useQuery({
    queryKey: ["source", sourceId],
    queryFn: () => getSource(sourceId!),
    enabled: !!sourceId,
  });

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tagInput, setTagInput] = useState("");
  const [tags, setTags] = useState<string[]>([]);

  useEffect(() => {
    if (source) {
      setTitle(source.title);
      setDescription(source.description);
      setTags(source.tags);
    }
  }, [source]);

  const updateMutation = useMutation({
    mutationFn: () => updateSource(sourceId!, { title, description, tags }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      queryClient.invalidateQueries({ queryKey: ["source", sourceId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteSource(sourceId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      onOpenChange(false);
    },
  });

  const reindexMutation = useMutation({
    mutationFn: () => reindexSource(sourceId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      queryClient.invalidateQueries({ queryKey: ["source", sourceId] });
    },
  });

  const addTag = () => {
    const tag = tagInput.trim();
    if (tag && !tags.includes(tag)) {
      setTags((prev) => [...prev, tag]);
      setTagInput("");
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-auto sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Source Details</SheetTitle>
        </SheetHeader>

        {isLoading || !source ? (
          <div className="space-y-4 pt-6">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-8 w-1/2" />
          </div>
        ) : (
          <div className="space-y-6 pt-6">
            {/* Editable fields */}
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-sm font-medium">Title</label>
                <Input value={title} onChange={(e) => setTitle(e.target.value)} />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Description</label>
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Tags</label>
                <div className="flex gap-2">
                  <Input
                    placeholder="Add tag..."
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addTag())}
                    className="flex-1"
                  />
                  <Button variant="outline" size="sm" onClick={addTag}>
                    Add
                  </Button>
                </div>
                {tags.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {tags.map((tag) => (
                      <Badge
                        key={tag}
                        variant="secondary"
                        className="cursor-pointer"
                        onClick={() => setTags((prev) => prev.filter((t) => t !== tag))}
                      >
                        {tag} &times;
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
              <Button
                onClick={() => updateMutation.mutate()}
                disabled={updateMutation.isPending}
                className="w-full"
              >
                <Save className="mr-2 h-4 w-4" />
                {updateMutation.isPending ? "Saving..." : "Save Changes"}
              </Button>
            </div>

            <Separator />

            {/* Read-only metadata */}
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Type</span>
                <span>{source.source_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Format</span>
                <span className="uppercase">{source.file_format}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Status</span>
                <Badge variant={source.status === "ready" ? "default" : "secondary"}>
                  {source.status}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Chunks</span>
                <span>{source.chunk_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tokens</span>
                <span>{source.total_tokens.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Ingested</span>
                <span>{new Date(source.ingested_at).toLocaleDateString()}</span>
              </div>
              {source.origin && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Origin</span>
                  <span className="max-w-[200px] truncate text-right">{source.origin}</span>
                </div>
              )}
              {source.error_message && (
                <div className="rounded bg-destructive/10 p-2 text-destructive">
                  {source.error_message}
                </div>
              )}
            </div>

            <Separator />

            {/* Actions */}
            <div className="flex flex-col gap-2">
              <Button variant="outline" asChild>
                <a href={getSourceViewUrl(source.id)} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  View Content
                </a>
              </Button>
              <Button variant="outline" asChild>
                <a href={getSourceOriginalUrl(source.id)} download>
                  <Download className="mr-2 h-4 w-4" />
                  Download Original
                </a>
              </Button>
              <Button
                variant="outline"
                onClick={() => reindexMutation.mutate()}
                disabled={reindexMutation.isPending}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                {reindexMutation.isPending ? "Re-indexing..." : "Re-index"}
              </Button>
              <Button
                variant="destructive"
                onClick={() => deleteMutation.mutate()}
                disabled={deleteMutation.isPending}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                {deleteMutation.isPending ? "Deleting..." : "Delete Source"}
              </Button>
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
