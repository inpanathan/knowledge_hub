import { User, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import type { ChatMessage } from "@/api/types";
import { CitationCard } from "./CitationCard";

interface ChatMessageItemProps {
  message: ChatMessage;
}

export function ChatMessageItem({ message }: ChatMessageItemProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-primary text-primary-foreground" : "bg-muted",
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Content */}
      <div className={cn("flex-1 space-y-2", isUser && "text-right")}>
        <div
          className={cn(
            "inline-block rounded-lg px-4 py-2.5 text-left",
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-muted",
          )}
        >
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          ) : (
            <MarkdownRenderer content={message.content} />
          )}
        </div>

        {/* Citations */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {message.citations.map((citation, i) => (
              <CitationCard key={i} citation={citation} index={i + 1} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
