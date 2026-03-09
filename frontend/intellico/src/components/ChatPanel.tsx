"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, MessageSquare } from "lucide-react";
import { askQuestion } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import type { ChatMessage } from "@/types";
import { toast } from "sonner";

export function ChatPanel({ paperId }: { paperId: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: q,
    };
    setMessages((m) => [...m, userMsg]);
    setLoading(true);
    try {
      const res = await askQuestion(paperId, q);
      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: res.answer,
        numChunks: res.num_chunks_used,
      };
      setMessages((m) => [...m, assistantMsg]);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to get answer.");
      setMessages((m) => m.filter((msg) => msg.id !== userMsg.id));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto bg-[var(--background)] px-6 py-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--primary)]/10 text-[var(--primary)]">
              <MessageSquare className="h-6 w-6" />
            </div>
            <p className="mt-4 text-sm text-[var(--muted-foreground)]">
              Ask questions about this paper. Answers are grounded via RAG.
            </p>
          </div>
        )}
        <div className="mx-auto max-w-2xl space-y-6">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                    : "bg-white text-[var(--foreground)] shadow-sm"
                }`}
              >
                <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                {msg.role === "assistant" && msg.numChunks != null && (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-xs text-[var(--muted-foreground)]">
                      Sources
                    </summary>
                    <p className="mt-1 text-xs text-[var(--muted-foreground)]">
                      Grounded in uploaded paper via RAG ({msg.numChunks} chunks used)
                    </p>
                  </details>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-2xl bg-white px-4 py-3 shadow-sm">
                <Loader2 className="h-4 w-4 animate-spin text-[var(--primary)]" />
                <span className="text-sm text-[var(--muted-foreground)]">Thinking…</span>
              </div>
            </div>
          )}
        </div>
        <div ref={bottomRef} />
      </div>
      <form
        onSubmit={handleSubmit}
        className="border-t border-[var(--border)] bg-white/90 px-4 py-3 backdrop-blur"
      >
        <div className="mx-auto flex max-w-2xl gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about this paper…"
            disabled={loading}
            className="flex-1"
          />
          <Button type="submit" disabled={loading || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </form>
    </div>
  );
}
