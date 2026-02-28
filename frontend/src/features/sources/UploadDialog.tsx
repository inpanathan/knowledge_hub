import { useCallback, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, Globe, Type, FileUp } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { uploadFile, ingestUrl, ingestText } from "@/api/sources";

interface UploadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UploadDialog({ open, onOpenChange }: UploadDialogProps) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // File upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);

  // URL state
  const [url, setUrl] = useState("");
  const [urlTitle, setUrlTitle] = useState("");

  // Text state
  const [textContent, setTextContent] = useState("");
  const [textTitle, setTextTitle] = useState("");

  // Tags (shared)
  const [tagInput, setTagInput] = useState("");
  const [tags, setTags] = useState<string[]>([]);

  const addTag = useCallback(() => {
    const tag = tagInput.trim();
    if (tag && !tags.includes(tag)) {
      setTags((prev) => [...prev, tag]);
      setTagInput("");
    }
  }, [tagInput, tags]);

  const resetForm = useCallback(() => {
    setSelectedFile(null);
    setUrl("");
    setUrlTitle("");
    setTextContent("");
    setTextTitle("");
    setTags([]);
    setTagInput("");
  }, []);

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["sources"] });
    resetForm();
    onOpenChange(false);
  }, [queryClient, onOpenChange, resetForm]);

  const fileMutation = useMutation({
    mutationFn: () => uploadFile(selectedFile!, tags.length ? tags : undefined),
    onSuccess,
  });

  const urlMutation = useMutation({
    mutationFn: () =>
      ingestUrl({ url, title: urlTitle || undefined, tags: tags.length ? tags : undefined }),
    onSuccess,
  });

  const textMutation = useMutation({
    mutationFn: () =>
      ingestText({
        content: textContent,
        title: textTitle || undefined,
        tags: tags.length ? tags : undefined,
      }),
    onSuccess,
  });

  const isLoading = fileMutation.isPending || urlMutation.isPending || textMutation.isPending;

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file) setSelectedFile(file);
  }, []);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Add Source</DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="file">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="file">
              <FileUp className="mr-1.5 h-4 w-4" />
              Upload
            </TabsTrigger>
            <TabsTrigger value="url">
              <Globe className="mr-1.5 h-4 w-4" />
              URL
            </TabsTrigger>
            <TabsTrigger value="text">
              <Type className="mr-1.5 h-4 w-4" />
              Text
            </TabsTrigger>
          </TabsList>

          {/* File upload */}
          <TabsContent value="file" className="space-y-4">
            <div
              className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
                dragActive
                  ? "border-primary bg-primary/5"
                  : "border-muted-foreground/25 hover:border-primary/50"
              }`}
              onDragOver={(e) => {
                e.preventDefault();
                setDragActive(true);
              }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="mb-2 h-8 w-8 text-muted-foreground" />
              {selectedFile ? (
                <p className="text-sm font-medium">{selectedFile.name}</p>
              ) : (
                <>
                  <p className="text-sm font-medium">Drop file here or click to browse</p>
                  <p className="text-xs text-muted-foreground">PDF, DOCX, TXT, MD</p>
                </>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt,.md"
                className="hidden"
                onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
              />
            </div>
            <Button
              className="w-full"
              disabled={!selectedFile || isLoading}
              onClick={() => fileMutation.mutate()}
            >
              {fileMutation.isPending ? "Uploading..." : "Upload"}
            </Button>
          </TabsContent>

          {/* URL */}
          <TabsContent value="url" className="space-y-4">
            <Input
              placeholder="https://example.com/article"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <Input
              placeholder="Title (optional)"
              value={urlTitle}
              onChange={(e) => setUrlTitle(e.target.value)}
            />
            <Button
              className="w-full"
              disabled={!url.trim() || isLoading}
              onClick={() => urlMutation.mutate()}
            >
              {urlMutation.isPending ? "Ingesting..." : "Ingest URL"}
            </Button>
          </TabsContent>

          {/* Text */}
          <TabsContent value="text" className="space-y-4">
            <Input
              placeholder="Title (optional)"
              value={textTitle}
              onChange={(e) => setTextTitle(e.target.value)}
            />
            <Textarea
              placeholder="Paste your text content here..."
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              rows={6}
            />
            <Button
              className="w-full"
              disabled={!textContent.trim() || isLoading}
              onClick={() => textMutation.mutate()}
            >
              {textMutation.isPending ? "Ingesting..." : "Add Text"}
            </Button>
          </TabsContent>
        </Tabs>

        {/* Shared tags */}
        <div className="space-y-2 border-t pt-3">
          <p className="text-sm font-medium">Tags</p>
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
            <div className="flex flex-wrap gap-1">
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

        {/* Error display */}
        {(fileMutation.isError || urlMutation.isError || textMutation.isError) && (
          <p className="text-sm text-destructive">
            {(fileMutation.error ?? urlMutation.error ?? textMutation.error)?.message ??
              "An error occurred"}
          </p>
        )}
      </DialogContent>
    </Dialog>
  );
}
