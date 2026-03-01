import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import { listBooks } from "@/api/books";
import { BookCard } from "./BookCard";
import { BookDetail } from "./BookDetail";

export function LibraryPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["books", search, statusFilter],
    queryFn: () =>
      listBooks({
        search: search || undefined,
        embedding_status: statusFilter === "all" ? undefined : statusFilter,
      }),
  });

  const books = data?.books ?? [];

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-6 py-4">
        <div>
          <h1 className="text-lg font-semibold">Library</h1>
          <p className="text-sm text-muted-foreground">
            Browse and manage your book collection
          </p>
        </div>
        {data && (
          <span className="text-sm text-muted-foreground">
            {data.total} {data.total === 1 ? "book" : "books"}
          </span>
        )}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 border-b px-6 py-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by title or author..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Embedding status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="processing">Processing</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-auto p-6">
        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-72 rounded-lg" />
            ))}
          </div>
        ) : books.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No books yet"
            description="Run the book seeding script to download and catalog books from Google Drive."
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {books.map((book) => (
              <BookCard
                key={book.id}
                book={book}
                onClick={() => setSelectedId(book.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Book detail sheet */}
      <BookDetail
        bookId={selectedId}
        open={!!selectedId}
        onOpenChange={(open) => !open && setSelectedId(null)}
      />
    </div>
  );
}
