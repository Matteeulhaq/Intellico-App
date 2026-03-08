"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, MessageSquare } from "lucide-react";
import { askQuestion } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { cleanMarkdown } from "@/lib/utils";
import { useStore } from "@/lib/store";
import type { ChatMessage } from "@/types";
import { toast } from "sonner";

export function ChatPanel({ paperId }: { paperId: string }) {
  const getPaper = useStore((s) => s.getPaper);
  const addChatMessage = useStore((s) => s.addChatMessage);
  const paper = getPaper(paperId);

  const [messages, setMessages] = useState<ChatMessage[]>(paper?.chatHistory || []);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load chat history from store when paperId changes
  useEffect(() => {
    setMessages(paper?.chatHistory || []);
  }, [paperId, paper]);

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
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    addChatMessage(paperId, userMsg);
    setLoading(true);
    try {
      const res = await askQuestion(paperId, q);
      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: res.answer,
        numChunks: res.num_chunks_used,
      };
      const finalMessages = [...newMessages, assistantMsg];
      setMessages(finalMessages);
      addChatMessage(paperId, assistantMsg);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to get answer.");
      setMessages(messages);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <MessageSquare className="h-12 w-12 text-neutral-300" />
            <p className="mt-4 text-sm text-neutral-600">
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
                    ? "bg-neutral-900 text-white"
                    : "bg-neutral-100 text-neutral-900"
                }`}
              >
                <p className="whitespace-pre-wrap text-sm">
                  {msg.role === "assistant" ? cleanMarkdown(msg.content) : msg.content}
                </p>
                {msg.role === "assistant" && msg.numChunks != null && (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-xs text-neutral-500">
                      Sources
                    </summary>
                    <p className="mt-1 text-xs text-neutral-500">
                      Grounded in uploaded paper via RAG ({msg.numChunks} chunks used)
                    </p>
                  </details>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-2xl bg-neutral-100 px-4 py-3">
                <Loader2 className="h-4 w-4 animate-spin text-neutral-500" />
                <span className="text-sm text-neutral-500">Thinking…</span>
              </div>
            </div>
          )}
        </div>
        <div ref={bottomRef} />
      </div>
      <form onSubmit={handleSubmit} className="border-t border-neutral-200 bg-white p-4">
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
