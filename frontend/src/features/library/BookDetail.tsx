import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, Trash2, Save } from "lucide-react";
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
import { ScrollArea } from "@/components/ui/scroll-area";
import { getBook, updateBook, deleteBook, getBookDownloadUrl, getBookCoverUrl } from "@/api/books";

interface BookDetailProps {
  bookId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function BookDetail({ bookId, open, onOpenChange }: BookDetailProps) {
  const queryClient = useQueryClient();

  const { data: book, isLoading } = useQuery({
    queryKey: ["book", bookId],
    queryFn: () => getBook(bookId!),
    enabled: !!bookId,
  });

  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [description, setDescription] = useState("");
  const [tagInput, setTagInput] = useState("");
  const [tags, setTags] = useState<string[]>([]);

  useEffect(() => {
    if (book) {
      setTitle(book.title);
      setAuthor(book.author);
      setDescription(book.description);
      setTags(book.tags);
    }
  }, [book]);

  const updateMutation = useMutation({
    mutationFn: () => updateBook(bookId!, { title, author, description, tags }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["books"] });
      queryClient.invalidateQueries({ queryKey: ["book", bookId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteBook(bookId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["books"] });
      onOpenChange(false);
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
          <SheetTitle>Book Details</SheetTitle>
        </SheetHeader>

        {isLoading || !book ? (
          <div className="space-y-4 pt-6">
            <Skeleton className="h-48 w-full rounded-lg" />
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-20 w-full" />
          </div>
        ) : (
          <div className="space-y-6 pt-6">
            {/* Cover image */}
            {book.cover_image_path && (
              <div className="overflow-hidden rounded-lg">
                <img
                  src={getBookCoverUrl(book.id)}
                  alt={book.title}
                  className="w-full object-contain max-h-64"
                />
              </div>
            )}

            {/* Editable fields */}
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-sm font-medium">Title</label>
                <Input value={title} onChange={(e) => setTitle(e.target.value)} />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Author</label>
                <Input value={author} onChange={(e) => setAuthor(e.target.value)} />
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
                <span className="text-muted-foreground">Format</span>
                <span className="uppercase">{book.file_format}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">File Size</span>
                <span>{formatBytes(book.file_size_bytes)}</span>
              </div>
              {book.page_count && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Pages</span>
                  <span>{book.page_count}</span>
                </div>
              )}
              {book.isbn && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">ISBN</span>
                  <span>{book.isbn}</span>
                </div>
              )}
              {book.publisher && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Publisher</span>
                  <span className="max-w-[200px] truncate text-right">{book.publisher}</span>
                </div>
              )}
              {book.publication_year && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Year</span>
                  <span>{book.publication_year}</span>
                </div>
              )}
              {book.language && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Language</span>
                  <span>{book.language}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Embeddings</span>
                <Badge variant={book.embedding_status === "completed" ? "default" : "secondary"}>
                  {book.embedding_status}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Added</span>
                <span>{new Date(book.created_at).toLocaleDateString()}</span>
              </div>
            </div>

            {/* Table of Contents */}
            {book.table_of_contents.length > 0 && (
              <>
                <Separator />
                <div>
                  <h4 className="mb-2 text-sm font-medium">Table of Contents</h4>
                  <ScrollArea className="h-48">
                    <ul className="space-y-1 text-sm text-muted-foreground">
                      {book.table_of_contents.map((entry, i) => (
                        <li key={i} className="truncate">
                          {entry}
                        </li>
                      ))}
                    </ul>
                  </ScrollArea>
                </div>
              </>
            )}

            <Separator />

            {/* Actions */}
            <div className="flex flex-col gap-2">
              <Button variant="outline" asChild>
                <a href={getBookDownloadUrl(book.id)} download>
                  <Download className="mr-2 h-4 w-4" />
                  Download Book
                </a>
              </Button>
              <Button
                variant="destructive"
                onClick={() => deleteMutation.mutate()}
                disabled={deleteMutation.isPending}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                {deleteMutation.isPending ? "Deleting..." : "Delete Book"}
              </Button>
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
