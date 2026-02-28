import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MessageSquare, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import { sendMessage, listSessions, getSession } from "@/api/chat";
import type { ChatMessage as ChatMessageType } from "@/api/types";
import { ChatInput } from "./ChatInput";
import { ChatMessageItem } from "./ChatMessage";
import { SessionList } from "./SessionList";

export function ChatPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>(sessionId);

  const { data: sessions } = useQuery({
    queryKey: ["chat-sessions"],
    queryFn: listSessions,
  });

  const { data: session, isLoading: sessionLoading } = useQuery({
    queryKey: ["chat-session", activeSessionId],
    queryFn: () => getSession(activeSessionId!),
    enabled: !!activeSessionId,
  });

  // Sync session messages
  useEffect(() => {
    if (session?.messages) {
      setMessages(session.messages);
    }
  }, [session]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMutation = useMutation({
    mutationFn: sendMessage,
    onSuccess: (data) => {
      setActiveSessionId(data.session_id);
      navigate(`/chat/${data.session_id}`, { replace: true });

      // Add assistant message
      const assistantMsg: ChatMessageType = {
        role: "assistant",
        content: data.answer,
        timestamp: new Date().toISOString(),
        citations: data.citations,
      };
      setMessages((prev) => [...prev, assistantMsg]);
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
    },
  });

  const handleSend = useCallback(
    (text: string) => {
      // Add user message immediately
      const userMsg: ChatMessageType = {
        role: "user",
        content: text,
        timestamp: new Date().toISOString(),
        citations: [],
      };
      setMessages((prev) => [...prev, userMsg]);

      sendMutation.mutate({
        message: text,
        session_id: activeSessionId,
      });
    },
    [activeSessionId, sendMutation],
  );

  const handleNewChat = useCallback(() => {
    setMessages([]);
    setActiveSessionId(undefined);
    navigate("/chat", { replace: true });
  }, [navigate]);

  const handleSelectSession = useCallback(
    (id: string) => {
      setActiveSessionId(id);
      navigate(`/chat/${id}`, { replace: true });
    },
    [navigate],
  );

  return (
    <div className="flex h-full">
      {/* Session sidebar */}
      <div className="hidden w-64 flex-col border-r md:flex">
        <div className="flex h-14 items-center justify-between border-b px-3">
          <span className="text-sm font-medium">Sessions</span>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleNewChat}>
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        <SessionList
          sessions={sessions ?? []}
          activeId={activeSessionId}
          onSelect={handleSelectSession}
        />
      </div>

      {/* Main chat area */}
      <div className="flex flex-1 flex-col">
        {messages.length === 0 && !sessionLoading ? (
          <div className="flex flex-1 items-center justify-center">
            <EmptyState
              icon={MessageSquare}
              title="Ask anything about your knowledge base"
              description="Start a conversation to search, analyze, and learn from your uploaded documents."
              action={
                <Button variant="outline" className="mt-2" onClick={() => navigate("/sources")}>
                  Upload sources first
                </Button>
              }
            />
          </div>
        ) : (
          <ScrollArea className="flex-1 px-4 py-6">
            <div className="mx-auto max-w-3xl space-y-6">
              {sessionLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="space-y-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-20 w-full" />
                  </div>
                ))
              ) : (
                messages.map((msg, i) => (
                  <ChatMessageItem key={i} message={msg} />
                ))
              )}
              {sendMutation.isPending && (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        )}

        <Separator />

        {/* Input */}
        <div className="mx-auto w-full max-w-3xl px-4 py-4">
          <ChatInput
            onSend={handleSend}
            disabled={sendMutation.isPending}
            placeholder={
              messages.length === 0
                ? "Ask a question about your documents..."
                : "Continue the conversation..."
            }
          />
          {sendMutation.isError && (
            <p className="mt-2 text-sm text-destructive">
              Failed to send message. Please try again.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
