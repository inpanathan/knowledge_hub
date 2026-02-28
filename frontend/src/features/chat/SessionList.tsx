import { MessageSquare } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import type { ChatSessionSummary } from "@/api/types";

interface SessionListProps {
  sessions: ChatSessionSummary[];
  activeId?: string;
  onSelect: (id: string) => void;
}

export function SessionList({ sessions, activeId, onSelect }: SessionListProps) {
  if (sessions.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center p-4">
        <p className="text-sm text-muted-foreground">No sessions yet</p>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1">
      <div className="space-y-0.5 p-2">
        {sessions.map((session) => (
          <button
            key={session.id}
            onClick={() => onSelect(session.id)}
            className={cn(
              "flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm transition-colors",
              activeId === session.id
                ? "bg-accent text-accent-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
            )}
          >
            <MessageSquare className="h-4 w-4 shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium">
                Session {session.id.slice(0, 8)}
              </p>
              <p className="text-xs opacity-70">
                {session.message_count} messages
              </p>
            </div>
          </button>
        ))}
      </div>
    </ScrollArea>
  );
}
