"use client";

import { useEffect, useState } from "react";
import { Copy, Loader2 } from "lucide-react";
import { getSummary, getPaperStatus } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { cleanMarkdown } from "@/lib/utils";
import { toast } from "sonner";

function truncateBySentences(text: string, count: number): string {
  const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
  return sentences.slice(0, count).join(" ").trim() || text;
}

export function SummaryTabs({ paperId }: { paperId: string }) {
  const [summary, setSummary] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadSummary = async () => {
      setLoading(true);
      setError(null);

      try {
        // First check if paper is ready
        const status = await getPaperStatus(paperId);

        if (status.status === "processing") {
          // Paper is still processing, show processing state
          if (!cancelled) {
            setProcessing(true);
            setError("Paper is still being processed. Please wait...");
          }
          setLoading(false);
          return;
        }

        // Paper is ready, fetch summary
        setProcessing(false);
        const res = await getSummary(paperId);
        if (!cancelled) setSummary(res.summary);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load summary");
          setProcessing(false);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    loadSummary();
    return () => { cancelled = true; };
  }, [paperId]);

  const handleCopy = () => {
    if (!summary) return;
    navigator.clipboard.writeText(summary);
    toast.success("Summary copied to clipboard.");
  };

  if (processing) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8">
        <Loader2 className="h-8 w-8 animate-spin text-neutral-400" />
        <p className="text-sm text-neutral-600">Paper is still being processed...</p>
        <p className="text-xs text-neutral-500">This typically takes 1-2 minutes after upload.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-neutral-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8">
        <p className="text-sm text-red-600">{error}</p>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="flex flex-1 items-center justify-center p-8 text-sm text-neutral-500">
        No summary available.
      </div>
    );
  }

  const short = truncateBySentences(summary, 2);
  const medium = truncateBySentences(summary, 4);
  const isShortTruncated = short.length < summary.length;
  const isMediumTruncated = medium.length < summary.length;

  return (
    <div className="flex flex-1 flex-col gap-4 p-6">
      <div className="flex items-center justify-between gap-4">
        <Tabs defaultValue="detailed" className="flex-1">
          <TabsList className="w-fit">
            <TabsTrigger value="short">
              Short {isShortTruncated && "(UI truncated)"}
            </TabsTrigger>
            <TabsTrigger value="medium">
              Medium {isMediumTruncated && "(UI truncated)"}
            </TabsTrigger>
            <TabsTrigger value="detailed">Detailed</TabsTrigger>
          </TabsList>
          <div className="mt-4">
            <TabsContent value="short">
              <Card className="prose prose-sm max-w-none">
                <p className="whitespace-pre-wrap text-neutral-700">{cleanMarkdown(short)}</p>
              </Card>
            </TabsContent>
            <TabsContent value="medium">
              <Card className="prose prose-sm max-w-none">
                <p className="whitespace-pre-wrap text-neutral-700">{cleanMarkdown(medium)}</p>
              </Card>
            </TabsContent>
            <TabsContent value="detailed">
              <Card className="prose prose-sm max-w-none">
                <p className="whitespace-pre-wrap text-neutral-700">{cleanMarkdown(summary)}</p>
              </Card>
            </TabsContent>
          </div>
        </Tabs>
        <Button variant="ghost" size="sm" className="shrink-0 gap-2" onClick={handleCopy}>
          <Copy className="h-4 w-4" />
          Copy
        </Button>
      </div>
    </div>
  );
}
