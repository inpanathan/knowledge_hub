import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { listSources } from "@/api/sources";

interface SourceSelectorProps {
  selected: string[];
  onChange: (ids: string[]) => void;
  className?: string;
}

export function SourceSelector({ selected, onChange, className }: SourceSelectorProps) {
  const [search, setSearch] = useState("");

  const { data } = useQuery({
    queryKey: ["sources", "selector"],
    queryFn: () => listSources(),
  });

  const sources = data?.sources ?? [];
  const filtered = sources.filter((s) =>
    s.title.toLowerCase().includes(search.toLowerCase()),
  );

  const toggle = (id: string) => {
    onChange(
      selected.includes(id)
        ? selected.filter((s) => s !== id)
        : [...selected, id],
    );
  };

  const selectedTitles = sources
    .filter((s) => selected.includes(s.id))
    .map((s) => s.title);

  return (
    <div className={cn("space-y-2", className)}>
      {/* Selected badges */}
      {selectedTitles.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {selectedTitles.map((title, i) => (
            <Badge key={selected[i]} variant="secondary" className="gap-1">
              {title}
              <button onClick={() => toggle(selected[i])} className="ml-0.5">
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
          <Button
            variant="ghost"
            size="sm"
            className="h-5 text-xs"
            onClick={() => onChange([])}
          >
            Clear all
          </Button>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search sources..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-8"
        />
      </div>

      {/* List */}
      <ScrollArea className="h-48 rounded-md border">
        <div className="p-1">
          {filtered.map((source) => (
            <button
              key={source.id}
              onClick={() => toggle(source.id)}
              className={cn(
                "flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-accent",
                selected.includes(source.id) && "bg-accent",
              )}
            >
              <div
                className={cn(
                  "flex h-4 w-4 shrink-0 items-center justify-center rounded-sm border",
                  selected.includes(source.id)
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-muted-foreground/25",
                )}
              >
                {selected.includes(source.id) && <Check className="h-3 w-3" />}
              </div>
              <span className="truncate">{source.title}</span>
              <Badge variant="outline" className="ml-auto shrink-0 text-xs">
                {source.file_format}
              </Badge>
            </button>
          ))}
          {filtered.length === 0 && (
            <p className="py-4 text-center text-sm text-muted-foreground">No sources found</p>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
